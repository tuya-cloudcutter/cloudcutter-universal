#  Copyright (c) Kuba Szczodrzyński 2024-3-22.

import asyncio
import ssl
from ipaddress import IPv4Address
from pathlib import Path

from cloudcutter.core import Cloudcutter
from cloudcutter.modules.base import ModuleBase
from cloudcutter.types import Ip4Config, NetworkInterface, WifiNetwork

from ._data import TuyaServerData
from ._types import Device
from .device import DeviceCore
from .dns import DnsCore
from .gateway import GatewayCore
from .ota import OtaCore


class TuyaServer(
    OtaCore,
    # MqttCore,
    GatewayCore,
    DnsCore,
    DeviceCore,
    TuyaServerData,
    ModuleBase,
):
    def __init__(
        self,
        core: Cloudcutter,
        interface: NetworkInterface,
        network: WifiNetwork,
    ):
        super().__init__()
        self.core = core
        self.interface = interface
        self.network = network
        self.schema_path = Path(__file__).parents[3] / "schema"

    @staticmethod
    def add_device(
        uuid: str,
        auth_key: str,
        psk: str,
        firmware_path: Path = None,
    ) -> None:
        TuyaServer.DEVICES.append(
            Device(
                uuid=uuid,
                auth_key=auth_key.encode(),
                psk=psk.encode(),
                firmware_path=firmware_path,
            )
        )

    async def run(self) -> None:
        ip_address = IPv4Address("10.42.42.1")
        ip_netmask = IPv4Address("255.255.255.0")
        ip_dhcp_start = IPv4Address("10.42.42.10")
        ip_dhcp_end = IPv4Address("10.42.42.40")

        self.ipconfig = Ip4Config(
            address=ip_address,
            netmask=ip_netmask,
            gateway=None,
        )
        self.upgraded_devices = set()

        await self.core.wifi.start_access_point(
            interface=self.interface,
            network=self.network,
        )

        if self.ipconfig not in (await self.core.network.get_ip4config(self.interface)):
            await self.core.network.set_ip4config(
                interface=self.interface,
                ipconfig=self.ipconfig,
            )

        self.core.dhcp.configure(
            ipconfig=self.ipconfig,
            ip_range=(ip_dhcp_start, ip_dhcp_end),
            dns=self.ipconfig.address,
        )
        await self.core.dhcp.start()

        self.core.dns.add_record("h2.iot-dns.com", "A", self.ipconfig.address)
        self.core.dns.add_record("h3.iot-dns.com", "A", self.ipconfig.address)
        self.core.dns.add_record("fakedns.com", "A", self.ipconfig.address)
        self.core.dns.add_record("cloudcutter.io", "A", self.ipconfig.address)
        regions = ["us", "eu", "cn", "in"]
        hosts = ["a", "a1", "a2", "a3", "m", "m1", "m2", "baal"]
        for region in regions:
            for host in hosts:
                self.core.dns.add_record(
                    host=f"{host}.tuya{region}.com",
                    type="A",
                    answer=self.ipconfig.address,
                )
        await self.core.dns.start()

        self.core.http.configure(
            address=self.ipconfig.address,
            https_protocol=ssl.PROTOCOL_TLSv1_2,
            https_ciphers="PSK-AES128-CBC-SHA256",
            https_psk_hint=b"1dHRsc2NjbHltbGx3eWh5" + (b"0" * 16),
        )
        self.core.http.add_ssl_cert(cert="cert.pem", key="key.pem")
        self.core.http.add_ssl_psk(self.calc_psk_openssl, identity=b"0x[0-9A-Fa-f]+")
        self.core.http.add_ssl_psk(self.calc_psk_v1, identity=b"\x01.+")
        self.core.http.add_ssl_psk(self.calc_psk_v2, identity=b"\x02.+")
        self.core.http.add_handlers(self)
        await self.core.http.start()

        self.core.mqtt.configure(
            address=self.ipconfig.address,
        )
        await self.core.mqtt.add_handlers(self)
        await self.core.mqtt.start()

        while True:
            await asyncio.sleep(10)

    async def cleanup(self) -> None:
        await super().cleanup()

        self.core.mqtt.clear_handlers()
        self.core.http.clear_handlers()
        self.core.http.clear_ssl_psk()
        self.core.http.clear_ssl_certs()
        self.core.dns.clear_records()
        await self.core.wifi.stop_access_point(self.interface)

        await self.core.mqtt.stop()
        await self.core.http.stop()
        await self.core.dns.stop()
        await self.core.dhcp.stop()

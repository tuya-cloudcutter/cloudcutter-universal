#  Copyright (c) Kuba Szczodrzyński 2023-11-10.

import json
from base64 import b64decode, b64encode
from binascii import crc32
from hashlib import md5
from time import time

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from ltchiptool.util.intbin import inttobe32

from cloudcutter.modules import mqtt as mqttm
from cloudcutter.modules.base import ModuleBase

from ._data import TuyaServerData
from ._events import TuyaDeviceDataEvent, TuyaDeviceLogEvent
from ._types import Device
from .device import DeviceCore


class MqttCore(DeviceCore, TuyaServerData, ModuleBase):
    def _decrypt_mqtt(
        self,
        topic: str,
        data: bytes,
    ) -> tuple[Device, dict]:
        uuid = topic.rpartition("/")[2]
        device = self.get_device(uuid=uuid)

        cleartext = False
        match data[0:3]:
            case b"2.1":
                data = b64decode(data[19:])
            case b"2.2":
                data = data[15:]
            case _:
                cleartext = True

        if not cleartext:
            aes = AES.new(key=device.auth_key[:16], mode=AES.MODE_ECB)
            data = aes.decrypt(data)
            data = unpad(data, block_size=16)

        obj = json.loads(data)
        self.debug(f"MQTT received body: {obj}")
        return device, obj

    def _encrypt_mqtt(
        self,
        device: Device,
        data: dict,
        protocol: str = "2.2",
    ) -> tuple[str, bytes]:
        obj = {**data, "t": int(time())}
        self.debug(f"MQTT sending body: {obj}")
        data = json.dumps(obj, separators=(",", ":")).encode()

        aes = AES.new(key=device.auth_key[:16], mode=AES.MODE_ECB)
        data = pad(data, block_size=16)
        data = aes.encrypt(data)

        match protocol:
            case "2.1":
                data = b64encode(data)
                signature = md5()
                signature.update(b"data=")
                signature.update(data)
                signature.update(f"||pv={protocol}||".encode())
                signature.update(device.auth_key[:16])
                sign = signature.hexdigest()[8:24].encode()
                data = protocol.encode() + sign + data
            case "2.2":
                timestamp = b"%08d" % (int(time() * 100) % 100_000_000)
                data = timestamp + data
                sign = inttobe32(crc32(data))
                data = protocol.encode() + sign + data
            case _:
                pass

        topic = f"smart/device/in/{device.uuid}"
        return topic, data

    @mqttm.subscribe("log/+/+")
    async def on_device_log(self, topic: str, message: bytes) -> None:
        uuid = topic.rpartition("/")[2]
        device = self.get_device(uuid=uuid)
        TuyaDeviceLogEvent(device, message.decode()).broadcast()

    @mqttm.subscribe("smart/device/out/+")
    async def on_device_data(self, topic: str, message: bytes) -> None:
        device, data = self._decrypt_mqtt(topic, message)
        TuyaDeviceDataEvent(device, data).broadcast()

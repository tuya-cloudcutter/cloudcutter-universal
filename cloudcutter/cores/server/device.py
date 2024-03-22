#  Copyright (c) Kuba Szczodrzyński 2023-11-10.

from cloudcutter.modules.base import ModuleBase
from cloudcutter.modules.http import Request

from ._data import TuyaServerData
from ._types import Device


class DeviceCore(TuyaServerData, ModuleBase):
    def get_device(
        self,
        uuid: str = None,
        psk_id: bytes = None,
        request: Request = None,
    ) -> Device:
        if request:
            uuid = request.query.get("uuid", None) or request.query.get("devid", None)
        device = None
        for device in self.dev_db:
            if device.uuid == uuid or device.psk_id == psk_id:
                break
        else:
            raise ValueError(f"Device by ID {uuid or psk_id} not found")
        if request:
            device.encryption_type = int(request.query.get("et", 0))
            if "uuid" in request.query:
                device.aes_key = device.auth_key
            elif "devid" in request.query:
                device.aes_key = device.auth_key[:16]
        return device

    def calc_psk_openssl(self, identity: bytes) -> bytes:
        identity = identity.decode()[2:]
        self.info(f"OpenSSL connection: {identity}")
        if identity[0:2] == "01":
            return self.calc_psk_v1(bytes.fromhex(identity))
        if identity[0:2] == "02":
            return self.calc_psk_v2(bytes.fromhex(identity))

    def calc_psk_v1(self, identity: bytes) -> bytes:
        # assert len(identity) == 50
        return b""

    def calc_psk_v2(self, identity: bytes) -> bytes:
        assert len(identity) == 49
        return self.get_device(psk_id=identity[17:49]).psk

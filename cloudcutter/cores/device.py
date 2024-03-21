#  Copyright (c) Kuba Szczodrzyński 2023-11-10.

from abc import ABC
from dataclasses import dataclass
from hashlib import sha256

from cloudcutter.modules.base import ModuleBase
from cloudcutter.modules.http import Request


@dataclass
class Device:
    uuid: str
    auth_key: bytes
    psk: bytes
    psk_id: bytes = None
    encryption_type: int = None
    aes_key: bytes = None

    def __post_init__(self) -> None:
        self.psk_id = sha256(self.uuid.encode()).digest()

    @property
    def active_key(self) -> str:
        # secKey, localKey, etc.
        return self.auth_key[:16].decode()


class DeviceCore(ModuleBase, ABC):
    dev_db: list[Device]

    def __init__(self):
        super().__init__()
        self.dev_db = []

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
        raise NotImplementedError()

    def calc_psk_v2(self, identity: bytes) -> bytes:
        assert len(identity) == 49
        return self.get_device(psk_id=identity[17:49]).psk

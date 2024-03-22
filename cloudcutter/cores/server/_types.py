#  Copyright (c) Kuba Szczodrzyński 2023-11-10.

from dataclasses import dataclass
from hashlib import sha256
from ipaddress import IPv4Address
from pathlib import Path


@dataclass
class Device:
    uuid: str
    auth_key: bytes
    psk: bytes
    psk_id: bytes = None
    encryption_type: int = None
    aes_key: bytes = None
    firmware_path: Path = None
    address: IPv4Address = None

    def __post_init__(self) -> None:
        self.psk_id = sha256(self.uuid.encode()).digest()

    @property
    def active_key(self) -> str:
        # secKey, localKey, etc.
        return self.auth_key[:16].decode()

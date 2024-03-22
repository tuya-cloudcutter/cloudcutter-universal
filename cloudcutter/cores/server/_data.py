#  Copyright (c) Kuba Szczodrzyński 2024-3-22.

from pathlib import Path

from cloudcutter.core import Cloudcutter
from cloudcutter.types import Ip4Config, NetworkInterface

from ._types import Device


class TuyaServerData:
    core: Cloudcutter
    interface: NetworkInterface
    dev_db: list[Device]
    schema_path: Path

    ipconfig: Ip4Config = None
    upgraded_devices: set[str] = None

#  Copyright (c) Kuba Szczodrzyński 2024-3-23.

from dataclasses import dataclass

from cloudcutter.modules.base import BaseEvent
from cloudcutter.types import WifiNetwork


@dataclass
class CoreTuyaServerStartCommand(BaseEvent):
    network: WifiNetwork


@dataclass
class CoreTuyaApCfgConnectCommand(BaseEvent):
    network: WifiNetwork
    target_network: WifiNetwork | None = None


@dataclass
class CoreTuyaApCfgExploitCommand(BaseEvent):
    profile: dict[str, str | int]
    uuid: str
    auth_key: str
    psk: str
    target_network: WifiNetwork | None = None

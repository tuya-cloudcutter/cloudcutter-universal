#  Copyright (c) Kuba Szczodrzyński 2024-3-23.

from dataclasses import dataclass
from ipaddress import IPv4Address

from cloudcutter.modules.base import BaseEvent
from cloudcutter.types import Ip4Config, WifiNetwork


@dataclass
class TuyaApCfgFoundEvent(BaseEvent):
    network: WifiNetwork


@dataclass
class TuyaApCfgConnectedEvent(BaseEvent):
    network: WifiNetwork
    ipconfig: Ip4Config


@dataclass
class TuyaApCfgReadyEvent(BaseEvent):
    network: WifiNetwork
    address: IPv4Address
    ping_rtt: float


@dataclass
class TuyaApCfgSentEvent(BaseEvent):
    network: WifiNetwork
    address: IPv4Address
    port: int


@dataclass
class TuyaApCfgFinishedEvent(BaseEvent):
    network: WifiNetwork
    address: IPv4Address

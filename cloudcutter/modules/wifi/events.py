#  Copyright (c) Kuba Szczodrzyński 2023-9-9.

from dataclasses import dataclass

from cloudcutter.modules.base import BaseEvent
from cloudcutter.types import WifiNetwork


@dataclass
class WifiRawEvent(BaseEvent):
    code: str
    data: object


@dataclass
class WifiScanCompleteEvent(BaseEvent):
    networks: list[WifiNetwork]


@dataclass
class WifiConnectedEvent(BaseEvent):
    ssid: str


@dataclass
class WifiDisconnectedEvent(BaseEvent):
    ssid: str


@dataclass
class WifiAPStartedEvent(BaseEvent):
    pass


@dataclass
class WifiAPStoppedEvent(BaseEvent):
    pass

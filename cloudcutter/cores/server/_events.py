#  Copyright (c) Kuba Szczodrzyński 2024-3-22.

from dataclasses import dataclass
from enum import IntEnum
from ipaddress import IPv4Address
from pathlib import Path

from cloudcutter.modules.base import BaseEvent

from ._types import Device


@dataclass
class TuyaUrlConfigEvent(BaseEvent):
    address: IPv4Address


@dataclass
class TuyaDeviceActiveEvent(BaseEvent):
    device: Device
    data: dict


@dataclass
class TuyaDeviceRequestEvent(BaseEvent):
    device: Device
    action: str
    data: dict


@dataclass
class TuyaDeviceLogEvent(BaseEvent):
    device: Device
    message: str


@dataclass
class TuyaDeviceDataEvent(BaseEvent):
    device: Device
    data: dict


@dataclass
class TuyaUpgradeSkipEvent(BaseEvent):
    device: Device
    reason: "Reason"

    class Reason(IntEnum):
        ALREADY_UPGRADED = 0
        NO_FIRMWARE_SET = 1


@dataclass
class TuyaUpgradeTriggerEvent(BaseEvent):
    device: Device
    action: str


@dataclass
class TuyaUpgradeInfoEvent(BaseEvent):
    device: Device
    action: str
    firmware_path: Path
    firmware_url: str


@dataclass
class TuyaUpgradeStatusEvent(BaseEvent):
    device: Device
    status: int


@dataclass
class TuyaUpgradeProgressEvent(BaseEvent):
    device: Device
    progress: int


@dataclass
class TuyaUpgradeDownloadEvent(BaseEvent):
    device: Device
    firmware_path: Path

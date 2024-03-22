#  Copyright (c) Kuba Szczodrzyński 2024-3-22.

from dataclasses import dataclass
from ipaddress import IPv4Address

from amqtt.session import ApplicationMessage

from cloudcutter.modules.base import BaseEvent


@dataclass
class MqttMessageEvent(BaseEvent):
    message: ApplicationMessage


@dataclass
class MqttClientConnectedEvent(BaseEvent):
    client_id: str
    address: IPv4Address


@dataclass
class MqttClientDisconnectedEvent(BaseEvent):
    client_id: str
    address: IPv4Address


@dataclass
class MqttClientSubscriptionAddEvent(BaseEvent):
    client_id: str
    address: IPv4Address
    topic: str


@dataclass
class MqttClientSubscriptionDelEvent(BaseEvent):
    client_id: str
    address: IPv4Address
    topic: str

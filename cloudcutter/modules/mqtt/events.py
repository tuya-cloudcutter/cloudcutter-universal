#  Copyright (c) Kuba Szczodrzyński 2024-3-22.

from dataclasses import dataclass

from amqtt.session import ApplicationMessage

from cloudcutter.modules.base import BaseEvent


@dataclass
class MqttMessageEvent(BaseEvent):
    message: ApplicationMessage

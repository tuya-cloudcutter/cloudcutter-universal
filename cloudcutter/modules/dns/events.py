#  Copyright (c) Kuba Szczodrzyński 2023-9-11.

from dataclasses import dataclass

from cloudcutter.modules.base import BaseEvent


@dataclass
class DnsQueryEvent(BaseEvent):
    host: str
    type: str

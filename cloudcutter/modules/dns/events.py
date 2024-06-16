#  Copyright (c) Kuba Szczodrzyński 2023-9-11.

from dataclasses import dataclass

from dnslib import RR

from cloudcutter.modules.base import BaseEvent


@dataclass
class DnsQueryEvent(BaseEvent):
    qname: str
    qtype: str
    rdata: list[str | RR]

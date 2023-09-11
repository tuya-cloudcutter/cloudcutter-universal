#  Copyright (c) Kuba Szczodrzyński 2023-9-11.

from dataclasses import dataclass
from ipaddress import IPv4Address

from macaddress import MAC

from cloudcutter.modules.base import BaseEvent


@dataclass
class DhcpLeaseEvent(BaseEvent):
    client: MAC
    address: IPv4Address
    host_name: str | None
    vendor_cid: str | None

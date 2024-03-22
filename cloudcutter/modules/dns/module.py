#  Copyright (c) Kuba Szczodrzyński 2023-9-11.

from ipaddress import IPv4Address

from dnserver import DNSServer
from dnserver.load_records import RecordType, Zone

from cloudcutter.modules.base import ModuleBase

from .events import DnsQueryEvent


class DnsModule(ModuleBase):
    def __init__(self):
        super().__init__()
        self.dns = DNSServer(
            records=None,
            port=53,
            upstream=None,
        )

    async def start(self) -> None:
        # noinspection PyProtectedMember
        from dnserver.main import handler, logger

        # intercept dnserver logging messages
        logger.info = self.on_message
        logger.removeHandler(handler)
        # start the server
        self.info(f"Starting DNS server on 0.0.0.0:{self.dns.port}")
        self.dns.start()
        # disable dnslib logging
        self.dns.tcp_server.server.logger.logf = lambda *_: None
        self.dns.udp_server.server.logger.logf = lambda *_: None

    async def stop(self) -> None:
        if self.dns.udp_server and self.dns.tcp_server:
            self.dns.stop()

    def on_message(self, msg: str, *args) -> None:
        if "no local zone found" in msg:
            self.warning(f"No DNS zone for {args[1]} {args[0]}")
            DnsQueryEvent(host=str(args[0]), type=args[1]).broadcast()
        elif "found zone for" in msg:
            self.info(f"Answering DNS request {args[1]} {args[0]}")
            DnsQueryEvent(host=str(args[0]), type=args[1]).broadcast()

    def add_record(
        self,
        host: str,
        type: RecordType,
        answer: str | IPv4Address,
    ) -> None:
        if isinstance(answer, IPv4Address):
            answer = str(answer)
        self.dns.add_record(Zone(host, type, answer))

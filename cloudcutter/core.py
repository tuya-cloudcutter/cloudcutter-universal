#  Copyright (c) Kuba Szczodrzyński 2024-3-22.

from logging import DEBUG

from ltchiptool.util.logging import LoggingHandler

from .modules.base import BaseEvent, ModuleBase, subscribe
from .modules.dhcp import DhcpModule
from .modules.dns import DnsModule
from .modules.http import HttpModule
from .modules.mqtt import MqttModule
from .modules.network import NetworkModule
from .modules.wifi import WifiModule


class Cloudcutter(ModuleBase):
    network: NetworkModule
    wifi: WifiModule
    dhcp: DhcpModule
    dns: DnsModule
    http: HttpModule
    mqtt: MqttModule

    def __init__(self):
        super().__init__()
        self.network = NetworkModule()
        self.wifi = WifiModule()
        self.dhcp = DhcpModule()
        self.dns = DnsModule()
        self.http = HttpModule()
        self.mqtt = MqttModule()

        logger = LoggingHandler.get()
        logger.level = DEBUG

    async def run(self) -> None:
        await self.network.start()
        await self.wifi.start()
        await super().run()

    async def cleanup(self) -> None:
        await super().cleanup()
        await self.wifi.stop()
        await self.network.stop()

    @subscribe(BaseEvent)
    async def on_event(self, event) -> None:
        self.debug(f"EVENT: {event}")

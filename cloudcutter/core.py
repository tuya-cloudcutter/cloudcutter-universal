#  Copyright (c) Kuba Szczodrzyński 2024-3-22.

from .events import (
    CoreTuyaApCfgConnectCommand,
    CoreTuyaApCfgExploitCommand,
    CoreTuyaServerStartCommand,
)
from .modules.base import BaseEvent, ModuleBase, subscribe
from .modules.dhcp import DhcpModule
from .modules.dns import DnsModule
from .modules.http import HttpModule
from .modules.mqtt import MqttModule
from .modules.network import NetworkModule
from .modules.wifi import WifiModule
from .types import NetworkInterface, WifiNetwork

CLOUDCUTTER_FLASH = WifiNetwork(ssid="cloudcutterflash", password=b"abcdabcd")


class Cloudcutter(ModuleBase):
    network: NetworkModule
    wifi: WifiModule
    dhcp: DhcpModule
    dns: DnsModule
    http: HttpModule
    mqtt: MqttModule

    tuya_server: ModuleBase | None = None
    tuya_ap_cfg: ModuleBase | None = None

    def __init__(self):
        super().__init__()
        self.network = NetworkModule()
        self.wifi = WifiModule()
        self.dhcp = DhcpModule()
        self.dns = DnsModule()
        self.http = HttpModule()
        self.mqtt = MqttModule()

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
        self.info(f"EVENT: {event}")

    @subscribe(CoreTuyaServerStartCommand)
    async def on_tuya_server_start_command(
        self,
        event: CoreTuyaServerStartCommand,
    ) -> None:
        from .cores.server import TuyaServer

        interface = await self.network.get_interface(NetworkInterface.Type.WIRELESS_AP)
        self.tuya_server = TuyaServer(
            core=self,
            interface=interface,
            network=event.network,
        )
        await self.tuya_server.start()

    @subscribe(CoreTuyaApCfgConnectCommand)
    async def on_tuya_ap_cfg_connect_command(
        self,
        event: CoreTuyaApCfgConnectCommand,
    ) -> None:
        if self.tuya_ap_cfg:
            await self.tuya_ap_cfg.stop()
            self.tuya_ap_cfg = None

        from .cores.apcfg import TuyaApCfg

        interface = await self.network.get_interface(NetworkInterface.Type.WIRELESS_STA)
        self.tuya_ap_cfg = ap_cfg = TuyaApCfg(
            core=self,
            interface=interface,
            target_network=event.target_network,
        )
        ap_cfg.set_wifi_network(network=event.network)
        await self.tuya_ap_cfg.start()

    @subscribe(CoreTuyaApCfgExploitCommand)
    async def on_tuya_ap_cfg_exploit_command(
        self,
        event: CoreTuyaApCfgExploitCommand,
    ) -> None:
        if self.tuya_ap_cfg:
            await self.tuya_ap_cfg.stop()
            self.tuya_ap_cfg = None

        from .cores.apcfg import TuyaApCfg

        interface = await self.network.get_interface(NetworkInterface.Type.WIRELESS_STA)
        self.tuya_ap_cfg = ap_cfg = TuyaApCfg(
            core=self,
            interface=interface,
            target_network=event.target_network,
        )
        ap_cfg.set_classic_profile(
            data=event.profile,
            uuid=event.uuid,
            auth_key=event.auth_key,
            psk=event.psk,
        )
        await self.tuya_ap_cfg.start()

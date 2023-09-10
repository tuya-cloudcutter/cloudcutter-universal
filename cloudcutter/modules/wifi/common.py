#  Copyright (c) Kuba Szczodrzyński 2023-9-9.

from cloudcutter.modules.base import ModuleBase
from cloudcutter.types import NetworkInterface, WifiNetwork


class WifiCommon(ModuleBase):
    async def scan_networks(
        self,
        interface: NetworkInterface,
    ) -> list[WifiNetwork]:
        raise NotImplementedError()

    async def start_station(
        self,
        interface: NetworkInterface,
        network: WifiNetwork,
    ) -> None:
        raise NotImplementedError()

    async def stop_station(
        self,
        interface: NetworkInterface,
    ) -> None:
        raise NotImplementedError()

    async def get_station_state(
        self,
        interface: NetworkInterface,
    ) -> WifiNetwork | None:
        raise NotImplementedError()

    async def start_access_point(
        self,
        interface: NetworkInterface,
        network: WifiNetwork,
    ) -> None:
        raise NotImplementedError()

    async def stop_access_point(
        self,
        interface: NetworkInterface,
    ) -> None:
        raise NotImplementedError()

    async def get_access_point_state(
        self,
        interface: NetworkInterface,
    ) -> bool:
        raise NotImplementedError()

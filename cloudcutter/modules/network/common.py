#  Copyright (c) Kuba Szczodrzyński 2023-9-9.

from ipaddress import IPv4Address

import ifaddr

from cloudcutter.modules.base import ModuleBase, module_thread
from cloudcutter.types import Ip4Config, NetworkInterface


class NetworkCommon(ModuleBase):
    @module_thread
    async def list_interfaces(self) -> list[NetworkInterface]:
        interfaces = []
        for adapter in ifaddr.get_adapters():
            title = adapter.nice_name
            if adapter.ips:
                nice_name = adapter.ips[0].nice_name
                if nice_name != adapter.nice_name:
                    title = f"{nice_name} ({adapter.nice_name})"
            interfaces.append(
                NetworkInterface(
                    name=adapter.name,
                    title=title,
                    type=NetworkInterface.Type.WIRED,
                    obj=None,
                )
            )
        await self._fill_interfaces(interfaces)
        return interfaces

    async def _fill_interfaces(self, interfaces: list[NetworkInterface]) -> None:
        raise NotImplementedError()

    @module_thread
    async def get_ip4config(
        self,
        interface: NetworkInterface,
    ) -> list[Ip4Config]:
        ipconfig = []
        for adapter in ifaddr.get_adapters():
            if adapter.name != interface.name:
                continue
            for ip in adapter.ips:
                if not ip.is_IPv4:
                    continue
                netmask_int = int(f"{(1 << ip.network_prefix) - 1:032b}"[::-1], 2)
                ipconfig.append(
                    Ip4Config(
                        address=IPv4Address(ip.ip),
                        netmask=IPv4Address(netmask_int),
                        gateway=None,
                    )
                )
        return ipconfig

    async def set_ip4config(
        self,
        interface: NetworkInterface,
        ipconfig: Ip4Config,
    ) -> None:
        raise NotImplementedError()

    async def get_interface(
        self,
        interface_type: NetworkInterface.Type,
    ) -> NetworkInterface | None:
        interfaces = await self.list_interfaces()
        try:
            return next(i for i in interfaces if i.type == interface_type)
        except StopIteration:
            return None

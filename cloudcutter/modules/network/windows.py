#  Copyright (c) Kuba Szczodrzyński 2023-9-9.

from win32wifi import Win32NativeWifiApi, Win32Wifi

from cloudcutter.modules.base import module_thread
from cloudcutter.types import Ip4Config, NetworkInterface
from cloudcutter.utils.windows import iphlpapi, wlanapi

from .common import NetworkCommon

IFACE_BLACKLIST = [
    "VMware",
    "VirtualBox",
    "ISATAP",
    "Loopback",
    "Wintun",
    "Bluetooth",
]


class NetworkWindows(NetworkCommon):
    async def _fill_interfaces(self, interfaces: list[NetworkInterface]) -> None:
        # remove known virtual interfaces
        for interface in list(interfaces):
            if any(s in interface.title for s in IFACE_BLACKLIST):
                interfaces.remove(interface)
        # mark Wi-Fi Station interfaces
        for iface in Win32Wifi.getWirelessInterfaces():
            for interface in interfaces:
                if interface.name == iface.guid_string:
                    interface.type = NetworkInterface.Type.WIRELESS_STA
        # mark Wi-Fi Access Point interfaces
        handle = Win32NativeWifiApi.WlanOpenHandle()
        status = wlanapi.WlanHostedNetworkQueryStatus(handle)
        for interface in interfaces:
            if interface.name == str(status.contents.IPDeviceID):
                interface.type = NetworkInterface.Type.WIRELESS_AP
        Win32NativeWifiApi.WlanCloseHandle(handle)

    @module_thread
    async def set_ip4config(
        self,
        interface: NetworkInterface,
        ipconfig: Ip4Config | None,
    ) -> None:
        index = 0
        for i in range(1, iphlpapi.GetNumberOfInterfaces() + 1):
            if_row = iphlpapi.GetIfEntry(i)
            if interface.name not in if_row.wszName:
                continue
            index = i
            break
        if not index:
            raise Exception("Interface not found")

        if not ipconfig:
            self.command(
                "netsh",
                "interface",
                "ipv4",
                "set",
                "address",
                f"name={index}",
                "source=dhcp",
                "store=active",
            )
            return

        self.command(
            "netsh",
            "interface",
            "ipv4",
            "set",
            "address",
            f"name={index}",
            "source=static",
            f"address={ipconfig.address}",
            f"mask={ipconfig.netmask}",
            f"gateway={ipconfig.gateway}".lower(),
            "store=active",
        )

#  Copyright (c) Kuba Szczodrzyński 2023-9-9.

from ctypes import POINTER, Structure, byref, c_uint, c_void_p, pointer
from ctypes.wintypes import DWORD, HANDLE, PDWORD, ULONG

from comtypes import GUID
from win32wifi import Win32NativeWifiApi
from win32wifi.Win32NativeWifiApi import DOT11_MAC_ADDRESS, DOT11_PHY_TYPE
from winerror import ERROR_SUCCESS

WLAN_HOSTED_NETWORK_STATE = c_uint
WLAN_HOSTED_NETWORK_STATE_DICT = {
    0: "wlan_hosted_network_unavailable",
    1: "wlan_hosted_network_idle",
    2: "wlan_hosted_network_active",
}

WLAN_HOSTED_NETWORK_PEER_AUTH_STATE = c_uint
WLAN_HOSTED_NETWORK_PEER_AUTH_STATE_DICT = {
    0: "wlan_hosted_network_peer_state_invalid",
    1: "wlan_hosted_network_peer_state_authenticated",
}


# noinspection PyPep8Naming
class WLAN_HOSTED_NETWORK_PEER_STATE(Structure):
    _fields_ = [
        ("PeerMacAddress", DOT11_MAC_ADDRESS),
        ("PeerAuthState", WLAN_HOSTED_NETWORK_PEER_AUTH_STATE),
    ]


# noinspection PyPep8Naming
class WLAN_HOSTED_NETWORK_STATUS(Structure):
    _fields_ = [
        ("HostedNetworkState", WLAN_HOSTED_NETWORK_STATE),
        ("IPDeviceID", GUID),
        ("wlanHostedNetworkBssid", DOT11_MAC_ADDRESS),
        ("dot11PhyType", DOT11_PHY_TYPE),
        ("ulChannelFrequency", ULONG),
        ("dwNumberOfPeers", DWORD),
        ("PeerList", WLAN_HOSTED_NETWORK_PEER_STATE * 0),
    ]
    HostedNetworkState: WLAN_HOSTED_NETWORK_STATE
    IPDeviceID: GUID
    wlanHostedNetworkBssid: DOT11_MAC_ADDRESS
    dot11PhyType: DOT11_PHY_TYPE
    ulChannelFrequency: ULONG
    dwNumberOfPeers: DWORD
    PeerList: WLAN_HOSTED_NETWORK_PEER_STATE * 0


# noinspection PyPep8Naming
def WlanHostedNetworkQueryStatus(hClientHandle):
    func_ref = Win32NativeWifiApi.wlanapi.WlanHostedNetworkQueryStatus
    func_ref.argtypes = [
        HANDLE,
        POINTER(POINTER(WLAN_HOSTED_NETWORK_STATUS)),
        c_void_p,
    ]
    func_ref.restype = DWORD
    wlan_hosted_network_status = pointer(WLAN_HOSTED_NETWORK_STATUS())
    result = func_ref(hClientHandle, byref(wlan_hosted_network_status), None)
    if result != ERROR_SUCCESS:
        raise Exception(f"WlanEnumInterfaces failed ({result})")
    return wlan_hosted_network_status


# noinspection PyPep8Naming,DuplicatedCode
def WlanHostedNetworkStartUsing(hClientHandle):
    func_ref = Win32NativeWifiApi.wlanapi.WlanHostedNetworkStartUsing
    func_ref.argtypes = [
        HANDLE,
        PDWORD,
        c_void_p,
    ]
    func_ref.restype = DWORD
    fail_reason = DWORD()
    result = func_ref(hClientHandle, byref(fail_reason), None)
    if result != ERROR_SUCCESS:
        raise Exception(
            f"WlanHostedNetworkStartUsing failed ({result} - {fail_reason.value})"
        )


# noinspection PyPep8Naming,DuplicatedCode
def WlanHostedNetworkStopUsing(hClientHandle):
    func_ref = Win32NativeWifiApi.wlanapi.WlanHostedNetworkStopUsing
    func_ref.argtypes = [
        HANDLE,
        PDWORD,
        c_void_p,
    ]
    func_ref.restype = DWORD
    fail_reason = DWORD()
    result = func_ref(hClientHandle, byref(fail_reason), None)
    if result != ERROR_SUCCESS:
        raise Exception(
            f"WlanHostedNetworkStopUsing failed ({result} - {fail_reason.value})"
        )

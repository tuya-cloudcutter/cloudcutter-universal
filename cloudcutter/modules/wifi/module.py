#  Copyright (c) Kuba Szczodrzyński 2023-9-9.

from abc import ABC

from cloudcutter.modules.base import ModuleBase

from .common import WifiCommon

ModuleImpl = None
if ModuleBase.is_windows():
    from .windows import WifiWindows

    ModuleImpl = WifiWindows


class WifiModule(ModuleImpl, WifiCommon, ABC):
    pass

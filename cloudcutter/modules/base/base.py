#  Copyright (c) Kuba Szczodrzyński 2023-9-8.

import os
import sys
from subprocess import PIPE, Popen

from .event import EventMixin


class ModuleBase(EventMixin):
    @staticmethod
    def is_windows() -> bool:
        return os.name == "nt"

    @staticmethod
    def is_linux() -> bool:
        return sys.platform == "linux"

    @staticmethod
    def command(*args: str) -> None:
        p = Popen(args=[*args], stdout=PIPE, stderr=PIPE)
        stdout, stderr = p.communicate()
        if p.wait() != 0:
            raise RuntimeError(
                f"Command failed ({p.returncode}): {(stdout or stderr).decode()}"
            )

#  Copyright (c) Kuba Szczodrzyński 2023-11-10.

from cloudcutter.modules import http as httpm
from cloudcutter.modules.base import ModuleBase
from cloudcutter.modules.http import Request, Response

from ._data import TuyaServerData
from ._events import TuyaUrlConfigEvent


class DnsCore(TuyaServerData, ModuleBase):
    @httpm.post("/v1/url_config", host=r"h\d\.iot-dns\.com")
    @httpm.post("/v2/url_config", host=r"h\d\.iot-dns\.com")
    async def on_url_config(self, request: Request) -> Response:
        TuyaUrlConfigEvent(request.address).broadcast()
        return {
            "caArr": [],
            "httpUrl": {
                "addr": f"http://{self.ipconfig.address}/d.json",
                "ips": [self.ipconfig.address],
            },
            "httpsPSKUrl": {
                "addr": f"https://{self.ipconfig.address}/d.json",
                "ips": [self.ipconfig.address],
            },
            "mqttUrl": {
                "addr": f"{self.ipconfig.address}:1883",
                "ips": [self.ipconfig.address],
            },
            # "mqttsPSKUrl": {
            #     "addr": f"{self.dns_host}:8886",
            #     "ips": [self.ipconfig.address],
            # },
            "ttl": 600,
        }

    @httpm.post("/device/url_config")
    async def on_url_config_old(self, request: Request) -> Response:
        TuyaUrlConfigEvent(request.address).broadcast()
        return {
            "caArr": [],
            "httpUrl": f"http://{self.ipconfig.address}/d.json",
            "mqttUrl": f"{self.ipconfig.address}:1883",
        }

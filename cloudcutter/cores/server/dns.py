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
        address = str(self.ipconfig.address)
        return {
            "caArr": None,
            "httpUrl": {
                "addr": f"http://{address}/d.json",
                "ips": [address],
            },
            "httpsUrl": {
                "addr": "",
                "ips": [""],
            },
            "httpsPSKUrl": {
                "addr": "",
                "ips": [""],
            },
            "mqttUrl": {
                "addr": f"{address}:1883",
                "ips": [address],
            },
            "mqttsUrl": {
                "addr": "",
                "ips": [""],
            },
            "mqttsPSKUrl": {
                "addr": "",
                "ips": [""],
            },
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

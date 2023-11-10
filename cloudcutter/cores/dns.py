#  Copyright (c) Kuba Szczodrzyński 2023-11-10.

from abc import ABC

from cloudcutter.modules import http as httpm
from cloudcutter.modules.base import ModuleBase
from cloudcutter.modules.http import Request, Response


class DnsCore(ModuleBase, ABC):
    dns_ip: str = None
    dns_host: str = None

    @httpm.post("/v1/url_config", host=r"h\d\.iot-dns\.com")
    @httpm.post("/v2/url_config", host=r"h\d\.iot-dns\.com")
    async def on_url_config(self, request: Request) -> Response:
        ips = [self.dns_ip]
        return {
            "caArr": [],
            "httpUrl": {
                "addr": f"http://{self.dns_host}/d.json",
                "ips": ips,
            },
            "httpsPSKUrl": {
                "addr": f"https://{self.dns_host}/d.json",
                "ips": ips,
            },
            "mqttUrl": {
                "addr": f"{self.dns_host}:1883",
                "ips": ips,
            },
            # "mqttsPSKUrl": {
            #     "addr": f"{self.dns_host}:8886",
            #     "ips": ips,
            # },
            "ttl": 600,
        }

    @httpm.post("/device/url_config")
    async def on_url_config_old(self, request: Request) -> Response:
        return {
            "caArr": [],
            "httpUrl": f"http://{self.dns_host}/d.json",
            "mqttUrl": f"{self.dns_host}:1883",
        }

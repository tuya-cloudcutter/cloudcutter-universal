#  Copyright (c) Kuba Szczodrzyński 2023-11-10.

import hmac
from abc import ABC
from hashlib import sha256
from pathlib import Path
from pprint import pprint

from cloudcutter.modules import http as httpm
from cloudcutter.modules import mqtt as mqttm
from cloudcutter.modules.base import ModuleBase
from cloudcutter.modules.http import Request, Response

from .gateway import GatewayCore
from .mqtt import MqttCore


class OtaCore(MqttCore, GatewayCore, ModuleBase, ABC):
    upgraded_devices: set[str] = None
    files_host: str = None
    files_dir_path: Path
    fw_name: str

    def __init__(self):
        super().__init__()
        self.upgraded_devices = set()

    @httpm.post("/d.json", query=dict(a="tuya.device.dynamic.config.ack"))
    @httpm.post("/d.json", query=dict(a="tuya.device.timer.count"))
    async def on_upgrade_trigger(self, request: Request) -> Response:
        device, data = self._decrypt_http(request)

        if device.uuid in self.upgraded_devices:
            return None

        action = request.query["a"]
        self.info(f"Upgrading {device.uuid} by {action} - triggering OTA upgrade")
        self.upgraded_devices.add(device.uuid)

        topic, message = self._encrypt_mqtt(
            device=device,
            data={
                "data": {
                    "firmwareType": 0,
                },
                "protocol": 15,
            },
            protocol="2.2",
        )
        await self.mqtt.publish(topic, message)

        # continue to the default schema handler
        return None

    @httpm.post("/d.json", query=dict(a="tuya.device.upgrade.silent.get"))
    async def on_upgrade_silent_get(self, request: Request) -> Response:
        device, data = self._decrypt_http(request)

        if device.uuid in self.upgraded_devices:
            self.info(f"Device {device.uuid} already upgraded, skipping silent upgrade")
            return self._encrypt_http(device=device, result={})
        self.upgraded_devices.add(device.uuid)

        return await self.on_upgrade_get(request)

    @httpm.post("/d.json", query=dict(a="tuya.device.upgrade.get"))
    async def on_upgrade_get(self, request: Request) -> Response:
        device, data = self._decrypt_http(request)

        action = request.query["a"]
        self.info(f"Upgrading {device.uuid} by {action} - sending upgrade information")
        self.upgraded_devices.add(device.uuid)

        fw_path = self.files_dir_path / self.fw_name
        fw_data = fw_path.read_bytes()
        fw_sha = sha256(fw_data).hexdigest().upper().encode()
        fw_hmac = (
            hmac.digest(device.active_key.encode(), fw_sha, "sha256").hex().upper()
        )

        return self._encrypt_http(
            device=device,
            result={
                "url": f"http://{self.files_host}/files/{self.fw_name}",
                "hmac": fw_hmac,
                "version": "9.0.0",
                "size": str(len(fw_data)),
                "type": 0,
            },
        )

    @httpm.post("/d.json", query=dict(a="tuya.device.upgrade.status.update"))
    async def on_upgrade_status(self, request: Request) -> Response:
        device, data = self._decrypt_http(request)

        self.info(f"Upgrading device {device.uuid} - status {data['upgradeStatus']}")

        return None

    @mqttm.subscribe("smart/device/out/+")
    async def on_upgrade_progress(self, topic: str, message: bytes) -> None:
        device, data = self._decrypt_mqtt(topic, message)

        if data.get("protocol", None) != 16:
            return
        data = data["data"]

        self.info(f"Upgrading device {device.uuid} - progress {data['progress']}%")

    @httpm.get("/files/(.*)")
    async def on_files_get(self, request: Request) -> Response:
        fw_name = request.path.rpartition("/")[2]
        return self.files_dir_path / fw_name

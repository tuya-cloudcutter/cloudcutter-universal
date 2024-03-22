#  Copyright (c) Kuba Szczodrzyński 2023-11-10.

import hmac
from hashlib import sha256

from cloudcutter.modules import http as httpm
from cloudcutter.modules import mqtt as mqttm
from cloudcutter.modules.base import ModuleBase
from cloudcutter.modules.http import Request, Response

from ._data import TuyaServerData
from ._events import (
    TuyaUpgradeDownloadEvent,
    TuyaUpgradeInfoEvent,
    TuyaUpgradeProgressEvent,
    TuyaUpgradeSkipEvent,
    TuyaUpgradeStatusEvent,
    TuyaUpgradeTriggerEvent,
)
from .gateway import GatewayCore
from .mqtt import MqttCore


class OtaCore(GatewayCore, MqttCore, TuyaServerData, ModuleBase):
    @httpm.post("/d.json", query=dict(a="tuya.device.dynamic.config.ack"))
    @httpm.post("/d.json", query=dict(a="tuya.device.timer.count"))
    async def on_upgrade_trigger(self, request: Request) -> Response:
        device, data = self._decrypt_http(request)

        if device.uuid in self.upgraded_devices:
            TuyaUpgradeSkipEvent(
                device=device,
                reason=TuyaUpgradeSkipEvent.Reason.ALREADY_UPGRADED,
            ).broadcast()
            return None
        if not device.firmware_path:
            TuyaUpgradeSkipEvent(
                device=device,
                reason=TuyaUpgradeSkipEvent.Reason.NO_FIRMWARE_SET,
            ).broadcast()
            return None
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
        await self.core.mqtt.publish(topic, message)

        TuyaUpgradeTriggerEvent(device, action=request.query["a"]).broadcast()

        # continue to the default schema handler
        return None

    @httpm.post("/d.json", query=dict(a="tuya.device.upgrade.silent.get"))
    async def on_upgrade_silent_get(self, request: Request) -> Response:
        device, data = self._decrypt_http(request)

        if device.uuid in self.upgraded_devices:
            TuyaUpgradeSkipEvent(
                device=device,
                reason=TuyaUpgradeSkipEvent.Reason.ALREADY_UPGRADED,
            ).broadcast()
            return self._encrypt_http(device=device, result={})
        if not device.firmware_path:
            TuyaUpgradeSkipEvent(
                device=device,
                reason=TuyaUpgradeSkipEvent.Reason.NO_FIRMWARE_SET,
            ).broadcast()
            return self._encrypt_http(device=device, result={})

        return await self.on_upgrade_get(request)

    @httpm.post("/d.json", query=dict(a="tuya.device.upgrade.get"))
    async def on_upgrade_get(self, request: Request) -> Response:
        device, data = self._decrypt_http(request)

        if not device.firmware_path:
            TuyaUpgradeSkipEvent(
                device=device,
                reason=TuyaUpgradeSkipEvent.Reason.NO_FIRMWARE_SET,
            ).broadcast()
            return self._encrypt_http(device=device, result={})
        self.upgraded_devices.add(device.uuid)

        fw_path = device.firmware_path
        fw_data = fw_path.read_bytes()
        fw_sha = sha256(fw_data).hexdigest().upper().encode()
        fw_hmac = (
            hmac.digest(device.active_key.encode(), fw_sha, "sha256").hex().upper()
        )
        # noinspection HttpUrlsUsage
        fw_url = f"http://{self.ipconfig.address}/files/{device.uuid}"

        TuyaUpgradeInfoEvent(
            device=device,
            action=request.query["a"],
            firmware_path=fw_path,
            firmware_url=fw_url,
        ).broadcast()

        return self._encrypt_http(
            device=device,
            result={
                "url": fw_url,
                "hmac": fw_hmac,
                "version": "9.0.0",
                "size": str(len(fw_data)),
                "type": 0,
            },
        )

    @httpm.post("/d.json", query=dict(a="tuya.device.upgrade.status.update"))
    async def on_upgrade_status(self, request: Request) -> Response:
        device, data = self._decrypt_http(request)

        TuyaUpgradeStatusEvent(device, status=data["upgradeStatus"]).broadcast()

        return None

    @mqttm.subscribe("smart/device/out/+")
    async def on_upgrade_progress(self, topic: str, message: bytes) -> None:
        device, data = self._decrypt_mqtt(topic, message)

        if data.get("protocol", None) != 16:
            return
        data = data["data"]

        TuyaUpgradeProgressEvent(device, progress=data["progress"]).broadcast()

    @httpm.get("/files/(.*)")
    async def on_files_get(self, request: Request) -> Response:
        device_uuid = request.path.rpartition("/")[2]
        device = self.get_device(uuid=device_uuid)
        TuyaUpgradeDownloadEvent(device, device.firmware_path).broadcast()
        return device.firmware_path

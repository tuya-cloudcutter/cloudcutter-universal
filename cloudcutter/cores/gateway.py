#  Copyright (c) Kuba Szczodrzyński 2023-11-10.

import json
from base64 import b64encode
from hashlib import md5
from pathlib import Path
from secrets import token_hex
from time import time

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

from cloudcutter.modules import http as httpm
from cloudcutter.modules.base import ModuleBase
from cloudcutter.modules.http import Request, Response

from .device import Device, DeviceCore


class GatewayCore(DeviceCore, ModuleBase):
    def _decrypt_data(
        self,
        request: Request,
    ) -> tuple[Device, dict]:
        device = self.get_device(request=request)
        data = bytes.fromhex(request.body["data"])
        match device.encryption_type:
            case 0:
                raise NotImplementedError()
            case 1:
                aes = AES.new(key=device.aes_key[:16], mode=AES.MODE_ECB)
                data = aes.decrypt(data)
                data = unpad(data, block_size=16)
            case 3:
                iv = data[:12]
                tag = data[-16:]
                data = data[12:-16]
                aes = AES.new(key=device.aes_key[:16], mode=AES.MODE_GCM, nonce=iv)
                data = aes.decrypt_and_verify(data, received_mac_tag=tag)
            case _:
                raise NotImplementedError()
        obj = json.loads(data)
        self.debug(f"Request body: {obj}")
        return device, obj

    def _encrypt_data(
        self,
        device: Device,
        result: str | dict | bool | int | None,
    ) -> Response:
        obj = {"success": True, "t": int(time())}
        if result is not None:
            obj["result"] = result
        else:
            obj["result"] = {}
        self.debug(f"Response body: {obj}")
        data = json.dumps(obj, separators=(",", ":")).encode()
        match device.encryption_type:
            case 0:
                raise NotImplementedError()
            case 1:
                aes = AES.new(key=device.aes_key[:16], mode=AES.MODE_ECB)
                data = pad(data, block_size=16)
                data = aes.encrypt(data)
            case 3:
                iv = token_hex(6).encode()
                aes = AES.new(key=device.aes_key[:16], mode=AES.MODE_GCM, nonce=iv)
                data, tag = aes.encrypt_and_digest(data)
                data = iv + data + tag
            case _:
                raise NotImplementedError()
        result_encoded = b64encode(data)
        signature = md5()
        signature.update(b"result=")
        signature.update(result_encoded)
        signature.update(f"||t={obj['t']}||".encode())
        signature.update(device.aes_key)
        return {
            "result": result_encoded.decode(),
            "t": obj["t"],
            "sign": signature.hexdigest()[8:24],
        }

    @httpm.post("/d.json", query=dict(a="tuya.device.active"))
    async def on_gateway_active(self, request: Request) -> Response:
        device, data = self._decrypt_data(request)
        self.debug(f"Activating device: uuid={device.uuid}, softVer={data['softVer']}")
        schema = [
            {
                "mode": "rw",
                "property": {
                    "type": "bool",
                },
                "id": 1,
                "type": "obj",
            }
        ]
        new_aes_key = device.auth_key[:16].decode()
        return self._encrypt_data(
            device=device,
            result={
                "schema": json.dumps(schema, separators=(",", ":")),
                "devId": device.uuid,
                "resetFactory": False,
                "timeZone": "+02:00",
                "capability": 1025,
                "secKey": new_aes_key,
                "stdTimeZone": "+01:00",
                "schemaId": "0000000000",
                "dstIntervals": [],
                "localKey": new_aes_key,
            },
        )

    @httpm.post("/d.json")
    async def on_gateway_other(self, request: Request) -> Response:
        action = request.query.get("a", None)
        self.info(f"Gateway request: {action}")
        device, data = self._decrypt_data(request)
        result = None
        schema_path = (
            Path(__file__).parent.parent.with_name("schema").joinpath(f"{action}.json")
        )
        if schema_path.is_file():
            text = schema_path.read_text()
            text = text.replace("DUMMY", device.uuid)
            result = json.loads(text).get("result", None)
        else:
            self.warning(f"Missing schema response for {action}")
        return self._encrypt_data(device, result=result)

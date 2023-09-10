#  Copyright (c) Kuba Szczodrzyński 2023-5-14.

import hashlib
from datetime import datetime
from hmac import HMAC
from struct import pack, unpack
from uuid import UUID

from Crypto.Cipher import AES
from datastruct import Adapter, Context

from .types import IV_LEN, KEY_LEN


class GUIDAdapter(Adapter):
    def encode(self, value: UUID, ctx: Context) -> bytes:
        return value.bytes_le

    def decode(self, value: bytes, ctx: Context) -> UUID:
        return UUID(bytes_le=value)


class UTF16LEAdapter(Adapter):
    def encode(self, value: str, ctx: Context) -> bytes:
        return (value + "\x00").encode("utf-16le")

    def decode(self, value: bytes, ctx: Context) -> str:
        return value.decode("utf-16le").rstrip("\x00")


class FiletimeAdapter(Adapter):
    def encode(self, value: datetime, ctx: Context) -> bytes:
        timestamp = value.timestamp()
        return pack("<Q", int((timestamp + 11644473600) * 10000000))

    def decode(self, value: bytes, ctx: Context) -> datetime:
        timestamp = int(unpack("<Q", value)[0] / 10000000) - 11644473600
        return datetime.fromtimestamp(timestamp)


class DpapiBlobAdapter(Adapter):
    @staticmethod
    def make_session_key(ctx: Context) -> bool:
        from .key import DpapiKey

        if ctx.session_key is not None:
            return True
        builder = ctx.key_builder
        if builder is None:
            return False
        master_key: DpapiKey = builder(ctx.guid_master_key)
        if master_key is None:
            return False
        session_key = HMAC(
            key=master_key.key_hash,
            msg=ctx.salt,
            digestmod=ctx.alg_hash.name,
        ).digest()

        if len(session_key) > KEY_LEN[ctx.alg_hash]:
            session_key = hashlib.new(ctx.alg_hash.name, session_key).digest()
        if len(session_key) < KEY_LEN[ctx.alg_crypt]:
            session_key += b"\x00" * KEY_LEN[ctx.alg_crypt]
            pad1 = bytes(session_key[i] ^ 0x36 for i in range(KEY_LEN[ctx.alg_hash]))
            pad2 = bytes(session_key[i] ^ 0x5C for i in range(KEY_LEN[ctx.alg_hash]))
            session_key = (
                hashlib.new(ctx.alg_hash.name, pad1).digest()
                + hashlib.new(ctx.alg_hash.name, pad2).digest()
            )
        ctx.master_key = master_key
        ctx.session_key = session_key
        return True

    def encode(self, value: bytes, ctx: Context) -> bytes:
        if not self.make_session_key(ctx):
            return value
        return AES.new(
            key=ctx.session_key[0 : KEY_LEN[ctx.alg_crypt]],
            mode=AES.MODE_CBC,
            iv=b"\x00" * IV_LEN[ctx.alg_crypt],
        ).encrypt(value)

    def decode(self, value: bytes, ctx: Context) -> bytes:
        if not self.make_session_key(ctx):
            return value
        return AES.new(
            key=ctx.session_key[0 : KEY_LEN[ctx.alg_crypt]],
            mode=AES.MODE_CBC,
            iv=b"\x00" * IV_LEN[ctx.alg_crypt],
        ).decrypt(value)

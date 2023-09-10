#  Copyright (c) Kuba Szczodrzyński 2023-5-14.

from dataclasses import dataclass
from hmac import HMAC
from io import BytesIO
from uuid import UUID

from datastruct import DataStruct, datastruct
from datastruct.fields import (
    adapter,
    built,
    checksum_end,
    checksum_field,
    checksum_start,
    field,
)

from .adapter import DpapiBlobAdapter, GUIDAdapter, UTF16LEAdapter
from .types import KEY_LEN, WCP_GUID, DpapiAlgoCrypt, DpapiAlgoHash


@dataclass
@datastruct(padding_pattern=b"\x00")
class DpapiBlob(DataStruct):
    version1: int = field("I", default=1)
    guid_default_provider: UUID = adapter(GUIDAdapter())(field(16, default=WCP_GUID))
    _checksum: ... = checksum_start(
        init=lambda ctx: BytesIO(),
        update=lambda v, obj, ctx: obj.write(v) and None,
        end=lambda obj, ctx: HMAC(
            ctx.master_key.key_hash,
            ctx.hmac_key + obj.getvalue(),
            ctx.alg_hash.name,
        ).digest(),
    )
    version2: int = field("I", default=1)
    guid_master_key: UUID = adapter(GUIDAdapter())(field(16))
    flags: int = field("I", default=0)
    name_len: int = built("I", lambda ctx: (len(ctx.name) + 1) * 2)
    name: str = adapter(UTF16LEAdapter())(field(lambda ctx: ctx.name_len, default=""))
    alg_crypt: DpapiAlgoCrypt = field("I", default=0x6610)
    alg_crypt_len: int = field("I", default=256)
    salt_len: int = built("I", lambda ctx: len(ctx.salt))
    salt: bytes = field(lambda ctx: ctx.salt_len)
    strong: int = field("I", default=0)
    alg_hash: DpapiAlgoHash = field("I", default=0x800E)
    alg_hash_len: int = field("I", default=512)
    hmac_key_len: int = built("I", lambda ctx: len(ctx.hmac_key))
    hmac_key: bytes = field(lambda ctx: ctx.hmac_key_len)
    data_len: int = built("I", lambda ctx: len(ctx.data))
    data: bytes = adapter(DpapiBlobAdapter())(field(lambda ctx: ctx.data_len))
    _2: ... = checksum_end(_checksum)
    sign_len: int = built("I", lambda ctx: KEY_LEN[ctx.alg_hash])
    sign: bytes = checksum_field("blob signature")(
        field(lambda ctx: ctx.sign_len, default=b"")
    )

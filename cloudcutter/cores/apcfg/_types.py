#  Copyright (c) Kuba Szczodrzyński 2024-3-23.

from binascii import crc32
from dataclasses import dataclass

from datastruct import DataStruct, Endianness, datastruct
from datastruct.fields import (
    built,
    checksum_end,
    checksum_field,
    checksum_start,
    const,
    field,
)


@dataclass
@datastruct(endianness=Endianness.NETWORK)
class ApCfgFrame(DataStruct):
    _crc_start: ... = checksum_start(
        init=lambda ctx: 0,
        update=lambda value, obj, ctx: crc32(value, obj),
        end=lambda obj, ctx: obj,
    )
    head: int = const(0x55AA)(field("I"))
    frame_num: int = field("I", default=0)
    frame_type: int = field("I", default=1)
    length: int = built("I", lambda ctx: len(ctx.payload) + 8)
    payload: bytes = field(lambda ctx: ctx.length - 8)
    _crc_end: ... = checksum_end(_crc_start)
    crc: int = checksum_field("packet CRC")(field("I", default=0))
    tail: int = const(0xAA55)(field("I"))

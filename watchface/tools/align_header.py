#!/usr/bin/env python3
"""把重打包 bin 的头部字段对齐到官方参考 bin。

Mi8WfBinTool 打包时会自己写 0x04（协议版本）和 0x1E（styleCount），与官方 bin
不同。手环是否校验这些字段未知，所以提供这个补丁脚本，方便真机对比测试：

    python3 align_header.py custom.bin samples/aod_362150007.bin custom_hdr.bin

只改这三个字段，不动其他内容：
    0x04..0x07  协议/版本 u32
    0x10..0x13  设备标志 u32
    0x1C..0x1F  faceCount u16 + faceStyleCount u16
"""

import struct
import sys


def main():
    if len(sys.argv) != 4:
        print(__doc__)
        return 1
    new_path, ref_path, out_path = sys.argv[1:4]
    new = bytearray(open(new_path, "rb").read())
    ref = open(ref_path, "rb").read()
    if new[:4] != b"\x5a\xa5\x34\x12" or ref[:4] != b"\x5a\xa5\x34\x12":
        print("不是表盘 bin（magic 不对）")
        return 1
    for off in (0x04, 0x10, 0x1C):
        new[off:off + 4] = ref[off:off + 4]
    open(out_path, "wb").write(new)
    print("%s: 版本=%s 设备=%s faceCount=%d styleCount=%d"
          % (out_path,
             struct.unpack("<I", new[0x04:0x08])[0],
             hex(struct.unpack("<I", new[0x10:0x14])[0]),
             struct.unpack("<H", new[0x1C:0x1E])[0],
             struct.unpack("<H", new[0x1E:0x20])[0]))
    return 0


if __name__ == "__main__":
    sys.exit(main())

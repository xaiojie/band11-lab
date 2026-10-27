#!/usr/bin/env python3
"""从小米手环 11 官方固件里提取出厂表盘 .bin。

用法:
    python3 extract_watchfaces.py <firmware.zip 或 vela_resource.bin> <输出目录>

固件包是 JAR/ZIP，里面 vela_resource.bin 是一个 Vela 版 romfs。
本脚本解析 romfs，遍历 /watchface/ 下的每个主题目录，取出其中的 resource.bin
（就是手表真正加载的表盘 bin）并另存。

romfs 结构（实测 v4.100.179 / q66cn）:
    条目 16 字节大端头: next_filehdr(u32) | spec_info(u32) | size(u32) | checksum(u32)
    紧接着是 NUL 结尾的文件名。

    - next_filehdr 低 4 位是类型: 9=目录, 2=普通文件, 0=./..
    - next_filehdr & ~0xF = 同级下一条的偏移 (0 表示没有下一条)
    - 目录的 spec_info = 第一个子条目的偏移
    - 文件数据从 align16(条目偏移 + 16 + 名字长度 + 1) 开始，长度 = size
"""

import os
import struct
import sys
import zipfile

RESOURCE_NAME = "vela_resource.bin"


def read_header(data, off):
    nxt, spec, size, _csum = struct.unpack(">IIII", data[off:off + 16])
    end = data.find(b"\x00", off + 16, off + 96)
    if end < 0:
        raise ValueError("bad name at %#x" % off)
    name = data[off + 16:end].decode("utf-8", "replace")
    return {"off": off, "next": nxt & ~0xF, "flag": nxt & 0xF,
            "spec": spec, "size": size, "name": name,
            "data_off": (off + 16 + len(data[off + 16:end]) + 1 + 15) & ~15}


def iter_children(data, dir_off):
    """遍历一个目录下的同级条目。"""
    off = read_header(data, dir_off)["spec"]
    while off:
        h = read_header(data, off)
        yield h
        off = h["next"]


def find_dir(data, path_parts):
    """按名字逐层向下找目录，返回目录条目。"""
    cur = read_header(data, 0x20)  # 根目录 '.'
    for want in path_parts:
        for h in iter_children(data, cur["off"]):
            if h["name"] == want and h["flag"] == 9:
                cur = h
                break
        else:
            raise KeyError("/".join(path_parts) + " 不存在")
    return cur


def extract(data, outdir):
    os.makedirs(outdir, exist_ok=True)
    wfdir = find_dir(data, ["watchface"])
    found = []

    def walk(dir_h, prefix):
        for h in iter_children(data, dir_h["off"]):
            if h["flag"] != 9:
                if h["name"].endswith(".csv"):
                    open(os.path.join(outdir, h["name"]), "wb").write(
                        data[h["data_off"]:h["data_off"] + h["size"]])
                continue
            label = prefix + h["name"]
            sub = list(iter_children(data, h["off"]))
            if any(f["name"] == "resource.bin" for f in sub):
                for f in sub:
                    if f["name"] != "resource.bin":
                        continue
                    blob = data[f["data_off"]:f["data_off"] + f["size"]]
                    path = os.path.join(outdir, label + ".bin")
                    open(path, "wb").write(blob)
                    ok = blob[:4] == b"\x5a\xa5\x34\x12"
                    found.append((label, path, len(blob), ok))
            else:
                walk(h, label + "_")

    walk(wfdir, "")
    return found


def main():
    if len(sys.argv) != 3:
        print(__doc__)
        return 1
    src, outdir = sys.argv[1], sys.argv[2]
    if zipfile.is_zipfile(src):
        with zipfile.ZipFile(src) as z:
            names = [n for n in z.namelist() if n.endswith(RESOURCE_NAME)]
            if not names:
                print("固件里没找到", RESOURCE_NAME)
                return 1
            data = z.read(names[0])
        print("固件:", src, "->", names[0], len(data), "字节")
    else:
        data = open(src, "rb").read()
        print("romfs:", src, len(data), "字节")
    assert data[:8] == b"-rom1fs-", "不是 romfs"
    found = extract(data, outdir)
    for name, path, size, ok in found:
        print("%-24s %9d 字节  magic=%s  -> %s" % (name, size, "OK" if ok else "?", path))
    print("共导出 %d 个表盘 bin -> %s" % (len(found), outdir))
    return 0


if __name__ == "__main__":
    sys.exit(main())

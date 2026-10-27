#!/usr/bin/env bash
# 下载手环 11（q66cn）官方固件并校验。
#
# 实测：GitHub release 直连会随机截断（只下到 6,201,100 B 就返回 200），
# 用 `curl -C -` 断点续传重试几次可以补齐；gh-proxy 镜像更省事。
#
#   ./get_firmware.sh [输出路径]
set -euo pipefail

OUT="${1:-band11_fw.bin}"
VER="v4.100.179"
ASSET="miwear.watch.q66cn_${VER}_full_a93678a9.bin"
GH="https://github.com/hrk666666/firmware-archives-public/releases/download/firmware-miwear.watch.q66cn-${VER}-06b04b64/${ASSET}"
MIRROR="https://gh-proxy.com/${GH}"
SIZE=66683899
SHA256="a93678a9bfff68dfa36fe3ff59f8ae2c4040156c75d7559bd3fe2ab2e90ac951"

size() { stat -f%z "$OUT" 2>/dev/null || stat -c%s "$OUT" 2>/dev/null || echo 0; }

if [ -f "$OUT" ] && [ "$(size)" -eq "$SIZE" ] && \
   [ "$(shasum -a 256 "$OUT" | cut -d' ' -f1)" = "$SHA256" ]; then
  echo "已有完整固件: $OUT"
  exit 0
fi

echo "下载 $VER 固件 -> $OUT"
for i in 1 2 3 4 5 6; do
  # 两个源轮着试，-C - 续传，避免每次从头
  url="$GH"; [ $((i % 2)) -eq 0 ] && url="$MIRROR"
  echo "  attempt $i: $url"
  curl -sSL -C - --max-time 600 -o "$OUT" "$url" || true
  echo "  size=$(size) / $SIZE"
  [ "$(size)" -ge "$SIZE" ] && break
  sleep 2
done

actual="$(shasum -a 256 "$OUT" | cut -d' ' -f1)"
if [ "$(size)" -ne "$SIZE" ] || [ "$actual" != "$SHA256" ]; then
  echo "校验失败: size=$(size) sha256=$actual" >&2
  exit 1
fi
echo "OK: $OUT ($SIZE B, sha256 匹配)"

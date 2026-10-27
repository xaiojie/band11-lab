#!/usr/bin/env python3
"""从 DeepSeek 余额接口拉一次「剩余额度」，烧进表盘并重打包。

表盘本身不能联网，所以额度是**快照**：跑一次 = 更新一次，然后重新装到手上。

用法（key 只在本机用，别贴到聊天里）：

    export DEEPSEEK_API_KEY=sk-xxxx          # 推荐：走环境变量
    python3 refresh_quota.py

    python3 refresh_quota.py --key sk-xxxx    # 也行，但会留在 shell history 里

可选：
    --cap 50        进度条满格对应的金额（默认 50 元）
    --art PATH      插画，默认 ../keyface/src_art.png
    --out PATH      工程目录，默认 ../keyface/build
    --no-pack       只生成图，不打包
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
KEYFACE = HERE.parent / "keyface"
BALANCE_URL = "https://api.deepseek.com/user/balance"


def fetch_balance(key: str) -> dict:
    req = urllib.request.Request(
        BALANCE_URL,
        headers={"Authorization": f"Bearer {key}", "Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            data = json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")
        print(f"HTTP {e.code}: {body}", file=sys.stderr)
        raise SystemExit(2)
    except urllib.error.URLError as e:
        print(f"网络错误: {e.reason}", file=sys.stderr)
        raise SystemExit(2)

    infos = data.get("balance_infos") or []
    if not infos:
        print(f"返回里没有 balance_infos: {data}", file=sys.stderr)
        raise SystemExit(2)
    info = next((i for i in infos if i.get("currency") == "CNY"), infos[0])
    return {
        "currency": info.get("currency", "CNY"),
        "total": float(info.get("total_balance", 0) or 0),
        "granted": float(info.get("granted_balance", 0) or 0),
        "topped": float(info.get("topped_up_balance", 0) or 0),
        "available": bool(data.get("is_available", True)),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--key", default=os.environ.get("DEEPSEEK_API_KEY", ""))
    ap.add_argument("--cap", type=float, default=50.0)
    ap.add_argument("--art", default=str(KEYFACE / "src_art.png"))
    ap.add_argument("--out", default=str(KEYFACE / "build"))
    ap.add_argument("--id", default="362155012")
    ap.add_argument("--name", default="深蓝额度")
    ap.add_argument("--no-pack", action="store_true")
    a = ap.parse_args()

    if not a.key:
        print("需要 key：export DEEPSEEK_API_KEY=sk-... 或 --key sk-...", file=sys.stderr)
        raise SystemExit(1)

    b = fetch_balance(a.key)
    stamp = dt.datetime.now().strftime("%m-%d %H:%M")
    print(f"余额 {b['currency']} {b['total']:.2f}（赠 {b['granted']:.2f} / 充 {b['topped']:.2f}） "
          f"available={b['available']}  @ {stamp}")

    cmd = [
        sys.executable, str(HERE / "build_keyface.py"),
        "--art", a.art, "--out", a.out,
        "--balance", f"{b['total']:.2f}",
        "--cap", str(a.cap),
        "--updated", stamp,
        "--id", a.id, "--name", a.name,
    ]
    if not a.no_pack:
        cmd.append("--pack")
    subprocess.run(cmd, check=True)


if __name__ == "__main__":
    main()

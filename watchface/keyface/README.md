# 深蓝额度 · 手环 11 表盘

蓝色主题 + 鲸鱼女仆插画 + DeepSeek 剩余额度显示的 212×520 表盘，可直接装到小米手环 11（q66）。

| 未同步 | 同步之后 |
|---|---|
| ![未同步](preview_未同步.png) | ![额度示例](preview_额度示例.png) |

## 成品

| 文件 | 说明 |
|---|---|
| `深蓝额度_362155012.bin` | 已打包好，可直接安装（额度显示 `--.--`，跑一次刷新脚本就有数） |
| `preview_未同步.png` / `preview_额度示例.png` | 212×520 的 2 倍预览 |
| `src_art.png` | 原插画（1254×1254，作者水印「枇杷」） |
| `build/` | 可重新打包的工程：`wfDef.json` + `images/` |

表盘 id `362155012`，名称「深蓝额度」，不覆盖官方表盘。

## ⚠️ 额度是静态快照

表盘本身不能联网（Vela 表盘没有任何网络能力，也没有「额度」这类数据源），所以额度是**打包那一刻烧进图片里的数字**：

- 想更新 → 本机跑 `refresh_quota.py` → 重新打包 → 再装一次（约 2 分钟）
- 面板底部那行 `10-27 11:52` 就是快照时间，所以放旧了也看得出来

## 刷一次（推荐用环境变量，key 别落在 history / 聊天里）

```bash
PY=/Users/jay/.dsh/dsh-runtimes/dsh-primary-runtime/dependencies/python/bin/python3

export DEEPSEEK_API_KEY=sk-你的key          # 只在当前 shell 生效
cd /Users/jay/开发/band11/watchface/tools
$PY refresh_quota.py                       # 拉余额 → 生成图 → 打包
```

产物：`../keyface/深蓝额度_362155012.bin`，直接拿去装。

常用参数：

```bash
$PY refresh_quota.py --cap 100             # 进度条满格对应 100 元（默认 50）
$PY refresh_quota.py --no-pack             # 只出图，不打包
```

## 装到手上

1. 手环：`设置 → 系统操作 → 连接新手机`（停在这个界面别退）
2. Mac 上 AstroBox 点设备连上（RFConnect 要等几秒）
3. 设备页 → 「表盘」卡片 → `+` → 选 `深蓝额度_362155012.bin` → 安装
4. 手环亮屏 → 切到「深蓝额度」
5. 装完回小米运动健康重连手机

## 版式

```
y   0-300   角色插画（按高度缩放、居中裁切、底部 110px 渐隐）
y 302-306   发光分隔线
y 330-394   时间 HH:MM（4 个单字符数字控件，冒号烘焙在底图里）
y 398-486   玻璃面板：DEEPSEEK · QUOTA + ¥ 余额 + 进度条 + 快照时间
y 500-520   底部品牌小字
```

时间不用整串数字控件，而是 4 个单字符控件，位置/字号完全可控：

| 控件 | dataSrc | 图数 | 说明 |
|---|---|---|---|
| 小时十位 | `0A11` | 3 | 0-2 |
| 小时个位 | `0911` | 10 | 0-9 |
| 分钟十位 | `1211` | 6 | 0-5 |
| 分钟个位 | `1111` | 10 | 0-9 |

这几个 dataSrc 是从固件里官方熄屏表盘 `362150004` 逆向出来的（同一固件、同一渲染引擎）。
若上机后发现数字不对，说明 q66 编码有差异，改回整串 `0821` 控件即可（模板见 `../template/wfDef.json`）。

## 安全

- 现在表盘里**不再有任何 key**，只有余额数字；key 只在本机作为 HTTP `Authorization` 头出现一次。
- `refresh_quota.py` 不会缓存 key，也不写文件；用完 `unset DEEPSEEK_API_KEY` 即可。
- 余额本身也算个人信息（能看出消费水平），bin 别乱发。

## 技术栈

- 打包：`java /Users/jay/开发/band11/_research/Mi8WfBinTool.java pack <dir> <out.bin> o66`
- 生成：`/Users/jay/开发/band11/watchface/tools/build_keyface.py`
- 刷新：`/Users/jay/开发/band11/watchface/tools/refresh_quota.py`
- 余额接口：`GET https://api.deepseek.com/user/balance`，返回 `balance_infos[0].total_balance`
- 图像压缩：RLE + 256 色调色板，成品 593 KB

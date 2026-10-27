# 腕上桌宠 · 小米手环 11 快应用

把 `dsh-pet-indesktop` 的桌宠搬到手环上：蓝发女仆 shenshen + 六个互动按钮 + 亲密度存档。

- 成品：`app/dist/com.jay.band11pet.debug.0.1.0.rpk`（3.0 MB）
- 布局预览：`mock_v2.png`
- 方案说明：`PLAN.md`

## 目录

```
pet/
├── app/                      Vela 快应用工程
│   ├── src/
│   │   ├── manifest.json     com.jay.band11pet / 腕上桌宠 / designWidth 212
│   │   ├── app.ux
│   │   ├── pages/index/index.ux   唯一页面（状态机 + 帧动画）
│   │   ├── common/images/icon.png
│   │   └── assets/pet/       18 个 clip、348 帧、3.8 MB
│   ├── dist/                 构建产物（.rpk）
│   └── package.json          devDependency: aiot-toolkit 2.0.5
├── tools/build_pet_assets.py 素材管线（webm → 帧序列）
└── mock_v2.png
```

## 构建

系统 Node 在 `/usr/local/bin/node`（dsh 自带的那份带 hardened runtime，
加载 rspack 原生模块会报 `different Team IDs`，别用）。

```bash
cd /Users/jay/开发/band11/pet/app
/usr/local/bin/node ./node_modules/.bin/aiot build
# → dist/com.jay.band11pet.debug.0.1.0.rpk
```

## 素材管线

```bash
PY=/Users/jay/.dsh/dsh-runtimes/dsh-primary-runtime/dependencies/python/bin/python3
$PY tools/build_pet_assets.py           # 全部重跑
$PY tools/build_pet_assets.py idle eat  # 只跑指定 clip
```

流程：`ffmpeg fps=N` 抽帧 → 黑底抠像（`alpha=(max(RGB)-22)/40`，颜色 `stored/alpha` 反解）
→ 按 `body_box` 固定框裁切 → 170 宽等比缩放 → 64 色 FASTOCTREE 量化 PNG。

| clip | 帧 | fps | KB |
|---|---|---|---|
| idle（待机呼吸） | 24 | 8 | 202 |
| happy / shy / pat | 14 ×3 | 12 | 382 |
| eat（大口吃零食） | 18 | 10 | 173 |
| sleep（原地小憩） | 20 | 8 | 190 |
| token（吃Token） | 18 | 10 | 114 |
| code（忙碌点按） | 18 | 10 | 145 |
| yawn（哈欠连天） | 20 | 10 | 167 |
| brush（晨间刷牙） | 20 | 10 | 176 |
| stretch（超大伸懒腰） | 20 | 10 | 180 |
| wake（打瞌睡被惊醒） | 18 | 10 | 160 |
| shock（被吓一跳） | 18 | 10 | 150 |
| dance1（优雅女仆舞） | 24 | 10 | 230 |
| dance2（轻快摇摆舞） | 24 | 10 | 225 |
| cat（撸猫） | 20 | 10 | 175 |
| rubik（原地玩魔方） | 20 | 10 | 172 |
| whale（蓝鲸现世） | 24 | 10 | 150 |

合计 348 帧 / 3.8 MB，平均 8.7 KB/帧。rpk 压完 3.0 MB。不量化是 66 KB/帧，量化是必需的。

## 交互

| 按钮 | clip | 效果 |
|---|---|---|
| 点宠物 / 摸摸 | pat / happy / shy（随机） | 振动 short，亲密度 +1 |
| 零食 | eat | 亲密度 +3，每日上限 5 次 |
| 睡觉 | sleep（循环） | 进入睡眠态，存档 |
| 喂Token | token | 亲密度 +2，DeepSeek 梗台词 |
| 码代码 | code | 亲密度 +2 |
| 伸懒腰 | yawn | 打哈欠台词 |
| 长按宠物 | cat | 撸猫，亲密度 +2 |
| 连点 3 下（900ms 内） | shock | 被吓一跳，长振动 |
| 每 15 次摸摸 | whale | 蓝鲸现世彩蛋，亲密度 +5 |
| 早上 6–10 点打开 | brush | 晨间刷牙 |
| 23 点后打开 | sleep | 自动进入睡眠态 |
| 待机 4 轮后（50% 概率） | cat / rubik / stretch / yawn | 待机随机小动作 |
| 升到 Lv.5 / Lv.10 | dance1 / dance2 | 女仆舞 / 摇摆舞 |

- 亲密度存 `storage` key `pet_state`，每 20 点升一级。
- 跨天自动重置「今日摸摸/喂食」计数。
- 非循环 clip 播完自动回 idle；`onHide` 停 timer 省电。

## 已知风险（P0 要验证的）

1. **帧率**：`setInterval` + `image` 换 src 能否稳定 8–12 fps。不行就把帧数砍半（`dur` 参数减半）或改精灵条方案。
2. **样式支持度**：`border-radius` / `flex` / `justify-content: space-between` 这些如果手环上不生效，布局会退化，需按真机截图调。
3. **首帧**：FMP 预算 2000 ms，现在一次只加载 1 张图，问题不大。
4. **安装**：必须走 AstroBox 本地安装（`表盘/快应用` 卡片 → `+` → 选 rpk）。手环要先「连接新手机」。

# 腕上奶蛙 · 小米手环 11 快应用

一只待在腕上的奶蛙：待机循环，点一下就捧腹大笑，还能从动画库里挑动作。

- 设备：小米手环 11（`miwear.watch.q66cn`，212×520）
- 技术：Vela QuickApp（rpk），`designWidth: 212`
- 素材：<https://github.com/Nailong-Studio/wallpaper> v2.7.0 **`pet/` 目录**，MIT
  （© 2026 Morningstar202604；动画源于 `liaosongjie/Codex-Voice-Input`，MIT）
- **不使用 `emotes/` 的任何素材**

## 两个页面

| 页面 | 内容 |
|---|---|
| `pages/index` | 时间 / 日期 → **奶蛙 204×246** → 台词气泡 → 「动画库」按钮 → 今日笑 + 连续陪伴 |
| `pages/library` | 4 张动画卡（待机 / 捧腹大笑 / 倾听 / 躺平），点一张回首页播放 |

交互：

- **待机**：`pet/奶蛙-桌宠-待机.gif` 循环
- **点一下奶蛙**：`pet/奶蛙-桌宠-捧腹大笑.gif`（今日笑 +1）
- **连点**：2.5 秒内再点，在 捧腹大笑 / 倾听 / 躺平 里随机切，且不会连着同一个
- **连点 7 下**：奶蛙吐槽「别戳了，我又不是按钮」
- **长按**：躺平
- **点「动画库」**：挑动作回首页播

## 目录

```
app/src/
  manifest.json            package com.jay.naiwa / 腕上奶蛙 / v0.2.0
  pages/index/index.ux     主屏
  pages/library/library.ux 动画库
  common/images/icon.png   192×192
  assets/frog/<clip>/f_###.png   204×246，已烘焙 #FDEBB2 舞台底色
tools/
  build_frog_assets.py     抽帧 → 联合 bbox 裁切 → 缩放 → 烘焙 → 量化
  preview.py               按 CSS 数值 1:1 出预览图
```

## 素材管线要点

1. `union_bbox()` 算出**整段动画的联合包围盒**再裁切 —— 否则逐帧裁切会让角色抖动。
2. 三个站立动画（idle / laugh / listen）共用**同一个**联合 bbox，切换动作时人物不跳位置。
3. 帧直接烘焙舞台底色 `#FDEBB2` 并量化到 160 色：不用 alpha，边缘零毛边，12 KB/帧。
4. `lie` 是趴姿，包围盒单独算（98×57），否则会被站立盒子切掉。

## 构建

```bash
cd /Users/jay/开发/band11/frog/app
/usr/local/bin/node ./node_modules/.bin/aiot build
# → dist/com.jay.naiwa.debug.0.2.0.rpk（约 580 KB / 92 个文件）
```

> 必须用 `/usr/local/bin/node`：dsh 自带的 node 带 hardened runtime，
> 加载 rspack 原生模块会报 `code signature ... different Team IDs`。

重生成素材：

```bash
PY=/Users/jay/.dsh/dsh-runtimes/dsh-primary-runtime/dependencies/python/bin/python3
cd /Users/jay/开发/band11/frog/tools
$PY build_frog_assets.py              # 四段全做
$PY build_frog_assets.py lie          # 只重建指定 clip
```

## 动画

| clip | 帧 | fps | 循环 | 触发 |
|---|---|---|---|---|
| idle | 19 | 8 | ✓ | 默认 / 动画库 |
| laugh | 25 | 10 | | 点奶蛙 / 动画库 |
| listen | 22 | 10 | | 动画库 |
| lie | 5 | 6 | ✓ | 长按 / 动画库 / 23 点后自动 |

共 71 帧，素材 604 KB。

## 存档

`storage` 两个键：

- `frog_state`：`{ l: 今日笑次数, s: 连续陪伴天数, d: 上次日期 }`
- `frog_play`：动画库选中的 clip 名，回首页时读取后立即清空

## 安装

AstroBox → 设备页 → 「快应用」卡片 → `+` → 选 rpk。
**同名包会冲突，先卸旧的。**

## 授权

- 代码：随本项目
- 素材：MIT（见 `frog_src/LICENSE` 与各文件的 `.txt` 档案）；再分发请保留
  「奶蛙艺术圣殿 / Nailong-Studio」「liaosongjie」署名
- 奶蛙为民间二创形象，本项目仅作个人学习使用

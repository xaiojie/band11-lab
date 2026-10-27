# band11-lab

小米手环 11（`q66` / `miwear.watch.q66cn`）的开发实验场：**表盘**、**Vela 快应用**，以及把它们从电脑送进手环的整套工具链。

设备实机验证环境：小米手环 11 标准版（212×520 AMOLED，fw 4.100.139）+ iPhone（AstroBox 2.0）／macOS（AstroBox，SPP 传输）。

```
.
├── quickapp/            最小 Vela 快应用脚手架（hello world）
├── pet/                 腕上桌宠 · 18 段动画的宠物 app
├── frog/                腕上奶蛙 · 4 段动画 + 动画库  ← 最新
└── watchface/
    ├── tools/           固件下载 / 表盘提取 / bin 打包脚本
    ├── keyface/         深蓝额度 · 显示 DeepSeek 余额的表盘
    └── template/        官方表盘解包产物（wfDef.json 参考）
```

---

## 一、两条技术路线

| 路线 | 产物 | 能做什么 | 现状 |
|---|---|---|---|
| **Vela 快应用** | `.rpk` | JS + 类 CSS + 声明式 UI，能跑动画、读写存储、振动、路由 | ✅ 实机跑通 |
| **自定义表盘** | `.bin` | 纯资源包（图片 + 控件定义），**不能跑业务逻辑** | ✅ 实机跑通 |

关键限制（都是实测/查文档确认的）：

- 表盘 bin **没有动画和 JS 控件可用**：现成工具 `Mi8WfBinTool` 只支持
  `widge_pointer` / `widge_imagelist` / `widge_dignum` / `widge_process` 四种控件。
  想要动画只能走快应用。
- 快应用**拿不到健康数据**：Vela 没有 health / step / heart 接口，`@system.sensor`
  只到手环 9/9 Pro/10/S5。心率步数只能做进表盘（需要未知的 `dataSrc` 编码）。
- 手环没有音频播放、没有 WebSocket、没有 BLE GATT，联网只能靠手机端 `@system.interconnect` 桥接。

## 二、装进手环

工具链在两端分工：**电脑/手机负责推送，手环要先进配对态**。

1. 手环：`设置 → 系统操作 → 连接新手机`
2. AstroBox 连上设备（iOS 用小米账号登录即可，不需要 AuthKey）
3. 设备页 →「表盘」或「快应用」卡片 → `+` → 选本地 `.bin` / `.rpk` → 安装
4. 装完回「小米运动健康」重连手机

> 同名包会冲突：装新版本前先在应用列表里卸掉旧的。
> 包名同时是 storage 的命名空间，换包名 = 存档清零。

## 三、构建快应用

```bash
cd pet/app            # 或 frog/app、quickapp
/usr/local/bin/node ./node_modules/.bin/aiot build
# → dist/<package>.debug.<version>.rpk
```

> ⚠️ 必须用 `/usr/local/bin/node`。dsh 自带的 node 带 hardened runtime，
> 加载 rspack 原生模块会报 `code signature ... different Team IDs`。

三个 app 的 manifest 都是 `config.designWidth: 212`，UI 按 212×520 写死尺寸。

## 四、构建表盘

```bash
# 1. 从固件里捞官方表盘（脚本自带断点续传 + sha256 校验）
bash watchface/tools/get_firmware.sh
/Users/jay/.dsh/dsh-runtimes/dsh-primary-runtime/dependencies/python/bin/python3 \
  watchface/tools/extract_watchfaces.py

# 2. 改图 + 定义 → 打包（o66 档位打出来的包 q66 能装）
java watchface/Mi8WfBinTool.java pack <dir> <out.bin> o66

# 3. 重新生成「深蓝额度」表盘（拉 DeepSeek 余额）
DEEPSEEK_API_KEY=sk-xxx python3 watchface/tools/refresh_quota.py
```

表盘头部 `id` 必须换新的（9 位完整数字），否则会覆盖官方表盘；
`name` 字段是 0x68..0xA8 的 **64 字节**定长，改的时候不能改变宽度。

## 五、素材来源与授权

| 内容 | 来源 | 授权 |
|---|---|---|
| 纯代码（本仓库） | — | MIT |
| 桌宠动画 | [MerZlin/dsh-pet-indesktop](https://github.com/MerZlin/dsh-pet-indesktop) | MIT |
| 奶蛙动画 | [Nailong-Studio/wallpaper](https://github.com/Nailong-Studio/wallpaper) `pet/` | MIT |
| 表盘插画 | 用户提供（`枇杷`） | 仅个人使用 |
| 塔罗牌面 | 1760 Nicolas Conver 版（公有领域） | PD |

第三方素材目录（`pet_src/`、`frog_src/`）和官方固件/表盘样本（`_research/`、
`watchface/samples/`）**不入库**，按上面命令自行获取。

奶蛙、鲸鱼女仆均为民间二创形象，本项目仅供个人学习，请勿商用。

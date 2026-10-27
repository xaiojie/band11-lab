# 手环 11 自定义表盘（.bin）

> 结论先行：**表盘 bin 的格式已经实测跑通解包/重打包**，而且手环 11 的**出厂表盘 bin
> 可以直接从官方固件里白嫖**——不用买、不用从手环导出。本文记录实测结果、
> 工具链、以及装到 iPhone + 手环 11 上的通道。

## 0. 当前状态

| 事项 | 状态 |
| --- | --- |
| 从官方固件提取手环 11 出厂表盘 bin | ✅ 已跑通，脚本 `tools/extract_watchfaces.py` |
| 解包 bin → `wfDef.json` + `images/*.png` | ✅ Mi8WfBinTool 用 `o66` 档位可解（单脸表盘） |
| 改素材 → 重打包 → 结构自洽 | ✅ 已验证 round-trip（解包→打包→再解包，wfDef 完全一致） |
| 重打包后的 bin 被手环接受 | ⏳ 未知，需真机验证（格式无签名/无 CRC，风险主要在头部字段）；已产出两个候选：`custom_362155001*.bin` |
| 多脸市场表盘（faceCount=6）解包 | ❌ 工具报错，需自己补逆向 |
| 装到 iPhone + 手环 11 | ⏳ 通道已明确（AstroBox / 伪 CDN），未实测 |

## 1. 现成的 bin（已导出，直接可用）

`samples/` 里的文件全部来自小米官方固件 `miwear.watch.q66cn v4.100.179`
（q66cn = 手环 11 国行），是手表真正加载的出厂表盘，不是网友改的：

| 文件 | 表盘 | 大小 |
| --- | --- | --- |
| `samples/aod_362150007.bin` | 长续航表盘（单脸，适合当模板） | 22,140 B |
| `samples/aod_362150004.bin` | 默认熄屏（AOD） | 188,945 B |
| `samples/120917427702.bin` | 市场表盘 ×6（多脸/多主题） | 0.5–7 MB |
| `samples/120917426783.bin` | 同上 | |
| `samples/120917426545.bin` | 同上 | |
| `samples/120917426209.bin` | 同上 | |
| `samples/120917424130.bin` | 同上 | |
| `samples/120917417165.bin` | 同上 | |
| `samples/sku_watchface_list.csv` | sn → watchface_id → theme_id 映射（13 条） | 326 B |
| `samples/custom_362155001.bin` | **自改示例**：长续航表盘的数字染成青色，名称「手环实验室」 | 18,789 B |
| `samples/custom_362155001_hdr.bin` | 同上，但头部字段对齐官方（见 `tools/align_header.py`） | 18,789 B |

要重新提取（或换固件版本）：

```bash
python3 tools/extract_watchfaces.py <固件.zip> out_dir
# 实测: vela_resource.bin 120,946,688 B → 8 个 bin + 1 个 csv
```

固件下载（官方固件档案馆 <https://hrk666666.github.io/firmware-archives-public/>）：

```bash
./tools/get_firmware.sh            # 自动重试 + 断点续传 + sha256 校验
```

实测注意：GitHub release **直连会随机截断**（连续几次都只下到 6,201,100 B 就返回 200），
用 `curl -C -` 续传重试第 5 次才补齐；`gh-proxy.com` 镜像（约 5.7MB/s）一次性成功。

| 项 | 值 |
| --- | --- |
| 完整大小 | 66,683,899 B |
| sha256 | `a93678a9bfff68dfa36fe3ff59f8ae2c4040156c75d7559bd3fe2ab2e90ac951` |
| 包内结构 | `ota.sh` / `vela_ap.bin`(12,293,060) / `vela_ota.bin`(786,432) / `vela_resource.bin`(120,946,688) / `META-INF/*` |

`unzip -t` 应输出 `No errors detected`；`vela_resource.bin` 以 `-rom1fs-` 开头才说明是对的。

## 2. bin 格式实测（q66 / 手环 11）

头都是**小端**：

| 偏移 | 字段 | 出厂「长续航表盘」 | 市场表盘 |
| --- | --- | --- | --- |
| 0x00 | magic | `5A A5 34 12` | 同 |
| 0x04 | 版本/协议 | `00 00 01 00` | `00 00 01 07` |
| 0x10 | 设备标志 u32 | `0x00000800` | `0x00000903` |
| 0x1C | faceCount u16 | `1` | `6` |
| 0x1E | faceStyleCount u16 | `0` | `6` |
| 0x20 | preview 图块偏移 u32 | `0x368` | `0x4C60` |
| 0x28 | 表盘 id（ASCII） | `362150007`（9 位） | `120917427702`（12 位） |
| 0x68 | 名称（UTF-8） | `长续航表盘` | 如 `默认熄屏` |

图片块压缩是 **RLE**（V1.0 / V1.1 / V2.0，256 色调色板），**不是 LZMA，也没有签名/CRC**。
（早期笔记里写的「q66 压缩」是错的：q66 是设备代号，压缩是 RLE。）

单脸表盘的布局和手环 8 Pro 家族基本同构：0xA8 主头 + 0x58 脸头 + 定义表 +
图片块，所以现有工具能直接用 `o66` 档位跑。

## 3. 工具链（Mac 上可跑）

```bash
mkdir -p tools/_bin && cd tools/_bin
curl -LO https://raw.githubusercontent.com/zhy8388608/Mi8WfBinTool/main/Mi8WfBinTool.java
javac Mi8WfBinTool.java        # 需要 JDK 8+（本机 21 实测 OK）

# 解包：device 用 o66（手环 10 的代号），实测能吃手环 11 的单脸 bin
java Mi8WfBinTool unpack ../samples/aod_362150007.bin ../template_edit o66
# 产物: wfDef.json + images/*.png（含 preview.png）

# 改图：保持文件名、尺寸、格式一致；数字图建议等宽，免得跳秒抖

# 重打包
java Mi8WfBinTool pack ../template_edit ../out.bin o66
```

实测结果：

- `unpack` 单脸 bin ✅；`pack` 后再 `unpack`，`wfDef.json` 逐字节一致 ✅；
- 但重打包的 bin 与官方 bin **不是字节相同**（18,739 B vs 22,140 B，头部版本字段、
  图片排布都不同）。这不一定有问题——bin 没有签名和 CRC——但**只能真机验证**。

已知坑：

- 市场多脸表盘（`1209174xxxxx`，faceCount=6）解包报
  `Width (0) and height (0) cannot be <= 0`，说明多脸/多主题的图片表布局与单脸不同，
  要自己补逆向（`readFace` 里的图块索引）。
- 打包时工具会把 0x04 版本字段写成 0、0x1E styleCount 写成 1，与官方（1、0）不同；
  如果手环拒收，优先怀疑这里，可用小脚本把这两个字段改回官方值再试。
- id 字段 9 字节，超过 9 位的市场 id 会被截断——自用表盘建议编个 9 位数字，
  别和市场 id 撞。

### 改一版试试（本地已跑通）

解包好的模板就在 `template/`（`wfDef.json` + 27 张 PNG），直接改它：

```bash
cp -R template /tmp/edit_face
# 改图：尺寸/文件名不变；或改 /tmp/edit_face/wfDef.json 的 name / id
java Mi8WfBinTool pack /tmp/edit_face /tmp/custom.bin o66
# 可选：把头部字段对齐官方参考 bin
python3 tools/align_header.py /tmp/custom.bin samples/aod_362150007.bin /tmp/custom_hdr.bin
```

`template_edit → custom_362155001.bin` 就是这么来的：把数字图染青、名字改成「手环实验室」、
id 改成 `362155001`，打包 18,789 B，再解包回去 `wfDef.json` 结构一致。

## 4. 装到 iPhone + 手环 11

手环 11 标准版（非 NFC）走蓝牙，iPhone 上没有「本地安装表盘」按钮，只有三条路：

### A. AstroBox 2.0（首选）

- iOS/Mac 版，小米账号登录；**iOS 端不需要 AuthKey**（安卓才要）。
- 用它连手环 → 表盘管理/本地安装 → 选 `.bin`。
- 官方仓库：GitHub `AstralSightStudios/AstroBox-*`（iOS 版在 TestFlight/企业分发，
  具体入口看项目 README）。

### B. 伪 CDN 服务器（老办法，已验证可用的一代方案）

`AstralSightStudios/XiaomiFitnessServer_S3_iOS`：

1. 电脑跑 node 服务（端口 3819），把自定义 bin 改名 `wf/resource.bin`；
2. iPhone 开 ShadowRocket 全局代理 → 电脑；
3. 电脑端 Fiddler/Charles 把
   `https://cdn.cnbj1.fds.api.mi-img.com/hlth-operate/watch_face/*.zip`
   重写到 `http://localhost:3819/`；
4. 小米运动健康 App 里选一个**没下载过**的表盘点安装（App 有缓存，装过的会直接命中缓存）。

### C. 官方 App 商店（只限 rpk 应用，不适用表盘）

小米运动健康 → 设备 → 手表应用商店，可以云端装 rpk 快捷应用；表盘商店里只能选官方
上架的表盘，第三方 bin 进不去。

## 5. 风险

- 装坏表盘一般能切回默认表盘恢复，但**刷写时别断连/断电**；
- 跨固件版本套模板可能黑屏（结构会变），换固件后先重新提取样本；
- 重打包 bin 的兼容性没保证，第一次测试建议用「只改一张图」的最小改动；
- 市场表盘 bin 是官方资源，自己玩可以，别二次分发。

## 6. 下一步（按投入排序）

1. **真机验证**：拿 `samples/aod_362150007.bin` 原样装一次，确认这条通道通；
2. 用 `template/` 改一张图（比如背景），重打包后装，确认改包也被接受；
3. 补多脸 bin 的解包（`1209174xxxxx`），这样能直接改市场表盘；
4. 写个 `make_face.py`：给一张背景图 + 时间数字图，直接出 bin（省掉手工拖拽）。

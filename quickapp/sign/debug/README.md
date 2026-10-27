# 调试签名（debug）

AIoT-IDE 在「运行 / 打包」时会自动为项目生成调试证书并签出可安装的 `.rpk`，
一般**不需要**手工放文件。只有在你脱离 AIoT-IDE 手工打包时才需要下面的材料：

| 文件 | 作用 |
| --- | --- |
| `private.pem` | 调试私钥（**不要提交到 git**，已被 `.gitignore` 忽略） |
| `certificate.pem` | 自签证书 |
| `debugProfile.json` | 调试 profile（AIoT-IDE 生成，记录包名与证书指纹） |

手工生成自签证书（可选）：

```bash
cd sign/debug
openssl genrsa -out private.pem 2048
openssl req -new -key private.pem -out cert.csr \
  -subj "/C=CN/ST=Beijing/L=Beijing/O=Band11Lab/OU=Dev/CN=com.jay.band11hello"
openssl x509 -req -in cert.csr -signkey private.pem -out certificate.pem -days 3650
```

> 调试签名的 rpk 只能本地安装（AstroBox / 开发者模式），不能上架。
> 签名算法与 profile 字段格式以 AIoT-IDE 生成物为准，不要自己臆造。

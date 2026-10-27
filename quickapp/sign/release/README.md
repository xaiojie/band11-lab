# 正式签名（release）

只有需要**上架小米应用商店（穿戴）**时才用正式签名，自用/本地安装一律用 `../debug`。

流程要点：

1. 在小米开放平台（Vela 应用）注册开发者、创建应用，拿到正式证书与 profile。
2. 把平台下发的 `private.pem` / `certificate.pem` / `releaseProfile.json` 放到本目录。
3. AIoT-IDE 打包时选择正式证书，产出可上架的 `.rpk`。
4. 每次改包都要把 `manifest.json` 里的 `versionCode` +1，否则会被判重。

注意：
- 正式私钥等同账号资产，切勿提交到 git（`.gitignore` 已忽略 `*.pem`）。
- 应用名称、包名、图标需与开放平台登记信息一致，否则审核不通过。

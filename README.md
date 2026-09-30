# stash-rules

自用的 Stash 规则。分两部分：

## 手写规则 `rule-set/`

纯文本，`behavior: domain`，`format: text`。

| 文件 | 用途 |
|---|---|
| `ads-domain` | 补充的广告/跟踪域名 |
| `can-be-direct` | 需要直连的域名 |
| `others-should-be-proxied` | 需要走代理的域名 |

```yaml
url: https://raw.githubusercontent.com/zaochih/stash-rules/refs/heads/main/rule-set/ads-domain
```

## 自建 geosite `release` 分支

由 GitHub Action 每天用 [v2fly/domain-list-community](https://github.com/v2fly/domain-list-community) 官方工具构建，
列表名单见 `geosite.list`，产物：

```yaml
behavior: domain
format: mrs
url: https://raw.githubusercontent.com/zaochih/stash-rules/refs/heads/release/geosite/geolocation-cn.mrs
```

`name@attr` 形式（如 `apple@cn`）表示只取带该属性的条目。每个 `.mrs` 旁边有同名 `.list` 明文，方便排查。

### 为什么不直接用 MetaCubeX/meta-rules-dat

它用 Loyalsoldier/domain-list-custom 的解析器处理 v2fly 数据，该解析器不支持 `include:X @-!cn`（排除属性）语法，
导致 `geolocation-cn` 里 bytedance/feishu/tencent/alibaba/jd 等整块子列表缺失。
详见 Loyalsoldier/domain-list-custom#135。

### 合并生成的 `cn`

`merge.list` 把 v2fly 的 `tld-cn` + `geolocation-cn` 和 [ChinaMax](https://github.com/blackmatrix7/ios_rule_script) 合并，
并删除被父级后缀覆盖的子域名。ChinaMax 条目多但没有 `.cn` 顶级域，v2fly 则带有飞书/字节等完整的公司列表，二者互补。

### 限制

- `regexp:` 和 `keyword:` 规则无法放进 `domain` 类型的 mrs，构建时会丢弃并在日志里提示数量。
- `cn` 依赖 ChinaMax 的第三方数据，口径与 v2fly 的 `cn` 不同，条目约 11 万。

### 本地构建

```sh
names=$(python3 scripts/build.py --print-export-names)
git clone --depth 1 https://github.com/v2fly/domain-list-community community
(cd community && go run ./ --datapath=./data --outputdir=../plain --exportlists="$names")
python3 scripts/build.py --plain-dir plain --out-dir dist --mihomo mihomo
```

# Quantumult X 自用配置

可订阅的 AI 分流规则、DNS 片段和简易主配置。AI 出口使用手动策略组，可以在 QX 中选择任意已导入节点。

## 链接

| 内容 | 链接 |
| --- | --- |
| AI 规则，供远程分流订阅 | [rules/ai.list](https://raw.githubusercontent.com/memoryttt/quantumultx-config/main/rules/ai.list) |
| AI 域名专用 DNS，复制到现有配置 | [snippets/ai-dns.conf](https://raw.githubusercontent.com/memoryttt/quantumultx-config/main/snippets/ai-dns.conf) |
| 策略组和订阅接入示例 | [snippets/integration.conf](https://raw.githubusercontent.com/memoryttt/quantumultx-config/main/snippets/integration.conf) |
| 简易完整主配置 | [qx.conf](https://raw.githubusercontent.com/memoryttt/quantumultx-config/main/qx.conf) |

## 已经使用墨鱼等现有配置

保留现有主配置，合并下面的条目到对应分节。不要重复创建分节。

在 `[policy]` 增加手动策略组：

```ini
static = AI, proxy, server-tag-regex=.*
```

在 `[filter_remote]` 添加：

```ini
https://raw.githubusercontent.com/memoryttt/quantumultx-config/main/rules/ai.list, tag=自用AI, force-policy=AI, update-interval=86400, enabled=true
```

如果原来启用了 `Ai-All-In-One`，希望以本仓库清单为准，可用这一行替换原 AI 订阅行，避免两份 AI 规则重复匹配。新清单只覆盖下文列出的服务，其他服务按现有规则处理。

将 `snippets/ai-dns.conf` 的条目追加到 `[dns]`。它是配置片段，不能作为远程分流资源导入。保留 `no-system`、`no-ipv6` 及现有国内 DNS，可实现“所列域名用境外 DoH，其余保持原设置”。如果之前添加过同域名 DNS 条目，应替换旧条目，避免重复。

最后在 QX 的“AI”策略组里手动选择希望使用的节点。也可让 `force-policy` 指向你现有的任意策略组，规则文件本身不绑定具体节点。

## 从简易主配置开始

先备份现有配置，再导入 `qx.conf`。这是独立的最小配置，包含 AI 手动分组、全球加速手动分组、局域网和国内直连、其余代理。它不包含墨鱼配置的广告规则、重写、脚本或证书。

节点订阅在 QX 本机添加，并在“AI”和“全球加速”组中选择节点。本仓库不提供节点；默认 `proxy` 使用 QX 当前选择的代理，导入节点前不能依靠它联网。

不要将私人订阅 URL、Sub-Store token、节点密码或 MITM 证书上传至公开仓库。重新导入主配置前保存本机的私人设置，更新可能覆盖这些设置。

## 可配置项

只维护两个源文件，GitHub Actions 会自动生成输出并提交到 `main`：

- [`config/settings.json`](config/settings.json)：策略组名称 `policy_name`、节点名称正则 `node_filter`、规则更新间隔、DNS 服务器和模式。`node_filter` 使用 QX 的正则语法，例如 `美国|日本|US|JP`；默认 `.*` 列出所有节点。
- [`config/ai-domains.json`](config/ai-domains.json)：域名、匹配类型及启用开关。`suffix` 覆盖主域名和子域名；`exact` 只覆盖指定主机；`enabled: false` 暂停该条目。

`dns.mode` 支持：

| 值 | 简易主配置的解析设置 |
| --- | --- |
| `split`，默认 | 清单中的域名使用 `ai_doh`，其余使用 `default_servers` |
| `global` | 默认使用 `ai_doh`，不添加国内默认 DNS |

`snippets/ai-dns.conf` 始终只含域名专用 DNS 条目，便于合并到其他配置。它不会自动改变你的现有主配置。

策略组当前选中的节点保存在 QX 本机，日常切换不需要修改仓库。`rules/ai.list` 里的通用 `proxy` 由订阅行的 `force-policy` 覆盖。修改策略组名称后，也要同步 QX 本机的策略定义和订阅行；仅更新规则不会改组名。

规则默认每 86400 秒更新一次，也可以在 QX 手动刷新。GitHub Actions 生成成功后，Raw 链接可能仍有短暂缓存。DNS、策略组或其他主配置变更，需要刷新主配置或重新合并对应片段，不能随规则订阅自动更新。

本地生成和验证：

```sh
python3 -m unittest discover -s tests -v
python3 scripts/generate.py
```

Python 仅使用标准库。生成器检查域名及配置字段，并确保 DNS 与分流使用同一清单。

## 初始清单与验证边界

初始清单来自本人的 Clash Verge `AI_DOMAINS`，去掉重复覆盖后为 13 项：Claude、OpenAI 及相关依赖。Gemini 在源配置中未启用，因此这里没有自动添加。

`sentry.io` 是共享服务后缀，匹配范围包括其他应用；`cdn.growthbook.io`、`challenges.cloudflare.com` 使用精确主机匹配。`chatgpt.site` 沿用原有清单，这不代表它属于 OpenAI。可以在域名文件中关闭或删除任一条目。

DoH 加密和指定境外解析器，不等于 DNS 连接本身一定通过所选代理。QX 中的 DNS 与代理远端解析也不等同于 Mihomo 的 `#策略名` 行为。`split` 模式下，未列入清单的检测域名仍可能显示国内解析器。`no-ipv6` 控制 AAAA 解析，不能据此推断所有系统 IPv6 流量都已阻断。

默认丢弃 STUN 和 QUIC，这可能影响部分实时音视频及 HTTP/3。若需要这些功能，可以在主配置的 `[general]` 中调整 `udp_drop_list`。

自动检查验证生成逻辑、匹配范围、可配置策略及输出一致性；尚不代表 iPhone 上的导入、连通性或防泄露效果已经实测。

语法依据：[Quantumult X 官方示例](https://github.com/crossutility/Quantumult-X/blob/master/sample.conf)。

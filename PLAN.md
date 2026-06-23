# novada-python 开发计划

将 Go SDK `novada-go` 移植为功能等价、风格地道的 Python 包。本计划与 `PROMPT.md`
配套：PROMPT 给 Claude Code 当系统级指令，PLAN 给人看进度与验收。

## 关键设计映射（从 Go 源码提取）

| Go 设计 | Python 对应 |
|---|---|
| 顶层 `Client`，三个 baseURL + Bearer 注入 + 重试 | `Client(api_key, *, base_url=..., web_unblocker_url=..., scraper_url=..., timeout=30, max_retries=2)` |
| Functional Options (`WithTimeout`...) | 构造函数关键字参数 |
| 子包 `proxy`/`scraper`/`wallet`，通过 `transport.Doer` 接口解耦 | 子模块 + 内部 `Transport` 协议，子服务挂在 `client.proxy/.scraper/.wallet` |
| 参数 struct + 客户端必填校验 → `ValidationError` | `@dataclass` 参数对象 + 校验抛 `ValidationError` |
| 统一响应包 `{code,data,msg,timestamp}`，仅 `code==0` 成功 | `_envelope.decode`，`code!=0` → `APIError` |
| `APIError` + `IsAuthError`/`IsRateLimited`/`CodeOf` | `NovadaError → APIError → AuthError/RateLimitError`，保留 `.code`/`.http_status` |
| 两套编码：multipart（/v1/*）、x-www-form-urlencoded（/request） | 两个 transport helper（含 `_raw` 变体） |
| 重试只针对网络错误 + 429/5xx，绝不重试业务 code | 同语义 |
| 抓取响应格式不定，返回原始字节/字符串 | `do()` 返回 raw；Google 走结构化解码 |
| 仅标准库 | 单一运行时依赖 `httpx` |

## 准备工作
- `reference/novada-go/`：Go 源码（`*.go`、`README.md`、`novada-go-sdk-spec.md`）。
- `reference/openapi/`：`novada-openapi.json`、`webunblocker_openapi.json`、`Serpapi_openapi.json`。
  （用仓库根的 `scripts/sync_reference.sh` 同步，见文末。）
- 确认 PyPI 分发名（`novada` 还是 `novada-sdk`）与最终仓库地址。

## 里程碑

### M0 — 脚手架与基础设施（半天）
- `pyproject.toml`（src 布局、httpx 依赖、ruff/mypy/pytest dev 依赖、py.typed）、`LICENSE`(MIT)、`_version.py`。
- `errors.py`：`NovadaError / APIError / AuthError / RateLimitError / ValidationError`。
- `_envelope.py`：envelope 解码 + `code!=0` 转 `APIError` + list 解包 helper。
- `_transport.py`：`do_multipart` / `do_form_urlencoded`（含 `_raw` 变体）、Bearer 注入、
  `Accept`/`User-Agent` 头、线性退避重试（仅网络错误 + 429/5xx）、`joinurl`、
  非 2xx → `AuthError`/`RateLimitError`/`APIError` 映射。
- `client.py`：构造、三 baseURL、env 回退、子服务装配（先留空）。
- **验收**：respx mock 一个 `white_list/list`，断言 Bearer 头、multipart body、envelope 解包、
  `code!=0` 抛 `APIError`。`ruff/mypy/pytest` 全绿。

### M1 — Proxy 最小闭环（半天）
- `proxy/_base.py`：form builder（req/opt 系列）、validator、分页默认值。
- `proxy/whitelist.py` + `proxy/account.py`，对应 `types.py` 的 Params/返回 dataclass + `Product` 枚举。
- **验收**：每个方法的成功路径 + `ValidationError`（必填缺失）单测；确立"参数 dataclass +
  校验 + form 编码 + 解码"的可复制模式。

### M2 — Proxy 全量铺开（1–1.5 天）
- 依据 `novada-openapi.json` 的 requestBody properties，批量生成
  `residential / mobile / rotating_isp / rotating_dc / static_isp / dedicated_dc /
  unlimited / prohibit_domain` 的方法、Params、返回类型与必填校验。
- 注意：导出类（静态 IP export）返回文件流 → 用 `_raw` 变体不走 envelope（对应 Go 的 `DoMultipartRaw`）。
- 共享类型：`TimeRange`、`FlowBalance`、`FlowConsumeLog` 等。
- **验收**：每个子服务至少一个编码 + 解包单测；mypy 友好。

### M3 — Scraper 通用驱动（半天）
- `scraper/__init__.py`：`Target` 枚举、`Request`/`Response` dataclass、`do()`
  （`scraper_params=json.dumps(params)`，整体 urlencode，按 `target` 选 host，返回 raw）、`ValidationError`。
- **验收**：单测断言 urlencoded body、`scraper_params` JSON、host 路由
  （ScraperAPI vs WebUnblocker）、`scraper_errors`。

### M4 — Scraper 强类型 + 查询接口（半天）
- `api.youtube.video_post`（薄封装 `do`）、`api.google.search`
  （**扁平 form 字段 + envelope 结构化解码**，对应 `GoogleSearchResult/Data`，`json` 字段保留为原始/`Any`）。
- `unblocker.scrape`（发 `target_url`/`response_format`/`js_render`/`country`/`wait_ms`，
  解码 `UnblockerResult`：HTML/Code/Msg/MsgDetail/UseBalance）。
- 走通用 host 的查询：`unblocker.countries()`、`browser.countries()`、`universal.balance()`、`universal.unit()`。
- **验收**：Google 结构化解码单测；unblocker scrape 字段单测；查询接口走通用 host 验证。

### M5 — Wallet（半天）
- `wallet.balance()`、`wallet.usage_record(...)`（分页默认 1/10）。
- **验收**：单测覆盖分页默认值 + 解码。

### M6 — 文档、示例、打包、CI（半天）
- `README.md`：安装、quick start、三 baseURL 表、proxy/scraper/wallet 各一例、错误处理示例（对齐 Go 版）。
- `examples/`：proxy / scraper / wallet 各一个可运行脚本（读 `NOVADA_API_KEY`）。
- `.github/workflows/ci.yml`：Python 3.9–3.13 矩阵，`ruff check` + `ruff format --check` + `mypy src` + `pytest`。
- `py.typed` 标记、`__init__.py` 导出面收敛。
- **验收**：`pip install -e .` 后 import 与示例可跑；CI 绿。

## 风险与注意点
- **OpenAPI 是字段真相**：表单字段以 `novada-openapi.json` 的 requestBody 为准，逐字段核对必填/可选。
- **`code==0` 才成功**：最容易踩的坑，不要用 HTTP 200 判断。
- **空值省略语义**：可选字段空字符串/零值不发送；三态布尔用 `Optional[bool]`。
- **抓取响应不解 envelope**（除 Google Search 外），格式不定，原样返回。
- **重试边界**：业务 `code!=0` 永不重试。

## 参考同步脚本
仓库根的 `scripts/sync_reference.sh` 会把 Go 项目源码与 OpenAPI 拷入 `reference/`。
如 Go 项目路径不同，编辑脚本顶部的 `GO_SRC` 变量。
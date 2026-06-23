# 任务：把 novada-go SDK 移植为一个 Python 包（novada-python）

你要在当前空仓库里，参照一份成熟的 Go SDK，实现一个**功能等价、API 风格地道**
的 Python SDK，用于 Novada API（代理管理 / 抓取 / 钱包）。

## 输入材料（必须先读）
1. Go 源码参考实现（权威设计来源），位于 `./reference/novada-go/`：
   - `client.go` `config.go` `transport.go` `errors.go` `envelope.go` `version.go`
   - `internal/transport/transport.go`（子服务依赖的接口）
   - `proxy/*.go` `scraper/*.go` `wallet/*.go`
   - `README.md` `novada-go-sdk-spec.md`（中文设计规范，含实施顺序）
2. OpenAPI 文档（接口字段的权威来源，用来生成参数与必填校验），位于 `./reference/openapi/`：
   - `novada-openapi.json`（51 个 /v1/* 管理接口）
   - `webunblocker_openapi.json`（Web Unblocker /request）
   - `Serpapi_openapi.json`（Google Search 等 scraper 参数）

   先把 Go 源码当作"形状"，把 OpenAPI 当作"字段事实来源"。两者冲突时以 OpenAPI 为准，
   并在代码注释里标注。

## 核心架构事实（不要重新发明）
- 鉴权：每个请求注入 `Authorization: Bearer <API_KEY>`。
- **三个 base URL**，全部可覆盖，默认指向生产：
  - 通用 `https://api-m.novada.com` —— 所有 `/v1/*`（proxy、wallet，以及 scraper 目录下查
    地区/余额/单价的 /v1/* 接口）
  - Web Unblocker `https://webunlocker.novada.com` —— 仅 Web Unblocker 的 `POST /request`
  - Scraper API `https://scraper.novada.com` —— 仅 Scraper API 的 `POST /request`
- **两套传输编码**：
  - `/v1/*` 管理接口：`multipart/form-data`，空值字段省略；响应是统一包裹。
  - 抓取 `/request`：`application/x-www-form-urlencoded`；字段 `scraper_name`、`scraper_id`、
    `scraper_params`（Params 列表 JSON 序列化后的字符串）、可选 `scraper_errors=true`。
- **统一响应包裹** `{code, data, msg, timestamp}`，**只有 `code==0` 才算成功**。
  解包流程：HTTP 非 2xx → APIError(http_status)；2xx 但 code!=0 → APIError(code,msg)；
  成功 → 把 `data` 解码进目标类型。
- **重试**：仅对网络错误和 HTTP 429/5xx 重试（线性退避，base 200ms × attempt），
  绝不对业务 code!=0 重试。重试次数 `max_retries` 默认 2。
- 列表接口的 data 形如 `{list:[...], total:N}`（个别还带 page/count）。
- 抓取 `/request` 的响应体是抓取产物本身（JSON/CSV/XLSX），格式不定 → 返回原始文本，
  不走 envelope 解码。例外：Google Search 走 envelope 并结构化解码（见 sources.go）。

## Python 化的设计决定（请严格执行）
- 目标 Python 版本：3.9+；全程类型注解，文件顶部 `from __future__ import annotations`。
- 唯一运行时依赖：`httpx`（同步 Client；结构上为将来加 async 留余地，但本次只交付同步）。
- 包名：分发名 `novada`（被占用则 `novada-sdk`），import 名 `novada`。`src/` 布局，含 `py.typed`。
- 顶层入口：

      from novada import Client
      client = Client("API_KEY")            # 空则回退读环境变量 NOVADA_API_KEY
      client = Client("API_KEY", base_url=..., web_unblocker_url=..., scraper_url=...,
                      timeout=30.0, max_retries=2, http_client=None, user_agent=...)

  无 key 且环境变量也空 → 抛 `NovadaError`（对应 Go 的 ErrNoAPIKey）。
- 子服务作为属性挂载（蛇形命名）：

      client.proxy.whitelist.list(...) / .add(...) / .delete(...) / .remark(...)
      client.proxy.account / .residential / .mobile / .rotating_isp / .rotating_dc /
                   .static_isp / .dedicated_dc / .unlimited / .prohibit_domain
      client.scraper.do(req) / .api.youtube.video_post(...) / .api.google.search(...) /
                     .unblocker.scrape(...) / .unblocker.countries() /
                     .universal.balance() / .universal.unit() / .browser.countries()
      client.wallet.balance() / .usage_record(...)

- 每个方法的参数用 `@dataclass` 参数对象（与 Go 的 *Params struct 一一对应），
  必填字段缺失在发请求前抛 `ValidationError`（列出所有缺失字段名，对应 Go 的 validator）。
  可选字段为空/零值时不发送（对应 Go 的 optStr/optInt）。需要"未设置 vs 设为 false"
  语义的布尔（Go 里是 *bool）用 `Optional[bool] = None`。
- 枚举：`Product(IntEnum)`，值固定（1 住宅 / 2 RotatingISP / 3 RotatingDC / 4 Unlimited /
  5 StaticISP / 7 Unblocker / 9 Mobile / 10 BrowserAPI）。
- 返回值：管理接口的 data 解码进 `@dataclass`（字段名直接对齐 JSON 的 snake_case key，
  解码时忽略未知 key 以向前兼容）；抓取 `do()` 返回 `Response(raw: str)`。
- 错误类型（在 `novada/errors.py`）：

      NovadaError(Exception)                  # 基类
      APIError(NovadaError)                    # 有 .http_status / .code / .message
      AuthError(APIError)                      # http 401/403
      RateLimitError(APIError)                 # http 429
      ValidationError(NovadaError)             # 客户端必填校验，有 .method / .fields

  同时提供与 Go 对齐的便捷判断（属性或函数皆可），如 err.code、isinstance 检查。

## 目录结构（建议）

    pyproject.toml
    README.md
    LICENSE                      # MIT，与 Go 版一致
    src/novada/
      __init__.py                # 导出 Client、错误类型、Product、版本号
      _version.py                # __version__ = "0.1.0"
      client.py                  # Client：三 baseURL、Bearer、构造、子服务装配
      _transport.py              # do_multipart / do_form_urlencoded（+ _raw 变体）、重试、joinurl
      _envelope.py               # envelope 解码 + code!=0 → APIError + list 解包
      errors.py
      proxy/
        __init__.py              # ProxyService 装配各子服务
        _base.py                 # form builder + validator + 分页默认值
        whitelist.py account.py residential.py mobile.py rotating.py static.py
        dedicated.py unlimited.py prohibit_domain.py
        types.py                 # 各 Params / 返回 dataclass / Product 枚举
      scraper/
        __init__.py              # ScraperService、Target 枚举、do()、Request/Response
        api.py                   # youtube / google 强类型封装
        unblocker.py universal.py browser.py
        types.py
      wallet/
        __init__.py
    tests/
    examples/proxy.py examples/scraper.py examples/wallet.py
    .github/workflows/ci.yml

## 测试与 CI
- 用 `pytest` + `respx`（mock httpx）模拟 `{code,data,msg,timestamp}` 响应。
  必须覆盖：code!=0 → APIError；HTTP 401/403/429/5xx 映射到对应异常；multipart 与
  urlencoded 的编码正确（含 scraper_params 的 JSON 序列化 + 空值省略）；Bearer 注入；
  list 解包；重试逻辑（429→重试、业务 code!=0→不重试）；ValidationError 在发请求前触发。
- 集成测试用环境变量 `NOVADA_API_KEY` 控制是否运行（pytest mark + skipif）。
- CI：GitHub Actions，矩阵 Python 3.9–3.13，跑 `ruff check`、`ruff format --check`、
  `mypy src`、`pytest`。
- 工具：ruff（lint+format）、mypy（strict 友好），全部配置进 pyproject.toml。

## 实施顺序（务必分步，每步先跑通再继续；详见 PLAN.md）
1. 脚手架 + 顶层 Client + transport + envelope + errors，用 respx 跑通一个最简管理
   接口（white_list/list）验证解包与 Bearer。
2. proxy.whitelist + proxy.account（最简单 CRUD），配单测，确立 multipart + dataclass 模式。
3. 按 OpenAPI 批量铺开 proxy 其余子服务（用 requestBody properties 生成 Params 与必填校验）。
4. scraper.do 通用驱动（urlencoded + scraper_params JSON），单测验证编码。
5. scraper.api.youtube / api.google（结构化）/ unblocker.scrape + 各 /v1/* 查询接口。
6. wallet。
7. README + examples + CI + py.typed + 打包元数据。

## 约束
- 不要引入 requests/aiohttp 等多余依赖；运行时只用 httpx + 标准库。
- 不要把 HTTP 200 当成功——一律以 code==0 判定。
- 保持与 Go 版 README 等价的文档示例（同样的三个 baseURL 表、错误处理示例）。
- 每完成一步运行 `ruff`、`mypy`、`pytest`，全绿再进入下一步。
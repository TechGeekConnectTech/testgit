# MarketMind AI — System Architecture

> **Educational platform.** Every output is informational, not financial advice.

---

## 1. Architectural principles

Five rules drive every decision in this document. When a later choice looks
arbitrary, trace it back to one of these.

| # | Principle | Consequence |
|---|-----------|-------------|
| 1 | **Deterministic work belongs in Python** | RSI, MACD, scores and P&L are computed by code with unit tests. The LLM never does arithmetic. |
| 2 | **The LLM explains; it never sources facts** | Every number in an AI response must already exist in the structured bundle we handed the model. A validation node enforces this programmatically. |
| 3 | **Every external dependency is a provider interface** | Broker, news and LLM are swappable. Demo Mode is not a special code path — it is a different provider registration. |
| 4 | **Secrets never cross the network boundary to the browser** | The React app holds no API keys. All third-party calls originate from FastAPI. |
| 5 | **Explainability over cleverness** | Scores expose their components and weights. Retrieval exposes its citations. Nothing is a black box a student cannot narrate. |

---

## 2. High-level system architecture

```
                                 ┌─────────────────────────┐
                                 │        Browser          │
                                 │  React 18 + Vite + TS   │
                                 │  Tailwind · TanStack    │
                                 │  Query · Recharts       │
                                 └────────────┬────────────┘
                                              │ HTTPS
                                              │ JSON over REST
                                              │ + SSE for chat streaming
                                              │ httpOnly refresh cookie
                                 ┌────────────▼────────────┐
                                 │      Nginx (443)        │
                                 │  TLS · static assets    │
                                 │  /api/* reverse proxy   │
                                 │  gzip · security headers│
                                 └────────────┬────────────┘
                                              │
                                 ┌────────────▼────────────┐
                                 │   FastAPI (uvicorn)     │
                                 │  ─────────────────────  │
                                 │  API layer  (routers)   │  ← validation, authz, HTTP only
                                 │  Service layer          │  ← business rules, no HTTP concerns
                                 │  Repository / ORM       │  ← SQLAlchemy 2.0
                                 └──┬────┬────┬────┬───┬───┘
                                    │    │    │    │   │
              ┌─────────────────────┘    │    │    │   └──────────────────┐
              │                ┌─────────┘    │    └────────┐             │
              ▼                ▼              ▼             ▼             ▼
     ┌────────────────┐ ┌───────────┐ ┌─────────────┐ ┌──────────┐ ┌───────────────┐
     │  PostgreSQL 16 │ │  Redis 7  │ │  ChromaDB   │ │ AI Layer │ │  Scheduler    │
     │  system of     │ │  cache ·  │ │  vector     │ │ LangChain│ │  APScheduler  │
     │  record        │ │ rate limit│ │  index      │ │ LangGraph│ │  periodic jobs│
     └────────────────┘ └───────────┘ └─────────────┘ └────┬─────┘ └───────────────┘
                                                            │
                                          ┌─────────────────┼─────────────────┐
                                          ▼                 ▼                 ▼
                                    ┌──────────┐     ┌────────────┐    ┌────────────┐
                                    │  OpenAI  │     │  yfinance  │    │ Kite Connect│
                                    │ chat +   │     │ Yahoo      │    │ (Zerodha)   │
                                    │ embedding│     │ Finance    │    │  read+order │
                                    └──────────┘     └────────────┘    └────────────┘
                                                            │
                                                     ┌──────▼──────┐
                                                     │News provider│
                                                     │RSS│NewsAPI  │
                                                     └─────────────┘
```

### Why each box exists

**Nginx** — terminates TLS, serves the compiled React bundle as static files, and
proxies `/api/*` to FastAPI. Keeping static delivery out of Python means the app
server only does application work. It is also where security headers (HSTS, CSP,
X-Frame-Options) are applied once for the whole site.

**FastAPI** — async by nature, which matters because most of what this backend
does is *wait*: on Yahoo, on OpenAI, on Postgres. Async lets one worker hold
hundreds of in-flight waits. Pydantic gives request/response validation and a
free OpenAPI schema at `/docs`.

**PostgreSQL** — the system of record. Everything durable and relational lives
here: users, portfolios, orders, analyses, chat history, and the canonical text of
every RAG chunk.

**Redis** — three jobs, explained in §7: read-through cache for market data,
rate-limit counters, and short-lived locks that stop duplicate refresh work.

**ChromaDB** — the vector index for semantic retrieval. Note the word *index*: the
authoritative chunk text lives in Postgres, so Chroma can be rebuilt from scratch
at any time. This is a deliberate durability choice.

**AI layer** — LangChain for model/prompt/tool/retriever plumbing, LangGraph for
orchestrating the multi-step analysis workflow. Detailed in `03-ai-architecture.md`.

**APScheduler** — in-process periodic jobs (market snapshot refresh, nightly
recommendation batch, news polling). Chosen over Celery for the MVP because it
adds zero new infrastructure and is one file a student can read end to end. §8
explains exactly when to graduate to Celery.

---

## 3. Request lifecycle — the three paths worth memorising

Students grasp the system fastest by tracing three concrete requests.

### Path A — cheap read: `GET /api/v1/stocks/TCS.NS`

```
React (TanStack Query, cached 30s)
  → Nginx → FastAPI router (auth dependency verifies JWT)
  → StockService.get_quote("TCS.NS")
      → Redis GET quote:TCS.NS            ── HIT (95% of the time) → return, ~3 ms
      → MISS: yfinance fetch (~400 ms)
        → upsert stock_quotes row (last-known-good)
        → Redis SETEX quote:TCS.NS 30s
  → Pydantic response model → JSON
```

The `stock_quotes` table is the fallback tier: if Yahoo is down *and* Redis is
cold, we serve the last known value **with its timestamp and a `stale: true`
flag** rather than an error. Showing stale-but-labelled data beats showing
nothing — and teaching that tradeoff is the point.

### Path B — expensive AI write: `POST /api/v1/stocks/TCS.NS/analyze`

```
React "Analyze with AI" button
  → FastAPI (per-user LLM rate limit checked in Redis)
  → returns 202 + analysis_id immediately; work runs in background task
  → LangGraph workflow (see 03-ai-architecture.md §4)
      fetch quote ┐
      indicators  ├─ run concurrently (asyncio.gather)
      fundamentals│
      news        │
      RAG         ┘
      → deterministic scoring (pure Python, no LLM)
      → build SourceBundle (the ONLY facts the LLM may use)
      → OpenAI structured-output call
      → validation node: numeric grounding + banned-phrase check
      → persist stock_analyses row (scores, rubric_version, bundle hash, tokens, latency)
  → React polls GET /api/v1/analysis/{id} until status=complete
```

Returning `202` rather than blocking for 8–15 seconds is what keeps the UI
responsive and lets us show a real progress indicator per workflow node.

### Path C — order placement (the safety-critical one)

```
React order form → Order Confirmation modal (explicit human step)
  → POST /api/v1/orders  { ..., idempotency_key }
  → OrderService
      → validate symbol, quantity > 0, market hours, sufficient funds
      → record confirmed_by_user_at  ← the audit proof a human approved
      → BrokerProvider.place_order()   [MockBroker | KiteBroker]
      → persist orders row + audit_logs row
  → return order with broker_order_id
```

**No AI code path can reach `OrderService.place_order`.** The AI tool registry
simply does not contain an order-placing tool. This is enforced structurally, not
by prompt instruction — a prompt can be talked around, a missing function cannot.

---

## 4. Backend architecture

### Layering rules

```
api/routes/      HTTP only: parse, authorize, delegate, serialize.
                 No business logic. No direct DB session use beyond passing it down.
     ↓
services/        All business rules. Framework-agnostic — a service function
                 could be called from a CLI or a scheduled job unchanged.
     ↓
models/ + db/    SQLAlchemy 2.0 ORM, sessions, transactions.

ai/              Depends on services (for tools); services never import ai.
                 One-way dependency keeps the core testable without an API key.
core/            config, security, logging, exceptions — imported by everyone.
```

The rule that earns its keep: **`ai/` may import `services/`, never the reverse.**
It means the entire market-data and scoring engine is unit-testable with no
OpenAI key present, which is exactly what you want in CI and in a classroom where
not every student has billing set up.

### Folder structure

```
backend/
├── app/
│   ├── main.py                   # app factory, middleware, router mounting, lifespan
│   ├── api/
│   │   ├── deps.py               # get_db, get_current_user, require_demo_off, rate_limit
│   │   └── routes/
│   │       ├── auth.py           # Google OAuth, refresh, logout, /me
│   │       ├── market.py         # indices, overview, trend, gainers/losers
│   │       ├── stocks.py         # search, detail, history, technical, fundamentals, risk
│   │       ├── analysis.py       # AI analysis trigger + retrieval
│   │       ├── news.py
│   │       ├── chatbot.py        # sessions, messages, SSE stream
│   │       ├── rag.py            # search, ingest, documents
│   │       ├── watchlist.py
│   │       ├── portfolio.py
│   │       ├── orders.py
│   │       ├── broker.py         # Zerodha connect / callback / sync / disconnect
│   │       ├── reports.py
│   │       ├── recommendations.py
│   │       └── system.py         # /health, /config (demo flag, feature flags)
│   ├── core/
│   │   ├── config.py             # pydantic-settings, single source of env truth
│   │   ├── security.py           # JWT issue/verify, Fernet encryption, CSRF
│   │   ├── logging.py            # structlog JSON, request-id binding, secret redaction
│   │   ├── exceptions.py         # domain exceptions → HTTP mapping
│   │   └── cache.py              # Redis client, @cached decorator, TTL constants
│   ├── models/                   # one file per aggregate — see 02-database-design.md
│   ├── schemas/                  # Pydantic request/response models (never reuse ORM models)
│   ├── services/
│   │   ├── stock_service.py      # yfinance wrapper + cache + fallback tier
│   │   ├── market_service.py     # index overview, market trend scoring
│   │   ├── technical_service.py  # orchestrates indicators.py, persists snapshots
│   │   ├── fundamental_service.py
│   │   ├── news_service.py       # provider-agnostic fetch + sentiment persistence
│   │   ├── risk_service.py
│   │   ├── scoring_service.py    # the transparent rubric — 05-scoring-methodology.md
│   │   ├── analysis_service.py   # invokes the LangGraph workflow, persists results
│   │   ├── portfolio_service.py  # holdings, P&L, allocation
│   │   ├── order_service.py      # validation, confirmation audit, broker dispatch
│   │   ├── report_service.py     # PDF generation
│   │   └── providers/
│   │       ├── broker/           # base.py · mock.py · kite.py
│   │       └── news/             # base.py · mock.py · rss.py · newsapi.py
│   ├── analytics/
│   │   └── indicators.py         # pure pandas/numpy — RSI, MACD, BB, ATR, Stoch, S/R
│   ├── ai/
│   │   ├── llm.py                # ChatOpenAI factory, structured output, retry
│   │   ├── embeddings.py
│   │   ├── prompts/              # versioned .py prompt templates
│   │   ├── rag/                  # chroma_client · ingest · retriever · citations
│   │   ├── tools/                # LangChain tools, thin wrappers over services
│   │   ├── graphs/               # analysis_graph.py · chat_graph.py · state.py
│   │   └── validation.py         # numeric grounding + banned-phrase guard
│   ├── jobs/
│   │   ├── scheduler.py          # APScheduler setup
│   │   └── tasks/                # refresh_market · refresh_news · nightly_recos · ingest
│   ├── db/
│   │   ├── database.py           # engine, session factory, Base
│   │   └── seeds/                # NIFTY 50 constituent list, curated RAG corpus
│   └── utils/
├── alembic/versions/
├── tests/                        # unit · integration · fixtures (recorded API payloads)
├── pyproject.toml
├── Dockerfile
└── .env.example
```

---

## 5. Frontend architecture

### Stack decisions

| Choice | Why |
|--------|-----|
| **Vite + React 18 + TypeScript** | TS types are generated from the FastAPI OpenAPI schema (`openapi-typescript`), so a backend field rename becomes a compile error instead of a runtime `undefined`. |
| **TanStack Query** | Server state is *not* client state. Query gives caching, stale-while-revalidate, polling and retry for free — which is exactly the behaviour a market dashboard needs. |
| **Zustand** | Only for genuine client state: theme, sidebar, active chat draft. Small and unceremonious; no Redux boilerplate. |
| **Tailwind + CVA** | Utility CSS with `class-variance-authority` for typed component variants. Design tokens live in `tailwind.config.ts`. |
| **Recharts** | Line/area/bar/pie across the app. React-idiomatic, composable, easy for students to read. |
| **lightweight-charts** | The price chart only. Recharts has no real candlestick or synced volume pane; TradingView's Apache-2.0 library is ~45 kB and does both properly. Two chart libraries is a deliberate, bounded tradeoff. |

### Folder structure

```
frontend/src/
├── app/              # router, providers, error boundary, theme provider
├── pages/
│   ├── public/       # Landing, Login, AuthCallback, NotFound
│   └── app/          # Dashboard, Market, Stocks, StockDetail, Watchlist,
│                     # Analysis, Chat, Portfolio, Orders, Reports,
│                     # Recommendations, Settings, Help
├── components/
│   ├── ui/           # Button, Card, Table, Badge, Tabs, Modal, Toast,
│   │                 # Skeleton, EmptyState, ErrorState, Tooltip
│   ├── charts/       # PriceChart, IndicatorPane, AllocationDonut, Sparkline
│   ├── market/       # IndexCard, MarketTrendBadge, GainersTable
│   ├── stock/        # StockHeader, MetricGrid, TechnicalPanel, FundamentalPanel,
│   │                 # NewsFeed, AIAnalysisPanel, RiskPanel, ScoreBreakdown
│   ├── ai/           # ChatWindow, MessageBubble, CitationChip, ToolTrace
│   └── layout/       # AppShell, Sidebar, Topbar, GlobalSearch, DemoBanner
├── features/         # one folder per domain: api calls + hooks + local types
├── lib/              # axios instance (refresh interceptor), formatters, constants
├── types/api.ts      # GENERATED from OpenAPI — never hand-edited
└── styles/
```

### Two frontend conventions that matter

**Facts and interpretation are visually distinct.** Anything sourced from an API
renders in the neutral data style with a timestamp. Anything the LLM produced
renders inside an AI-surface component — violet accent, "AI-generated" label,
disclaimer footer. A user should never have to wonder which is which. This is
principle #2 expressed in CSS.

**Every data view implements four states.** Loading (skeleton, never a spinner on
a layout we can shape), empty (explains what to do next), error (human message +
retry), and success. `<QueryBoundary>` wraps the pattern once so pages stay clean.

---

## 6. Authentication architecture

Google OAuth 2.0 **Authorization Code flow, completed server-side** (a
backend-for-frontend). The browser never sees the client secret and never handles
a Google token.

```
Browser                    FastAPI                      Google
   │                          │                            │
   │ GET /auth/google/login   │                            │
   ├─────────────────────────►│                            │
   │                          │ generate state + PKCE,     │
   │                          │ store in Redis (5 min TTL) │
   │ 302 → accounts.google    │                            │
   │◄─────────────────────────┤                            │
   │────────────── user consents ──────────────────────────►│
   │                          │                            │
   │ 302 /auth/google/callback?code&state                   │
   ├─────────────────────────►│                            │
   │                          │ verify state (CSRF)        │
   │                          │ exchange code ────────────►│
   │                          │◄──── id_token + access ────┤
   │                          │ verify id_token signature, │
   │                          │ iss, aud, exp, email_verified
   │                          │ upsert users + oauth_accounts
   │                          │ issue OUR tokens           │
   │ 302 → /dashboard         │                            │
   │ Set-Cookie: refresh_token (httpOnly, Secure,          │
   │             SameSite=Lax, Path=/api/v1/auth)          │
   │◄─────────────────────────┤                            │
   │                          │                            │
   │ POST /auth/refresh  → { access_token }  (in memory only)
```

**Why this shape:**

- *Access token in JavaScript memory, not `localStorage`* — a single XSS in any
  dependency can read `localStorage`. Memory dies with the tab, and a 15-minute
  TTL bounds the damage.
- *Refresh token in an httpOnly cookie* — unreadable by JS, scoped by `Path` so
  it is only sent to the refresh endpoint.
- *Refresh rotation with reuse detection* — each refresh issues a new token and
  revokes the old. If a revoked token is ever presented, the whole token family is
  killed and an `audit_logs` entry is written. That is the signal for a stolen token.
- *Google's own tokens are stored encrypted* (Fernet) and only used if we later
  need Google APIs. They are never returned to the browser.

Protected routes are guarded twice: `<ProtectedRoute>` in React for UX, and the
`get_current_user` dependency in FastAPI for actual security. Client-side guards
are convenience; the server is the authority.

---

## 7. Caching architecture

yfinance is an unofficial client for Yahoo Finance endpoints, with real rate
limits and no SLA. Thirty students loading a dashboard simultaneously will get
the host throttled. Caching is therefore not an optimisation here — it is what
makes the app usable in a classroom.

| Data | TTL | Key | Rationale |
|------|-----|-----|-----------|
| Quote (market open) | 30 s | `quote:{symbol}` | Fresh enough to feel live; 120× fewer upstream calls. |
| Quote (market closed) | 15 min | same | The number literally cannot change. |
| Index overview | 30 s | `market:overview` | One key serves every dashboard in the class. |
| Intraday history | 5 min | `hist:{symbol}:{interval}:{range}` | Last candle is the only mutable part. |
| Daily history | 6 h | same | Settled data. |
| Fundamentals | 24 h | `fund:{symbol}` | Changes quarterly at most. |
| Technical snapshot | 15 min | `tech:{symbol}:{interval}` | Derived from history; recompute is cheap but not free. |
| News list | 10 min | `news:{symbol}` | Balances freshness against provider quotas. |
| Article sentiment | permanent (DB) | `news_sentiment` row | An article's text never changes — classify once, ever. |
| AI analysis | 30 min (DB) | `stock_analyses` row | Re-serve a recent analysis rather than burn tokens. |
| Search suggestions | 60 s | `search:{q}` | Cheap protection against per-keystroke fan-out. |

**Stampede protection:** a Redis `SET NX` lock per cache key means that when a
popular key expires, one request refreshes it and the rest briefly serve the
stale value. Without this, a class of 30 produces 30 simultaneous Yahoo calls the
instant a TTL rolls over.

**Tiered degradation** — when a provider fails we walk down the tiers rather than
erroring: Redis → `stock_quotes` last-known-good (flagged `stale`, with timestamp)
→ explicit, friendly error state. Users see labelled old data, never a stack trace
and never a fabricated number.

---

## 8. Background jobs

**APScheduler, in-process, for the MVP.** A single `AsyncIOScheduler` started in
the FastAPI lifespan, with a Redis lock per job so only one worker runs each.

| Job | Schedule | Purpose |
|-----|----------|---------|
| `refresh_market_snapshot` | every 60 s, 09:15–15:30 IST, Mon–Fri | Warm index + NIFTY-50 quotes so the dashboard is always a cache hit. |
| `refresh_news` | every 15 min | Pull articles, classify new ones, persist sentiment. |
| `nightly_recommendations` | 18:30 IST | Score all NIFTY 50 constituents; powers the Recommendations page instantly. |
| `sync_broker_portfolios` | every 30 min, market hours | Refresh holdings for connected Zerodha accounts. |
| `cleanup` | 02:00 IST | Expire old reports, prune revoked tokens, vacuum stale cache rows. |

One-off long work (PDF generation, RAG ingestion) uses FastAPI `BackgroundTasks`
plus a `job_runs` row, so the UI can poll real status instead of guessing.

**When to move to Celery** — say this explicitly to students rather than
cargo-culting a broker on day one. Adopt Celery when *any* of these becomes true:
you need more than one backend host, a job must survive a backend restart, you
need retries with backoff and a dead-letter queue, or job duration starts
interfering with request latency. Until then Celery is three extra moving parts
(worker, beat, broker) buying nothing.

---

## 9. Deployment architecture

```
                       Internet
                          │
                    ┌─────▼──────┐
                    │ DNS + TLS  │  Let's Encrypt via certbot, auto-renew
                    └─────┬──────┘
                          │
  ┌───────────────────────▼────────────────────────────────────────┐
  │  Ubuntu 22.04 LTS VPS  ·  UFW (22, 80, 443 only)  ·  fail2ban  │
  │                                                                 │
  │  ┌──────────────────── docker compose ──────────────────────┐  │
  │  │                                                            │ │
  │  │  nginx ──────► frontend (static build, nginx:alpine)      │ │
  │  │    │                                                       │ │
  │  │    └─/api/──► backend (gunicorn + uvicorn workers)         │ │
  │  │                  │                                         │ │
  │  │                  ├──► postgres:16   (named volume)         │ │
  │  │                  ├──► redis:7       (appendonly)           │ │
  │  │                  └──► chromadb      (named volume)         │ │
  │  │                                                            │ │
  │  │  Only nginx publishes ports. Everything else is on the     │ │
  │  │  internal bridge network — not reachable from the internet.│ │
  │  └────────────────────────────────────────────────────────────┘│
  └─────────────────────────────────────────────────────────────────┘
```

- **Images:** multi-stage builds; non-root `appuser`; frontend compiled in a Node
  stage then copied into `nginx:alpine` (final image carries no Node runtime).
- **Config:** `.env` on the host, `chmod 600`, never in the image, never in git.
- **Migrations:** `alembic upgrade head` runs in an init container before the
  backend starts — never automatically on import.
- **Health:** `/api/v1/health` checks Postgres, Redis and Chroma; compose
  healthchecks gate startup order.
- **Backups:** nightly `pg_dump` + Chroma volume tar, retained 7 days, restore
  procedure documented and *tested* (an untested backup is a rumour).
- **Logs:** structlog JSON → Docker `json-file` driver with rotation.

This fits comfortably on a 4 GB / 2 vCPU VPS for classroom scale. The dominant
cost is OpenAI tokens, not compute — which is why §7's caching and the DB-backed
analysis reuse matter to the budget, not just to latency.

---

## 10. UI page map

### Public
| Route | Contents |
|-------|----------|
| `/` | Hero, live NIFTY strip (no login needed), 10 feature cards, How It Works (8 steps), tech badges, disclaimer band |
| `/login` | Google sign-in, Demo Mode entry |
| `/auth/callback` | Token exchange, redirect |

### Authenticated (inside `AppShell`)
| Route | Key elements |
|-------|--------------|
| `/dashboard` | Index cards · market trend · gainers/losers · trending · AI insight · news · portfolio snapshot |
| `/market` | Index detail, breadth, sector heatmap |
| `/stocks` | Browse/filter NIFTY 50 with scores |
| `/stock/:symbol` | Header, chart, metric grid, 8 tabs (Overview · Technical · Fundamental · News · AI Analysis · Risk · Historical · Recommendation) |
| `/watchlist` | Price, change, AI score, trend, news sentiment |
| `/analysis` | Past AI analyses, re-run, compare |
| `/chat` | Session list, streaming chat, citations, tool trace |
| `/portfolio` | Summary tiles, allocation charts, holdings table, Connect Zerodha |
| `/orders` | Tabbed order book, place/cancel with confirmation modal |
| `/reports` | Generate and download PDFs |
| `/recommendations` | Educational opportunity cards |
| `/settings` | Profile · preferences · theme · currency · notifications · broker · privacy |
| `/help` | Glossary, indicator explanations, full disclaimer |

---

## 11. Design system

| Token | Light | Dark | Use |
|-------|-------|------|-----|
| `bg` | `#F8FAFC` | `#0B1220` | Page ground |
| `surface` | `#FFFFFF` | `#131C2E` | Cards |
| `border` | `#E2E8F0` | `#1E2A42` | Dividers |
| `text` / `muted` | `#0F172A` / `#64748B` | `#E8EDF5` / `#8A99B0` | Type |
| `positive` | `#0E9F6E` | `#22C55E` | Gains |
| `negative` | `#E02424` | `#F05252` | Losses |
| `ai` | `#7C5CFF` | `#9B87FF` | AI-generated surfaces only |
| `warn` | `#D97706` | `#F59E0B` | Demo banner, stale data |

Rules: numbers use tabular figures so columns align; `ai` violet is reserved
exclusively for model-generated content; colour is never the sole carrier of
meaning — gains/losses also carry ▲/▼ and a sign, which keeps the app usable for
red-green colour-blind users. Targets: WCAG AA contrast, visible focus rings,
full keyboard navigation, `aria-live` on toasts.

---

## 12. Security architecture

| Layer | Control |
|-------|---------|
| Transport | TLS 1.2+, HSTS, secure cookies |
| Headers | CSP, X-Content-Type-Options, X-Frame-Options DENY, Referrer-Policy |
| Auth | Google OIDC (id_token signature/iss/aud/exp verified), 15-min JWT, rotating refresh with reuse detection |
| Authorization | Every user-scoped query filters by `user_id` at the repository layer — not in the route |
| Secrets | pydantic-settings from env; Fernet-encrypted broker tokens at rest; `.env` gitignored; structlog redaction filter |
| Input | Pydantic on every request; symbol allow-list regex `^[A-Z0-9&\-]{1,20}(\.(NS|BO))?$` |
| SQL | SQLAlchemy parameterised queries exclusively — no string-built SQL |
| CORS | Explicit origin allow-list from env, `allow_credentials=True`, never `*` |
| Rate limits | Per-user Redis token bucket: 60/min general, 10/min analysis, 20/min chat, 5/min reports |
| Trading | AI has no order tool; `confirmed_by_user_at` required; idempotency keys prevent double submission |
| Audit | `audit_logs` for login, logout, broker connect, order place/cancel, RAG upload, settings change |
| Errors | Domain exceptions → sanitised HTTP responses; stack traces only to logs, never to clients |

**Threat model note for class discussion:** the three assets worth attacking here
are (1) the Zerodha access token, (2) the OpenAI key, and (3) other users' data.
Encryption at rest plus a server-only key boundary covers 1 and 2; repository-level
`user_id` filtering and Chroma metadata filtering cover 3.

---

## 13. Demo Mode

A `DEMO_MODE` env flag, surfaced to the browser through `GET /api/v1/config`
(never a build-time frontend constant, so it can be toggled without a rebuild).

| Concern | Demo Mode | Full Mode |
|---------|-----------|-----------|
| Market data | **Real yfinance** — the demo is genuine where it can be | Real yfinance |
| News | RSS provider, or labelled `MockNewsProvider` if offline | RSS / NewsAPI |
| LLM | Real OpenAI if key present; otherwise a canned-response provider clearly labelled | Real OpenAI |
| Broker | `MockBroker` — simulated fills, no real money, no Zerodha account needed | `KiteBroker` |
| Portfolio | Seeded sample holdings | User's real/synced data |

A persistent amber **DEMO MODE** banner sits in the app shell, and any card
containing simulated data carries its own "Simulated" chip. The principle: the
system must never be ambiguous about whether a number is real.

---

## 14. Observability

Structured JSON logs via structlog, with a request-id bound to every line in a
request's lifetime (and returned as `X-Request-ID`, so a user-reported error maps
to exact log lines).

Logged: method, path, status, duration, user id, request id, cache hit/miss,
upstream latency, AI model, token counts, estimated cost, workflow node timings.
Redacted, always: API keys, OAuth secrets, broker tokens, cookies, email bodies.

Two tables make cost and reliability visible rather than theoretical:
`ai_invocations` (per-call model, tokens, cost, latency, outcome) and `job_runs`
(per-job status and duration). A simple admin view over these is a better lesson
in LLM economics than any lecture slide.

---

*Companion documents:* `02-database-design.md` · `03-ai-architecture.md` ·
`04-api-design.md` · `05-scoring-methodology.md` · `06-roadmap-and-mvp.md`

# rentSIM

A real-estate portfolio simulator modelled on the Shenandoah Valley, VA rental market. Create portfolios, inject capital, buy and sell properties, watch loans amortise month by month, and let the sim run forward in time to see how the numbers play out.

**Live:** https://frontend-production-a569.up.railway.app

---

## Features

- Multi-portfolio dashboard with tab switching
- Real-time month-by-month simulation over WebSocket
- Rent estimates sampled from four Shenandoah Valley sub-markets (Woodstock, Strasburg, Front Royal, Winchester)
- Amortising mortgages at 80% LTV with configurable extra repayment
- Floating `+$` / `-$` event notifications per rent collection and loan payment
- Auto-step at configurable speed (0.5 s → 5 s per month)
- Auto-buy trigger: automatically purchase when cash reaches a set threshold
- JWT auth — 15-minute access tokens, 30-day httpOnly refresh cookies
- Fully persistent across sessions (Postgres-backed)

---

## System Architecture

```mermaid
graph TD
    Browser["Browser"]

    subgraph Railway
        FE["Frontend\nnginx · React SPA\nfrontend-*.railway.app"]
        BE["Backend\nFastAPI · uvicorn\nbackend-*.railway.app"]
        DB[("PostgreSQL\nRailway managed")]
    end

    Browser -->|"HTTPS — page load"| FE
    Browser -->|"HTTPS REST /api/..."| BE
    Browser -->|"WSS /ws/{portfolio_id}"| BE
    BE -->|SQLAlchemy ORM| DB
```

The frontend is a static React/Vite build served by nginx. On startup the container runs `env.sh`, which writes `env-config.js` into the served directory so that `VITE_API_URL` / `VITE_WS_URL` are injected at runtime without a rebuild. All simulation state lives in Postgres; in-memory sim objects are reconstructed per WebSocket connection.

---

## Authentication Flow

```mermaid
sequenceDiagram
    participant B as Browser
    participant F as nginx (Frontend)
    participant A as FastAPI (Backend)
    participant D as Postgres

    B->>F: GET /
    F-->>B: React SPA + /env-config.js

    B->>A: POST /api/auth/register or /login
    A->>D: Lookup / create user (bcrypt hash)
    D-->>A: user row
    A-->>B: { access_token } + Set-Cookie: refresh_token (httpOnly, 30d)

    loop Every 13 minutes
        B->>A: POST /api/auth/refresh  (cookie sent automatically)
        A-->>B: new access_token
    end

    B->>A: GET /api/portfolios  (Authorization: Bearer access_token)
    A-->>B: portfolio list

    B->>A: WS /ws/{portfolio_id}?token=access_token
    A-->>B: connected event + full state snapshot
```

---

## Simulation Loop

Each portfolio has a dedicated WebSocket connection. The client sends action messages; the server runs them against an in-memory `Portfolio` object, persists the result to Postgres, and streams events back to the client.

```mermaid
flowchart TD
    CONN["WS connect\n/ws/{id}?token=..."] --> AUTH{"Valid JWT?"}
    AUTH -- No --> CLOSE["Close 4001"]
    AUTH -- Yes --> LOAD["Reconstruct Portfolio + Houses + Loans\nfrom Postgres into sim objects"]
    LOAD --> SEND["Send 'connected' + full state snapshot"]
    SEND --> WAIT["Await next action"]

    WAIT --> ACT_STEP["action: step"]
    WAIT --> ACT_BUY["action: buy_house"]
    WAIT --> ACT_SELL["action: sell_house"]
    WAIT --> ACT_INVEST["action: invest"]
    WAIT --> ACT_SETTINGS["action: update_settings"]
    WAIT --> ACT_DEL["action: delete_house\nor delete_loan"]

    ACT_STEP --> STEP["step_month()"]
    STEP --> INF["World inflation tick\nworld.inflation ×= 1 + 0.00205"]
    INF --> HOUSES["Per house:\nvalue ×= 1 + appreciation_rate\nrent = get_rent(value)\nnet = rent − expenses"]
    HOUSES --> NEG{"Cash < 0?"}
    NEG -- Yes --> ELOAN["Emergency loan\n18% · 1-month term"]
    NEG -- No --> LOANS
    ELOAN --> LOANS["Pay loans — largest balance first\nbase_payment + extra × repay_rate\n(reserve floor respected)"]
    LOANS --> AUTO{"auto_buy_threshold\nmet?"}
    AUTO -- Yes --> ABUY["buy_house()\n20% down · 80% mortgage"]
    AUTO -- No --> SAVE
    ABUY --> SAVE["Persist to Postgres\ntick month counter"]
    SAVE --> EVENTS["Stream events to client\ninflation_updated · rent_collected\nloan_payment · month_complete ..."]
    EVENTS --> WAIT

    ACT_BUY --> BHOUSE["buy_house(price)\ndeduct down payment · create Loan"] --> SAVE2["Persist"] --> STATE2["Send state_update"] --> WAIT
    ACT_SELL --> SHOUSE["sell_house(id)\nadd value to cash · remove house"] --> SAVE2
    ACT_INVEST --> INV["cash += amount\ninvested += amount"] --> SAVE2
    ACT_SETTINGS --> SETS["Update repay_rate / reserve / auto_buy"] --> SAVE2
    ACT_DEL --> DEL["Remove house or loan from sim + DB"] --> SAVE2
```

---

## Monthly Step — Detail

```mermaid
flowchart LR
    subgraph step_month
        direction TB
        A["Inflation tick\nworld.inflation ×= 1 + rate"] -->
        B["House loop\nappreciate value\nrent = get_rent(current value)\nnet = rent − expenses"] -->
        C["Loan loop — largest balance first\npayment = base + extra\nextra = max 0, cash−reserve−base_total × repay_rate"] -->
        D["Auto-buy check\nif cash−reserve >= threshold"] -->
        E["Emit month_complete\nwith full state snapshot"]
    end
```

---

## Data Model

```mermaid
erDiagram
    USER {
        int      id              PK
        string   email           UK
        string   hashed_password
        datetime created_at
    }
    PORTFOLIO {
        int    id                PK
        int    user_id           FK
        string name
        float  cash
        float  invested
        float  reserved
        float  inflation
        int    life
        int    length
        int    month
        float  loan_repay_rate
        float  auto_buy_threshold
        bool   is_closed
    }
    HOUSE {
        int   id               PK
        int   portfolio_id     FK
        int   house_id
        float price
        float value
        float appreciation_rate
        json  rent_metadata
    }
    LOAN {
        int   id            PK
        int   portfolio_id  FK
        int   loan_id
        float amount
        float original
        float rate
        float years
    }

    USER     ||--o{ PORTFOLIO : owns
    PORTFOLIO ||--o{ HOUSE    : contains
    PORTFOLIO ||--o{ LOAN     : carries
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 18 · Vite · Tailwind CSS · React Router |
| Real-time | Browser WebSocket API · FastAPI WebSocket |
| Backend | FastAPI · uvicorn · SQLAlchemy 2 |
| Auth | python-jose (JWT) · bcrypt 4 · httpOnly refresh cookies |
| Database | PostgreSQL (Railway managed) |
| Serving | nginx — SPA routing + runtime env injection via `envsubst` |
| Deployment | Railway — 3 services: frontend, backend, Postgres |
| Rent model | Custom Shenandoah Valley estimator (4 sub-markets, bedroom distribution) |

---

## Project Structure

```
rentSIM/
├── backend/
│   ├── api/
│   │   ├── auth.py            # register / login / refresh / logout
│   │   ├── portfolios.py      # CRUD + available-houses generator
│   │   └── ws.py              # WebSocket endpoint + DB↔sim conversion
│   ├── sim/
│   │   ├── world.py           # cumulative inflation accumulator
│   │   ├── house.py           # per-house appreciation + rent sampling
│   │   ├── loan.py            # amortising loan with extra repayment
│   │   ├── portfolio.py       # month step, buy/sell, auto-buy logic
│   │   └── rent_estimator.py  # Shenandoah Valley rent model
│   ├── models.py              # SQLAlchemy ORM models
│   ├── schemas.py             # Pydantic request/response schemas
│   ├── database.py            # engine + session factory
│   ├── auth.py                # JWT encode/decode, bcrypt helpers
│   ├── main.py                # FastAPI app, CORS, router mounts
│   ├── requirements.txt
│   └── Dockerfile
│
└── frontend/
    ├── src/
    │   ├── App.jsx                      # Dashboard, portfolio tabs, routing
    │   ├── pages/
    │   │   ├── Login.jsx
    │   │   └── Register.jsx
    │   ├── components/
    │   │   ├── PortfolioCard.jsx        # 3-column card shell
    │   │   ├── PortfolioControls.jsx    # stats, step/auto, invest, reserve
    │   │   ├── HouseList.jsx            # house cards + buy modal
    │   │   ├── LoanList.jsx             # loan cards + repay-rate slider
    │   │   └── FloatingNotification.jsx
    │   ├── hooks/
    │   │   └── useSimWebSocket.js       # WS connection + state management
    │   └── context/
    │       └── AuthContext.jsx          # JWT state + silent refresh loop
    ├── nginx.conf.template              # SPA server with PORT substitution
    ├── env.sh                           # runtime env-config.js injection
    └── Dockerfile
```

---

## Rent Model

Houses are priced from a base set ($180 k–$480 k) scaled by the portfolio's cumulative inflation multiplier. Each month, rent is re-sampled from the Shenandoah Valley estimator:

1. A **market** is drawn uniformly from four sub-markets, each with a calibrated gross yield rate and rent floor/ceiling.
2. A **bedroom count** is drawn from a weighted distribution skewed toward 2–4 BR.
3. Base rent = `property_value × gross_yield / 12`, clamped to floor/ceiling, then scaled by a bedroom multiplier.

Monthly expenses (property tax + insurance + maintenance) are computed as **2.28% of current value annualised** and deducted from gross rent to produce net cash flow.

| Market | Gross yield | Rent floor | Rent ceiling |
|---|---|---|---|
| Woodstock, VA | 5.60% | $900 | $3,200 |
| Strasburg, VA | 5.20% | $850 | $2,800 |
| Front Royal, VA | 6.00% | $950 | $3,500 |
| Winchester, VA | 4.70% | $950 | $3,800 |

---

## Local Development

```bash
# Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
DATABASE_URL=postgresql://localhost/rentsim \
SECRET_KEY=dev-secret \
ALLOWED_ORIGINS=http://localhost:5173 \
uvicorn main:app --reload

# Frontend (separate terminal)
cd frontend
npm install
VITE_API_URL=http://localhost:8000 \
VITE_WS_URL=ws://localhost:8000 \
npm run dev
```

---

## Railway Deployment

Three services in one Railway project:

| Service | Source | Public URL |
|---|---|---|
| `frontend` | `frontend/Dockerfile` | Yes |
| `backend` | `backend/Dockerfile` | Yes |
| `Postgres` | Railway template | No |

**backend environment variables**

```
DATABASE_URL      # injected automatically by the Railway Postgres plugin
SECRET_KEY        # random string for JWT signing
ALLOWED_ORIGINS   # comma-separated frontend origins, e.g. https://frontend-*.up.railway.app
PORT              # 8000
```

**frontend environment variables**

```
VITE_API_URL   # https://backend-production-*.up.railway.app
VITE_WS_URL    # wss://backend-production-*.up.railway.app
PORT           # 80
```

Deployments trigger automatically on push to `main`.

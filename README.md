# Excel AI

**Your Intelligent Spreadsheet Assistant** — An AI-powered Excel add-in for data analysis, cleaning, auditing, forecasting, fraud detection, and business intelligence.

Built with TypeScript + React (Office.js) for the frontend and Python + FastAPI for the backend.

---

## Features

### AI Assistant
Unified chat interface for all AI tasks — generate formulas, explain functions, analyze data, and ask questions about your spreadsheet.

### Data Analysis
- **Explain Data** — Auto-generated insights, statistics, and AI-powered explanations
- **Data Cleaner** — Detect missing values, duplicates, outliers, and invalid data; apply fixes
- **Workbook Audit** — 7 types of structural and data quality checks across all sheets

### Business Intelligence
- **CEO Dashboard** — One-click KPI dashboard with charts and export to PDF/PPT
- **Forecast** — Time series forecasting using Prophet (with linear regression fallback)
- **Business Insights** — Trends, anomalies, correlations, and top performers

### Enterprise Intelligence
- **Fraud Detection** — Isolation Forest + Benford's Law + rule-based anomaly detection
- **Risk Scoring** — Multi-dimensional risk assessment (volatility, concentration, trend)
- **Financial Health** — Profitability, liquidity, and efficiency ratios with health score
- **Inventory Intelligence** — Dead/slow/fast-moving stock, aging, reorder suggestions
- **Sales Intelligence** — Top customers, product performance, regional analysis
- **HR Intelligence** — Salary analysis, headcount, overtime, duplicate detection

### SQL Connector
Connect directly to PostgreSQL, MySQL, SQL Server, or SQLite databases — import data without CSV exports.

### AI Settings
Bring Your Own Key (BYOK) — supports 9 AI providers:

| Provider | Model | Key Format |
|---|---|---|
| **OpenAI** | gpt-4o | `sk-...` |
| **DeepSeek** | deepseek-chat | `sk-...` |
| **Mistral AI** | mistral-large-latest | API key |
| **Groq** | llama-3.3-70b-versatile | `gsk_...` |
| **Together AI** | Mixtral-8x7B | API key |
| **OpenRouter** | openai/gpt-4o | `sk-or-...` |
| **Google Gemini** | gemini-2.0-flash | `AIza...` |
| **Anthropic Claude** | claude-sonnet-4 | `sk-ant-...` |
| **Ollama** (local) | llama3.2 | Not needed |

---

## Technology Stack

### Frontend (Office Add-in)
- **TypeScript** + **React 18**
- **Office.js** — Excel integration
- **Chart.js** — Dashboard visualizations
- **lucide-react** — UI icons
- **Webpack** — Module bundler

### Backend
- **Python 3.11+** + **FastAPI**
- **pandas** / **NumPy** / **Polars** — Data processing
- **DuckDB** — In-process SQL analytics
- **scikit-learn** — Isolation Forest (fraud detection)
- **XGBoost** / **LightGBM** — Predictive modeling
- **Prophet** — Time series forecasting
- **Plotly** — Chart generation for exports
- **SQLAlchemy** + **SQLite** / **PostgreSQL** — Data persistence
- **fpdf2** + **python-pptx** — PDF/PPT report generation

---

## Installation

### Prerequisites
- **Node.js 18+** and **npm**
- **Python 3.11+**
- **Microsoft Excel** (for add-in usage)

### 1. Clone & Setup
```bash
git clone https://github.com/yourusername/excel-ai.git
cd excel-ai
```

### 2. Backend
```bash
cd backend

# Create virtual environment
python -m venv .venv

# Activate
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start server
uvicorn app.main:app --reload --port 8000
```

### 3. Frontend
```bash
cd addin

# Install dependencies
npm install --legacy-peer-deps

# Development server (for browser testing)
npm run dev

# Or sideload into Excel
npm start
```

### 4. Access
- **Frontend**: https://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

---

## How to Use

### In Browser (Demo Mode)
1. Open https://localhost:3000
2. Click **Settings** → select AI provider → enter API key → **Test Connection**
3. Navigate to any feature and click **Baca Excel** (or use sample data if available)
4. Some pages support manual CSV input

### In Excel
1. Open Excel
2. Go to **Insert** → **Add-ins** → **My Add-ins**
3. Upload `addin/manifest.xml` or sideload via `npm start`
4. The add-in appears as a task pane
5. Data is automatically read from the active worksheet

### Getting API Keys

| Provider | How to Get |
|---|---|
| **OpenAI** | https://platform.openai.com/api-keys |
| **DeepSeek** | https://platform.deepseek.com/api_keys |
| **Mistral** | https://console.mistral.ai/api-keys/ |
| **Groq** | https://console.groq.com/keys |
| **Together AI** | https://api.together.ai/settings/api-keys |
| **OpenRouter** | https://openrouter.ai/keys |
| **Gemini** | https://aistudio.google.com/apikey |
| **Claude** | https://console.anthropic.com/ |
| **Ollama** | https://ollama.ai/ (local, free) |

---

## Project Structure

```
excel-ai/
├── backend/                     # Python FastAPI server
│   ├── app/
│   │   ├── main.py              # Entry point, router registration
│   │   ├── config.py            # Environment config
│   │   ├── models/schemas.py    # Pydantic models
│   │   ├── routers/             # API endpoints
│   │   │   ├── formula.py       # Formula generation/explanation
│   │   │   ├── explain.py       # Data analysis
│   │   │   ├── cleaner.py       # Data cleaning
│   │   │   ├── audit.py         # Workbook audit
│   │   │   ├── chat.py          # AI chat
│   │   │   ├── dashboard.py     # CEO dashboard
│   │   │   ├── forecast.py      # Time series forecast
│   │   │   ├── insights.py      # Business insights
│   │   │   ├── fraud.py         # Fraud detection
│   │   │   ├── risk.py          # Risk scoring
│   │   │   ├── financial.py     # Financial health
│   │   │   ├── inventory.py     # Inventory analysis
│   │   │   ├── sales_intel.py   # Sales intelligence
│   │   │   ├── hr_intel.py      # HR analytics
│   │   │   ├── connector.py     # SQL database connector
│   │   │   ├── analytics.py     # DuckDB SQL + ML prediction
│   │   │   ├── reports.py       # PDF/PPT generation
│   │   │   ├── database.py      # Analysis history storage
│   │   │   └── settings.py      # API key validation
│   │   └── services/            # Business logic layer
│   ├── requirements.txt
│   └── .env.example
│
├── core/                        # Shared Python library
│   ├── analysis/                # Analysis modules
│   │   ├── explainer.py         # Data explanation
│   │   ├── data_quality.py      # Quality checks & fixes
│   │   ├── audit.py             # Workbook audit rules
│   │   ├── dashboard.py         # KPI + chart generation
│   │   ├── forecast.py          # Prophet forecasting
│   │   ├── business_insights.py # Trend/anomaly detection
│   │   ├── fraud_detection.py   # Isolation Forest + rules
│   │   ├── risk_scoring.py      # Multi-factor risk
│   │   ├── financial_health.py  # Financial ratios
│   │   ├── inventory_intelligence.py
│   │   ├── sales_intelligence.py
│   │   ├── hr_intelligence.py
│   │   ├── sql_connector.py     # DB connection
│   │   ├── duckdb_analytics.py  # DuckDB SQL engine
│   │   ├── visualizations.py    # Plotly chart generator
│   │   └── reports.py           # PDF/PPT generator
│   ├── ml/
│   │   └── predictive.py        # XGBoost/LightGBM models
│   └── utils/
│       ├── llm_client.py        # Unified AI client (9 providers)
│       ├── excel_reader.py      # DataFrame utilities
│       ├── data_engine.py       # Polars data engine
│       └── database.py          # SQLAlchemy storage
│
├── addin/                       # Office.js frontend
│   ├── src/
│   │   ├── index.tsx            # App entry + routing
│   │   ├── styles.css           # Design system (blue theme)
│   │   ├── contexts/
│   │   │   ├── WorkbookContext.tsx  # Shared workbook data
│   │   │   └── RightSidebarContext.tsx
│   │   ├── components/
│   │   │   ├── Navbar.tsx       # Group + sub-tab navigation
│   │   │   ├── Layout.tsx       # 3-column layout
│   │   │   ├── DataBar.tsx      # Data status indicator
│   │   │   ├── LoadingSpinner.tsx
│   │   │   └── ErrorAlert.tsx
│   │   ├── pages/               # 16 feature pages
│   │   └── services/api.ts      # Axios API client
│   ├── manifest.xml             # Excel add-in manifest
│   ├── package.json
│   ├── tsconfig.json
│   └── webpack.config.js
│
├── docker/
│   └── docker-compose.yml
└── README.md
```

---

## API Overview

| Method | Endpoint | Description |
|---|---|---|
| **V1** | | |
| POST | `/api/v1/formula/generate` | Generate Excel formula |
| POST | `/api/v1/formula/explain` | Explain Excel formula |
| POST | `/api/v1/explain/data` | Analyze data with AI |
| POST | `/api/v1/cleaner/analyze` | Detect data quality issues |
| POST | `/api/v1/cleaner/apply` | Apply cleaning fixes |
| POST | `/api/v1/audit/run` | Run workbook audit |
| POST | `/api/v1/chat/message` | Chat with workbook data |
| POST | `/api/v1/settings/validate-key` | Test API key |
| **V2** | | |
| POST | `/api/v2/dashboard/generate` | Generate CEO dashboard |
| POST | `/api/v2/forecast/run` | Run time series forecast |
| POST | `/api/v2/insights/generate` | Generate business insights |
| POST | `/api/v2/reports/pdf` | Export PDF report |
| POST | `/api/v2/reports/ppt` | Export PowerPoint |
| **V3** | | |
| POST | `/api/v3/fraud/detect` | Fraud detection |
| POST | `/api/v3/risk/score` | Risk scoring |
| POST | `/api/v3/financial/analyze` | Financial health analysis |
| POST | `/api/v3/inventory/analyze` | Inventory intelligence |
| POST | `/api/v3/sales/analyze` | Sales intelligence |
| POST | `/api/v3/hr/analyze` | HR analytics |
| POST | `/api/v3/connector/test` | Test SQL connection |
| POST | `/api/v3/connector/tables` | List database tables |
| POST | `/api/v3/connector/preview` | Preview table data |
| POST | `/api/v3/connector/import` | Import query results |
| POST | `/api/v3/analytics/sql` | Run DuckDB SQL query |
| POST | `/api/v3/analytics/train` | Train ML model |
| POST | `/api/v3/analytics/predict` | Make predictions |
| POST | `/api/v3/db/save` | Save analysis result |
| GET | `/api/v3/db/history` | Get analysis history |

---

## Development

### Add a New Page
1. Create page in `addin/src/pages/`
2. Add tab entry in `addin/src/components/Navbar.tsx`
3. Add route in `addin/src/index.tsx`

### Add a New Backend Endpoint
1. Create router in `backend/app/routers/`
2. Create service in `backend/app/services/`
3. Add Pydantic models in `backend/app/models/schemas.py`
4. Register router in `backend/app/main.py`
5. (Optional) Add core logic in `core/analysis/` or `core/ml/`

---

## License

MIT

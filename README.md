# Economic Policy Impact Tracker

**Correlate economic indicators with legislative actions. Built for Senate staffers who need data-driven policy briefings.**

This project was built as a concept for a Palantir AIP demo. It demonstrates how to:
- Ingest public economic data (FRED, BLS, Congress.gov)
- Model it in a connected Ontology
- Use AI to answer natural language policy questions
- Generate Senate-style briefing memos backed by real data

---

## What's in This Repo

```
├── webapp/                    # Next.js web app (deployable to Vercel)
│   ├── src/
│   │   ├── app/              # Pages and API routes
│   │   ├── components/       # Chart, timeline, briefing panel
│   │   └── lib/              # Data loading and AI integration
│   └── public/               # Sample CSV datasets
│
├── data_collectors/           # Python scripts to pull real data
│   ├── fred_collector.py     # FRED API (GDP, CPI, unemployment, etc.)
│   ├── bls_collector.py      # BLS API (state employment, industry data)
│   └── congress_collector.py # Congress.gov API (bill timelines)
│
├── scripts/
│   └── generate_sample_data.py  # Generate realistic sample data (no API keys needed)
│
├── sample_data/               # Pre-generated CSVs ready for Palantir upload
│   ├── fred_national_indicators.csv
│   ├── fred_state_indicators.csv
│   ├── policy_timeline.csv
│   └── bls_national_industry.csv
│
└── docs/
    ├── AIP_BUILD_GUIDE.md    # Step-by-step Palantir AIP build instructions
    └── VIDEO_SCRIPT.md       # 5-minute demo video script with timing
```

---

## Quick Start — Run the Web App Locally

```bash
cd webapp
npm install
npm run dev
```

Open http://localhost:3000. The app works immediately with sample data — no API keys needed.

### Optional: Enable AI Briefings

Create `webapp/.env.local`:
```
OPENAI_API_KEY=your_key_here
```

Without an OpenAI key, briefings use a template-based generator that still shows relevant data and policies.

---

## Quick Start — Collect Real Data

1. Get free API keys:
   - FRED: https://fred.stlouisfed.org/docs/api/api_key.html
   - BLS: https://data.bls.gov/registrationEngine/
   - Congress.gov: https://api.congress.gov/sign-up/

2. Create `.env` in the project root:
   ```
   FRED_API_KEY=your_key
   BLS_API_KEY=your_key
   CONGRESS_API_KEY=your_key
   ```

3. Run collectors:
   ```bash
   pip install -r requirements.txt

   # National indicators
   python data_collectors/fred_collector.py

   # State data (specific states)
   python data_collectors/fred_collector.py --states ID TX CA

   # BLS industry employment
   python data_collectors/bls_collector.py

   # Policy timeline
   python data_collectors/congress_collector.py

   # Or just use sample data (no keys needed)
   python scripts/generate_sample_data.py
   ```

---

## Building in Palantir AIP

See **[docs/AIP_BUILD_GUIDE.md](docs/AIP_BUILD_GUIDE.md)** for complete step-by-step instructions covering:

1. **Data Ingestion** — Upload CSVs to Foundry
2. **Ontology Design** — Model indicators, policies, and industries as connected objects
3. **AIP Functions** — Query trends, find policies, calculate impact
4. **AIP Agent** — Natural language Q&A with Senate-style briefing output
5. **Workshop App** — Interactive dashboard with charts and timeline

---

## Recording the Demo Video

See **[docs/VIDEO_SCRIPT.md](docs/VIDEO_SCRIPT.md)** for:
- Full script with timing (fits in 4:45)
- What to show on screen at each point
- Recording tips
- What Palantir evaluators are looking for

---

## The Problem This Solves

Senate staffers working on economic policy face this workflow daily:

1. Pull data from FRED, BLS, Census — separate websites, different formats
2. Cross-reference with legislative timelines — when was the CHIPS Act signed?
3. Manually correlate — did manufacturing employment change after?
4. Draft a briefing memo — synthesize data into actionable talking points

**This tool collapses steps 1-4 into a single natural language query.**

Example: *"How has manufacturing employment changed since the CHIPS Act passed?"*

The system pulls the data, identifies the relevant policy, calculates the change, and generates a briefing memo — in seconds.

---

## Data Sources

All data is publicly available from US government sources:

| Source | What | URL |
|--------|------|-----|
| FRED | GDP, CPI, unemployment, employment, Fed funds rate | https://fred.stlouisfed.org |
| BLS | State employment, industry employment, wages | https://www.bls.gov/data/ |
| Congress.gov | Bill timelines, signing dates, policy areas | https://api.congress.gov |

---

## Deploy to Vercel

```bash
cd webapp
npx vercel
```

Or connect the GitHub repo to Vercel for automatic deploys.

Set environment variables in Vercel dashboard:
- `OPENAI_API_KEY` (optional — for AI briefings)

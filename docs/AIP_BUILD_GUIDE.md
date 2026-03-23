# Building the Economic Policy Impact Tracker in Palantir AIP

Complete guide — from pulling real federal data to a working AIP agent and Workshop dashboard in Foundry DevTier.

**Time estimate:** 4-5 hours total across all phases.

**Before you start:** Complete the Palantir "Speedrun: Your First E2E Workflow" tutorial (60-90 min) at https://learn.palantir.com/speedrun-your-first-e2e-workflow — it covers the Ontology and Workshop basics you'll need.

---

## Phase 0: Prerequisites (15 minutes)

### Accounts

1. **Palantir AIP DevTier** — https://www.palantir.com/aip/activate
2. **FRED API key** (free, instant) — https://fred.stlouisfed.org/docs/api/api_key.html
3. **Python 3.10+** with pip

### Install Dependencies

```bash
pip install foundry-platform-sdk pandas pyarrow requests python-dotenv
```

Note: The SDK package is `foundry-platform-sdk` but imports as `foundry_sdk`.

### Get Your Foundry Hostname and Token

1. Log into Foundry. Your URL is: `https://YOURNAME.usw-XX.palantirfoundry.com/`
2. Your hostname is everything after `https://` (e.g., `myname.usw-18.palantirfoundry.com`)
3. Generate a personal access token:
   - Click the **gear icon** (bottom-left) → **Tokens** → **Generate new token**
   - Name: `bootstrap`
   - Grant all available scopes
   - **Copy the token immediately** — you won't see it again
   - Token expires in ~7 days

### Find Your Space RID

```bash
python scripts/foundry_bootstrap.py \
  --foundry-token YOUR_TOKEN \
  --foundry-host  YOURNAME.usw-XX.palantirfoundry.com \
  --list-spaces
```

This prints your available spaces. Copy the **RID** (starts with `ri.compass.main.folder.`).

### Clean Up Example Objects (Important!)

DevTier comes with example aviation object types (Airports, Flights, Aircraft, etc.) that count toward a ~60 object type limit. Before building:

1. Open **Ontology Manager** (search for it with **Cmd+K** or **Ctrl+K**)
2. Check how many example object types exist (they're prefixed with `[Example]`)
3. If you're close to the limit, delete the ones you don't need

---

## Phase 1: Data Pipeline (20 minutes)

The bootstrap script pulls **real federal economic data** and uploads it to Foundry.

### Run It

```bash
python scripts/foundry_bootstrap.py \
  --foundry-token YOUR_FOUNDRY_TOKEN \
  --foundry-host  YOURNAME.usw-XX.palantirfoundry.com \
  --fred-key      YOUR_FRED_API_KEY \
  --space-rid     ri.compass.main.folder.XXXXX
```

### What It Creates in Foundry

A folder called **"Economic Policy Impact Tracker"** with three datasets:

| Dataset | ~Records | Primary Key | Contents |
|---------|----------|-------------|----------|
| `economic_indicators` | ~5,600 | `pk` (series_id:date) | FRED national (GDP, CPI, unemployment, etc.) + state-level (10 states) — all in one dataset |
| `bls_national_industry` | ~1,700 | `pk` (indicator:date) | BLS employment by industry sector (9 sectors) |
| `policy_timeline` | 43 | `bill_id` (congress_type_number) | Enacted laws: 7 landmarks + 36 major economic bills |

**Why one combined FRED dataset?** Foundry Object Types need a single backing dataset. Multi-datasource Object Types (MDOs) only support column-wise joins, not row unions. So we union national + state data upfront with a synthetic primary key.

The script prints the **dataset RIDs** at the end. Save them.

### Data Sources (All Real)

- **FRED** (Federal Reserve Economic Data): GDP, CPI, Core CPI, unemployment, payrolls, manufacturing employment, Fed funds rate, PCE, industrial production, retail sales. National + 10 states. 2010-present.
- **BLS** (Bureau of Labor Statistics): Employment by sector — manufacturing, construction, information, financial, healthcare, etc. National, monthly, 2010-present.
- **Congress.gov**: 43 curated laws including Tax Cuts & Jobs Act, CARES, American Rescue Plan, Infrastructure Act, CHIPS Act, Inflation Reduction Act, plus major appropriations, trade deals, and COVID response bills.

---

## Phase 2: Build the Ontology (45 minutes)

The Ontology turns flat datasets into connected objects the AIP agent can reason about.

### Open Ontology Manager

- Press **Cmd+K** (Mac) or **Ctrl+K** (Windows) and search "Ontology Manager"
- Or find it in the left sidebar under Ontology building tools

### Object Type 1: Economic Indicator Reading

Each row = one data point (e.g., "CPI was 305.2 in January 2024")

1. In Ontology Manager, click **New** → **Create object type**
2. Name: `Economic Indicator Reading`
3. Click **Select a backing datasource** → navigate to your project folder → select `economic_indicators`
4. Foundry auto-detects columns. Map these properties:

| Property | Column | Type |
|----------|--------|------|
| pk | pk | String |
| date | date | Date |
| value | value | Double |
| indicator_name | indicator_name | String |
| unit | unit | String |
| geography | geography | String |
| state_code | state_code | String (nullable) |
| geo_level | geo_level | String |
| series_id | series_id | String |

5. **Primary Key:** `pk` (the synthetic key: `series_id:YYYY-MM-DD`)
6. **Title Key:** Set to `indicator_name` (what shows up as the display name)
7. Click **Save** (upper right)

### Object Type 2: Industry Employment

Each row = one industry sector employment reading.

1. **New** → **Create object type**
2. Name: `Industry Employment`
3. Backing datasource: `bls_national_industry`
4. Properties:

| Property | Column | Type |
|----------|--------|------|
| pk | pk | String |
| date | date | Date |
| value | value | Double |
| indicator_name | indicator_name | String |
| unit | unit | String |
| geography | geography | String |

5. **Primary Key:** `pk`
6. **Title Key:** `indicator_name`
7. **Save**

### Object Type 3: Policy Action

Each row = one enacted law.

1. **New** → **Create object type**
2. Name: `Policy Action`
3. Backing datasource: `policy_timeline`
4. Properties:

| Property | Column | Type |
|----------|--------|------|
| bill_id | bill_id | String |
| short_name | short_name | String |
| signed_date | signed_date | Date |
| policy_area | policy_area | String |
| summary | summary | String (nullable) |
| is_landmark | is_landmark | Boolean |
| congress | congress | Integer |
| bill_type | bill_type | String |
| bill_number | bill_number | Integer |

5. **Primary Key:** `bill_id` (e.g., `117_hr_5376`)
6. **Title Key:** `short_name`
7. **Save**

### After Saving All Three

Wait 2-3 minutes for DevTier to sync the object types. You can verify by:
- Going to Ontology Manager → Object Types and checking status
- Trying to search for objects in the Ontology search bar

### Link Types (Optional)

You can create a link between Policy Action and Economic Indicator Reading:
- In Ontology Manager → **Link Types** → **New**
- From: Policy Action → To: Economic Indicator Reading
- Name: `impacts_indicators`

**However:** This is hard to configure as a time-based link in the UI. If it's causing friction, skip it — the AIP Agent can correlate by date without explicit links.

---

## Phase 3: AIP Agent (45 minutes)

This is the core of the demo — an agent that can query your Ontology and produce Senate-style briefing memos.

### Why Skip Custom Functions

The AIP Agent has a built-in **Object Query** tool that can search, filter, and aggregate your Ontology objects directly — no custom code needed. For this demo, Object Query is sufficient and saves you the complexity of Code Repositories.

(If you want to add custom Functions later for more precise calculations, see the appendix at the end of this guide.)

### Create the Agent

1. Press **Cmd+J** (Mac) or **Ctrl+J** (Windows) to open quick search
2. Search "AIP Agent" or navigate to **Files** → **+ New** → **AIP Agent**
3. Save it in your project folder
4. Name: **Economic Policy Analyst**

### Choose a Model

Under model settings, select **GPT-4o** or **Claude 3.5 Sonnet**. Both are available on DevTier and work well for briefing generation.

### Add Tools

In the agent configuration, add tools:

1. **Object Query** — this is the key tool
   - Configure it with access to all three object types:
     - Economic Indicator Reading
     - Industry Employment
     - Policy Action
   - The agent will be able to search, filter, and aggregate objects

### Add Retrieval Context (Optional but Recommended)

1. Add **Ontology context** for Policy Action
   - This gives the agent awareness of the policy timeline without needing to query it every time
   - Select only key properties: `short_name`, `signed_date`, `policy_area`, `is_landmark`, `summary`
   - **Do NOT include** all properties — token overflow is a common DevTier issue

### Set the System Prompt

```
You are an economic policy analyst supporting a United States Senator's office. Your job is to correlate economic indicator data with legislative timelines and produce professional briefing memos.

Available data:
- Economic indicators (2010-present): GDP, CPI, Core CPI, unemployment rate, total nonfarm payroll, manufacturing employment, Federal funds rate, PCE price index, industrial production, retail sales. National data plus state-level for ID, TX, CA, OH, PA, AZ, MI, GA, NC, WA.
- Industry employment (2010-present): 9 sectors including manufacturing, construction, information, financial activities, education & health, professional services, trade/transport/utilities.
- Policy timeline (2017-2025): 43 economically significant enacted laws including Tax Cuts & Jobs Act (Dec 2017), CARES Act (Mar 2020), American Rescue Plan (Mar 2021), Infrastructure Act (Nov 2021), CHIPS Act (Aug 2022), and Inflation Reduction Act (Aug 2022).

When answering questions:
1. Query the relevant indicator data for the time period
2. Identify what legislation was active in that period
3. Quantify changes with specific numbers and percentages
4. Present findings as a concise, politically neutral briefing memo with clear sections

Always cite specific data points, dates, and values. Use the Object Query tool to look up exact numbers rather than guessing.
```

### Test Questions

Try these to verify the agent works:

1. **"How has manufacturing employment changed since the CHIPS Act was signed?"**
   - Should query Economic Indicator Reading for Manufacturing Employment from Aug 2022 onward

2. **"What was the unemployment impact of the COVID stimulus packages?"**
   - Should query unemployment data 2019-2022, reference CARES Act + American Rescue Plan

3. **"Brief me on inflation trends since 2021"**
   - Should pull CPI and PCE data, note Inflation Reduction Act

4. **"Compare Idaho and California unemployment during COVID recovery"**
   - Should query state-level data for both states, show different trajectories

**If the agent can't find data:** Verify in Ontology Manager that your object types are published and the agent has the Object Query tool configured for each type.

**If you hit rate limits:** DevTier has ~130,000 tokens/minute. Wait 60 seconds and try again. Keep prompts concise.

---

## Phase 4: Workshop App (60 minutes)

### Create the App

1. Press **Cmd+K** and search "Workshop"
2. Click **+ Create new application**
3. Name: **Economic Policy Impact Tracker**
4. Save in your project folder

If you don't see Workshop, go to **Control Panel** → **Application Access** and enable it.

### Layout

#### Row 1 — Controls (full width)

Add three control widgets:

- **Dropdown: Select Indicator**
  - Data source: Economic Indicator Reading, property `indicator_name`
  - This populates with: Real GDP, CPI All Urban Consumers, Unemployment Rate, etc.

- **Dropdown: Select Geography**
  - Data source: Economic Indicator Reading, property `geography`
  - Populates with: United States, Idaho, Texas, California, etc.

- **Date Range Picker**
  - Default: 2018-01-01 to present

Connect these to **application variables** so they filter other widgets.

#### Row 2 — Visualization (2/3 + 1/3 split)

- **Time Series Chart** (2/3 width)
  - Widget: Chart XY or Time Series Analysis
  - Data: Economic Indicator Reading objects, filtered by the dropdown variables
  - X-axis: `date`
  - Y-axis: `value`
  - Add **vertical reference lines** for Policy Action `signed_date` (landmark bills only)

- **Metric Cards** (1/3 width)
  - Latest value
  - Period change (%)
  - Trend direction

#### Row 3 — AI Briefing (full width)

- **AIP Agent widget**
  - Found under AIP widgets section
  - Select your "Economic Policy Analyst" agent
  - Optionally toggle "Show agent reasoning"
  - Map application variables so the agent knows the current filter context

#### Row 4 — Policy Timeline (full width)

- **Object Table**
  - Data: Policy Action objects
  - Columns: `short_name`, `signed_date`, `policy_area`, `is_landmark`
  - Sort by `signed_date` descending
  - Filter by the date range variable

### Connecting Widgets Together

Workshop widgets communicate via **application variables**:
1. Create variables for: `selectedIndicator`, `selectedGeography`, `startDate`, `endDate`
2. Wire each dropdown/picker to write its variable
3. Wire the chart and table to filter by those variables
4. Wire the agent widget to read those variables as context

---

## Phase 5: Record the Demo (30 minutes)

See `docs/VIDEO_SCRIPT.md` for the full 5-minute script.

### Key Demo Flow

1. **The problem** (30 sec): "Every week in the Senator's office, correlating economic data with legislation takes hours of manual research across multiple federal databases..."
2. **The data pipeline** (45 sec): Show the three datasets. Explain: FRED, BLS, Congress.gov → Foundry.
3. **The Ontology** (30 sec): Show the three object types and how they're structured.
4. **Live agent queries** (2 min): Ask 2-3 questions. Show the agent querying real data and producing briefings.
5. **The dashboard** (1 min): Filter by state, change indicators, show policy overlay on the chart.
6. **Impact** (15 sec): "What used to take 2 hours of manual research is now a 30-second query."

---

## DevTier Limitations

| Limitation | Details |
|-----------|---------|
| **Object Type limit** | ~60 total. Delete unused example types if near the limit. |
| **LLM Rate Limit** | ~130,000 tokens/minute. Keep agent prompts concise. Wait 60s if throttled. |
| **Compute/Storage** | Hard caps (Control Panel → Your Plan). Not billed, just blocked. |
| **Object Sets** | `.all()` errors above 100,000 objects. Our datasets are well under this. |
| **Auth** | Authorization Code OAuth only. No service-to-service tokens. |
| **Token overflow** | When using Ontology context in agents, select only the properties you need. |

### Available LLMs

GPT-4o/4.1, Claude 3.5/4, Gemini 2.5, Llama 4, and others. **GPT-4o** or **Claude 3.5 Sonnet** recommended.

### Resources

- **Speedrun: Your First E2E Workflow** (essential): https://learn.palantir.com/speedrun-your-first-e2e-workflow
- **Speedrun: Your First AIP Workflow**: https://learn.palantir.com/speedrun-your-e2e-aip-workflow
- **Palantir Developer Community**: https://community.palantir.com/
- **AIP for Developers**: https://www.palantir.com/aip/developers/

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `foundry_sdk` not found | Package is `foundry-platform-sdk`, imports as `foundry_sdk` |
| `ApiFeaturePreviewUsageOnly` | Update SDK: `pip install --upgrade foundry-platform-sdk` (need >= 1.70) |
| FRED API returns 500 | Transient server error. Script retries automatically. If persistent, wait a few minutes. |
| Datasets show "no schema" in Foundry | The bootstrap sets schemas. If missing, check the script output for errors. |
| Object type won't sync | DevTier has limited compute. Wait 2-3 minutes after publishing. |
| Agent can't find data | Verify object types are published in Ontology Manager and the Object Query tool is configured for each type. |
| Agent hits token overflow | In Ontology context config, select only key properties. Exclude large text fields. |
| Workshop not visible | Enable via Control Panel → Application Access. |
| Object type limit exceeded | Delete unused `[Example]` object types in Ontology Manager. |

---

## Appendix: Custom Functions (Optional)

If you want more precise agent capabilities, you can create custom Functions in a Code Repository. This is optional — the Object Query tool handles most queries.

### Setup

1. In your project folder: **+ New** → **Code Repository**
2. Language: **TypeScript**
3. Foundry auto-generates type-safe bindings from your Ontology

### Example: queryIndicatorTrend

```typescript
import { Function } from "@foundry/functions-api";
import { Objects, EconomicIndicatorReading } from "@foundry/ontology-api";

export class EconFunctions {
  @Function()
  public queryIndicatorTrend(
    indicatorName: string,
    geography: string,
    startDate: string,
    endDate: string
  ): EconomicIndicatorReading[] {
    return Objects.search()
      .economicIndicatorReading()
      .filter(r =>
        r.indicatorName.exactMatch(indicatorName)
        && r.geography.exactMatch(geography)
        && r.date.range().gte(startDate).lte(endDate)
      )
      .orderBy(r => r.date.asc())
      .all();
  }
}
```

### Deploying Functions

1. Write code in the Code Repository editor
2. Click **Build** to compile
3. Click **Tag** to create a release
4. Functions auto-publish to the Ontology
5. In Agent Studio, add a **Function** tool and select your function

**Note:** The generated type names (e.g., `EconomicIndicatorReading`) depend on your exact Ontology naming. Check the auto-generated imports.

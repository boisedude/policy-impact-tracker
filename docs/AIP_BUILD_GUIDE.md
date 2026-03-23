# Building the Economic Policy Impact Tracker in Palantir AIP

This guide walks through the complete build — from pulling real federal data to a working AIP agent and Workshop app in Foundry DevTier.

**Time estimate:** 4-5 hours total across all phases.

---

## Phase 0: Prerequisites (15 minutes)

### Accounts You Need

1. **Palantir AIP DevTier** — https://www.palantir.com/aip/activate
2. **FRED API key** (free, instant) — https://fred.stlouisfed.org/docs/api/api_key.html
3. **Python 3.10+** with pip

### Install Dependencies

```bash
pip install foundry-platform-sdk pandas pyarrow requests python-dotenv
```

### Find Your Foundry Hostname and Space RID

1. Log into Foundry. Your URL will look like: `https://YOURNAME.usw-XX.palantirfoundry.com/`
2. Your hostname is `YOURNAME.usw-XX.palantirfoundry.com`
3. Generate a personal access token: **Settings** (gear icon) > **Tokens** > **Generate new token**
   - Give it a name like "bootstrap"
   - Grant all available scopes
   - Copy the token immediately (you won't see it again)

4. Find your Space RID:
```bash
python scripts/foundry_bootstrap.py \
  --foundry-token YOUR_TOKEN \
  --foundry-host  YOURNAME.usw-XX.palantirfoundry.com \
  --list-spaces
```
This will print your available spaces with their RIDs. Copy the RID for your space.

---

## Phase 1: Data Pipeline (20 minutes)

The bootstrap script pulls **real data** from federal APIs and uploads it directly to Foundry as queryable Parquet datasets.

### Run the Bootstrap

```bash
python scripts/foundry_bootstrap.py \
  --foundry-token YOUR_FOUNDRY_TOKEN \
  --foundry-host  YOURNAME.usw-XX.palantirfoundry.com \
  --fred-key      YOUR_FRED_API_KEY \
  --space-rid     ri.compass.main.folder.XXXXX
```

### What It Does

1. **Pulls from FRED** (Federal Reserve Economic Data):
   - 10 national indicators: GDP, CPI, unemployment, payrolls, manufacturing employment, Fed funds rate, PCE, industrial production, retail sales
   - State-level data for 10 states (ID, TX, CA, OH, PA, AZ, MI, GA, NC, WA)
   - Date range: 2010 to present

2. **Pulls from BLS** (Bureau of Labor Statistics):
   - Employment by industry sector: manufacturing, construction, information, financial, healthcare, etc.
   - 9 industry sectors, monthly data since 2010

3. **Builds a curated policy timeline:**
   - 7 landmark bills: Tax Cuts and Jobs Act, CARES Act, American Rescue Plan, Infrastructure Act, CHIPS Act, Inflation Reduction Act, NDAA FY2024
   - 36 additional economically significant laws: major appropriations, budget deals, trade agreements, COVID response, financial regulation
   - 43 total bills, all real, all from Congress.gov

4. **Uploads everything to Foundry** as Parquet datasets with proper schemas.

### What You'll See in Foundry After Running

In your Space, a new folder: **Economic Policy Impact Tracker** containing:

| Dataset | ~Records | What It Contains |
|---------|----------|-----------------|
| `fred_national_indicators` | ~1,800 | GDP, CPI, unemployment, etc. (national) |
| `fred_state_indicators` | ~3,800 | Unemployment + employment for 10 states |
| `bls_national_industry` | ~1,700 | Employment by industry sector |
| `policy_timeline` | 43 | Enacted laws with signing dates |

The script prints the **dataset RIDs** at the end — save these, you'll need them for the Ontology.

---

## Phase 2: Build the Ontology (45 minutes)

The Ontology turns your datasets into connected objects that the AIP agent can reason about.

### Step 1: Open Ontology Manager

1. In Foundry, click the **compass icon** (left sidebar) to browse files
2. Navigate to your **Economic Policy Impact Tracker** folder
3. Click on any dataset (e.g., `fred_national_indicators`)
4. In the dataset view, look for **"Create object type"** or go to **Ontology Manager** from the left sidebar

### Step 2: Create "Economic Indicator Reading" Object Type

This is your main object — each row is one data point (e.g., "CPI was 305.2 in January 2024").

1. Click **Create Object Type**
2. Name: `Economic Indicator Reading`
3. Click **Back with dataset** → select `fred_national_indicators`
4. Map these properties:

| Property | Column | Type | Nullable |
|----------|--------|------|----------|
| date | date | Date | No |
| value | value | Double | No |
| indicator_name | indicator_name | String | No |
| unit | unit | String | No |
| geography | geography | String | No |
| geo_level | geo_level | String | No |
| series_id | series_id | String | No |

5. **Primary Key:** `series_id` + `date` (composite)
6. Click **Save** and **Publish**

7. **Add a second backing dataset:** After creating, edit the object type and add `fred_state_indicators` as an additional backing dataset. The columns match, so Foundry will union them automatically. This gives you both national and state-level data in one object type.

### Step 3: Create "Policy Action" Object Type

Each row is an enacted law.

1. **Create Object Type** → name: `Policy Action`
2. Back with dataset → `policy_timeline`
3. Map these properties:

| Property | Column | Type | Nullable |
|----------|--------|------|----------|
| short_name | short_name | String | No |
| signed_date | signed_date | Date | No |
| policy_area | policy_area | String | No |
| summary | summary | String | Yes |
| is_landmark | is_landmark | Boolean | No |
| congress | congress | Integer | No |
| bill_type | bill_type | String | No |
| bill_number | bill_number | Integer | No |

4. **Primary Key:** You'll need a unique ID. Options:
   - Use a **computed property**: `congress` + `_` + `bill_type` + `_` + `bill_number` (e.g., "117_hr_5376")
   - Or use `bill_number` if you're only covering one Congress at a time

5. **Save** and **Publish**

### Step 4: Create "Industry Employment" Object Type

1. **Create Object Type** → name: `Industry Employment`
2. Back with dataset → `bls_national_industry`
3. Map:

| Property | Column | Type | Nullable |
|----------|--------|------|----------|
| date | date | Date | No |
| value | value | Double | No |
| indicator_name | indicator_name | String | No |
| unit | unit | String | No |
| geography | geography | String | No |

4. **Primary Key:** `indicator_name` + `date` (composite)
5. **Save** and **Publish**

### Step 5: Create Link Types (Relationships)

This is optional but makes the agent smarter:

1. In Ontology Manager, go to **Link Types**
2. Create: **Policy Action** → **Economic Indicator Reading**
   - Name: `impacts_indicators`
   - Logic: indicator readings where `date >= policy.signed_date`
   - This lets you ask "what happened to GDP after the CHIPS Act?"

**Note:** If link types are complex to set up in DevTier, skip this — the AIP Functions in Phase 3 will handle the correlation logic instead.

---

## Phase 3: AIP Functions (60 minutes)

Functions let the LLM query your ontology programmatically.

### Where to Create Functions

1. Go to your project folder in Compass
2. Click **+ New** → **Code repository** (or **Function**)
3. Select **TypeScript** as the language

### Function 1: queryIndicatorTrend

```typescript
import { Function, OntologyEditFunction } from "@foundry/functions-api";
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

### Function 2: findPoliciesInRange

```typescript
@Function()
public findPoliciesInRange(
  startDate: string,
  endDate: string,
  policyArea?: string
): PolicyAction[] {
  let query = Objects.search()
    .policyAction()
    .filter(r =>
      r.signedDate.range().gte(startDate).lte(endDate)
    );

  if (policyArea) {
    query = query.filter(r => r.policyArea.exactMatch(policyArea));
  }

  return query.orderBy(r => r.signedDate.asc()).all();
}
```

### Function 3: calculateImpactSincePolicy

```typescript
@Function()
public calculateImpactSincePolicy(
  indicatorName: string,
  geography: string,
  policySignedDate: string,
  monthsAfter: number = 12
): string {
  // Get value at policy date
  const baseline = Objects.search()
    .economicIndicatorReading()
    .filter(r =>
      r.indicatorName.exactMatch(indicatorName)
      && r.geography.exactMatch(geography)
      && r.date.range().lte(policySignedDate)
    )
    .orderBy(r => r.date.desc())
    .take(1);

  // Get value monthsAfter later
  const endDate = new Date(policySignedDate);
  endDate.setMonth(endDate.getMonth() + monthsAfter);

  const later = Objects.search()
    .economicIndicatorReading()
    .filter(r =>
      r.indicatorName.exactMatch(indicatorName)
      && r.geography.exactMatch(geography)
      && r.date.range().lte(endDate.toISOString().split('T')[0])
    )
    .orderBy(r => r.date.desc())
    .take(1);

  if (baseline.length === 0 || later.length === 0) {
    return "Insufficient data for this indicator/geography combination.";
  }

  const beforeVal = baseline[0].value!;
  const afterVal = later[0].value!;
  const changePct = ((afterVal - beforeVal) / beforeVal * 100).toFixed(2);
  const trend = afterVal > beforeVal ? "increased" : "decreased";

  return `${indicatorName} in ${geography}: ${trend} from ${beforeVal} to ${afterVal} (${changePct}%) over ${monthsAfter} months after policy signing.`;
}
```

### How to Deploy

1. Write the code in the Code Repository editor
2. Click **Build** (or **Checks**) — Foundry compiles and validates
3. Click **Tag** to create a release version
4. The functions auto-publish to the Ontology and become available to AIP agents

**Important:** The exact TypeScript API depends on your Ontology naming. Foundry auto-generates type-safe bindings from your object type names. If your object type is "Economic Indicator Reading", the generated class is `EconomicIndicatorReading`.

**If Functions are too complex:** You can skip this phase and go straight to the AIP Agent in Phase 4. The agent can reason over the Ontology objects directly without custom functions — functions just make it more precise.

---

## Phase 4: AIP Agent (30 minutes)

### Create the Agent

1. Go to **AIP Agent Studio** (left sidebar or search for it)
2. Click **Create Agent**
3. Name: **Economic Policy Analyst**
4. **Model:** GPT-4o or Claude 3.5 Sonnet (both available on DevTier)

### System Prompt

```
You are an economic policy analyst supporting a United States Senator's office.

Your job is to correlate economic indicator data with legislative timelines and produce Senate-style briefing memos.

When asked about economic indicators or policy impacts:
1. Query the relevant indicator data for the time period
2. Identify what legislation was signed in that period
3. Quantify the changes (percentage change, trend direction)
4. Synthesize into a professional briefing memo

Data available:
- National indicators: GDP, CPI, unemployment, payrolls, manufacturing employment, Fed funds rate, PCE, industrial production, retail sales (2010-present)
- State-level: unemployment rate and employment for ID, TX, CA, OH, PA, AZ, MI, GA, NC, WA
- Industry employment: 9 sectors (manufacturing, construction, information, financial, healthcare, etc.)
- Policy timeline: 43 economically significant laws (2017-2025) including Tax Cuts & Jobs Act, CARES Act, American Rescue Plan, Infrastructure Act, CHIPS Act, Inflation Reduction Act

Always cite specific data points and dates. Be politically neutral.
Format responses as professional briefing memos with sections.
```

### Give the Agent Tools

- Add your **three functions** as tools (if you built them in Phase 3)
- OR add **Ontology object search** permissions for your three object types
- The agent needs read access to: Economic Indicator Reading, Policy Action, Industry Employment

### Test Questions

Try these in the agent chat:

1. **"How has manufacturing employment changed since the CHIPS Act was signed?"**
   - Agent should: pull manufacturing data from Aug 2022 onward, note the CHIPS Act signing date, calculate change

2. **"What was the unemployment impact of the COVID stimulus packages?"**
   - Agent should: pull unemployment data 2019-2022, correlate with CARES Act (Mar 2020), American Rescue Plan (Mar 2021)

3. **"Brief me on inflation trends since 2021 and what legislation might have contributed"**
   - Agent should: pull CPI/PCE data, identify Inflation Reduction Act, American Rescue Plan, note the trajectory

4. **"Compare Idaho and California unemployment rates during COVID recovery"**
   - Agent should: pull state-level data for both states, show the different recovery curves

---

## Phase 5: Workshop App (60 minutes)

### Create the App

1. Go to **Workshop** (left sidebar)
2. **Create new application**: "Economic Policy Impact Tracker"

### Layout

**Row 1 — Controls (full width):**
- **Dropdown:** Select Indicator — populated from the `indicator_name` property of Economic Indicator Reading
- **Dropdown:** Select Geography — "United States" + the 10 state names
- **Date Range Picker:** Start/End dates (default: 2018-01-01 to present)

**Row 2 — Charts (split 2/3 + 1/3):**
- **Time Series Chart** (2/3 width):
  - Data source: Economic Indicator Reading objects, filtered by the dropdowns
  - X-axis: `date`
  - Y-axis: `value`
  - Add **vertical reference lines** for Policy Action `signed_date` values (landmark bills)
- **Stats Card** (1/3 width):
  - Latest value
  - Period change (%)
  - Trend direction arrow

**Row 3 — AI Briefing Panel (full width):**
- **Text Input:** "Ask a question about economic policy..."
- **AIP Agent Panel:** Connected to your "Economic Policy Analyst" agent
- The agent response appears below the input

**Row 4 — Policy Timeline (full width):**
- **Object Table:** Policy Action objects, sorted by `signed_date` desc
- Columns: `short_name`, `signed_date`, `policy_area`, `is_landmark`
- Click a row to see details

### Connecting Widgets

- The dropdowns filter the chart data via **variables**
- The date range picker filters both the chart and the policy table
- The agent panel passes the current filter context to the agent

---

## Phase 6: Record the Demo (30 minutes)

See `docs/VIDEO_SCRIPT.md` for the full 5-minute script.

### Key Demo Flow

1. **Open with the problem** (30 sec): "Every week in the Senator's office, correlating economic data with legislation takes hours..."
2. **Show the data pipeline** (45 sec): Explain FRED/BLS/Congress.gov → Foundry. Show the datasets.
3. **Show the Ontology** (30 sec): Object types, how they're connected
4. **Live queries** (2 min): Ask the agent 2-3 questions, show it reasoning over real data
5. **Workshop dashboard** (1 min): Show the chart, filter by state, overlay policy dates
6. **Close with impact** (15 sec): "2-hour research task → 30-second query"

---

## DevTier Limitations

| Limitation | Details |
|-----------|---------|
| **LLM Rate Limit** | ~130,000 tokens/minute. Keep agent prompts concise. |
| **Compute/Storage** | Hard caps (check Control Panel > Your Plan). Not billed, just blocked. |
| **Object Sets** | `.all()` errors above 100,000 objects. Our datasets are well under this. |
| **Auth** | Authorization Code OAuth only. Fine for a demo. |

### Available LLMs

GPT-4o/4.1, Claude 3.5/4, Gemini 2.5, Llama 4, and others. For the agent, **GPT-4o** or **Claude 3.5 Sonnet** are good choices.

### Learning Resources

- **Speedrun: Your First E2E Workflow** (60-90 min): https://learn.palantir.com/speedrun-your-first-e2e-workflow
- **Speedrun: Your First AIP Workflow**: https://learn.palantir.com/speedrun-your-e2e-aip-workflow
- Complete at least the first one before building. It covers Ontology + Workshop basics.

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| **Bootstrap script fails with `foundry_sdk` not found** | `pip install foundry-platform-sdk` (note: imports as `foundry_sdk`) |
| **"ApiFeaturePreviewUsageOnly" error** | The SDK handles this — make sure you're on `foundry-platform-sdk >= 1.70` |
| **FRED 500 errors** | Transient — the script retries automatically. If persistent, wait a few minutes. |
| **Datasets show "no schema"** | The bootstrap sets schemas automatically. If missing, re-run the upload. |
| **Object type won't sync** | DevTier has smaller compute. Wait 2-3 minutes after publishing. |
| **Agent doesn't find data** | Verify the object types are published and the agent has access to them. |
| **Functions won't compile** | Check that your object type API names match exactly (case-sensitive). |

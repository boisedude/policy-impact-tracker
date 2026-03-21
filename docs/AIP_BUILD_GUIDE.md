# Building the Economic Policy Impact Tracker in Palantir AIP

This guide walks through recreating this project in Palantir AIP DevTier, step by step.

## Prerequisites

1. Create a Palantir AIP DevTier account at https://www.palantir.com/aip/activate
2. Have the sample CSV files from `sample_data/` ready for upload
3. (Optional) Get API keys to collect real data — see `data_collectors/` README

---

## Phase 1: Data Ingestion (30 minutes)

### Step 1: Upload Datasets

1. Log into your AIP workspace
2. Navigate to **Data Connection** > **File Import**
3. Upload each CSV file:
   - `fred_national_indicators.csv` — National economic indicators (GDP, CPI, unemployment, etc.)
   - `fred_state_indicators.csv` — State-level economic data
   - `policy_timeline.csv` — Major legislation with signing dates
   - `bls_national_industry.csv` — Employment by industry sector

4. For each file, Foundry will auto-detect the schema. Verify:
   - `date` columns are typed as **Date**
   - `value` columns are typed as **Double/Decimal**
   - `is_landmark` is typed as **Boolean**

### Step 2: Create a Project Folder

1. Go to **Compass** (the file browser)
2. Create a new folder: `Economic Policy Impact Tracker`
3. Move all uploaded datasets into this folder

---

## Phase 2: Build the Ontology (45 minutes)

The Ontology is how Palantir AIP understands your data as connected objects, not just tables.

### Object Types to Create

#### 1. Economic Indicator Reading

Represents a single data point (e.g., "CPI was 305.2 in January 2024")

| Property | Source Column | Type |
|----------|-------------|------|
| `date` | date | Date |
| `value` | value | Double |
| `indicator_name` | indicator_name | String |
| `unit` | unit | String |
| `geography` | geography | String |
| `state_code` | state_code | String (nullable) |
| `geo_level` | geo_level | String |
| `series_id` | series_id | String |

**Primary Key:** Composite of `series_id` + `date`

**Backing datasets:** `fred_national_indicators` and `fred_state_indicators`

#### 2. Policy Action

Represents a signed bill/law

| Property | Source Column | Type |
|----------|-------------|------|
| `bill_id` | (computed: congress + bill_type + bill_number) | String |
| `title` | title | String |
| `short_name` | short_name | String |
| `signed_date` | signed_date | Date |
| `policy_area` | policy_area | String |
| `summary` | summary | String |
| `economic_impact_category` | economic_impact_category | String |
| `is_landmark` | is_landmark | Boolean |

**Primary Key:** `bill_id`

**Backing dataset:** `policy_timeline`

#### 3. Industry Employment

Represents industry-sector employment levels

| Property | Source Column | Type |
|----------|-------------|------|
| `date` | date | Date |
| `value` | value | Double |
| `indicator_name` | indicator_name | String |
| `unit` | unit | String |

**Primary Key:** Composite of `indicator_name` + `date`

**Backing dataset:** `bls_national_industry`

### How to Create Object Types

1. Go to **Ontology Manager**
2. Click **Create Object Type**
3. Name it (e.g., "Economic Indicator Reading")
4. Click **Back with dataset** and select the appropriate CSV
5. Map properties to columns
6. Set the primary key
7. Click **Save**

### Link Types (Relationships)

Create a time-based link between Policy Actions and Economic Indicator Readings:

- **Policy Action** → **Economic Indicator Reading**: "impacts_indicators"
  - Logic: All indicator readings where `date >= policy.signed_date`
  - This lets you ask "what happened to indicators after this policy?"

---

## Phase 3: AIP Logic & Functions (60 minutes)

This is where AIP's AI capabilities shine. You'll create functions that let the LLM reason over your data.

### Function 1: Query Indicator Trend

**Purpose:** Given an indicator name and date range, return the trend data

```
Name: queryIndicatorTrend
Inputs:
  - indicator_name: String
  - geography: String (default: "United States")
  - start_date: Date
  - end_date: Date
Output: List of Economic Indicator Reading objects

Logic:
  Search Economic Indicator Reading objects where:
    indicator_name == input.indicator_name
    AND geography == input.geography
    AND date >= input.start_date
    AND date <= input.end_date
  Order by date ascending
```

### Function 2: Find Related Policies

**Purpose:** Given a date range, find what bills were signed

```
Name: findPoliciesInRange
Inputs:
  - start_date: Date
  - end_date: Date
  - policy_area: String (optional)
Output: List of Policy Action objects

Logic:
  Search Policy Action objects where:
    signed_date >= input.start_date
    AND signed_date <= input.end_date
    AND (policy_area == input.policy_area if provided)
  Order by signed_date ascending
```

### Function 3: Calculate Change

**Purpose:** Calculate the percentage change in an indicator since a policy was signed

```
Name: calculateImpactSincePolicy
Inputs:
  - indicator_name: String
  - geography: String
  - policy_signed_date: Date
  - months_after: Integer (default: 12)
Output: Object with { before_value, after_value, change_percent, trend }

Logic:
  1. Get the indicator value on/nearest to policy_signed_date
  2. Get the indicator value months_after months later
  3. Calculate percentage change
  4. Return summary
```

### How to Create Functions in AIP

1. Go to **AIP Logic**
2. Click **Create Function**
3. Define inputs and output types
4. Write the logic using the visual builder or TypeScript
5. Test with sample inputs
6. Publish the function

---

## Phase 4: AIP Agent & Workshop App (90 minutes)

### Create an AIP Agent

1. Go to **AIP Agent Studio**
2. Create a new agent: "Economic Policy Analyst"
3. Give it access to your three functions:
   - `queryIndicatorTrend`
   - `findPoliciesInRange`
   - `calculateImpactSincePolicy`

4. Set the system prompt:

```
You are an economic policy analyst for a United States Senator's office.
When asked about economic indicators or policy impacts:
1. Use queryIndicatorTrend to get the relevant data
2. Use findPoliciesInRange to identify what legislation was active
3. Use calculateImpactSincePolicy to quantify changes
4. Synthesize findings into a concise, Senate-style briefing memo

Always cite specific data points and dates. Be politically neutral.
Format responses as professional briefing memos.
```

5. Test with questions like:
   - "How has manufacturing employment changed since the CHIPS Act?"
   - "What was the unemployment impact of COVID stimulus?"
   - "Brief me on inflation trends since 2021"

### Build a Workshop App

1. Go to **Workshop**
2. Create a new application: "Economic Policy Impact Tracker"
3. Add these widgets:

**Row 1 — Controls:**
- Dropdown: Select Indicator (populated from Ontology)
- Dropdown: Select Geography (United States + state list)
- Date Range Picker: Start/End dates

**Row 2 — Visualization:**
- Time Series Chart (2/3 width):
  - X-axis: date
  - Y-axis: value
  - Add vertical reference lines for policy signing dates
- Stats Card (1/3 width):
  - Latest value
  - Period change
  - Trend direction

**Row 3 — AI Panel:**
- Text Input: "Ask a question about economic indicators..."
- AIP Agent Response Panel: Connected to your "Economic Policy Analyst" agent
- Policy Timeline: List of relevant policies with dates

**Row 4 — Detail:**
- Table: Raw data with filtering
- Policy detail card: Shows full bill info on click

---

## Phase 5: Polish & Record Demo (60 minutes)

### Demo Flow (suggested for 5-minute video)

See `docs/VIDEO_SCRIPT.md` for the full script.

### Tips for a Winning Demo

1. **Start with the problem** — "Every week in the Senator's office, we need to correlate..."
2. **Show the data pipeline** — Brief walkthrough of how data gets in
3. **Demo the Ontology** — Show how objects are connected
4. **Live query** — Ask a real policy question, show the agent reasoning
5. **Emphasize the workflow** — This isn't just a dashboard, it's an analyst tool
6. **End with impact** — "This turns a 2-hour research task into a 30-second query"

---

## DevTier Limitations to Know

| Limitation | Details |
|-----------|---------|
| **LLM Rate Limit** | ~130,000 tokens/minute across all LLM calls. Keep agent prompts concise. |
| **Compute/Storage** | Hard caps (check Control Panel > Your Plan). Not billed, just blocked. |
| **Object Sets** | `.all()` throws an error if >100,000 objects. Our datasets are well under this. |
| **Auth** | Only Authorization Code OAuth — no service-to-service. Fine for a demo. |
| **Beta Features** | Must request via support ticket. Stick to GA features for the demo. |

### Available LLMs on DevTier

You can choose from: GPT-4o/4.1, Claude 3.5/4, Gemini 2.5, Llama 4, and others. For the agent, **GPT-4o** or **Claude 3.5 Sonnet** are good choices — fast and capable for briefing generation.

### Key Learning Resources

- **Speedrun: Your First E2E Workflow** (60-90 min): https://learn.palantir.com/speedrun-your-first-e2e-workflow
- **Speedrun: Your First AIP Workflow**: https://learn.palantir.com/speedrun-your-e2e-aip-workflow
- Complete these BEFORE building. They walk through exactly the steps above.

---

## Troubleshooting

### Common DevTier Issues

- **CSV upload fails:** Check for encoding issues. Save as UTF-8 CSV.
- **Date columns not recognized:** Ensure dates are in `YYYY-MM-DD` format.
- **Ontology sync is slow:** DevTier has smaller compute. Wait a few minutes after publishing.
- **AIP Logic function errors:** Test with minimal inputs first. Check that object type names match exactly.
- **Agent doesn't use functions:** Make sure functions are published AND added to the agent's tool list.
- **LLM rate limit errors:** Keep prompts short. Avoid bulk LLM operations. If hit, wait 60 seconds.
- **Workflow Builder missing:** Manually enable in Control Panel > Application Access > Ontology.

### Getting Help

- Palantir Developer Community: https://community.palantir.com/
- Foundry docs: Look in the product documentation for your specific version
- AIP Logic examples: Check the AIP Community Registry on GitHub

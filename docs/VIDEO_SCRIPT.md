# Demo Video Script — Economic Policy Impact Tracker

**Target length:** 4-5 minutes
**Format:** Screen recording with voiceover (Loom, OBS, or QuickTime)

---

## Opening (0:00 - 0:30)

**[Show: Title slide or your AIP workspace]**

> "Hi, I'm Hudson Odom. I work in a United States Senator's office supporting economic policy.
>
> Every week, our team needs to answer questions like: 'How has manufacturing employment changed in our state since the CHIPS Act passed?' or 'What's the latest inflation picture heading into this committee hearing?'
>
> Today that process involves pulling data from three or four government websites, cross-referencing bill timelines, and manually drafting briefing memos. It takes hours.
>
> I built this tool in Palantir AIP to turn that into a 30-second workflow."

---

## The Data (0:30 - 1:15)

**[Show: Foundry data browser with your datasets]**

> "I started by pulling publicly available economic data from three federal sources:
>
> First, **FRED** — the Federal Reserve's economic database. I pulled GDP, CPI, unemployment rate, manufacturing employment, and other key indicators. Both national and state-level.
>
> Second, **BLS** — the Bureau of Labor Statistics. This gives us detailed employment data broken down by industry sector.
>
> Third, **Congress.gov**. I pulled the timeline of major economic legislation — the CARES Act, the American Rescue Plan, the CHIPS Act, the Inflation Reduction Act — with their signing dates and summaries.
>
> All of this is public data. I wrote Python scripts to collect and format it, then uploaded the CSVs to Foundry."

**[Show: Click through each dataset briefly]**

---

## The Ontology (1:15 - 2:00)

**[Show: Ontology Manager with your object types]**

> "In Palantir's Ontology, I modeled this data as three connected object types:
>
> **Economic Indicator Readings** — each data point has a date, value, indicator name, and geography. So I can ask for 'CPI in California from 2020 to 2024.'
>
> **Policy Actions** — each major bill with its signing date, policy area, and economic impact summary.
>
> **Industry Employment** — sector-level employment so we can see which industries were affected by specific policies.
>
> The key connection: I can link any policy action to the indicator readings that followed it. This is what lets the AI reason about cause and effect."

**[Show: Click on a Policy Action object, show linked indicator readings]**

---

## The AI Agent (2:00 - 3:15)

**[Show: AIP Agent Studio or Workshop app with the chat interface]**

> "Here's where it gets powerful. I created an AIP agent with access to three functions:
>
> It can query indicator trends, find policies in a date range, and calculate the change in any indicator since a policy was signed.
>
> Let me show you a real question."

**[Type: "How has manufacturing employment changed since the CHIPS Act passed in August 2022?"]**

> "Watch — the agent calls the queryIndicatorTrend function to get manufacturing employment data, finds the CHIPS Act signing date, and calculates the change. Then it synthesizes this into a briefing memo."

**[Show: Agent response with data points and analysis]**

> "In 30 seconds, I have a data-backed briefing that would have taken our team an hour to compile manually."

**[Type another question: "Brief me on inflation trends since 2021 and what legislation was relevant"]**

> "Let me try another one — this is the kind of question that comes up before a committee hearing."

**[Show: Agent response correlating CPI data with American Rescue Plan, rate hikes, Inflation Reduction Act]**

---

## The Dashboard (3:15 - 4:00)

**[Show: Workshop app with chart, timeline, and stats]**

> "I also built a Workshop dashboard for visual analysis.
>
> On the left, a time series chart — here showing national unemployment rate. The dashed red lines mark when major bills were signed. You can immediately see the CARES Act coinciding with the COVID spike, and the recovery pattern after stimulus.
>
> On the right, a policy timeline showing what legislation was active during the period.
>
> Below that, summary statistics — latest value, trend direction, and month-over-month change.
>
> Everything updates when I change the indicator or geography."

**[Demo: Switch to CPI, then switch geography to a specific state]**

---

## Why This Matters (4:00 - 4:30)

**[Show: Back to the agent or a summary view]**

> "This tool solves a real problem I face every day:
>
> Senate staffers need to make data-driven policy recommendations, but the data lives across a dozen government websites and the analysis is manual.
>
> With AIP, I connected public economic data to a policy timeline and gave an AI agent the tools to reason across both. A question that used to take hours of research now takes 30 seconds.
>
> And because it's built on real government data sources, it's trustworthy and auditable — every data point traces back to FRED, BLS, or Congress.gov."

---

## Closing (4:30 - 4:45)

> "This is the Economic Policy Impact Tracker, built in Palantir AIP. Thank you."

---

## Recording Tips

1. **Practice the demo flow 2-3 times** before recording
2. **Pre-load your queries** — have the AIP agent ready with a fresh context
3. **Use a clean workspace** — close unnecessary tabs, use full screen
4. **Keep mouse movements deliberate** — slow, clear clicks
5. **Audio quality matters** — use a headset or external mic, record in a quiet room
6. **If you stumble, keep going** — one continuous take is better than spliced clips
7. **Upload as unlisted YouTube video** as instructed

## What They're Evaluating

Based on Palantir's instructions, they want to see:
- **Problem decomposition** — Can you break a real problem into data + logic + AI?
- **Technical execution** — Did you actually use AIP features (Ontology, Functions, Agent)?
- **Communication** — Can you explain why this matters to a non-technical audience?
- **Authenticity** — Does this feel like a real problem you care about?

Your Senate background is your superpower here. Lean into it.

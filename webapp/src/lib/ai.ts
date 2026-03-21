import OpenAI from "openai";

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY || "",
});

export interface BriefingRequest {
  question: string;
  indicatorData: Array<{ date: string; value: number; indicator_name: string; unit: string }>;
  relevantPolicies: Array<{ short_name: string; signed_date: string; summary: string; policy_area: string }>;
  summary: {
    latestValue: number;
    previousValue: number;
    change: number;
    changePercent: number;
    trend: string;
    period: string;
  } | null;
  geography: string;
}

export async function generateBriefing(req: BriefingRequest): Promise<string> {
  const { question, indicatorData, relevantPolicies, summary, geography } = req;

  // Build a data summary for the LLM (don't send all data points, just key stats)
  const recentData = indicatorData.slice(-12); // Last 12 data points
  const dataPoints = recentData
    .map((d) => `${d.date.substring(0, 7)}: ${d.value}`)
    .join(", ");

  const policyList = relevantPolicies
    .map((p) => `- ${p.short_name} (signed ${p.signed_date}): ${p.summary}`)
    .join("\n");

  const systemPrompt = `You are an economic policy analyst preparing briefings for a United States Senator's office.
Your briefings should be:
- Concise and actionable (2-3 paragraphs max)
- Data-driven with specific numbers
- Connected to relevant policy actions
- Written in professional Senate staffer style
- Politically neutral and factual

Format your response with:
1. A headline summary (one sentence)
2. Key findings with data
3. Policy context (which bills/actions are relevant)
4. Implications or suggested talking points`;

  const userPrompt = `Question: ${question}

Geography: ${geography}
Indicator: ${indicatorData[0]?.indicator_name || "Unknown"}
Unit: ${indicatorData[0]?.unit || "Unknown"}

Current Trend: ${summary ? `${summary.trend} over ${summary.period}` : "Insufficient data"}
Latest Value: ${summary?.latestValue ?? "N/A"}
Month-over-Month Change: ${summary ? `${summary.change} (${summary.changePercent}%)` : "N/A"}

Recent Data Points: ${dataPoints}

Relevant Policy Actions During This Period:
${policyList || "None identified"}

Please generate a Senate-style briefing memo addressing the question above.`;

  const completion = await openai.chat.completions.create({
    model: "gpt-4o-mini",
    messages: [
      { role: "system", content: systemPrompt },
      { role: "user", content: userPrompt },
    ],
    max_tokens: 800,
    temperature: 0.3,
  });

  return completion.choices[0]?.message?.content || "Unable to generate briefing.";
}

export function generateFallbackBriefing(req: BriefingRequest): string {
  const { summary, relevantPolicies, geography } = req;
  const indicator = req.indicatorData[0]?.indicator_name || "the selected indicator";
  const unit = req.indicatorData[0]?.unit || "";

  if (!summary) {
    return "Insufficient data available for the selected parameters. Please adjust your query.";
  }

  const trendWord = summary.trend === "increasing" ? "risen" : summary.trend === "decreasing" ? "fallen" : "remained stable";
  const changeDir = summary.change >= 0 ? "up" : "down";

  let briefing = `**${indicator} — ${geography}**\n\n`;
  briefing += `Over the period ${summary.period}, ${indicator.toLowerCase()} in ${geography} has ${trendWord}. `;
  briefing += `The most recent reading is **${summary.latestValue.toLocaleString()} ${unit}**, `;
  briefing += `${changeDir} ${Math.abs(summary.change).toLocaleString()} (${Math.abs(summary.changePercent)}%) from the prior period.\n\n`;

  if (relevantPolicies.length > 0) {
    briefing += `**Relevant Policy Actions:**\n`;
    for (const p of relevantPolicies.slice(0, 5)) {
      briefing += `- **${p.short_name}** (${p.signed_date.substring(0, 10)}): ${p.summary}\n`;
    }
    briefing += `\nThese legislative actions may have contributed to the observed trends. Further analysis recommended for causal attribution.\n`;
  }

  return briefing;
}

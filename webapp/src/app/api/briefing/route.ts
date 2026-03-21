import { NextRequest } from "next/server";
import { buildBriefingContext } from "@/lib/data";
import { generateBriefing, generateFallbackBriefing } from "@/lib/ai";

export async function POST(request: NextRequest) {
  const body = await request.json();
  const {
    question,
    indicator,
    geography = "United States",
    startDate,
    endDate,
  } = body as {
    question: string;
    indicator: string;
    geography?: string;
    startDate?: string;
    endDate?: string;
  };

  if (!question || !indicator) {
    return Response.json(
      { error: "question and indicator are required" },
      { status: 400 },
    );
  }

  const context = buildBriefingContext(indicator, geography, startDate, endDate);

  const briefingReq = {
    question,
    indicatorData: context.indicatorData,
    relevantPolicies: context.relevantPolicies,
    summary: context.summary,
    geography,
  };

  let briefing: string;
  let aiPowered = false;

  if (process.env.OPENAI_API_KEY) {
    try {
      briefing = await generateBriefing(briefingReq);
      aiPowered = true;
    } catch {
      briefing = generateFallbackBriefing(briefingReq);
    }
  } else {
    briefing = generateFallbackBriefing(briefingReq);
  }

  return Response.json({
    briefing,
    aiPowered,
    summary: context.summary,
    policiesConsidered: context.relevantPolicies.length,
    dataPointsAnalyzed: context.indicatorData.length,
  });
}

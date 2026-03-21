import { NextRequest } from "next/server";
import { buildBriefingContext, getAvailableIndicators } from "@/lib/data";

export async function POST(request: NextRequest) {
  const body = await request.json();
  const {
    indicator,
    geography = "United States",
    startDate,
    endDate,
  } = body as {
    indicator: string;
    geography?: string;
    startDate?: string;
    endDate?: string;
  };

  if (!indicator) {
    return Response.json(
      {
        error: "indicator is required",
        available: getAvailableIndicators(),
      },
      { status: 400 },
    );
  }

  const context = buildBriefingContext(indicator, geography, startDate, endDate);

  return Response.json({
    indicator,
    geography,
    dataPoints: context.indicatorData.length,
    summary: context.summary,
    relevantPolicies: context.relevantPolicies,
    data: context.indicatorData,
  });
}

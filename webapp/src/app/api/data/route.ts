import { NextRequest } from "next/server";
import {
  getNationalIndicators,
  getStateIndicators,
  getPolicyTimeline,
  getIndustryData,
  getAvailableStates,
  getAvailableIndicators,
} from "@/lib/data";

export async function GET(request: NextRequest) {
  const { searchParams } = request.nextUrl;
  const type = searchParams.get("type");

  switch (type) {
    case "national":
      return Response.json(getNationalIndicators());
    case "state": {
      const stateCode = searchParams.get("state");
      let data = getStateIndicators();
      if (stateCode) {
        data = data.filter((r) => r.state_code === stateCode.toUpperCase());
      }
      return Response.json(data);
    }
    case "policies":
      return Response.json(getPolicyTimeline());
    case "industry":
      return Response.json(getIndustryData());
    case "meta":
      return Response.json({
        states: getAvailableStates(),
        indicators: getAvailableIndicators(),
      });
    default:
      return Response.json(
        { error: "Specify type: national, state, policies, industry, or meta" },
        { status: 400 },
      );
  }
}

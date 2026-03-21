import Papa from "papaparse";
import fs from "fs";
import path from "path";

export interface EconomicRecord {
  date: string;
  value: number;
  series_id?: string;
  indicator_name: string;
  frequency?: string;
  unit: string;
  geography: string;
  state_code?: string;
  geo_level: string;
  source?: string;
}

export interface PolicyBill {
  congress: number;
  bill_type: string;
  bill_number: number;
  title: string;
  short_name: string;
  signed_date: string;
  policy_area: string;
  summary: string;
  is_landmark: boolean;
  economic_impact_category?: string;
}

export interface IndustryRecord {
  date: string;
  value: number;
  indicator_name: string;
  unit: string;
  geography: string;
  geo_level: string;
  source: string;
}

function readCSV<T>(filename: string): T[] {
  const filePath = path.join(process.cwd(), "public", filename);
  const csv = fs.readFileSync(filePath, "utf-8");
  const result = Papa.parse<T>(csv, {
    header: true,
    dynamicTyping: true,
    skipEmptyLines: true,
  });
  return result.data;
}

let _nationalCache: EconomicRecord[] | null = null;
let _stateCache: EconomicRecord[] | null = null;
let _policyCache: PolicyBill[] | null = null;
let _industryCache: IndustryRecord[] | null = null;

export function getNationalIndicators(): EconomicRecord[] {
  if (!_nationalCache) {
    _nationalCache = readCSV<EconomicRecord>("fred_national_indicators.csv");
  }
  return _nationalCache;
}

export function getStateIndicators(): EconomicRecord[] {
  if (!_stateCache) {
    _stateCache = readCSV<EconomicRecord>("fred_state_indicators.csv");
  }
  return _stateCache;
}

export function getPolicyTimeline(): PolicyBill[] {
  if (!_policyCache) {
    _policyCache = readCSV<PolicyBill>("policy_timeline.csv");
  }
  return _policyCache;
}

export function getIndustryData(): IndustryRecord[] {
  if (!_industryCache) {
    _industryCache = readCSV<IndustryRecord>("bls_national_industry.csv");
  }
  return _industryCache;
}

export function getAvailableStates(): string[] {
  const data = getStateIndicators();
  const states = new Set(data.map((r) => r.state_code).filter(Boolean));
  return Array.from(states).sort() as string[];
}

export function getAvailableIndicators(): string[] {
  const national = getNationalIndicators();
  const names = new Set(national.map((r) => r.indicator_name));
  return Array.from(names).sort();
}

export function queryIndicator(
  indicatorName: string,
  geography?: string,
  startDate?: string,
  endDate?: string,
): EconomicRecord[] {
  let data: EconomicRecord[];

  if (geography && geography !== "United States") {
    data = getStateIndicators().filter(
      (r) =>
        r.state_code === geography ||
        r.geography.toLowerCase() === geography.toLowerCase(),
    );
  } else {
    data = getNationalIndicators();
  }

  let filtered = data.filter(
    (r) => r.indicator_name.toLowerCase() === indicatorName.toLowerCase(),
  );

  if (startDate) {
    filtered = filtered.filter((r) => r.date >= startDate);
  }
  if (endDate) {
    filtered = filtered.filter((r) => r.date <= endDate);
  }

  return filtered.sort((a, b) => a.date.localeCompare(b.date));
}

export function findPoliciesInRange(
  startDate: string,
  endDate: string,
): PolicyBill[] {
  const policies = getPolicyTimeline();
  return policies.filter(
    (p) => p.signed_date >= startDate && p.signed_date <= endDate,
  );
}

export function buildBriefingContext(
  indicator: string,
  geography: string,
  startDate?: string,
  endDate?: string,
): {
  indicatorData: EconomicRecord[];
  relevantPolicies: PolicyBill[];
  summary: {
    latestValue: number;
    previousValue: number;
    change: number;
    changePercent: number;
    trend: string;
    period: string;
  } | null;
} {
  const indicatorData = queryIndicator(
    indicator,
    geography,
    startDate,
    endDate,
  );
  const dateRange = {
    start: startDate || (indicatorData[0]?.date ?? "2017-01-01"),
    end: endDate || (indicatorData[indicatorData.length - 1]?.date ?? "2025-12-01"),
  };

  const relevantPolicies = findPoliciesInRange(dateRange.start, dateRange.end);

  let summary = null;
  if (indicatorData.length >= 2) {
    const latest = indicatorData[indicatorData.length - 1];
    const previous = indicatorData[indicatorData.length - 2];
    const first = indicatorData[0];
    const change = latest.value - previous.value;
    const changePercent =
      previous.value !== 0 ? (change / previous.value) * 100 : 0;
    const overallChange = latest.value - first.value;
    const trend =
      overallChange > 0 ? "increasing" : overallChange < 0 ? "decreasing" : "flat";

    summary = {
      latestValue: latest.value,
      previousValue: previous.value,
      change: Math.round(change * 100) / 100,
      changePercent: Math.round(changePercent * 100) / 100,
      trend,
      period: `${first.date.substring(0, 7)} to ${latest.date.substring(0, 7)}`,
    };
  }

  return { indicatorData, relevantPolicies, summary };
}

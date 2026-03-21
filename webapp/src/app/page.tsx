"use client";

import { useState, useEffect, useCallback } from "react";
import IndicatorChart from "@/components/IndicatorChart";
import PolicyTimeline from "@/components/PolicyTimeline";
import BriefingPanel from "@/components/BriefingPanel";

interface Meta {
  states: string[];
  indicators: string[];
}

interface DataPoint {
  date: string;
  value: number;
  indicator_name: string;
  unit: string;
}

interface Policy {
  short_name: string;
  signed_date: string;
  summary: string;
  policy_area: string;
  economic_impact_category?: string;
}

interface QueryResult {
  indicator: string;
  geography: string;
  dataPoints: number;
  summary: {
    latestValue: number;
    previousValue: number;
    change: number;
    changePercent: number;
    trend: string;
    period: string;
  } | null;
  relevantPolicies: Policy[];
  data: DataPoint[];
}

const STATE_NAMES: Record<string, string> = {
  ID: "Idaho", TX: "Texas", CA: "California", OH: "Ohio",
  PA: "Pennsylvania", AZ: "Arizona", MI: "Michigan",
  GA: "Georgia", NC: "North Carolina", WA: "Washington",
};

export default function Home() {
  const [meta, setMeta] = useState<Meta | null>(null);
  const [indicator, setIndicator] = useState("Unemployment Rate");
  const [geography, setGeography] = useState("United States");
  const [startDate, setStartDate] = useState("2017-01-01");
  const [endDate, setEndDate] = useState("2025-12-01");
  const [result, setResult] = useState<QueryResult | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetch("/api/data?type=meta")
      .then((r) => r.json())
      .then(setMeta);
  }, []);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const resp = await fetch("/api/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ indicator, geography, startDate, endDate }),
      });
      const data = await resp.json();
      setResult(data);
    } catch {
      console.error("Failed to fetch data");
    } finally {
      setLoading(false);
    }
  }, [indicator, geography, startDate, endDate]);

  useEffect(() => {
    if (meta) fetchData();
  }, [meta, fetchData]);

  return (
    <div className="min-h-screen">
      {/* Header */}
      <header className="bg-gradient-to-r from-blue-950 to-blue-900 text-white">
        <div className="max-w-7xl mx-auto px-6 py-6">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-white/10 rounded-lg">
              <svg className="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z" />
              </svg>
            </div>
            <div>
              <h1 className="text-xl font-bold tracking-tight">
                Economic Policy Impact Tracker
              </h1>
              <p className="text-blue-200 text-sm">
                Correlate economic indicators with legislative actions
              </p>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-6">
        {/* Controls */}
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5 mb-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {/* Indicator Selector */}
            <div>
              <label className="block text-xs font-medium text-gray-500 uppercase tracking-wider mb-1.5">
                Economic Indicator
              </label>
              <select
                value={indicator}
                onChange={(e) => setIndicator(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {meta?.indicators.map((ind) => (
                  <option key={ind} value={ind}>
                    {ind}
                  </option>
                ))}
              </select>
            </div>

            {/* Geography Selector */}
            <div>
              <label className="block text-xs font-medium text-gray-500 uppercase tracking-wider mb-1.5">
                Geography
              </label>
              <select
                value={geography}
                onChange={(e) => setGeography(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="United States">United States (National)</option>
                {meta?.states.map((st) => (
                  <option key={st} value={st}>
                    {STATE_NAMES[st] || st}
                  </option>
                ))}
              </select>
            </div>

            {/* Date Range */}
            <div>
              <label className="block text-xs font-medium text-gray-500 uppercase tracking-wider mb-1.5">
                Start Date
              </label>
              <input
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-500 uppercase tracking-wider mb-1.5">
                End Date
              </label>
              <input
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>
        </div>

        {loading && (
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
          </div>
        )}

        {result && !loading && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Main Chart Area */}
            <div className="lg:col-span-2 space-y-6">
              {/* Chart */}
              <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5">
                <IndicatorChart
                  data={result.data}
                  title={`${result.indicator} — ${geography === "United States" ? "National" : STATE_NAMES[geography] || geography}`}
                  unit={result.data[0]?.unit || ""}
                  policies={result.relevantPolicies}
                  height={420}
                />
              </div>

              {/* Briefing Panel */}
              <BriefingPanel
                indicator={indicator}
                geography={geography}
                startDate={startDate}
                endDate={endDate}
              />
            </div>

            {/* Sidebar */}
            <div className="space-y-6">
              {/* Quick Stats */}
              {result.summary && (
                <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5">
                  <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-3">
                    Quick Stats
                  </h3>
                  <dl className="space-y-3">
                    <div>
                      <dt className="text-xs text-gray-500">Latest Value</dt>
                      <dd className="text-2xl font-bold text-gray-900">
                        {result.summary.latestValue.toLocaleString()}
                      </dd>
                    </div>
                    <div>
                      <dt className="text-xs text-gray-500">
                        Month-over-Month
                      </dt>
                      <dd
                        className={`text-lg font-semibold ${result.summary.change >= 0 ? "text-green-600" : "text-red-600"}`}
                      >
                        {result.summary.change >= 0 ? "+" : ""}
                        {result.summary.change.toLocaleString()} (
                        {result.summary.changePercent}%)
                      </dd>
                    </div>
                    <div>
                      <dt className="text-xs text-gray-500">Overall Trend</dt>
                      <dd className="text-sm font-medium capitalize text-gray-700">
                        {result.summary.trend} over {result.summary.period}
                      </dd>
                    </div>
                    <div>
                      <dt className="text-xs text-gray-500">Data Points</dt>
                      <dd className="text-sm text-gray-700">
                        {result.dataPoints}
                      </dd>
                    </div>
                  </dl>
                </div>
              )}

              {/* Policy Timeline */}
              <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5">
                <PolicyTimeline policies={result.relevantPolicies} />
              </div>
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="mt-auto border-t border-gray-200 bg-white">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <p className="text-xs text-gray-400 text-center">
            Economic Policy Impact Tracker — Data from FRED, BLS, Congress.gov
            | Built as a Palantir AIP Demo Concept
          </p>
        </div>
      </footer>
    </div>
  );
}

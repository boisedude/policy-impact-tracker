"use client";

import { useState } from "react";

interface BriefingResponse {
  briefing: string;
  aiPowered: boolean;
  summary: {
    latestValue: number;
    previousValue: number;
    change: number;
    changePercent: number;
    trend: string;
    period: string;
  } | null;
  policiesConsidered: number;
  dataPointsAnalyzed: number;
}

const EXAMPLE_QUESTIONS = [
  "How has manufacturing employment changed since the CHIPS Act passed?",
  "What was the impact of COVID stimulus on unemployment?",
  "Brief me on inflation trends since 2021 and relevant policy actions",
  "How did the Tax Cuts and Jobs Act affect GDP growth?",
  "What is the current state of the labor market compared to pre-pandemic?",
];

export default function BriefingPanel({
  indicator,
  geography,
  startDate,
  endDate,
}: {
  indicator: string;
  geography: string;
  startDate?: string;
  endDate?: string;
}) {
  const [question, setQuestion] = useState("");
  const [briefing, setBriefing] = useState<BriefingResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function askQuestion(q?: string) {
    const query = q || question;
    if (!query.trim()) return;

    setLoading(true);
    setError(null);
    try {
      const resp = await fetch("/api/briefing", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question: query,
          indicator,
          geography,
          startDate,
          endDate,
        }),
      });
      if (!resp.ok) throw new Error("Failed to generate briefing");
      const data = await resp.json();
      setBriefing(data);
    } catch {
      setError("Failed to generate briefing. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
      <div className="bg-gradient-to-r from-blue-900 to-blue-800 px-5 py-4">
        <h2 className="text-white font-semibold text-lg flex items-center gap-2">
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          Senate Briefing Generator
        </h2>
        <p className="text-blue-200 text-sm mt-1">
          Ask a policy question — get a data-driven briefing memo
        </p>
      </div>

      <div className="p-5">
        {/* Question Input */}
        <div className="flex gap-2">
          <input
            type="text"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && askQuestion()}
            placeholder="Ask a question about economic indicators and policy..."
            className="flex-1 px-4 py-2.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
          <button
            onClick={() => askQuestion()}
            disabled={loading || !question.trim()}
            className="px-5 py-2.5 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? (
              <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
            ) : (
              "Generate Briefing"
            )}
          </button>
        </div>

        {/* Example Questions */}
        <div className="mt-3 flex flex-wrap gap-1.5">
          {EXAMPLE_QUESTIONS.map((eq, i) => (
            <button
              key={i}
              onClick={() => {
                setQuestion(eq);
                askQuestion(eq);
              }}
              className="text-xs px-2.5 py-1 bg-gray-100 text-gray-600 rounded-full hover:bg-blue-50 hover:text-blue-700 transition-colors"
            >
              {eq}
            </button>
          ))}
        </div>

        {/* Error */}
        {error && (
          <div className="mt-4 p-3 bg-red-50 text-red-700 rounded-lg text-sm">
            {error}
          </div>
        )}

        {/* Briefing Result */}
        {briefing && (
          <div className="mt-5">
            <div className="flex items-center gap-3 mb-3">
              <div className="flex items-center gap-1.5 text-xs text-gray-500">
                <span className={`inline-block w-2 h-2 rounded-full ${briefing.aiPowered ? "bg-green-500" : "bg-amber-500"}`} />
                {briefing.aiPowered ? "AI-Generated" : "Template-Based"}
              </div>
              <span className="text-xs text-gray-400">|</span>
              <span className="text-xs text-gray-500">
                {briefing.dataPointsAnalyzed} data points · {briefing.policiesConsidered} policies
              </span>
            </div>

            {/* Summary Stats */}
            {briefing.summary && (
              <div className="grid grid-cols-4 gap-3 mb-4">
                <div className="bg-gray-50 rounded-lg p-3 text-center">
                  <div className="text-lg font-bold text-gray-900">
                    {briefing.summary.latestValue.toLocaleString()}
                  </div>
                  <div className="text-xs text-gray-500">Latest Value</div>
                </div>
                <div className="bg-gray-50 rounded-lg p-3 text-center">
                  <div className={`text-lg font-bold ${briefing.summary.change >= 0 ? "text-green-600" : "text-red-600"}`}>
                    {briefing.summary.change >= 0 ? "+" : ""}
                    {briefing.summary.change.toLocaleString()}
                  </div>
                  <div className="text-xs text-gray-500">MoM Change</div>
                </div>
                <div className="bg-gray-50 rounded-lg p-3 text-center">
                  <div className={`text-lg font-bold ${briefing.summary.changePercent >= 0 ? "text-green-600" : "text-red-600"}`}>
                    {briefing.summary.changePercent >= 0 ? "+" : ""}
                    {briefing.summary.changePercent}%
                  </div>
                  <div className="text-xs text-gray-500">% Change</div>
                </div>
                <div className="bg-gray-50 rounded-lg p-3 text-center">
                  <div className="text-lg font-bold text-gray-900 capitalize">
                    {briefing.summary.trend}
                  </div>
                  <div className="text-xs text-gray-500">Trend</div>
                </div>
              </div>
            )}

            {/* Briefing Text */}
            <div className="prose prose-sm max-w-none bg-gray-50 rounded-lg p-5 border border-gray-200">
              <div className="whitespace-pre-wrap text-sm text-gray-800 leading-relaxed">
                {briefing.briefing.split("\n").map((line, i) => {
                  if (line.startsWith("**") && line.endsWith("**")) {
                    return (
                      <p key={i} className="font-bold text-gray-900 mt-3 first:mt-0">
                        {line.replace(/\*\*/g, "")}
                      </p>
                    );
                  }
                  if (line.startsWith("- ")) {
                    return (
                      <li key={i} className="ml-4 list-disc">
                        {line.substring(2).split("**").map((part, j) =>
                          j % 2 === 1 ? (
                            <strong key={j}>{part}</strong>
                          ) : (
                            <span key={j}>{part}</span>
                          ),
                        )}
                      </li>
                    );
                  }
                  if (line.trim() === "") return <br key={i} />;
                  return (
                    <p key={i} className="mt-1">
                      {line.split("**").map((part, j) =>
                        j % 2 === 1 ? (
                          <strong key={j}>{part}</strong>
                        ) : (
                          <span key={j}>{part}</span>
                        ),
                      )}
                    </p>
                  );
                })}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

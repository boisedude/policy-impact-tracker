"use client";

import dynamic from "next/dynamic";

const Plot = dynamic(() => import("react-plotly.js"), { ssr: false });

interface DataPoint {
  date: string;
  value: number;
}

interface PolicyMarker {
  signed_date: string;
  short_name: string;
}

export default function IndicatorChart({
  data,
  title,
  unit,
  policies = [],
  height = 400,
}: {
  data: DataPoint[];
  title: string;
  unit: string;
  policies?: PolicyMarker[];
  height?: number;
}) {
  if (!data.length) {
    return (
      <div className="flex items-center justify-center h-64 bg-gray-50 rounded-lg border border-dashed border-gray-300">
        <p className="text-gray-400">No data available</p>
      </div>
    );
  }

  const dates = data.map((d) => d.date);
  const values = data.map((d) => d.value);

  // Policy vertical lines as shapes
  const shapes = policies.map((p) => ({
    type: "line" as const,
    x0: p.signed_date,
    x1: p.signed_date,
    y0: 0,
    y1: 1,
    yref: "paper" as const,
    line: {
      color: "rgba(220, 38, 38, 0.4)",
      width: 1.5,
      dash: "dash" as const,
    },
  }));

  // Policy annotations
  const annotations = policies.map((p, i) => ({
    x: p.signed_date,
    y: 1 - i * 0.08,
    yref: "paper" as const,
    text: p.short_name,
    showarrow: false,
    font: { size: 9, color: "rgba(220, 38, 38, 0.8)" },
    textangle: "-45",
    xanchor: "left" as const,
  }));

  return (
    <Plot
      data={[
        {
          x: dates,
          y: values,
          type: "scatter",
          mode: "lines",
          line: { color: "#2563eb", width: 2 },
          fill: "tozeroy",
          fillcolor: "rgba(37, 99, 235, 0.06)",
          name: title,
          hovertemplate: `%{x|%b %Y}<br><b>%{y:,.1f}</b> ${unit}<extra></extra>`,
        },
      ]}
      layout={{
        title: { text: title },
        xaxis: {
          title: { text: "" },
          gridcolor: "#f1f5f9",
          tickformat: "%b %Y",
        },
        yaxis: {
          title: { text: unit },
          gridcolor: "#f1f5f9",
        },
        shapes,
        annotations,
        margin: { l: 60, r: 30, t: 50, b: 50 },
        paper_bgcolor: "transparent",
        plot_bgcolor: "transparent",
        hovermode: "x unified",
        height,
      }}
      config={{
        responsive: true,
        displayModeBar: false,
      }}
      className="w-full"
    />
  );
}

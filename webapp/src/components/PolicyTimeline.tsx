"use client";

interface Policy {
  short_name: string;
  signed_date: string;
  summary: string;
  policy_area: string;
  economic_impact_category?: string;
}

const CATEGORY_COLORS: Record<string, string> = {
  "Tax Policy": "bg-red-100 border-red-400 text-red-800",
  "Fiscal Stimulus": "bg-green-100 border-green-400 text-green-800",
  "Infrastructure & Investment": "bg-blue-100 border-blue-400 text-blue-800",
  "Industrial Policy": "bg-purple-100 border-purple-400 text-purple-800",
  "Tax & Energy Policy": "bg-amber-100 border-amber-400 text-amber-800",
  "Labor & Safety Net": "bg-teal-100 border-teal-400 text-teal-800",
  "Defense Spending": "bg-slate-100 border-slate-400 text-slate-800",
  "Foreign Aid & Trade": "bg-orange-100 border-orange-400 text-orange-800",
};

export default function PolicyTimeline({
  policies,
  onPolicyClick,
}: {
  policies: Policy[];
  onPolicyClick?: (policy: Policy) => void;
}) {
  if (!policies.length) return null;

  return (
    <div className="space-y-3">
      <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wider">
        Policy Timeline
      </h3>
      <div className="relative">
        <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-gray-200" />
        <div className="space-y-4">
          {policies.map((policy, i) => {
            const cat = policy.economic_impact_category || policy.policy_area;
            const colorClass =
              CATEGORY_COLORS[cat] ||
              "bg-gray-100 border-gray-400 text-gray-800";
            return (
              <div
                key={i}
                className="relative pl-10 cursor-pointer group"
                onClick={() => onPolicyClick?.(policy)}
              >
                <div className="absolute left-2.5 top-1.5 w-3 h-3 rounded-full bg-white border-2 border-blue-500 group-hover:bg-blue-500 transition-colors" />
                <div
                  className={`border-l-4 rounded-r-lg p-3 ${colorClass} group-hover:shadow-md transition-shadow`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-sm">
                      {policy.short_name}
                    </span>
                    <span className="text-xs opacity-75">
                      {policy.signed_date.substring(0, 10)}
                    </span>
                  </div>
                  <p className="text-xs mt-1 opacity-80">{policy.summary}</p>
                  <span className="inline-block mt-1 text-[10px] font-medium px-1.5 py-0.5 rounded bg-white/50">
                    {cat}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

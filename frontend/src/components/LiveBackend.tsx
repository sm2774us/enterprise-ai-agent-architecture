import React, { useEffect, useState } from "react";
import { CheckCircle2, XCircle, RefreshCw, Terminal } from "lucide-react";

interface HealthEntry {
  reachable: boolean;
  status?: string;
  service?: string;
}

type HealthMap = Record<string, HealthEntry>;

const SERVICE_LABELS: Record<string, string> = {
  agentOrchestrator: "agent-orchestrator (AI Agent Studio)",
  controlTower: "control-tower (AI Control Tower)",
  mcpA2aGateway: "mcp-a2a-gateway (MCP / A2A)",
  llmGateway: "llm-gateway (LLM + Vector Search)",
};

/**
 * Live Python Backend tab.
 *
 * Every other tab in this app can run purely on mock data. This tab proves
 * the other tabs *aren't just UI*: it calls the actual FastAPI services in
 * services/ over HTTP (proxied through this frontend's server.ts) and shows
 * real health, a real governance decision, and a real vector search result.
 *
 * If the backends aren't running (e.g. you haven't done `docker compose up`),
 * this tab degrades gracefully and tells you exactly that -- it never fakes
 * a "reachable" result.
 */
export const LiveBackend: React.FC = () => {
  const [health, setHealth] = useState<HealthMap | null>(null);
  const [loading, setLoading] = useState(false);
  const [policyResult, setPolicyResult] = useState<any>(null);
  const [searchResult, setSearchResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const refreshHealth = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch("/api/live/health");
      const data = await res.json();
      setHealth(data);
    } catch (e) {
      setError("Could not reach the frontend server's /api/live/health proxy.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refreshHealth();
  }, []);

  const runPolicyCheck = async () => {
    try {
      const res = await fetch("/api/live/policy/check", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          agent_id: "itsm-triage-agent",
          skill_id: "create_change_request",
          risk_tier: "write_high_risk",
          requires_human_approval: true,
          max_autonomous_risk_tier: "write_high_risk",
        }),
      });
      setPolicyResult(await res.json());
    } catch {
      setPolicyResult({ error: "control-tower unreachable" });
    }
  };

  const runVectorSearch = async () => {
    try {
      const res = await fetch("/api/live/vector/search", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: "payment gateway latency incident", top_k: 3 }),
      });
      setSearchResult(await res.json());
    } catch {
      setSearchResult({ error: "llm-gateway unreachable" });
    }
  };

  return (
    <div className="max-w-5xl mx-auto p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold text-slate-100">Live Python Backend</h2>
          <p className="text-slate-400 text-sm mt-1">
            Real FastAPI services from <code>services/</code> — not mocked. Run{" "}
            <code>docker compose up --build</code> from the repo root, then refresh below.
          </p>
        </div>
        <button
          onClick={refreshHealth}
          className="flex items-center gap-2 px-3 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-sm"
        >
          <RefreshCw size={16} className={loading ? "animate-spin" : ""} />
          Refresh
        </button>
      </div>

      {error && <div className="text-amber-400 text-sm">{error}</div>}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {health &&
          Object.entries(health).map(([key, entry]) => (
            <div
              key={key}
              className="flex items-center justify-between rounded-lg border border-slate-800 bg-slate-900/60 px-4 py-3"
            >
              <span className="text-slate-200 text-sm">{SERVICE_LABELS[key] || key}</span>
              {entry.reachable ? (
                <span className="flex items-center gap-1 text-emerald-400 text-xs">
                  <CheckCircle2 size={14} /> reachable
                </span>
              ) : (
                <span className="flex items-center gap-1 text-rose-400 text-xs">
                  <XCircle size={14} /> unreachable
                </span>
              )}
            </div>
          ))}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
        <div className="rounded-lg border border-slate-800 bg-slate-950/60 p-4">
          <h3 className="text-slate-200 text-sm font-medium mb-2">
            Real AI Control Tower policy decision
          </h3>
          <button
            onClick={runPolicyCheck}
            className="text-xs px-3 py-1.5 rounded bg-indigo-600/20 text-indigo-300 border border-indigo-600/40 hover:bg-indigo-600/30 mb-3"
          >
            Evaluate a high-risk skill call
          </button>
          {policyResult && (
            <pre className="text-xs text-slate-400 overflow-x-auto bg-black/30 rounded p-3 flex items-start gap-2">
              <Terminal size={14} className="mt-0.5 shrink-0" />
              {JSON.stringify(policyResult, null, 2)}
            </pre>
          )}
        </div>

        <div className="rounded-lg border border-slate-800 bg-slate-950/60 p-4">
          <h3 className="text-slate-200 text-sm font-medium mb-2">
            Real vector search (llm-gateway)
          </h3>
          <button
            onClick={runVectorSearch}
            className="text-xs px-3 py-1.5 rounded bg-emerald-600/20 text-emerald-300 border border-emerald-600/40 hover:bg-emerald-600/30 mb-3"
          >
            Search knowledge base
          </button>
          {searchResult && (
            <pre className="text-xs text-slate-400 overflow-x-auto bg-black/30 rounded p-3 flex items-start gap-2">
              <Terminal size={14} className="mt-0.5 shrink-0" />
              {JSON.stringify(searchResult, null, 2)}
            </pre>
          )}
        </div>
      </div>
    </div>
  );
};

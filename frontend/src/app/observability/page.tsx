"use client";

import { useQuery } from "@tanstack/react-query";
import { getMetrics, getResources, getTraces, getDocuments, getAgents, getMemoryStats, getLatency, getCosts } from "@/lib/api";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell,
} from "recharts";
import { Clock, Cpu, Activity, Server, Database, Bot, BookOpen, FileText, Zap, Globe, DollarSign } from "lucide-react";

const COLORS = ["#6366f1", "#06b6d4", "#10b981", "#f59e0b", "#ef4444", "#ec4899"];

export default function ObservabilityPage() {
  const { data: metrics } = useQuery({ queryKey: ["metrics"], queryFn: getMetrics, refetchInterval: 5000 });
  const { data: resources } = useQuery({ queryKey: ["resources"], queryFn: getResources, refetchInterval: 5000 });
  const { data: traces } = useQuery({ queryKey: ["traces"], queryFn: getTraces, refetchInterval: 10000 });
  const { data: docsData } = useQuery({ queryKey: ["documents"], queryFn: getDocuments });
  const { data: agentsData } = useQuery({ queryKey: ["agents"], queryFn: getAgents });
  const { data: memStats } = useQuery({ queryKey: ["memoryStats"], queryFn: getMemoryStats });
  const { data: latencyDetail } = useQuery({ queryKey: ["latencyDetail"], queryFn: getLatency, refetchInterval: 10000 });
  const { data: costs } = useQuery({ queryKey: ["costs"], queryFn: getCosts, refetchInterval: 10000 });

  const latencyData = metrics?.latency
    ? [
        { name: "Avg", value: Math.round(metrics.latency.avg_ms || 0) },
        { name: "P50", value: Math.round(metrics.latency.p50_ms || 0) },
        { name: "P95", value: Math.round(metrics.latency.p95_ms || 0) },
        { name: "P99", value: Math.round(metrics.latency.p99_ms || 0) },
      ]
    : [];

  // Provider distribution from latency detail
  const providerBreakdown = latencyDetail?.by_provider || {};
  const providerData = Object.entries(providerBreakdown).map(([name, stats]: [string, any]) => ({
    name: name === "ollama" ? "Local (Ollama)" : name === "groq" ? "Cloud (Groq)" : name,
    value: stats.count || 0,
    avgMs: Math.round(stats.avg_ms || 0),
  }));

  // Agent distribution from traces
  const agentCounts: Record<string, number> = {};
  (traces?.traces || []).forEach((t: { source: string; type: string }) => {
    if (t.type === "task_response") {
      agentCounts[t.source] = (agentCounts[t.source] || 0) + 1;
    }
  });
  const agentDistribution = Object.entries(agentCounts).map(([name, count]) => ({ name, value: count }));

  // Document categorization
  const allDocs = docsData?.documents || [];
  const systemDocs = allDocs.filter((d: { metadata: Record<string, unknown> }) => d.metadata?.system_document === "true");
  const userDocs = allDocs.filter((d: { metadata: Record<string, unknown> }) => d.metadata?.system_document !== "true");
  const categories: Record<string, number> = {};
  allDocs.forEach((d: { metadata: Record<string, unknown> }) => {
    const cat = String(d.metadata?.category || d.metadata?.source || "unknown").replace(".pdf", "");
    categories[cat] = (categories[cat] || 0) + 1;
  });
  const categoryData = Object.entries(categories).slice(0, 6).map(([name, value]) => ({ name: name.slice(0, 15), value }));

  const errorRate = ((metrics?.error_rate || 0) * 100);
  const totalRequests = metrics?.total_requests || 0;

  return (
    <div className="max-w-7xl mx-auto space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold">Observability Dashboard</h1>
        <p className="text-sm text-muted-foreground">Real-time performance metrics, agent activity, and system health</p>
      </div>

      {/* Top stats cards */}
      <div className="grid grid-cols-2 md:grid-cols-6 gap-3">
        <div className="glass rounded-xl p-4 space-y-1">
          <div className="flex items-center gap-2 text-xs text-muted-foreground"><Activity size={12} />Total Requests</div>
          <p className="text-2xl font-bold">{totalRequests}</p>
          <p className="text-[10px] text-muted">{metrics?.total_errors || 0} errors</p>
        </div>
        <div className="glass rounded-xl p-4 space-y-1">
          <div className="flex items-center gap-2 text-xs text-muted-foreground"><Clock size={12} />Avg Latency</div>
          <p className="text-2xl font-bold">{Math.round(metrics?.latency?.avg_ms || 0)}<span className="text-sm text-muted">ms</span></p>
          <p className="text-[10px] text-muted">P95: {Math.round(metrics?.latency?.p95_ms || 0)}ms</p>
        </div>
        <div className="glass rounded-xl p-4 space-y-1">
          <div className="flex items-center gap-2 text-xs text-muted-foreground"><Zap size={12} />Error Rate</div>
          <p className={`text-2xl font-bold ${errorRate > 10 ? "text-danger" : errorRate > 0 ? "text-warning" : "text-success"}`}>{errorRate.toFixed(1)}%</p>
          <p className="text-[10px] text-muted">{errorRate === 0 ? "All clear" : "Check logs"}</p>
        </div>
        <div className="glass rounded-xl p-4 space-y-1">
          <div className="flex items-center gap-2 text-xs text-muted-foreground"><DollarSign size={12} className="text-success" />Total Cost</div>
          <p className="text-2xl font-bold font-mono">${(costs?.total_cost_usd || 0).toFixed(5)}</p>
          <p className="text-[10px] text-muted">Saved: ${(costs?.savings?.estimated_savings_usd || 0).toFixed(5)}</p>
        </div>
        <div className="glass rounded-xl p-4 space-y-1">
          <div className="flex items-center gap-2 text-xs text-muted-foreground"><BookOpen size={12} />Knowledge Base</div>
          <p className="text-2xl font-bold">{allDocs.length}</p>
          <p className="text-[10px] text-muted">{systemDocs.length} system · {userDocs.length} user</p>
        </div>
        <div className="glass rounded-xl p-4 space-y-1">
          <div className="flex items-center gap-2 text-xs text-muted-foreground"><Bot size={12} />Agents Active</div>
          <p className="text-2xl font-bold">{agentsData?.agents?.length || 0}</p>
          <p className="text-[10px] text-muted">{(traces?.traces || []).length} events</p>
        </div>
      </div>

      {/* Charts row */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Latency Distribution */}
        <div className="glass rounded-xl p-5 space-y-4">
          <h3 className="text-sm font-semibold flex items-center gap-2"><Clock size={14} className="text-primary" />Latency Distribution</h3>
          {latencyData.length > 0 && latencyData.some(d => d.value > 0) ? (
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={latencyData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
                <XAxis dataKey="name" stroke="#71717a" fontSize={11} />
                <YAxis stroke="#71717a" fontSize={11} tickFormatter={(v) => `${v > 1000 ? `${(v/1000).toFixed(1)}s` : `${v}ms`}`} />
                <Tooltip contentStyle={{ background: "#111113", border: "1px solid #27272a", borderRadius: "8px", fontSize: "12px" }}
                  formatter={(value) => { const v = Number(value); return [`${v > 1000 ? `${(v/1000).toFixed(1)}s` : `${v}ms`}`, "Latency"]; }} />
                <Bar dataKey="value" fill="#6366f1" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-[200px] flex items-center justify-center text-sm text-muted">Send some chat messages to see latency data</div>
          )}
        </div>

        {/* Provider Distribution */}
        <div className="glass rounded-xl p-5 space-y-4">
          <h3 className="text-sm font-semibold flex items-center gap-2"><Globe size={14} className="text-accent" />Provider Distribution</h3>
          {providerData.length > 0 ? (
            <>
              <ResponsiveContainer width="100%" height={160}>
                <PieChart>
                  <Pie data={providerData} cx="50%" cy="50%" innerRadius={40} outerRadius={65} paddingAngle={5} dataKey="value" label={false}>
                    {providerData.map((_, index) => (
                      <Cell key={index} fill={index === 0 ? "#6366f1" : "#06b6d4"} />
                    ))}
                  </Pie>
                  <Tooltip contentStyle={{ background: "#111113", border: "1px solid #27272a", borderRadius: "8px", fontSize: "12px" }} />
                </PieChart>
              </ResponsiveContainer>
              <div className="space-y-1">
                {providerData.map((p, i) => (
                  <div key={i} className="flex justify-between text-xs items-center">
                    <div className="flex items-center gap-1.5">
                      <span className="w-2.5 h-2.5 rounded-full shrink-0" style={{ backgroundColor: i === 0 ? "#6366f1" : "#06b6d4" }} />
                      <span className="text-muted-foreground">{p.name}</span>
                    </div>
                    <span className="font-mono">{p.value} reqs · avg {p.avgMs}ms</span>
                  </div>
                ))}
              </div>
              <div className="h-px bg-border my-3" />
              <div className="space-y-1.5 text-xs">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Total Tokens</span>
                  <span className="font-mono">{costs?.token_usage?.total_tokens || 0}</span>
                </div>
                <div className="flex justify-between text-[10px] text-muted">
                  <span>Input / Output</span>
                  <span className="font-mono">{costs?.token_usage?.total_input_tokens || 0} / {costs?.token_usage?.total_output_tokens || 0}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Est. Local Savings</span>
                  <span className="font-mono text-success font-semibold">+${(costs?.savings?.estimated_savings_usd || 0).toFixed(5)}</span>
                </div>
              </div>
            </>
          ) : (
            <div className="h-[200px] flex items-center justify-center text-sm text-muted">No routing data yet</div>
          )}
        </div>

        {/* Knowledge by Category */}
        <div className="glass rounded-xl p-5 space-y-4">
          <h3 className="text-sm font-semibold flex items-center gap-2"><FileText size={14} className="text-warning" />Knowledge by Category</h3>
          {categoryData.length > 0 ? (
            <>
              <ResponsiveContainer width="100%" height={160}>
                <PieChart>
                  <Pie data={categoryData} cx="50%" cy="50%" innerRadius={40} outerRadius={65} paddingAngle={5} dataKey="value" label={false}>
                    {categoryData.map((_, index) => (
                      <Cell key={index} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip contentStyle={{ background: "#111113", border: "1px solid #27272a", borderRadius: "8px", fontSize: "12px" }} />
                </PieChart>
              </ResponsiveContainer>
              <div className="space-y-1 mt-2">
                {categoryData.map((c, i) => (
                  <div key={i} className="flex justify-between text-xs items-center">
                    <div className="flex items-center gap-1.5 truncate">
                      <span className="w-2.5 h-2.5 rounded-full shrink-0" style={{ backgroundColor: COLORS[i % COLORS.length] }} />
                      <span className="text-muted-foreground truncate">{c.name}</span>
                    </div>
                    <span className="font-mono font-semibold">{c.value} doc{c.value > 1 ? "s" : ""}</span>
                  </div>
                ))}
              </div>
            </>
          ) : (
            <div className="h-[200px] flex items-center justify-center text-sm text-muted">No documents ingested yet</div>
          )}
        </div>
      </div>

      {/* System Resources */}
      <div className="glass rounded-xl p-5 space-y-4">
        <h3 className="text-sm font-semibold flex items-center gap-2"><Server size={14} className="text-accent" />System Resources</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="space-y-2">
            <div className="flex justify-between text-xs"><span className="text-muted-foreground">CPU</span><span>{resources?.cpu_percent || 0}%</span></div>
            <div className="h-2 bg-surface-2 rounded-full overflow-hidden">
              <div className={`h-full rounded-full transition-all duration-500 ${(resources?.cpu_percent || 0) > 80 ? "bg-danger" : "bg-primary"}`} style={{ width: `${resources?.cpu_percent || 0}%` }} />
            </div>
          </div>
          <div className="space-y-2">
            <div className="flex justify-between text-xs"><span className="text-muted-foreground">RAM</span><span>{resources?.memory_percent || 0}%</span></div>
            <div className="h-2 bg-surface-2 rounded-full overflow-hidden">
              <div className={`h-full rounded-full transition-all duration-500 ${(resources?.memory_percent || 0) > 85 ? "bg-danger" : "bg-accent"}`} style={{ width: `${resources?.memory_percent || 0}%` }} />
            </div>
          </div>
          <div className="text-xs space-y-1">
            <span className="text-muted-foreground">Memory</span>
            <p className="font-mono">{resources?.memory_used_gb || 0} / {resources?.memory_total_gb || 0} GB</p>
          </div>
          <div className="text-xs space-y-1">
            <span className="text-muted-foreground">Uptime</span>
            <p className="font-mono">{metrics?.resources ? `${Math.floor((metrics.resources.cpu_percent || 0))}% load` : "—"}</p>
          </div>
        </div>
      </div>

      {/* Bottom row: Memory + Agent Activity */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="glass rounded-xl p-5 space-y-4">
          <h3 className="text-sm font-semibold flex items-center gap-2"><Database size={14} className="text-primary" />Memory Tiers</h3>
          <div className="space-y-3">
            <div className="flex items-center justify-between p-3 bg-surface-2 rounded-lg">
              <span className="text-xs">Semantic Store (ChromaDB)</span>
              <span className="text-sm font-mono font-bold">{memStats?.semantic?.documents || allDocs.length} chunks</span>
            </div>
            <div className="flex items-center justify-between p-3 bg-surface-2 rounded-lg">
              <span className="text-xs">Ephemeral Sessions</span>
              <span className="text-sm font-mono font-bold">{memStats?.ephemeral?.active_sessions || 0}</span>
            </div>
            <div className="flex items-center justify-between p-3 bg-surface-2 rounded-lg">
              <span className="text-xs">Knowledge Graph Nodes</span>
              <span className="text-sm font-mono font-bold">{memStats?.graph?.total_nodes || 0}</span>
            </div>
            <div className="flex items-center justify-between p-3 bg-surface-2 rounded-lg">
              <span className="text-xs">Graph Edges</span>
              <span className="text-sm font-mono font-bold">{memStats?.graph?.total_edges || 0}</span>
            </div>
          </div>
        </div>

        <div className="glass rounded-xl p-5 space-y-4">
          <h3 className="text-sm font-semibold flex items-center gap-2"><Bot size={14} className="text-warning" />Agent Activity</h3>
          {agentDistribution.length > 0 ? (
            <div className="space-y-2">
              {agentDistribution.map((a, i) => (
                <div key={i} className="flex items-center gap-3">
                  <span className="text-xs text-muted-foreground w-24 truncate">{a.name}</span>
                  <div className="flex-1 h-5 bg-surface-2 rounded-full overflow-hidden">
                    <div className="h-full rounded-full transition-all duration-500"
                      style={{ width: `${(a.value / Math.max(...agentDistribution.map(x => x.value))) * 100}%`, background: COLORS[i % COLORS.length] }} />
                  </div>
                  <span className="text-xs font-mono w-8 text-right">{a.value}</span>
                </div>
              ))}
            </div>
          ) : (
            <div className="h-[180px] flex items-center justify-center text-sm text-muted">Send chat messages to see agent activity</div>
          )}
        </div>
      </div>

      {/* Recent Traces */}
      <div className="glass rounded-xl p-5 space-y-4">
        <h3 className="text-sm font-semibold flex items-center gap-2"><Activity size={14} className="text-primary" />Recent Events</h3>
        <div className="max-h-60 overflow-y-auto space-y-1">
          {(traces?.traces || []).slice(0, 30).map((t: { event_id: string; type: string; source: string; timestamp: string }, i: number) => (
            <div key={i} className="flex items-center gap-3 p-2 bg-surface-2 rounded-lg text-xs">
              <span className="text-primary font-mono w-20 shrink-0 truncate">{t.event_id.slice(0, 8)}</span>
              <span className={`px-1.5 py-0.5 rounded text-[10px] font-medium ${
                t.type === "task_response" ? "bg-success/10 text-success" : t.type === "agent_register" ? "bg-accent/10 text-accent" : "bg-primary/10 text-primary"
              }`}>{t.type}</span>
              <span className="text-muted-foreground truncate flex-1">{t.source}</span>
              <span className="text-muted shrink-0">{new Date(t.timestamp).toLocaleTimeString()}</span>
            </div>
          ))}
          {(!traces?.traces || traces.traces.length === 0) && (
            <p className="text-sm text-muted text-center py-4">No events recorded yet — start chatting to generate data</p>
          )}
        </div>
      </div>
    </div>
  );
}


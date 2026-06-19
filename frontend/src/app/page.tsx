"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { getHealth, getMetrics, getCosts } from "@/lib/api";
import { MessageSquare, BookOpen, Wrench, BarChart3, Shield, Activity, DollarSign, Clock, Cpu } from "lucide-react";

export default function HomePage() {
  const { data: health } = useQuery({ queryKey: ["health"], queryFn: getHealth });
  const { data: metrics } = useQuery({ queryKey: ["metrics"], queryFn: getMetrics });
  const { data: costs } = useQuery({ queryKey: ["costs"], queryFn: getCosts });

  const cards = [
    { href: "/chat", icon: MessageSquare, title: "Multi-Agent Chat", desc: "Interact with Tutor, Admin, Orientation, and Synthesis agents", color: "from-indigo-500 to-purple-500" },
    { href: "/knowledge", icon: BookOpen, title: "Knowledge Base", desc: "Upload documents, configure RAG pipeline, test retrieval", color: "from-cyan-500 to-blue-500" },
    { href: "/tools", icon: Wrench, title: "MCP Tools", desc: "Manage tool registry, test executions, configure RBAC", color: "from-emerald-500 to-teal-500" },
    { href: "/observability", icon: BarChart3, title: "Observability", desc: "Latency metrics, cost tracking, execution traces", color: "from-amber-500 to-orange-500" },
    { href: "/privacy", icon: Shield, title: "Privacy & GDPR", desc: "Right to be forgotten, audit logs, data compliance", color: "from-rose-500 to-pink-500" },
  ];

  return (
    <div className="max-w-7xl mx-auto space-y-8 animate-fade-in">
      <div className="text-center space-y-3 py-8">
        <h1 className="text-4xl font-bold gradient-text">ENSAM Agentic OS</h1>
        <p className="text-muted-foreground max-w-2xl mx-auto">
          Integrated agentic platform for university governance, observability, and performance.
          Powered by hybrid LLM routing with local Qwen2.5:3B and Groq API.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="glass rounded-xl p-5 space-y-2">
          <div className="flex items-center gap-2">
            <Activity size={16} className="text-success" />
            <span className="text-sm font-medium">System Status</span>
          </div>
          <p className="text-2xl font-bold">{health?.status === "healthy" ? "Healthy" : "Degraded"}</p>
          <p className="text-xs text-muted">Uptime: {health ? Math.floor(health.uptime_seconds / 60) : 0}m</p>
        </div>
        <div className="glass rounded-xl p-5 space-y-2">
          <div className="flex items-center gap-2">
            <DollarSign size={16} className="text-warning" />
            <span className="text-sm font-medium">Total Cost</span>
          </div>
          <p className="text-2xl font-bold">${costs?.total_cost_usd?.toFixed(4) || "0.0000"}</p>
          <p className="text-xs text-muted">{costs?.token_usage?.total_requests || 0} requests</p>
        </div>
        <div className="glass rounded-xl p-5 space-y-2">
          <div className="flex items-center gap-2">
            <Clock size={16} className="text-accent" />
            <span className="text-sm font-medium">Avg Latency</span>
          </div>
          <p className="text-2xl font-bold">{metrics?.latency?.avg_ms?.toFixed(0) || "0"}ms</p>
          <p className="text-xs text-muted">p95: {metrics?.latency?.p95_ms?.toFixed(0) || "0"}ms</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {cards.map((card) => (
          <Link
            key={card.href}
            href={card.href}
            className="group glass rounded-xl p-6 hover:border-primary/30 transition-all duration-300 hover:glow"
          >
            <div className={`w-10 h-10 rounded-lg bg-gradient-to-br ${card.color} flex items-center justify-center mb-4 group-hover:scale-110 transition-transform`}>
              <card.icon size={20} className="text-white" />
            </div>
            <h3 className="text-lg font-semibold mb-1">{card.title}</h3>
            <p className="text-sm text-muted-foreground">{card.desc}</p>
          </Link>
        ))}
      </div>
    </div>
  );
}

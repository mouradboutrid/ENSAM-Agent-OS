"use client";

import { useQuery } from "@tanstack/react-query";
import { getHealth } from "@/lib/api";
import { useApp } from "@/lib/providers";
import { Activity, Cpu, Globe, Lock, Cloud, Sun, Moon } from "lucide-react";

const MODE_CONFIG = {
  hybrid: { icon: Globe, label: "Hybrid", color: "text-muted-foreground", bg: "bg-card border-border hover:bg-card-hover" },
  local: { icon: Lock, label: "Local Only", color: "text-warning", bg: "bg-warning/10 border-warning/30 hover:bg-warning/20" },
  cloud: { icon: Cloud, label: "Cloud Only", color: "text-accent", bg: "bg-accent/10 border-accent/30 hover:bg-accent/20" },
} as const;

export function Header() {
  const { routingMode, setRoutingMode, theme, setTheme } = useApp();
  const { data: health } = useQuery({ queryKey: ["health"], queryFn: getHealth, refetchInterval: 15000 });

  const cycleMode = () => {
    const modes: Array<"hybrid" | "local" | "cloud"> = ["hybrid", "local", "cloud"];
    const next = modes[(modes.indexOf(routingMode) + 1) % modes.length];
    setRoutingMode(next);
  };

  const mode = MODE_CONFIG[routingMode];
  const ModeIcon = mode.icon;

  return (
    <header className="h-14 border-b border-border bg-card flex items-center justify-between px-6 sticky top-0 z-10">
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2">
          <Activity size={14} className={health?.status === "healthy" ? "text-success" : "text-warning"} />
          <span className="text-xs text-muted-foreground">
            {health?.status === "healthy" ? "All Systems Operational" : "Degraded"}
          </span>
        </div>
        <div className="h-4 w-px bg-border" />
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5">
            <div className={`w-2 h-2 rounded-full ${health?.ollama_healthy ? "bg-success" : "bg-danger"}`} />
            <span className="text-[11px] text-muted-foreground">
              <Cpu size={11} className="inline mr-0.5" />Ollama
            </span>
          </div>
          <div className="flex items-center gap-1.5">
            <div className={`w-2 h-2 rounded-full ${health?.groq_healthy ? "bg-success" : "bg-danger"}`} />
            <span className="text-[11px] text-muted-foreground">
              <Globe size={11} className="inline mr-0.5" />Groq
            </span>
          </div>
        </div>
      </div>

      <div className="flex items-center gap-4">
        {health?.uptime_seconds && (
          <span className="text-[11px] text-muted">
            Uptime: {Math.floor(health.uptime_seconds / 60)}m
          </span>
        )}
        <button
          onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
          className="p-1.5 rounded-lg border border-border bg-card hover:bg-card-hover text-muted-foreground hover:text-foreground transition-all duration-200"
          title={theme === "dark" ? "Switch to Light Mode" : "Switch to Dark Mode"}
        >
          {theme === "dark" ? <Sun size={14} /> : <Moon size={14} />}
        </button>
        <button
          onClick={cycleMode}
          className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium transition-all duration-200 border ${mode.bg}`}
        >
          <ModeIcon size={13} className={mode.color} />
          <span className={mode.color}>{mode.label}</span>
        </button>
      </div>
    </header>
  );
}

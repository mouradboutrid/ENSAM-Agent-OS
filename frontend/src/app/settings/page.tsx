"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getSystemConfig, getHealth, toggleRouting, switchModel } from "@/lib/api";
import { useApp } from "@/lib/providers";
import { Settings, Cpu, Globe, Lock, RefreshCw, Languages, ChevronDown } from "lucide-react";
import { useState } from "react";

export default function SettingsPage() {
  const { routingMode, setRoutingMode, sessionId, setSessionId, language, setLanguage } = useApp();
  const queryClient = useQueryClient();
  const { data: config } = useQuery({ queryKey: ["config"], queryFn: getSystemConfig });
  const { data: health, refetch } = useQuery({ queryKey: ["health"], queryFn: getHealth });
  const [localModel, setLocalModel] = useState(config?.ollama_model || "qwen2.5:3b");

  const routingMutation = useMutation({
    mutationFn: (mode: "hybrid" | "local" | "cloud") => toggleRouting(mode === "local"),
    onSuccess: () => {},
  });

  const modelMutation = useMutation({
    mutationFn: (model: string) => switchModel(model),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ["config"] }); },
  });

  return (
    <div className="max-w-4xl mx-auto space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold">System Settings</h1>
        <p className="text-sm text-muted-foreground">Configure routing, models, and system parameters</p>
      </div>

      <div className="glass rounded-xl p-6 space-y-5">
        <h3 className="text-sm font-semibold flex items-center gap-2"><Settings size={14} className="text-primary" />Runtime Configuration</h3>
        <div className="grid grid-cols-2 gap-6">
          <div className="space-y-3">
            <div className="space-y-1">
              <label className="text-xs text-muted-foreground">Local Model</label>
              <div className="relative">
                <select
                  value={localModel}
                  onChange={(e) => { setLocalModel(e.target.value); modelMutation.mutate(e.target.value); }}
                  className="w-full appearance-none bg-surface-2 border border-border rounded-lg px-3 py-2 pr-8 text-sm font-mono cursor-pointer hover:border-border-bright transition-colors focus:outline-none focus:border-primary"
                >
                  <option value="qwen2.5:3b">qwen2.5:3b (Fast, 2GB)</option>
                  <option value="qwen2.5:7b">qwen2.5:7b (Quality, 4.5GB)</option>
                </select>
                <ChevronDown size={12} className="absolute right-3 top-1/2 -translate-y-1/2 text-muted pointer-events-none" />
              </div>
              {modelMutation.isPending && <p className="text-[10px] text-accent">Switching model...</p>}
            </div>
            <div className="space-y-1">
              <label className="text-xs text-muted-foreground">Cloud Model</label>
              <div className="flex items-center gap-2 bg-surface-2 border border-border rounded-lg px-3 py-2">
                <Globe size={14} className="text-accent" />
                <span className="text-sm font-mono">{config?.groq_model || "llama-3.3-70b-versatile"}</span>
              </div>
            </div>
          </div>
          <div className="space-y-3">
            <div className="space-y-1">
              <label className="text-xs text-muted-foreground">Rate Limit</label>
              <div className="bg-surface-2 border border-border rounded-lg px-3 py-2 text-sm font-mono">
                {config?.rate_limit_rpm || 60} RPM
              </div>
            </div>
            <div className="space-y-1">
              <label className="text-xs text-muted-foreground">Chunk Size / Overlap</label>
              <div className="bg-surface-2 border border-border rounded-lg px-3 py-2 text-sm font-mono">
                {config?.chunk_size || 512} / {config?.chunk_overlap || 50}
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="glass rounded-xl p-6 space-y-4">
        <h3 className="text-sm font-semibold flex items-center gap-2"><Lock size={14} className="text-warning" />Model Routing</h3>
        <div className="grid grid-cols-3 gap-3">
          {(["hybrid", "local", "cloud"] as const).map((mode) => {
            const config = {
              hybrid: { icon: "🔀", title: "Hybrid Mode", desc: "Routes between local and Groq based on complexity and privacy.", color: "border-border" },
              local: { icon: "🔒", title: "Local Only", desc: "All queries processed by local Qwen2.5:3B. No external calls.", color: "border-warning/30" },
              cloud: { icon: "☁️", title: "Cloud Only", desc: "All queries sent to Groq API for maximum quality.", color: "border-accent/30" },
            }[mode];
            return (
              <button key={mode} onClick={() => { setRoutingMode(mode); routingMutation.mutate(mode); }}
                className={`p-4 rounded-lg border transition-all duration-200 text-left ${
                  routingMode === mode ? `bg-primary/10 border-primary/30 glow` : `bg-surface-2 ${config.color} hover:border-border-bright`
                }`}>
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-lg">{config.icon}</span>
                  <span className={`text-sm font-medium ${routingMode === mode ? "text-primary" : ""}`}>{config.title}</span>
                </div>
                <p className="text-xs text-muted-foreground">{config.desc}</p>
              </button>
            );
          })}
        </div>
      </div>

      <div className="glass rounded-xl p-6 space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-semibold flex items-center gap-2"><RefreshCw size={14} className="text-accent" />Service Health</h3>
          <button onClick={() => refetch()} className="text-xs text-muted hover:text-foreground transition-colors">Refresh</button>
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div className={`p-4 rounded-lg border ${health?.ollama_healthy ? "bg-success/5 border-success/20" : "bg-danger/5 border-danger/20"}`}>
            <div className="flex items-center gap-2 mb-1">
              <div className={`w-2.5 h-2.5 rounded-full ${health?.ollama_healthy ? "bg-success" : "bg-danger"}`} />
              <span className="text-sm font-medium">Ollama (Local)</span>
            </div>
            <p className="text-xs text-muted-foreground">
              {health?.ollama_healthy ? "Connected and healthy" : "Not reachable"}
            </p>
          </div>
          <div className={`p-4 rounded-lg border ${health?.groq_healthy ? "bg-success/5 border-success/20" : "bg-danger/5 border-danger/20"}`}>
            <div className="flex items-center gap-2 mb-1">
              <div className={`w-2.5 h-2.5 rounded-full ${health?.groq_healthy ? "bg-success" : "bg-danger"}`} />
              <span className="text-sm font-medium">Groq API (Cloud)</span>
            </div>
            <p className="text-xs text-muted-foreground">
              {health?.groq_healthy ? "Connected and healthy" : "Not reachable"}
            </p>
          </div>
        </div>
      </div>

      <div className="glass rounded-xl p-6 space-y-4">
        <h3 className="text-sm font-semibold flex items-center gap-2"><Languages size={14} className="text-primary" />Response Language</h3>
        <p className="text-xs text-muted-foreground">Choose which language the LLM agents respond in. The system will also detect language changes mid-conversation and suggest switching.</p>
        <div className="grid grid-cols-2 gap-3">
          <button
            onClick={() => setLanguage("en")}
            className={`p-4 rounded-lg border transition-all duration-200 text-left ${
              language === "en" ? "bg-primary/10 border-primary/30 glow" : "bg-surface-2 border-border hover:border-border-bright"
            }`}
          >
            <div className="flex items-center gap-2 mb-1">
              <span className="text-lg">🇬🇧</span>
              <span className={`text-sm font-medium ${language === "en" ? "text-primary" : ""}`}>English</span>
            </div>
            <p className="text-xs text-muted-foreground">All agent responses will be in English</p>
          </button>
          <button
            onClick={() => setLanguage("fr")}
            className={`p-4 rounded-lg border transition-all duration-200 text-left ${
              language === "fr" ? "bg-primary/10 border-primary/30 glow" : "bg-surface-2 border-border hover:border-border-bright"
            }`}
          >
            <div className="flex items-center gap-2 mb-1">
              <span className="text-lg">🇫🇷</span>
              <span className={`text-sm font-medium ${language === "fr" ? "text-primary" : ""}`}>Français</span>
            </div>
            <p className="text-xs text-muted-foreground">Toutes les réponses seront en français</p>
          </button>
        </div>
      </div>

      <div className="glass rounded-xl p-6 space-y-4">
        <h3 className="text-sm font-semibold">Session Management</h3>
        <div className="flex gap-2">
          <input
            type="text" value={sessionId} onChange={(e) => setSessionId(e.target.value)}
            className="flex-1 bg-surface-2 border border-border rounded-lg px-4 py-2 text-sm font-mono focus:outline-none focus:border-primary"
          />
          <button onClick={() => setSessionId(`session_${Date.now()}`)} className="px-4 py-2 bg-card border border-border rounded-lg text-xs hover:border-border-bright transition-colors">
            New Session
          </button>
        </div>
      </div>
    </div>
  );
}

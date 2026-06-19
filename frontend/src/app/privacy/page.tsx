"use client";

import { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { forgetUser, getAuditLog, exportAudit, getMemoryStats } from "@/lib/api";
import { useApp } from "@/lib/providers";
import {
  Shield, Trash2, FileDown, AlertTriangle, CheckCircle, Lock, Eye, Database,
} from "lucide-react";

export default function PrivacyPage() {
  const queryClient = useQueryClient();
  const { routingMode, setRoutingMode } = useApp();
  const [forgetUserId, setForgetUserId] = useState("");
  const [showConfirm, setShowConfirm] = useState(false);

  useEffect(() => {
    if (typeof window !== "undefined") {
      const activeUserId = localStorage.getItem("userId") || "anonymous";
      setForgetUserId(activeUserId);
    }
  }, []);

  const { data: auditData } = useQuery({ queryKey: ["audit"], queryFn: () => getAuditLog(50) });
  const { data: memStats } = useQuery({ queryKey: ["memoryStats"], queryFn: getMemoryStats });

  const forgetMutation = useMutation({
    mutationFn: (userId: string) => forgetUser(userId),
    onSuccess: () => {
      setShowConfirm(false);
      setForgetUserId("");
      queryClient.invalidateQueries({ queryKey: ["memoryStats"] });
    },
  });

  const exportMutation = useMutation({ mutationFn: exportAudit });

  return (
    <div className="max-w-5xl mx-auto space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold">Privacy & Compliance</h1>
        <p className="text-sm text-muted-foreground">GDPR compliance, data erasure, audit logs, and security controls</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="glass rounded-xl p-5 space-y-3">
          <div className="flex items-center gap-2">
            <Lock size={16} className={routingMode === "local" ? "text-warning" : "text-muted"} />
            <span className="text-sm font-semibold">Data Perimeter</span>
          </div>
          <p className="text-xs text-muted-foreground">
            {routingMode === "local" ? "All data stays local. Groq API is disabled." : routingMode === "cloud" ? "Cloud mode. Data processed by Groq API." : "Hybrid mode. Non-sensitive data may use Groq API."}
          </p>
          <button
            onClick={() => setRoutingMode(routingMode === "local" ? "hybrid" : "local")}
            className={`w-full py-2 rounded-lg text-xs font-medium transition-all ${
              routingMode === "local"
                ? "bg-warning/10 text-warning border border-warning/30 hover:bg-warning/20"
                : "bg-card border border-border hover:border-border-bright"
            }`}
          >
            {routingMode === "local" ? "🔒 Local Only Active" : "🌐 Enable Local Only"}
          </button>
        </div>

        <div className="glass rounded-xl p-5 space-y-3">
          <div className="flex items-center gap-2">
            <Database size={16} className="text-primary" />
            <span className="text-sm font-semibold">Memory Status</span>
          </div>
          <div className="space-y-1 text-xs">
            <div className="flex justify-between"><span className="text-muted-foreground">Documents</span><span>{memStats?.semantic?.documents || 0}</span></div>
            <div className="flex justify-between"><span className="text-muted-foreground">User Profiles</span><span>{memStats?.semantic?.user_profiles || 0}</span></div>
            <div className="flex justify-between"><span className="text-muted-foreground">Conversations</span><span>{memStats?.semantic?.conversations || 0}</span></div>
            <div className="flex justify-between"><span className="text-muted-foreground">Graph Nodes</span><span>{memStats?.graph?.total_nodes || 0}</span></div>
          </div>
        </div>

        <div className="glass rounded-xl p-5 space-y-3">
          <div className="flex items-center gap-2">
            <Eye size={16} className="text-accent" />
            <span className="text-sm font-semibold">Audit Stats</span>
          </div>
          <div className="space-y-1 text-xs">
            <div className="flex justify-between"><span className="text-muted-foreground">Total Entries</span><span>{auditData?.stats?.total_entries || 0}</span></div>
            <div className="flex justify-between"><span className="text-muted-foreground">Unique Users</span><span>{auditData?.stats?.unique_users || 0}</span></div>
            <div className="flex justify-between"><span className="text-muted-foreground">Unique Sessions</span><span>{auditData?.stats?.unique_sessions || 0}</span></div>
          </div>
          <button
            onClick={() => exportMutation.mutate()}
            className="w-full flex items-center justify-center gap-1.5 py-2 bg-card border border-border rounded-lg text-xs hover:border-border-bright transition-colors"
          >
            <FileDown size={12} />{exportMutation.isPending ? "Exporting..." : exportMutation.isSuccess ? "Exported ✓" : "Export Audit Log"}
          </button>
        </div>
      </div>

      <div className="glass rounded-xl p-6 space-y-4 border-danger/20">
        <div className="flex items-center gap-2">
          <Trash2 size={18} className="text-danger" />
          <h3 className="text-lg font-semibold">Right to be Forgotten</h3>
        </div>
        <p className="text-sm text-muted-foreground">
          Trigger immediate, atomic erasure of all user data across Redis cache, ChromaDB vectors, and NetworkX graph.
          This action is irreversible.
        </p>
        <div className="flex gap-2">
          <input
            type="text" value={forgetUserId} onChange={(e) => setForgetUserId(e.target.value)}
            placeholder="Enter User ID to erase..."
            className="flex-1 bg-surface-2 border border-border rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:border-danger"
          />
          <button
            onClick={() => {
              const currentUserId = typeof window !== "undefined" ? localStorage.getItem("userId") || "anonymous" : "anonymous";
              setForgetUserId(currentUserId);
              setShowConfirm(true);
            }}
            className="px-5 py-2.5 bg-danger text-white rounded-lg text-sm font-medium hover:bg-danger/90 transition-colors shrink-0"
          >
            Erase My Data
          </button>
          <button
            onClick={() => setShowConfirm(true)}
            disabled={!forgetUserId.trim()}
            className="px-5 py-2.5 bg-danger/10 text-danger border border-danger/30 rounded-lg text-sm font-medium hover:bg-danger/20 transition-colors disabled:opacity-50"
          >
            Erase Custom ID
          </button>
        </div>

        {showConfirm && (
          <div className="p-4 bg-danger/5 border border-danger/20 rounded-lg space-y-3 animate-slide-up">
            <div className="flex items-center gap-2 text-danger">
              <AlertTriangle size={16} />
              <span className="text-sm font-semibold">Confirm Permanent Erasure</span>
            </div>
            <p className="text-xs text-muted-foreground">
              All data for user &ldquo;{forgetUserId}&rdquo; will be permanently deleted from all memory tiers. This cannot be undone.
            </p>
            <div className="flex gap-2">
              <button
                onClick={() => forgetMutation.mutate(forgetUserId)}
                disabled={forgetMutation.isPending}
                className="px-4 py-2 bg-danger text-white rounded-lg text-xs font-medium hover:bg-danger/90 transition-colors"
              >
                {forgetMutation.isPending ? "Erasing..." : "Confirm Erase"}
              </button>
              <button onClick={() => setShowConfirm(false)} className="px-4 py-2 bg-card border border-border rounded-lg text-xs hover:bg-card-hover transition-colors">
                Cancel
              </button>
            </div>
            {forgetMutation.isSuccess && (
              <div className="flex items-center gap-2 text-success text-xs">
                <CheckCircle size={14} />
                Erasure complete: {forgetMutation.data?.ephemeral_deleted} cache entries, {JSON.stringify(forgetMutation.data?.semantic_deleted)} vectors, {forgetMutation.data?.graph_deleted} graph nodes deleted.
              </div>
            )}
          </div>
        )}
      </div>

      <div className="glass rounded-xl p-5 space-y-4">
        <h3 className="text-sm font-semibold flex items-center gap-2"><Shield size={14} className="text-primary" />Recent Audit Log</h3>
        <div className="max-h-60 overflow-y-auto space-y-1">
          {(auditData?.entries || []).slice(0, 30).map((entry: { timestamp: string; request_id?: string; user_id?: string; routing?: { target: string; reason: string } }, i: number) => (
            <div key={i} className="flex items-center gap-3 p-2 bg-surface-2 rounded-lg text-xs">
              <span className="text-muted shrink-0 w-24">{new Date(entry.timestamp).toLocaleTimeString()}</span>
              <span className="text-primary font-mono w-20 truncate">{entry.request_id?.slice(0, 8) || "system"}</span>
              <span className="text-muted-foreground">{entry.user_id || "—"}</span>
              {entry.routing && (
                <span className={`px-1.5 py-0.5 rounded text-[10px] ${entry.routing.target === "ollama" ? "bg-success/10 text-success" : "bg-accent/10 text-accent"}`}>
                  {entry.routing.target} — {entry.routing.reason}
                </span>
              )}
            </div>
          ))}
          {(!auditData?.entries || auditData.entries.length === 0) && (
            <p className="text-sm text-muted text-center py-4">No audit entries yet</p>
          )}
        </div>
      </div>
    </div>
  );
}

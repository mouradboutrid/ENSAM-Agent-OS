"use client";

import { useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { getTools, testTool } from "@/lib/api";
import {
  Wrench, Play, CheckCircle, XCircle, Shield, Tag, Clock, ChevronDown, ChevronRight,
} from "lucide-react";

export default function ToolsPage() {
  const { data: toolsData } = useQuery({ queryKey: ["tools"], queryFn: getTools });
  const tools = toolsData?.tools || [];
  const [selectedTool, setSelectedTool] = useState<string | null>(null);
  const [testParams, setTestParams] = useState<string>("{}");
  const [testResult, setTestResult] = useState<{ success: boolean; result?: unknown; error?: string } | null>(null);

  const testMutation = useMutation({
    mutationFn: ({ toolId, params }: { toolId: string; params: Record<string, unknown> }) => testTool(toolId, params),
    onSuccess: (data) => setTestResult(data),
  });

  const handleTest = (toolId: string) => {
    try {
      const params = JSON.parse(testParams);
      testMutation.mutate({ toolId, params });
    } catch {
      setTestResult({ success: false, error: "Invalid JSON parameters" });
    }
  };

  const securityColors: Record<string, string> = {
    public: "bg-success/10 text-success",
    student: "bg-accent/10 text-accent",
    faculty: "bg-warning/10 text-warning",
    admin: "bg-danger/10 text-danger",
  };

  return (
    <div className="max-w-6xl mx-auto space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold">MCP Tool Registry</h1>
        <p className="text-sm text-muted-foreground">Manage, discover, and test connected university tools and services</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        <div className="glass rounded-xl p-4 text-center">
          <p className="text-2xl font-bold text-primary">{tools.length}</p>
          <p className="text-xs text-muted">Registered Tools</p>
        </div>
        <div className="glass rounded-xl p-4 text-center">
          <p className="text-2xl font-bold text-success">{tools.filter((t: { status: string }) => t.status === "active").length}</p>
          <p className="text-xs text-muted">Active</p>
        </div>
        <div className="glass rounded-xl p-4 text-center">
          <p className="text-2xl font-bold text-warning">{new Set(tools.flatMap((t: { tags: string[] }) => t.tags)).size}</p>
          <p className="text-xs text-muted">Categories</p>
        </div>
      </div>

      <div className="space-y-3">
        {tools.map((tool: { tool_id: string; name: string; description: string; status: string; security_level: string; tags: string[] }) => (
          <div key={tool.tool_id} className="glass rounded-xl overflow-hidden">
            <button
              onClick={() => setSelectedTool(selectedTool === tool.tool_id ? null : tool.tool_id)}
              className="w-full p-4 flex items-center justify-between hover:bg-card-hover transition-colors text-left"
            >
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-surface-2 flex items-center justify-center">
                  <Wrench size={18} className="text-primary" />
                </div>
                <div>
                  <h3 className="text-sm font-semibold">{tool.name}</h3>
                  <p className="text-xs text-muted-foreground">{tool.description}</p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <div className="flex gap-1">
                  {tool.tags.map((tag) => (
                    <span key={tag} className="text-[10px] px-2 py-0.5 bg-surface-2 rounded-full text-muted flex items-center gap-0.5">
                      <Tag size={8} />{tag}
                    </span>
                  ))}
                </div>
                <span className={`text-[10px] px-2 py-0.5 rounded-full font-medium ${securityColors[tool.security_level] || ""}`}>
                  <Shield size={8} className="inline mr-0.5" />{tool.security_level}
                </span>
                <div className={`w-2 h-2 rounded-full ${tool.status === "active" ? "bg-success" : "bg-danger"}`} />
                <ChevronRight size={14} className={`text-muted transition-transform ${selectedTool === tool.tool_id ? "rotate-90" : ""}`} />
              </div>
            </button>

            {selectedTool === tool.tool_id && (
              <div className="px-4 pb-4 space-y-3 animate-slide-up border-t border-border/50 pt-3">
                <div className="space-y-2">
                  <label className="text-xs text-muted-foreground">Test Parameters (JSON)</label>
                  <textarea
                    value={testParams}
                    onChange={(e) => setTestParams(e.target.value)}
                    className="w-full bg-surface-2 border border-border rounded-lg px-3 py-2 text-xs font-mono focus:outline-none focus:border-primary h-20 resize-none"
                    placeholder='{"param": "value"}'
                  />
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => handleTest(tool.tool_id)}
                    disabled={testMutation.isPending}
                    className="flex items-center gap-1.5 px-4 py-2 gradient-primary rounded-lg text-xs font-medium text-white hover:opacity-90 transition-opacity"
                  >
                    <Play size={12} />Execute Test
                  </button>
                </div>
                {testResult && (
                  <div className={`p-3 rounded-lg text-xs font-mono ${
                    testResult.success ? "bg-success/5 border border-success/20" : "bg-danger/5 border border-danger/20"
                  }`}>
                    <div className="flex items-center gap-1.5 mb-1">
                      {testResult.success ? <CheckCircle size={12} className="text-success" /> : <XCircle size={12} className="text-danger" />}
                      <span className={testResult.success ? "text-success" : "text-danger"}>
                        {testResult.success ? "Success" : "Error"}
                      </span>
                    </div>
                    <pre className="text-muted-foreground overflow-x-auto whitespace-pre-wrap">
                      {JSON.stringify(testResult.success ? testResult.result : testResult.error, null, 2)}
                    </pre>
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

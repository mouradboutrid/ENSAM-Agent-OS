"use client";

import { useState, useCallback, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { ingestDocument, searchDocuments, getDocuments, deleteDocument, getGraph } from "@/lib/api";
import { useDropzone } from "react-dropzone";
import {
  Upload, Search, FileText, Database, Loader2, CheckCircle, AlertCircle, Sliders,
  Trash2, Lock, FolderOpen, Network, Eye,
} from "lucide-react";
import { ReactFlow, Controls, Background, MiniMap } from "@xyflow/react";
import "@xyflow/react/dist/style.css";

// 2D Spring Force Layout simulation in Pure JS for beautiful clustering
function runForceLayout(nodes: any[], edges: any[]) {
  const kRepulsion = 40000;
  const kAttraction = 0.08;
  const idealLength = 140;
  
  // Set initial random positions if not set
  const layoutNodes = nodes.map((n, idx) => ({
    ...n,
    x: n.x ?? (200 + Math.cos(idx) * 180 + Math.random() * 20),
    y: n.y ?? (200 + Math.sin(idx) * 180 + Math.random() * 20),
    vx: 0,
    vy: 0,
  }));
  
  const nodeMap = new Map(layoutNodes.map(n => [n.id, n]));
  
  // Run simulation steps
  for (let step = 0; step < 120; step++) {
    // 1. Repel nodes
    for (let i = 0; i < layoutNodes.length; i++) {
      const u = layoutNodes[i];
      for (let j = i + 1; j < layoutNodes.length; j++) {
        const v = layoutNodes[j];
        const dx = u.x - v.x;
        const dy = u.y - v.y;
        const distSq = dx * dx + dy * dy + 0.1;
        const dist = Math.sqrt(distSq);
        if (dist < 450) {
          const force = kRepulsion / distSq;
          const fx = (dx / dist) * force;
          const fy = (dy / dist) * force;
          u.vx += fx;
          u.vy += fy;
          v.vx -= fx;
          v.vy -= fy;
        }
      }
    }
    
    // 2. Attract connected nodes
    for (const e of edges) {
      const u = nodeMap.get(e.source);
      const v = nodeMap.get(e.target);
      if (u && v) {
        const dx = v.x - u.x;
        const dy = v.y - u.y;
        const dist = Math.sqrt(dx * dx + dy * dy) + 0.1;
        const force = kAttraction * (dist - idealLength);
        const fx = (dx / dist) * force;
        const fy = (dy / dist) * force;
        u.vx += fx;
        u.vy += fy;
        v.vx -= fx;
        v.vy -= fy;
      }
    }
    
    // 3. Damping and limits
    for (const n of layoutNodes) {
      n.vx *= 0.82;
      n.vy *= 0.82;
      
      const vMag = Math.sqrt(n.vx * n.vx + n.vy * n.vy);
      if (vMag > 15) {
        n.vx = (n.vx / vMag) * 15;
        n.vy = (n.vy / vMag) * 15;
      }
      
      n.x += n.vx;
      n.y += n.vy;
    }
  }
  
  return layoutNodes.map(n => ({ id: n.id, x: n.x, y: n.y }));
}

export default function KnowledgePage() {
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState<"docs" | "graph">("docs");
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<Array<{ text: string; score: number; doc_id: string; metadata: Record<string, unknown> }>>([]);
  const [chunkSize, setChunkSize] = useState(512);
  const [chunkOverlap, setChunkOverlap] = useState(50);
  const [showConfig, setShowConfig] = useState(false);
  const [filter, setFilter] = useState<"all" | "system" | "user">("all");
  const [positions, setPositions] = useState<Record<string, { x: number; y: number }>>({});
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const { data: docsData } = useQuery({ queryKey: ["documents"], queryFn: getDocuments });
  const { data: graphData } = useQuery({ queryKey: ["graph"], queryFn: getGraph, enabled: activeTab === "graph", refetchInterval: 10000 });

  const ingestMutation = useMutation({
    mutationFn: (file: File) => ingestDocument(file, chunkSize, chunkOverlap),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["documents"] });
      queryClient.invalidateQueries({ queryKey: ["graph"] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (docId: string) => deleteDocument(docId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["documents"] });
      queryClient.invalidateQueries({ queryKey: ["graph"] });
    },
  });

  const searchMutation = useMutation({
    mutationFn: (q: string) => searchDocuments(q),
    onSuccess: (data) => setSearchResults(data.results || []),
  });

  const onDrop = useCallback((acceptedFiles: File[]) => {
    acceptedFiles.forEach((file) => ingestMutation.mutate(file));
  }, [chunkSize, chunkOverlap]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "application/pdf": [".pdf"],
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"],
      "text/markdown": [".md"],
      "text/plain": [".txt"],
      "text/csv": [".csv"],
    },
  });

  // Calculate layout when graph changes
  useEffect(() => {
    if (graphData?.nodes && graphData?.edges) {
      const posMap = runForceLayout(graphData.nodes, graphData.edges);
      const newPos: Record<string, { x: number; y: number }> = {};
      posMap.forEach((p: any) => {
        newPos[p.id] = { x: p.x, y: p.y };
      });
      setPositions(newPos);
    }
  }, [graphData]);

  const allDocs = docsData?.documents || [];
  const systemDocs = allDocs.filter((d: { metadata: Record<string, unknown> }) => d.metadata?.system_document === "true");
  const userDocs = allDocs.filter((d: { metadata: Record<string, unknown> }) => d.metadata?.system_document !== "true");
  const filteredDocs = filter === "system" ? systemDocs : filter === "user" ? userDocs : allDocs;

  // React Flow Node / Edge Mapper
  const flowNodes = (graphData?.nodes || []).map((node: any) => {
    const pos = positions[node.id] || { x: 300, y: 300 };
    let borderClr = "var(--color-border)";
    let typeLabel = node.entity_type;

    if (node.entity_type === "category") {
      borderClr = "var(--color-success)";
    } else if (node.entity_type === "document") {
      borderClr = "var(--color-primary)";
    } else if (node.entity_type === "agent") {
      borderClr = "var(--color-accent)";
    } else if (node.entity_type === "session") {
      borderClr = "var(--color-warning)";
    } else if (node.entity_type === "query") {
      borderClr = "var(--color-danger)";
    }

    return {
      id: node.id,
      position: pos,
      data: {
        label: (
          <div className="flex flex-col items-center">
            <span className="text-[8px] uppercase tracking-wider font-semibold opacity-60">{typeLabel}</span>
            <span className="text-[11px] font-bold font-mono truncate max-w-[130px] mt-0.5">{node.id.replace(".pdf", "")}</span>
          </div>
        ),
      },
      style: {
        background: "var(--color-card)",
        color: "var(--color-foreground)",
        border: `2px solid ${borderClr}`,
        borderRadius: "8px",
        padding: "6px 12px",
        width: 160,
        boxShadow: "0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)",
      },
    };
  });

  const flowEdges = (graphData?.edges || []).map((edge: any) => ({
    id: `e-${edge.source}-${edge.target}`,
    source: edge.source,
    target: edge.target,
    label: edge.relation_type,
    animated: edge.relation_type === "routed_to" || edge.relation_type === "contains_query",
    style: { stroke: "var(--color-border-bright)", strokeWidth: 1.5 },
    labelStyle: { fill: "var(--color-muted)", fontSize: 8, fontWeight: 500 },
  }));

  return (
    <div className="max-w-6xl mx-auto space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Knowledge Base</h1>
          <p className="text-sm text-muted-foreground">RAG pipeline management — ingest, chunk, embed, and search documents</p>
        </div>
        <div className="flex items-center gap-2">
          {/* Tab switches */}
          <div className="flex bg-surface-2 rounded-lg p-1 border border-border text-xs">
            <button
              onClick={() => setActiveTab("docs")}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md transition-colors ${
                activeTab === "docs" ? "bg-primary text-white" : "text-muted-foreground hover:text-foreground"
              }`}
            >
              <FileText size={13} />Documents
            </button>
            <button
              onClick={() => setActiveTab("graph")}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md transition-colors ${
                activeTab === "graph" ? "bg-primary text-white" : "text-muted-foreground hover:text-foreground"
              }`}
            >
              <Network size={13} />Knowledge Graph
            </button>
          </div>
          <button
            onClick={() => setShowConfig(!showConfig)}
            className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition-all ${
              showConfig ? "bg-primary/10 text-primary border border-primary/20" : "glass"
            }`}
          >
            <Sliders size={14} />Chunking Config
          </button>
        </div>
      </div>

      {showConfig && (
        <div className="glass rounded-xl p-5 space-y-4 animate-slide-up">
          <h3 className="text-sm font-semibold flex items-center gap-2"><Sliders size={14} className="text-primary" />Chunking Configuration</h3>
          <div className="grid grid-cols-2 gap-6">
            <div className="space-y-2">
              <label className="text-xs text-muted-foreground flex justify-between">
                <span>Chunk Size</span><span className="text-foreground font-mono">{chunkSize}</span>
              </label>
              <input type="range" min={100} max={4096} step={50} value={chunkSize} onChange={(e) => setChunkSize(Number(e.target.value))}
                className="w-full accent-primary" />
              <div className="flex justify-between text-[10px] text-muted"><span>100</span><span>4096</span></div>
            </div>
            <div className="space-y-2">
              <label className="text-xs text-muted-foreground flex justify-between">
                <span>Chunk Overlap</span><span className="text-foreground font-mono">{chunkOverlap}</span>
              </label>
              <input type="range" min={0} max={500} step={10} value={chunkOverlap} onChange={(e) => setChunkOverlap(Number(e.target.value))}
                className="w-full accent-primary" />
              <div className="flex justify-between text-[10px] text-muted"><span>0</span><span>500</span></div>
            </div>
          </div>
        </div>
      )}

      {activeTab === "docs" ? (
        <>
          <div
            {...getRootProps()}
            className={`glass rounded-xl p-10 text-center cursor-pointer transition-all duration-200 ${
              isDragActive ? "border-primary bg-primary/5 glow" : "hover:border-border-bright"
            }`}
          >
            <input {...getInputProps()} />
            <Upload size={40} className={`mx-auto mb-3 ${isDragActive ? "text-primary" : "text-muted"}`} />
            {ingestMutation.isPending ? (
              <div className="flex items-center justify-center gap-2">
                <Loader2 size={16} className="animate-spin text-primary" />
                <span className="text-sm text-primary">Processing document...</span>
              </div>
            ) : ingestMutation.isSuccess ? (
              <div className="flex items-center justify-center gap-2">
                <CheckCircle size={16} className="text-success" />
                <span className="text-sm text-success">
                  Ingested {ingestMutation.data?.total_chunks} chunks successfully
                </span>
              </div>
            ) : ingestMutation.isError ? (
              <div className="flex items-center justify-center gap-2">
                <AlertCircle size={16} className="text-danger" />
                <span className="text-sm text-danger">Error ingesting document</span>
              </div>
            ) : (
              <>
                <p className="text-sm font-medium mb-1">
                  {isDragActive ? "Drop files here" : "Drag & drop files to ingest"}
                </p>
                <p className="text-xs text-muted">Supports PDF, DOCX, MD, TXT, CSV</p>
              </>
            )}
          </div>

          <div className="glass rounded-xl p-5 space-y-4">
            <h3 className="text-sm font-semibold flex items-center gap-2"><Search size={14} className="text-accent" />Semantic Search Tester</h3>
            <div className="flex gap-2">
              <input
                type="text" value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && searchQuery.trim() && searchMutation.mutate(searchQuery)}
                placeholder="Test a search query..." className="flex-1 bg-surface-2 border border-border rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:border-primary"
              />
              <button
                onClick={() => searchQuery.trim() && searchMutation.mutate(searchQuery)}
                disabled={searchMutation.isPending}
                className="px-5 py-2.5 gradient-primary rounded-lg text-sm font-medium text-white hover:opacity-90 transition-opacity disabled:opacity-50"
              >
                {searchMutation.isPending ? <Loader2 size={14} className="animate-spin" /> : "Search"}
              </button>
            </div>
            {searchResults.length > 0 && (
              <div className="space-y-2 max-h-80 overflow-y-auto">
                {searchResults.map((r, i) => (
                  <div key={i} className="p-3 bg-surface-2 rounded-lg border border-border/50">
                    <div className="flex justify-between mb-1">
                      <span className="text-xs font-mono text-primary">{r.doc_id?.slice(0, 12)}</span>
                      <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${
                        r.score > 0.8 ? "bg-success/10 text-success" : r.score > 0.5 ? "bg-warning/10 text-warning" : "bg-muted/10 text-muted"
                      }`}>{(r.score * 100).toFixed(0)}% match</span>
                    </div>
                    <p className="text-xs text-muted-foreground line-clamp-3">{r.text}</p>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="glass rounded-xl p-5 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-semibold flex items-center gap-2"><Database size={14} className="text-primary" />Indexed Documents</h3>
              <div className="flex items-center gap-2">
                <span className="text-[10px] text-muted">{systemDocs.length} system · {userDocs.length} user</span>
                <div className="flex bg-surface-2 rounded-lg overflow-hidden text-[10px] border border-border">
                  {(["all", "system", "user"] as const).map((f) => (
                    <button key={f} onClick={() => setFilter(f)}
                      className={`px-2.5 py-1 transition-colors capitalize ${filter === f ? "bg-primary text-white" : "text-muted-foreground hover:text-foreground"}`}
                    >{f}</button>
                  ))}
                </div>
              </div>
            </div>

            {filteredDocs.length > 0 ? (
              <div className="space-y-2 max-h-80 overflow-y-auto">
                {filteredDocs.map((doc: { id: string; text_preview: string; metadata: Record<string, unknown> }, i: number) => {
                  const isSystem = doc.metadata?.system_document === "true";
                  return (
                    <div key={i} className="flex items-start gap-3 p-3 bg-surface-2 rounded-lg border border-border/50 group">
                      <div className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 ${isSystem ? "bg-warning/10" : "bg-primary/10"}`}>
                        {isSystem ? <Lock size={14} className="text-warning" /> : <FileText size={14} className="text-primary" />}
                      </div>
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center gap-2">
                          <p className="text-xs font-mono text-primary truncate">{doc.metadata?.source ? String(doc.metadata.source) : doc.id.slice(0, 16)}</p>
                          {isSystem ? (
                            <span className="text-[9px] px-1.5 py-0.5 rounded bg-warning/10 text-warning font-medium shrink-0">SYSTEM</span>
                          ) : (
                            <span className="text-[9px] px-1.5 py-0.5 rounded bg-primary/10 text-primary font-medium shrink-0">USER</span>
                          )}
                          {doc.metadata?.category ? (
                            <span className="text-[9px] px-1.5 py-0.5 rounded bg-surface-3 text-muted shrink-0">
                              <FolderOpen size={8} className="inline mr-0.5" />{String(doc.metadata.category)}
                            </span>
                          ) : null}
                        </div>
                        <p className="text-xs text-muted-foreground line-clamp-2 mt-0.5">{doc.text_preview}</p>
                      </div>
                      {!isSystem && (
                        <button
                          onClick={() => deleteMutation.mutate(doc.id)}
                          disabled={deleteMutation.isPending}
                          className="opacity-0 group-hover:opacity-100 p-1.5 rounded-lg hover:bg-danger/10 text-muted hover:text-danger transition-all shrink-0"
                          title="Delete document"
                        >
                          <Trash2 size={14} />
                        </button>
                      )}
                    </div>
                  );
                })}
              </div>
            ) : (
              <p className="text-sm text-muted text-center py-6">
                {filter === "user" ? "No user-uploaded documents yet." : filter === "system" ? "System documents loading..." : "No documents indexed yet. Upload files above."}
              </p>
            )}
          </div>
        </>
      ) : (
        /* Tab 2: Interactive Knowledge Graph Visualizer */
        <div className="glass rounded-xl p-5 space-y-4 animate-fade-in">
          <div className="flex justify-between items-center">
            <div>
              <h3 className="text-sm font-semibold flex items-center gap-2"><Network size={14} className="text-primary" />Knowledge Graph Explorer</h3>
              <p className="text-xs text-muted-foreground mt-0.5">Visualize agent routing decisions, document category mapping, and ephemeral session query flows.</p>
            </div>
            {/* Graph Legend */}
            <div className="flex gap-3 text-[10px] border border-border p-2 rounded-lg bg-surface-2">
              <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-sm bg-card border border-primary" />Document</span>
              <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-sm bg-card border border-success" />Category</span>
              <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-sm bg-card border border-accent" />Agent</span>
              <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-sm bg-card border border-warning" />Session</span>
              <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-sm bg-card border border-danger" />Query</span>
            </div>
          </div>

          <div className="h-[550px] w-full relative rounded-xl border border-border overflow-hidden bg-background">
            {mounted && flowNodes.length > 0 ? (
              <ReactFlow
                nodes={flowNodes}
                edges={flowEdges}
                fitView
                fitViewOptions={{ padding: 0.2 }}
                minZoom={0.2}
                maxZoom={2.0}
              >
                <Background color="var(--color-border-bright)" gap={16} size={1} />
                <Controls showInteractive={false} className="bg-card border border-border text-foreground fill-foreground" />
                <MiniMap 
                  style={{ background: "var(--color-card)", border: "1px solid var(--color-border)" }}
                  nodeColor={(node) => {
                    if (node.style?.border && typeof node.style.border === "string") {
                      const parts = node.style.border.split(" ");
                      return parts[parts.length - 1];
                    }
                    return "var(--color-border-bright)";
                  }}
                  maskColor="rgba(0, 0, 0, 0.1)"
                />
              </ReactFlow>
            ) : (
              <div className="flex flex-col items-center justify-center h-full space-y-2 text-sm text-muted">
                <Loader2 size={24} className="animate-spin text-primary" />
                <p>Loading decision mapping and categories...</p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

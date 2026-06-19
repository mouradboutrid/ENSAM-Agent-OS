"use client";

import { useState, useRef, useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { getAgents } from "@/lib/api";
import { useApp } from "@/lib/providers";
import ReactMarkdown from "react-markdown";
import {
  Send, Bot, User, ChevronDown, Zap, Cpu, Globe, Clock, Loader2,
  Info, ChevronRight, Languages, X, Sparkles, Plus, MessageSquare, Trash2,
} from "lucide-react";

type Message = {
  role: string;
  content: string;
  agent_id?: string;
  agent_name?: string;
  model?: string;
  provider?: string;
  sources?: Array<{ text: string; score: number; doc_id: string }>;
  trace?: Array<Record<string, unknown>>;
  latency_ms?: number;
  cost_usd?: number;
};

type ChatSession = {
  id: string;
  title: string;
  messages: Message[];
  createdAt: number;
};

function detectLanguage(text: string): "en" | "fr" | null {
  const frWords = ["le", "la", "les", "de", "du", "des", "un", "une", "est", "et", "en", "que", "qui", "dans", "pour", "avec", "sur", "pas", "ce", "je", "tu", "il", "nous", "vous", "sont", "ont", "fait", "bien", "aussi", "mais", "ou", "bonjour", "merci", "comment", "quoi", "quel", "quelle"];
  const enWords = ["the", "is", "are", "was", "were", "have", "has", "do", "does", "will", "would", "can", "could", "should", "what", "how", "why", "where", "when", "which", "this", "that", "with", "from", "they", "been", "about", "hello", "thanks", "please"];
  const words = text.toLowerCase().split(/\s+/);
  let frScore = 0, enScore = 0;
  for (const w of words) { if (frWords.includes(w)) frScore++; if (enWords.includes(w)) enScore++; }
  if (frScore > enScore && frScore >= 2) return "fr";
  if (enScore > frScore && enScore >= 2) return "en";
  return null;
}

export default function ChatPage() {
  const { 
    routingMode, 
    sessionId, 
    setSessionId, 
    language, 
    setLanguage,
    sessions,
    setSessions,
    activeSessionId,
    setActiveSessionId,
    isSending,
    sendGlobalMessage,
    createNewSession,
    deleteSession
  } = useApp();

  const [mounted, setMounted] = useState(false);
  const [input, setInput] = useState("");
  const [selectedAgent, setSelectedAgent] = useState("general");
  const [webSearch, setWebSearch] = useState(false);
  const [showTrace, setShowTrace] = useState<number | null>(null);
  const [showSources, setShowSources] = useState<number | null>(null);
  const [langSuggestion, setLangSuggestion] = useState<"en" | "fr" | null>(null);
  const [showHistory, setShowHistory] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const currentSession = sessions.find(s => s.id === activeSessionId);
  const messages = currentSession?.messages || [];

  const { data: agentsData } = useQuery({ queryKey: ["agents"], queryFn: getAgents });
  const agents = agentsData?.agents || [];

  const setMessages = (updater: (prev: Message[]) => Message[]) => {
    setSessions(prev => prev.map(s =>
      s.id === activeSessionId ? { ...s, messages: updater(s.messages) } : s
    ));
  };

  const switchSession = (id: string) => {
    setActiveSessionId(id);
    setSessionId(id);
  };

  const handleSend = () => {
    if (!input.trim() || isSending) return;

    if (!currentSession) { 
      const newId = createNewSession();
      const userMsg: Message = { role: "user", content: input };
      setSessions(prev => prev.map(s => s.id === newId ? { ...s, messages: [userMsg] } : s));
      const forceLocal = routingMode === "local";
      const forceCloud = routingMode === "cloud";
      sendGlobalMessage({
        message: input, session_id: newId, agent_id: selectedAgent,
        force_local: forceLocal, force_cloud: forceCloud, language,
        web_search: webSearch,
      });
      setInput("");
      return;
    }

    const detected = detectLanguage(input);
    if (detected && detected !== language) setLangSuggestion(detected);

    // Update session title from first message
    if (messages.length === 0) {
      const title = input.slice(0, 40) + (input.length > 40 ? "..." : "");
      setSessions(prev => prev.map(s => s.id === activeSessionId ? { ...s, title } : s));
    }

    const userMsg: Message = { role: "user", content: input };
    setMessages((prev) => [...prev, userMsg]);

    const forceLocal = routingMode === "local";
    const forceCloud = routingMode === "cloud";

    sendGlobalMessage({
      message: input, session_id: activeSessionId, agent_id: selectedAgent,
      force_local: forceLocal, force_cloud: forceCloud, language,
      web_search: webSearch,
    });
    setInput("");
  };

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  useEffect(() => {
    setMounted(true);
    if (sessions.length === 0) createNewSession();
  }, []);

  const currentAgent = agents.find((a: { id: string }) => a.id === selectedAgent);

  return (
    <div className="h-[calc(100vh-8rem)] flex gap-4 max-w-7xl mx-auto animate-fade-in">
      {/* Language suggestion popup */}
      {langSuggestion && (
        <div className="fixed top-20 right-6 z-50 glass rounded-xl p-4 shadow-lg border border-primary/30 glow animate-slide-up max-w-xs">
          <div className="flex items-start gap-3">
            <Languages size={20} className="text-primary shrink-0 mt-0.5" />
            <div className="space-y-2 flex-1">
              <p className="text-sm font-medium">
                {langSuggestion === "fr" ? "On dirait que vous parlez français !" : "It looks like you're writing in English!"}
              </p>
              <p className="text-xs text-muted-foreground">
                {langSuggestion === "fr" ? "Voulez-vous que l'assistant réponde en français ?" : "Would you like the assistant to respond in English?"}
              </p>
              <div className="flex gap-2">
                <button onClick={() => { setLanguage(langSuggestion); setLangSuggestion(null); }}
                  className="px-3 py-1.5 gradient-primary rounded-lg text-xs font-medium text-white hover:opacity-90 transition-opacity">
                  {langSuggestion === "fr" ? "Oui" : "Yes"}
                </button>
                <button onClick={() => setLangSuggestion(null)}
                  className="px-3 py-1.5 bg-card border border-border rounded-lg text-xs hover:bg-card-hover transition-colors">
                  {langSuggestion === "fr" ? "Non" : "No"}
                </button>
              </div>
            </div>
            <button onClick={() => setLangSuggestion(null)} className="text-muted hover:text-foreground"><X size={14} /></button>
          </div>
        </div>
      )}

      {/* Chat history sidebar */}
      {showHistory && (
        <div className="w-64 shrink-0 flex flex-col glass rounded-xl overflow-hidden animate-fade-in">
          <div className="p-3 border-b border-border flex items-center justify-between">
            <span className="text-xs font-semibold">Chat History</span>
            <button onClick={createNewSession} className="p-1.5 rounded-lg hover:bg-card-hover transition-colors" title="New chat">
              <Plus size={14} className="text-primary" />
            </button>
          </div>
          <div className="flex-1 overflow-y-auto p-2 space-y-1">
            {sessions.map(s => (
              <div key={s.id} onClick={() => switchSession(s.id)} role="button" tabIndex={0}
                onKeyDown={(e) => e.key === "Enter" && switchSession(s.id)}
                className={`w-full text-left p-2.5 rounded-lg transition-all duration-150 group flex items-center gap-2 cursor-pointer ${
                  s.id === activeSessionId ? "bg-primary/10 border border-primary/20" : "hover:bg-card-hover"
                }`}>
                <MessageSquare size={13} className={s.id === activeSessionId ? "text-primary shrink-0" : "text-muted shrink-0"} />
                <div className="min-w-0 flex-1">
                  <p className="text-xs font-medium truncate">{s.title}</p>
                  <p className="text-[10px] text-muted">{s.messages.length} msgs · {mounted ? new Date(s.createdAt).toLocaleDateString() : ""}</p>
                </div>
                <button onClick={(e) => { e.stopPropagation(); deleteSession(s.id); }}
                  className="opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-danger/10 hover:text-danger transition-all shrink-0">
                  <Trash2 size={11} />
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Main chat area */}
      <div className="flex-1 flex flex-col min-w-0">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-3">
            <button onClick={() => setShowHistory(!showHistory)}
              className={`p-2 rounded-lg transition-colors ${showHistory ? "bg-primary/10 text-primary" : "text-muted hover:text-foreground"}`}>
              <MessageSquare size={16} />
            </button>
            <div>
              <h1 className="text-lg font-bold">
                {currentSession?.title || "New Chat"}
              </h1>
              <p className="text-[11px] text-muted-foreground">{language === "fr" ? "Français" : "English"} · {routingMode}</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <div className="flex bg-card border border-border rounded-lg overflow-hidden text-xs">
              <button onClick={() => setLanguage("en")}
                className={`px-2.5 py-1 transition-colors ${language === "en" ? "bg-primary text-white" : "text-muted-foreground"}`}>EN</button>
              <button onClick={() => setLanguage("fr")}
                className={`px-2.5 py-1 transition-colors ${language === "fr" ? "bg-primary text-white" : "text-muted-foreground"}`}>FR</button>
            </div>
            <button onClick={() => setWebSearch(!webSearch)}
              type="button"
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium border transition-all ${
                webSearch
                  ? "bg-cyan-500/10 text-cyan-500 border-cyan-500/30"
                  : "bg-card border-border text-muted-foreground hover:bg-card-hover"
              }`}
              title="Toggle Web Search">
              <Globe size={13} className={webSearch ? "animate-pulse text-cyan-500" : "text-muted-foreground"} />
              <span>Search</span>
            </button>
            <div className="relative">
              <select value={selectedAgent} onChange={(e) => setSelectedAgent(e.target.value)}
                className="appearance-none bg-card border border-border rounded-lg px-3 py-1.5 pr-7 text-xs font-medium cursor-pointer hover:border-border-bright transition-colors focus:outline-none focus:border-primary">
                {agents.filter((a: { id: string }) => a.id !== "research").map((a: { id: string; name: string }) => (
                  <option key={a.id} value={a.id}>{a.name}</option>
                ))}
              </select>
              <ChevronDown size={12} className="absolute right-2 top-1/2 -translate-y-1/2 text-muted pointer-events-none" />
            </div>
          </div>
        </div>

        {currentAgent && (
          <div className="glass rounded-lg p-3 mb-3 flex flex-col gap-1.5 text-xs text-muted-foreground w-full">
            <div className="flex items-center gap-1.5 font-semibold text-foreground">
              {selectedAgent === "general" ? <Sparkles size={12} className="text-accent" /> : <Bot size={12} className="text-primary" />}
              <span>{currentAgent.name}</span>
            </div>
            <p className="text-[11px] text-muted-foreground leading-relaxed">{currentAgent.description}</p>
          </div>
        )}

        <div className="flex-1 overflow-y-auto space-y-4 mb-3 pr-2">
          {messages.length === 0 && (
            <div className="flex items-center justify-center h-full text-muted-foreground">
              <div className="text-center space-y-3">
                <Bot size={48} className="mx-auto text-border" />
                <p className="text-lg font-medium">{language === "fr" ? "Démarrer une conversation" : "Start a conversation"}</p>
                <p className="text-sm">{language === "fr" ? "Utilisez le mode Général pour un routage automatique." : "Use General mode for automatic intent routing."}</p>
              </div>
            </div>
          )}

          {messages.map((msg, i) => (
            <div key={i} className={`flex gap-3 animate-slide-up ${msg.role === "user" ? "justify-end" : ""}`}>
              {msg.role === "assistant" && (
                <div className="w-8 h-8 rounded-lg gradient-primary flex items-center justify-center shrink-0 mt-1">
                  <Bot size={16} className="text-white" />
                </div>
              )}
              <div className={`max-w-[75%] space-y-2 ${msg.role === "user" ? "order-first" : ""}`}>
                <div className={`rounded-xl px-4 py-3 ${msg.role === "user" ? "bg-primary text-white ml-auto" : "glass"}`}>
                  <div className="prose prose-sm prose-invert max-w-none text-sm">
                    <ReactMarkdown>{msg.content}</ReactMarkdown>
                  </div>
                </div>
                {msg.role === "assistant" && (
                  <div className="flex items-center gap-3 text-[11px] text-muted flex-wrap">
                    {msg.agent_name && <span className="flex items-center gap-1 text-accent font-medium"><Bot size={11} />{msg.agent_name}</span>}
                    {msg.provider && <span className="flex items-center gap-1">{msg.provider === "ollama" ? <Cpu size={11} /> : <Globe size={11} />}{msg.model}</span>}
                    {msg.latency_ms && <span className="flex items-center gap-1"><Clock size={11} />{msg.latency_ms.toFixed(0)}ms</span>}
                    {msg.cost_usd !== undefined && msg.cost_usd > 0 && <span className="flex items-center gap-1"><Zap size={11} />${msg.cost_usd.toFixed(5)}</span>}
                    {msg.sources && msg.sources.length > 0 && (
                      <button onClick={() => setShowSources(showSources === i ? null : i)} className="flex items-center gap-1 text-accent hover:text-accent/80 transition-colors">
                        <Info size={11} />{msg.sources.length} sources<ChevronRight size={11} className={`transition-transform ${showSources === i ? "rotate-90" : ""}`} />
                      </button>
                    )}
                    {msg.trace && msg.trace.length > 0 && (
                      <button onClick={() => setShowTrace(showTrace === i ? null : i)} className="flex items-center gap-1 text-primary hover:text-primary-hover transition-colors">
                        <Info size={11} />Trace<ChevronRight size={11} className={`transition-transform ${showTrace === i ? "rotate-90" : ""}`} />
                      </button>
                    )}
                  </div>
                )}
                {showTrace === i && msg.trace && (
                  <div className="glass rounded-lg p-3 text-xs space-y-1 animate-fade-in max-h-48 overflow-y-auto">
                    {msg.trace.map((t, j) => (
                      <div key={j} className="flex items-start gap-2 py-1 border-b border-border/50 last:border-0">
                        <span className="text-primary font-mono shrink-0">{String(t.step)}</span>
                        <span className="text-muted-foreground break-all">{JSON.stringify(Object.fromEntries(Object.entries(t).filter(([k]) => !["step","timestamp","agent"].includes(k))))}</span>
                      </div>
                    ))}
                  </div>
                )}
                {showSources === i && msg.sources && msg.sources.length > 0 && msg.role === "assistant" && (
                  <div className="glass rounded-lg p-3 space-y-2 animate-fade-in">
                    <p className="text-[11px] font-medium text-muted-foreground">Sources</p>
                    {msg.sources.map((s, j) => (
                      <div key={j} className="text-xs p-2 bg-surface-2 rounded border border-border/50">
                        <div className="flex justify-between mb-1">
                          <span className="text-primary font-mono">{s.doc_id?.slice(0, 8)}</span>
                          <span className="text-muted">{(s.score * 100).toFixed(0)}%</span>
                        </div>
                        <p className="text-muted-foreground line-clamp-2">{s.text}</p>
                      </div>
                    ))}
                  </div>
                )}
              </div>
              {msg.role === "user" && (
                <div className="w-8 h-8 rounded-lg bg-card border border-border flex items-center justify-center shrink-0 mt-1">
                  <User size={16} className="text-muted-foreground" />
                </div>
              )}
            </div>
          ))}
          {isSending && (
            <div className="flex gap-3 animate-slide-up">
              <div className="w-8 h-8 rounded-lg gradient-primary flex items-center justify-center shrink-0"><Bot size={16} className="text-white" /></div>
              <div className="glass rounded-xl px-4 py-3"><Loader2 size={16} className="animate-spin text-primary" /></div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        <div className="glass rounded-xl p-2 flex items-center gap-2">
          <input type="text" value={input} onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSend()}
            placeholder={language === "fr" ? "Posez une question..." : "Ask a question..."}
            className="flex-1 bg-transparent px-4 py-3 text-sm focus:outline-none placeholder:text-muted" />
          <button onClick={handleSend} disabled={!input.trim() || isSending}
            className="w-10 h-10 rounded-lg gradient-primary flex items-center justify-center text-white disabled:opacity-50 hover:opacity-90 transition-opacity">
            <Send size={16} />
          </button>
        </div>
      </div>
    </div>
  );
}

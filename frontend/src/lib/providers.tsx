"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState, createContext, useContext, useEffect, type ReactNode } from "react";
import { sendMessage } from "./api";

const queryClient = new QueryClient({
  defaultOptions: { queries: { refetchInterval: 10000, retry: 2 } },
});

export type Message = {
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

export type ChatSession = {
  id: string;
  title: string;
  messages: Message[];
  createdAt: number;
};

type AppContextType = {
  sidebarOpen: boolean;
  setSidebarOpen: (v: boolean) => void;
  routingMode: "hybrid" | "local" | "cloud";
  setRoutingMode: (v: "hybrid" | "local" | "cloud") => void;
  sessionId: string;
  setSessionId: (v: string) => void;
  language: "en" | "fr";
  setLanguage: (v: "en" | "fr") => void;
  theme: "dark" | "light";
  setTheme: (v: "dark" | "light") => void;
  
  // Global Chat States
  sessions: ChatSession[];
  setSessions: React.Dispatch<React.SetStateAction<ChatSession[]>>;
  activeSessionId: string;
  setActiveSessionId: (id: string) => void;
  isSending: boolean;
  sendGlobalMessage: (data: {
    message: string;
    session_id: string;
    agent_id: string;
    force_local: boolean;
    force_cloud: boolean;
    language: string;
    web_search: boolean;
  }) => Promise<void>;
  createNewSession: () => string;
  deleteSession: (id: string) => void;
};

const AppContext = createContext<AppContextType>({
  sidebarOpen: true,
  setSidebarOpen: () => {},
  routingMode: "hybrid",
  setRoutingMode: () => {},
  sessionId: "default",
  setSessionId: () => {},
  language: "en",
  setLanguage: () => {},
  theme: "dark",
  setTheme: () => {},
  sessions: [],
  setSessions: () => {},
  activeSessionId: "default",
  setActiveSessionId: () => {},
  isSending: false,
  sendGlobalMessage: async () => {},
  createNewSession: () => "",
  deleteSession: () => {},
});

export const useApp = () => useContext(AppContext);

export function Providers({ children }: { children: ReactNode }) {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [routingMode, setRoutingMode] = useState<"hybrid" | "local" | "cloud">("hybrid");
  const [sessionId, setSessionId] = useState("default");
  const [language, setLanguage] = useState<"en" | "fr">("en");
  const [theme, setThemeState] = useState<"dark" | "light">("dark");

  // Global Chat states
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string>("default");
  const [isSending, setIsSending] = useState(false);
  const [hasLoaded, setHasLoaded] = useState(false);

  // Load theme & chat sessions from localStorage on client-side mount
  useEffect(() => {
    const savedTheme = localStorage.getItem("theme") as "dark" | "light";
    if (savedTheme) {
      setThemeState(savedTheme);
    } else {
      const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
      setThemeState(prefersDark ? "dark" : "light");
    }

    const savedSessions = localStorage.getItem("chat_sessions");
    if (savedSessions) {
      try {
        const parsed = JSON.parse(savedSessions) as ChatSession[];
        setSessions(parsed);
        if (parsed.length > 0) {
          setActiveSessionId(parsed[0].id);
          setSessionId(parsed[0].id);
        }
      } catch (e) {
        console.error("Failed to parse chat sessions", e);
      }
    }
    setHasLoaded(true);
  }, []);

  // Sync sessions to localStorage
  useEffect(() => {
    if (hasLoaded) {
      localStorage.setItem("chat_sessions", JSON.stringify(sessions));
    }
  }, [sessions, hasLoaded]);

  // Sync theme to DOM html class list
  useEffect(() => {
    const root = window.document.documentElement;
    if (theme === "dark") {
      root.classList.add("dark");
    } else {
      root.classList.remove("dark");
    }
  }, [theme]);

  const setTheme = (t: "dark" | "light") => {
    setThemeState(t);
    localStorage.setItem("theme", t);
  };

  const createNewSession = () => {
    const id = `session_${Date.now()}`;
    const session: ChatSession = { id, title: "New Chat", messages: [], createdAt: Date.now() };
    setSessions(prev => [session, ...prev]);
    setActiveSessionId(id);
    setSessionId(id);
    return id;
  };

  const deleteSession = (id: string) => {
    const remaining = sessions.filter(s => s.id !== id);
    setSessions(remaining);
    if (activeSessionId === id) {
      if (remaining.length > 0) {
        setActiveSessionId(remaining[0].id);
        setSessionId(remaining[0].id);
      } else {
        const newId = `session_${Date.now()}`;
        const session: ChatSession = { id: newId, title: "New Chat", messages: [], createdAt: Date.now() };
        setSessions([session]);
        setActiveSessionId(newId);
        setSessionId(newId);
      }
    }
  };

  const sendGlobalMessage = async (data: {
    message: string;
    session_id: string;
    agent_id: string;
    force_local: boolean;
    force_cloud: boolean;
    language: string;
    web_search: boolean;
  }) => {
    setIsSending(true);
    try {
      const response = await sendMessage(data);
      setSessions(prev => prev.map(s => {
        if (s.id === data.session_id) {
          return {
            ...s,
            messages: [
              ...s.messages,
              {
                role: "assistant",
                content: response.content,
                agent_id: response.agent_id,
                agent_name: response.agent_name,
                model: response.model,
                provider: response.provider,
                sources: response.sources,
                trace: response.trace,
                latency_ms: response.usage?.latency_ms,
                cost_usd: response.usage?.cost_usd,
              }
            ]
          };
        }
        return s;
      }));
    } catch (err: any) {
      console.error("Global message send error:", err);
      const errorMsg = err.response?.data?.detail || err.message || "Unknown error";
      setSessions(prev => prev.map(s => {
        if (s.id === data.session_id) {
          return {
            ...s,
            messages: [
              ...s.messages,
              {
                role: "assistant",
                content: `⚠️ **Error**: ${errorMsg}`,
                agent_id: "system",
                agent_name: "System",
                model: "none",
                provider: "error"
              }
            ]
          };
        }
        return s;
      }));
    } finally {
      setIsSending(false);
    }
  };

  return (
    <QueryClientProvider client={queryClient}>
      <AppContext.Provider
        value={{
          sidebarOpen,
          setSidebarOpen,
          routingMode,
          setRoutingMode,
          sessionId,
          setSessionId,
          language,
          setLanguage,
          theme,
          setTheme,
          sessions,
          setSessions,
          activeSessionId,
          setActiveSessionId,
          isSending,
          sendGlobalMessage,
          createNewSession,
          deleteSession,
        }}
      >
        {children}
      </AppContext.Provider>
    </QueryClientProvider>
  );
}

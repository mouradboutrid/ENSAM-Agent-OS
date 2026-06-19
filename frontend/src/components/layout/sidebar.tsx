"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useApp } from "@/lib/providers";
import {
  MessageSquare, BookOpen, Wrench, BarChart3, Shield, Settings, ChevronLeft, ChevronRight, Bot,
} from "lucide-react";

const NAV_ITEMS = [
  { href: "/chat", label: "Chat", icon: MessageSquare, desc: "Multi-Agent Chat" },
  { href: "/knowledge", label: "Knowledge", icon: BookOpen, desc: "RAG Pipeline" },
  { href: "/tools", label: "Tools", icon: Wrench, desc: "MCP Registry" },
  { href: "/observability", label: "Observability", icon: BarChart3, desc: "Metrics & Traces" },
  { href: "/privacy", label: "Privacy", icon: Shield, desc: "GDPR & Security" },
  { href: "/settings", label: "Settings", icon: Settings, desc: "System Config" },
];

export function Sidebar() {
  const pathname = usePathname();
  const { sidebarOpen, setSidebarOpen } = useApp();

  return (
    <aside
      className={`${sidebarOpen ? "w-64" : "w-[72px]"} shrink-0 h-screen sticky top-0 flex flex-col border-r border-border bg-surface transition-all duration-300 ease-in-out`}
    >
      <div className="p-4 flex items-center gap-3 border-b border-border">
        <div className="w-9 h-9 rounded-lg gradient-primary flex items-center justify-center shrink-0">
          <Bot size={20} className="text-white" />
        </div>
        {sidebarOpen && (
          <div className="animate-fade-in overflow-hidden">
            <h1 className="text-sm font-bold gradient-text whitespace-nowrap">ENSAM Agentic OS</h1>
            <p className="text-[10px] text-muted">v0.1.0</p>
          </div>
        )}
      </div>

      <nav className="flex-1 p-3 space-y-1">
        {NAV_ITEMS.map((item) => {
          const isActive = pathname === item.href || pathname?.startsWith(item.href + "/");
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200 group ${
                isActive
                  ? "bg-primary/10 text-primary border border-primary/20"
                  : "text-muted-foreground hover:text-foreground hover:bg-card-hover"
              }`}
            >
              <item.icon size={18} className={`shrink-0 ${isActive ? "text-primary" : "group-hover:text-primary transition-colors"}`} />
              {sidebarOpen && (
                <div className="animate-fade-in overflow-hidden">
                  <span className="text-sm font-medium block">{item.label}</span>
                  <span className="text-[10px] text-muted block">{item.desc}</span>
                </div>
              )}
            </Link>
          );
        })}
      </nav>

      <button
        onClick={() => setSidebarOpen(!sidebarOpen)}
        className="p-3 border-t border-border text-muted hover:text-foreground transition-colors flex items-center justify-center"
      >
        {sidebarOpen ? <ChevronLeft size={18} /> : <ChevronRight size={18} />}
      </button>
    </aside>
  );
}

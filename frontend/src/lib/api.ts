import axios from "axios";

const api = axios.create({
  baseURL: "http://localhost:8000",
  timeout: 300000, // 5 minutes (LLMs can be slow)
  headers: { "Content-Type": "application/json" },
});

api.interceptors.request.use((config) => {
  const userId = localStorage.getItem("userId") || "anonymous";
  config.headers["X-User-ID"] = userId;
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error("API Error:", error.response?.data || error.message);
    return Promise.reject(error);
  }
);

export default api;

export async function sendMessage(data: {
  message: string;
  session_id?: string;
  agent_id?: string;
  user_id?: string;
  force_local?: boolean;
  force_cloud?: boolean;
  language?: string;
  web_search?: boolean;
}) {
  const res = await api.post("/api/chat", data);
  return res.data;
}

export async function getAgents() {
  const res = await api.get("/api/agents");
  return res.data;
}

export async function runDebate(data: {
  topic: string;
  agent_a_name?: string;
  agent_b_name?: string;
  rounds?: number;
  force_local?: boolean;
}) {
  const res = await api.post("/api/agents/debate", data);
  return res.data;
}

export async function ingestDocument(file: File, chunkSize = 512, chunkOverlap = 50, metadata = {}) {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("chunk_size", String(chunkSize));
  formData.append("chunk_overlap", String(chunkOverlap));
  formData.append("metadata", JSON.stringify(metadata));
  const res = await api.post("/api/rag/ingest", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return res.data;
}

export async function searchDocuments(query: string, nResults = 5) {
  const res = await api.post("/api/rag/search", { query, n_results: nResults });
  return res.data;
}

export async function ragQuery(question: string, nResults = 5, provider = "groq") {
  const res = await api.post("/api/rag/query", { question, n_results: nResults, provider });
  return res.data;
}

export async function getDocuments() {
  const res = await api.get("/api/rag/documents");
  return res.data;
}

export async function deleteDocument(docId: string) {
  const res = await api.delete(`/api/rag/documents/${docId}`);
  return res.data;
}

export async function getTools() {
  const res = await api.get("/api/mcp/tools");
  return res.data;
}

export async function testTool(toolId: string, parameters: Record<string, unknown>) {
  const res = await api.post("/api/mcp/tools/test", { tool_id: toolId, parameters });
  return res.data;
}

export async function getMetrics() {
  const res = await api.get("/api/observability/metrics");
  return res.data;
}

export async function getCosts() {
  const res = await api.get("/api/observability/costs");
  return res.data;
}

export async function getLatency() {
  const res = await api.get("/api/observability/metrics/latency");
  return res.data;
}

export async function getAuditLog(limit = 100) {
  const res = await api.get(`/api/observability/audit?limit=${limit}`);
  return res.data;
}

export async function exportAudit() {
  const res = await api.post("/api/observability/audit/export");
  return res.data;
}

export async function getHealth() {
  const res = await api.get("/api/system/health");
  return res.data;
}

export async function getSystemConfig() {
  const res = await api.get("/api/system/config");
  return res.data;
}

export async function toggleRouting(localOnly: boolean) {
  const res = await api.put("/api/system/routing", { local_only: localOnly });
  return res.data;
}

export async function getResources() {
  const res = await api.get("/api/system/resources");
  return res.data;
}

export async function getMemoryStats() {
  const res = await api.get("/api/memory/stats");
  return res.data;
}

export async function getGraph() {
  const res = await api.get("/api/memory/graph");
  return res.data;
}

export async function forgetUser(userId: string) {
  const res = await api.post("/api/memory/gdpr/forget", { user_id: userId, confirm: true });
  return res.data;
}

export async function getChatHistory(sessionId: string) {
  const res = await api.get(`/api/chat/history/${sessionId}`);
  return res.data;
}

export async function getTraces() {
  const res = await api.get("/api/observability/traces");
  return res.data;
}

export async function switchModel(model: string) {
  const res = await api.put("/api/system/model", { model });
  return res.data;
}


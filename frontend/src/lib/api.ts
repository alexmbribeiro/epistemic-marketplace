import axios from "axios";
import type { Claim, CognitiveAgent, Debate, JudgeBiasRow, LeaderboardEntry } from "@/types";

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
});

api.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("token");
    if (token) config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const claimsApi = {
  list: (limit = 20, offset = 0) =>
    api.get<Claim[]>("/claims/", { params: { limit, offset } }).then((r) => r.data),
  get: (id: string) => api.get<Claim>(`/claims/${id}`).then((r) => r.data),
  create: (body: { content: string; category: string; is_verifiable: boolean }) =>
    api.post<Claim>("/claims/", body).then((r) => r.data),
};

export const debatesApi = {
  list: (limit = 20, offset = 0) =>
    api.get<Debate[]>("/debates/", { params: { limit, offset } }).then((r) => r.data),
  get: (id: string) => api.get<Debate>(`/debates/${id}`).then((r) => r.data),
  create: (body: { claim_id: string; agent_ids?: string[]; agent_archetypes?: string[] }) =>
    api.post<Debate>("/debates/", body).then((r) => r.data),
};

export const agentsApi = {
  list: () => api.get<CognitiveAgent[]>("/agents/").then((r) => r.data),
  get: (id: string) => api.get<CognitiveAgent>(`/agents/${id}`).then((r) => r.data),
  create: (body: {
    name: string;
    archetype: string;
    system_prompt: string;
    description: string;
    config: Record<string, unknown>;
    is_public: boolean;
  }) => api.post<CognitiveAgent>("/agents/", body).then((r) => r.data),
};

export const calibrationApi = {
  leaderboard: () => api.get<LeaderboardEntry[]>("/calibration/leaderboard").then((r) => r.data),
  judgeBias: () => api.get<JudgeBiasRow[]>("/calibration/judge-bias").then((r) => r.data),
};

export const authApi = {
  register: (body: { email: string; username: string; password: string }) =>
    api.post<{ access_token: string; user_id: string; username: string }>("/auth/register", body).then((r) => r.data),
  login: (body: { email: string; password: string }) =>
    api.post<{ access_token: string; user_id: string; username: string }>("/auth/login", body).then((r) => r.data),
};

export default api;

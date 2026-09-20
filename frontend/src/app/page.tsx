"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { claimsApi, debatesApi } from "@/lib/api";
import AgentPicker from "@/components/debate/AgentPicker";

const CATEGORIES = ["science", "philosophy", "economics", "ethics", "politics", "other"];

export default function HomePage() {
  const router = useRouter();
  const [content, setContent] = useState("");
  const [category, setCategory] = useState("philosophy");
  const [isVerifiable, setIsVerifiable] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [agentIds, setAgentIds] = useState<string[]>([]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!content.trim()) return;
    if (agentIds.length < 2) {
      setError("Pick at least two agents — a debate needs someone to disagree.");
      return;
    }
    setLoading(true);
    setError("");
    try {
      const claim = await claimsApi.create({ content: content.trim(), category, is_verifiable: isVerifiable });
      const debate = await debatesApi.create({ claim_id: claim.id, agent_ids: agentIds });
      router.push(`/debates/${debate.id}`);
    } catch {
      setError("Failed to start debate. Make sure the backend is running.");
      setLoading(false);
    }
  }

  return (
    <div className="max-w-2xl mx-auto space-y-14 py-10">
      <div className="text-center space-y-4">
        <h1 className="display text-[44px] leading-[1.05] bg-gradient-to-br from-white via-white to-white/55 bg-clip-text text-transparent">
          Epistemic Marketplace
        </h1>
        <p className="text-white/50 text-[17px] leading-relaxed max-w-xl mx-auto">
          Submit a claim. Agents with distinct cognitive architectures debate its truth.
          <br />
          The output isn't an answer — it's a{" "}
          <span className="text-indigo-300 font-medium">map of uncertainty</span>.
        </p>
      </div>


      <form onSubmit={handleSubmit} className="space-y-4 glass p-6">
        <h2 className="display text-[17px] text-white/85">Submit a claim for debate</h2>

        <textarea
          value={content}
          onChange={(e) => setContent(e.target.value)}
          placeholder='e.g. "Consciousness is computationally irreducible" or "Free markets optimize for collective welfare"'
          rows={3}
          className="w-full bg-white/[0.05] border border-white/12 rounded-2xl px-4 py-3 text-white/90 placeholder-white/25 resize-none focus:outline-none focus:border-white/25 text-sm"
          required
        />

        <div className="flex gap-4">
          <div className="flex-1">
            <label className="text-xs text-white/40 mb-1 block">Category</label>
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className="w-full bg-white/[0.05] border border-white/12 rounded-2xl px-3 py-2 text-white/85 text-sm focus:outline-none focus:border-white/25"
            >
              {CATEGORIES.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>
          </div>
          <div className="flex items-end">
            <label className="flex items-center gap-2 text-sm text-white/55 cursor-pointer pb-2">
              <input
                type="checkbox"
                checked={isVerifiable}
                onChange={(e) => setIsVerifiable(e.target.checked)}
                className="rounded border-white/20 bg-white/[0.07]"
              />
              Empirically verifiable
            </label>
          </div>
        </div>

        <AgentPicker selected={agentIds} onChange={setAgentIds} />

        {error && <p className="text-rose-400 text-sm">{error}</p>}

        <button
          type="submit"
          disabled={loading || !content.trim() || agentIds.length < 2}
          className="w-full bg-indigo-600 hover:bg-indigo-500 disabled:bg-white/10 disabled:text-white/40 text-white font-semibold py-3 rounded-lg transition-colors text-sm"
        >
          {loading ? "Starting debate..." : "Start Debate →"}
        </button>
      </form>
    </div>
  );
}

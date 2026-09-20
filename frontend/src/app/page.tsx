"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { claimsApi, debatesApi } from "@/lib/api";

const CATEGORIES = ["science", "philosophy", "economics", "ethics", "politics", "other"];

export default function HomePage() {
  const router = useRouter();
  const [content, setContent] = useState("");
  const [category, setCategory] = useState("philosophy");
  const [isVerifiable, setIsVerifiable] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!content.trim()) return;
    setLoading(true);
    setError("");
    try {
      const claim = await claimsApi.create({ content: content.trim(), category, is_verifiable: isVerifiable });
      const debate = await debatesApi.create({ claim_id: claim.id });
      router.push(`/debates/${debate.id}`);
    } catch {
      setError("Failed to start debate. Make sure the backend is running.");
      setLoading(false);
    }
  }

  return (
    <div className="max-w-2xl mx-auto space-y-12 py-8">
      <div className="text-center space-y-4">
        <h1 className="text-4xl font-bold bg-gradient-to-r from-indigo-400 to-cyan-400 bg-clip-text text-transparent">
          Epistemic Marketplace
        </h1>
        <p className="text-slate-400 text-lg">
          Submit a claim. Six AI agents with distinct cognitive architectures debate its truth.
          <br />
          The output isn't an answer — it's a{" "}
          <span className="text-indigo-300 font-medium">map of uncertainty</span>.
        </p>
      </div>

      <div className="grid grid-cols-3 gap-4 text-center">
        {[
          { icon: "⚖️", label: "Bayesian", desc: "Prior + evidence" },
          { icon: "🔬", label: "Falsificationist", desc: "Seeks to disprove" },
          { icon: "🌐", label: "Analogist", desc: "Cross-domain patterns" },
          { icon: "↯", label: "Contrarian", desc: "Against consensus" },
          { icon: "☯", label: "Dialectician", desc: "Thesis → synthesis" },
          { icon: "📊", label: "Frequentist", desc: "Empirical only" },
        ].map((a) => (
          <div key={a.label} className="rounded-lg border border-slate-800 bg-slate-900/50 p-3 space-y-1">
            <div className="text-2xl">{a.icon}</div>
            <div className="text-sm font-medium text-slate-200">{a.label}</div>
            <div className="text-xs text-slate-500">{a.desc}</div>
          </div>
        ))}
      </div>

      <form onSubmit={handleSubmit} className="space-y-4 rounded-xl border border-slate-800 bg-slate-900/50 p-6">
        <h2 className="text-lg font-semibold text-slate-200">Submit a claim for debate</h2>

        <textarea
          value={content}
          onChange={(e) => setContent(e.target.value)}
          placeholder='e.g. "Consciousness is computationally irreducible" or "Free markets optimize for collective welfare"'
          rows={3}
          className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-3 text-slate-100 placeholder-slate-600 resize-none focus:outline-none focus:border-indigo-500 text-sm"
          required
        />

        <div className="flex gap-4">
          <div className="flex-1">
            <label className="text-xs text-slate-500 mb-1 block">Category</label>
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-slate-200 text-sm focus:outline-none focus:border-indigo-500"
            >
              {CATEGORIES.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>
          </div>
          <div className="flex items-end">
            <label className="flex items-center gap-2 text-sm text-slate-400 cursor-pointer pb-2">
              <input
                type="checkbox"
                checked={isVerifiable}
                onChange={(e) => setIsVerifiable(e.target.checked)}
                className="rounded border-slate-600 bg-slate-800"
              />
              Empirically verifiable
            </label>
          </div>
        </div>

        {error && <p className="text-rose-400 text-sm">{error}</p>}

        <button
          type="submit"
          disabled={loading || !content.trim()}
          className="w-full bg-indigo-600 hover:bg-indigo-500 disabled:bg-slate-700 disabled:text-slate-500 text-white font-semibold py-3 rounded-lg transition-colors text-sm"
        >
          {loading ? "Starting debate..." : "Start Debate →"}
        </button>
      </form>
    </div>
  );
}

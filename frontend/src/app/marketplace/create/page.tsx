"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { agentsApi } from "@/lib/api";

export default function CreateAgentPage() {
  const router = useRouter();
  const [form, setForm] = useState({
    name: "",
    description: "",
    system_prompt: "",
    archetype: "custom",
    is_public: true,
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      await agentsApi.create({ ...form, config: {} });
      router.push("/marketplace");
    } catch {
      setError("Failed to create agent. Make sure you are logged in.");
      setLoading(false);
    }
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold text-white/90">Create Cognitive Agent</h1>
      <p className="text-white/55 text-sm">
        Define a custom epistemic architecture. Your agent will participate in debates and earn reputation based on calibration.
      </p>

      <form onSubmit={handleSubmit} className="space-y-5 glass p-6">
        <div>
          <label className="text-sm text-white/55 block mb-1">Agent Name</label>
          <input
            value={form.name}
            onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
            className="w-full bg-white/[0.05] border border-white/12 rounded-2xl px-4 py-2.5 text-white/90 text-sm focus:outline-none focus:border-white/25"
            placeholder="e.g. Skeptical Pragmatist"
            required
          />
        </div>

        <div>
          <label className="text-sm text-white/55 block mb-1">Description</label>
          <input
            value={form.description}
            onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))}
            className="w-full bg-white/[0.05] border border-white/12 rounded-2xl px-4 py-2.5 text-white/90 text-sm focus:outline-none focus:border-white/25"
            placeholder="How does this agent reason?"
            required
          />
        </div>

        <div>
          <label className="text-sm text-white/55 block mb-1">
            System Prompt{" "}
            <span className="text-white/28 text-xs">(defines the cognitive architecture)</span>
          </label>
          <textarea
            value={form.system_prompt}
            onChange={(e) => setForm((f) => ({ ...f, system_prompt: e.target.value }))}
            rows={8}
            className="w-full bg-white/[0.05] border border-white/12 rounded-2xl px-4 py-3 text-white/90 text-sm resize-none focus:outline-none focus:border-white/25 font-mono"
            placeholder="You are an epistemic agent that reasons by... Your output must always include a belief_score between 0 and 1..."
            required
          />
        </div>

        <label className="flex items-center gap-2 text-sm text-white/55 cursor-pointer">
          <input
            type="checkbox"
            checked={form.is_public}
            onChange={(e) => setForm((f) => ({ ...f, is_public: e.target.checked }))}
            className="rounded border-white/20 bg-white/[0.07]"
          />
          Make this agent public
        </label>

        {error && <p className="text-rose-400 text-sm">{error}</p>}

        <button
          type="submit"
          disabled={loading}
          className="w-full bg-indigo-600 hover:bg-indigo-500 disabled:bg-white/10 disabled:text-white/40 text-white font-semibold py-3 rounded-lg transition-colors text-sm"
        >
          {loading ? "Creating..." : "Deploy Agent →"}
        </button>
      </form>
    </div>
  );
}

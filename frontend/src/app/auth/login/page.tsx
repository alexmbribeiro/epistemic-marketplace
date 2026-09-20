"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { authApi } from "@/lib/api";
import Link from "next/link";

export default function LoginPage() {
  const router = useRouter();
  const [form, setForm] = useState({ email: "", password: "" });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const res = await authApi.login(form);
      localStorage.setItem("token", res.access_token);
      router.push("/");
    } catch {
      setError("Invalid credentials");
      setLoading(false);
    }
  }

  return (
    <div className="max-w-sm mx-auto mt-16 space-y-6">
      <h1 className="text-2xl font-bold text-white/90 text-center">Sign In</h1>
      <form onSubmit={handleSubmit} className="space-y-4 glass p-6">
        <div>
          <label className="text-sm text-white/55 block mb-1">Email</label>
          <input type="email" value={form.email} onChange={(e) => setForm((f) => ({ ...f, email: e.target.value }))}
            className="w-full bg-white/[0.05] border border-white/12 rounded-2xl px-4 py-2.5 text-white/90 text-sm focus:outline-none focus:border-white/25" required />
        </div>
        <div>
          <label className="text-sm text-white/55 block mb-1">Password</label>
          <input type="password" value={form.password} onChange={(e) => setForm((f) => ({ ...f, password: e.target.value }))}
            className="w-full bg-white/[0.05] border border-white/12 rounded-2xl px-4 py-2.5 text-white/90 text-sm focus:outline-none focus:border-white/25" required />
        </div>
        {error && <p className="text-rose-400 text-sm">{error}</p>}
        <button type="submit" disabled={loading}
          className="w-full bg-indigo-600 hover:bg-indigo-500 disabled:bg-white/10 text-white font-semibold py-3 rounded-lg transition-colors text-sm">
          {loading ? "Signing in..." : "Sign In"}
        </button>
      </form>
      <p className="text-center text-sm text-white/40">
        No account?{" "}
        <Link href="/auth/register" className="text-indigo-400 hover:underline">Register →</Link>
      </p>
    </div>
  );
}

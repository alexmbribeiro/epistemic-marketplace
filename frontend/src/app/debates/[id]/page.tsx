"use client";

import { useQuery } from "@tanstack/react-query";
import { claimsApi, debatesApi } from "@/lib/api";
import DebateRoom from "@/components/debate/DebateRoom";
import Link from "next/link";

interface Props {
  params: { id: string };
}

export default function DebatePage({ params }: Props) {
  const { data: debate } = useQuery({
    queryKey: ["debate", params.id],
    queryFn: () => debatesApi.get(params.id),
  });

  const { data: claim } = useQuery({
    queryKey: ["claim", debate?.claim_id],
    queryFn: () => claimsApi.get(debate!.claim_id),
    enabled: !!debate?.claim_id,
  });

  return (
    <div className="space-y-6">
      <div>
        <Link href="/debates" className="text-sm text-white/40 hover:text-white/75 transition-colors">
          ← All debates
        </Link>
      </div>

      {claim && (
        <div className="rounded-xl border border-indigo-900/50 bg-indigo-950/20 p-5">
          <p className="text-xs text-indigo-400 font-semibold uppercase tracking-wider mb-2">Claim</p>
          <p className="text-lg text-white/90 font-medium">"{claim.content}"</p>
          <div className="flex gap-3 mt-2">
            <span className="text-xs text-white/40 bg-white/[0.07] px-2 py-0.5 rounded-full">{claim.category}</span>
            {claim.is_verifiable && (
              <span className="text-xs text-emerald-400 bg-emerald-950 px-2 py-0.5 rounded-full">verifiable</span>
            )}
          </div>
        </div>
      )}

      <DebateRoom debateId={params.id} />
    </div>
  );
}

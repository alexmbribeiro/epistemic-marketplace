"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const links = [
  { href: "/", label: "Home" },
  { href: "/debates", label: "Debates" },
  { href: "/marketplace", label: "Agents" },
  { href: "/calibration", label: "Ranking" },
];

export default function Nav() {
  const pathname = usePathname();

  return (
    <div className="sticky top-0 z-50 px-5 pt-5">
      <nav className="glass max-w-6xl mx-auto px-5 py-3 flex items-center gap-8">
        <Link href="/" className="display text-[15px] text-white/90 whitespace-nowrap">
          epistemic<span className="text-white/30">.</span>market
        </Link>
        <div className="flex gap-1">
          {links.map((l) => {
            const active = pathname === l.href;
            return (
              <Link
                key={l.href}
                href={l.href}
                className={`pill px-3.5 py-1.5 text-[13px] transition-colors ${
                  active
                    ? "bg-white/10 text-white"
                    : "text-white/45 hover:text-white/80 hover:bg-white/5"
                }`}
              >
                {l.label}
              </Link>
            );
          })}
        </div>
      </nav>
    </div>
  );
}

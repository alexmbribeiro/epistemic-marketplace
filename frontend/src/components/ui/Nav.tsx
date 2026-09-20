"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const links = [
  { href: "/", label: "Home" },
  { href: "/debates", label: "Debates" },
  { href: "/marketplace", label: "Marketplace" },
  { href: "/calibration", label: "Calibration" },
];

export default function Nav() {
  const pathname = usePathname();
  return (
    <nav className="border-b border-slate-800 bg-slate-950/80 backdrop-blur sticky top-0 z-50">
      <div className="max-w-6xl mx-auto px-4 py-3 flex items-center gap-8">
        <Link href="/" className="font-bold text-indigo-400 text-lg tracking-tight">
          epistemic<span className="text-slate-400">.</span>market
        </Link>
        <div className="flex gap-6">
          {links.map((l) => (
            <Link
              key={l.href}
              href={l.href}
              className={`text-sm transition-colors ${
                pathname === l.href ? "text-indigo-400 font-medium" : "text-slate-500 hover:text-slate-300"
              }`}
            >
              {l.label}
            </Link>
          ))}
        </div>
      </div>
    </nav>
  );
}

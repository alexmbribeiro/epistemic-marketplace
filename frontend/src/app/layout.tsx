import type { Metadata } from "next";
import "./globals.css";
import Providers from "./providers";
import Nav from "@/components/ui/Nav";

export const metadata: Metadata = {
  title: "Epistemic Marketplace",
  description: "A marketplace where AI agents with different cognitive architectures debate truth",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-[#0a0f1e] text-slate-100 antialiased">
        <Providers>
          <Nav />
          <main className="max-w-6xl mx-auto px-4 py-8">{children}</main>
        </Providers>
      </body>
    </html>
  );
}

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
      <body className="min-h-screen antialiased">
        <div className="ambient" aria-hidden="true" />
        <Providers>
          <Nav />
          <main className="max-w-6xl mx-auto px-5 pb-24 pt-8">{children}</main>
        </Providers>
      </body>
    </html>
  );
}

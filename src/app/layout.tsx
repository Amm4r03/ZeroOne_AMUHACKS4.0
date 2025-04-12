import type { Metadata } from "next";
import { DM_Sans } from "next/font/google";
import { Suspense } from "react";

import Providers from "@/components/providers";

import "./globals.css";

const dmSans = DM_Sans({
  subsets: ["latin"],
  weight: "400",
});

export const metadata: Metadata = {
  title: "ClarityHub",
  description:
    "Learn with High-Quality Study Materials , Read AI-curated content , Watch recommended educational videos",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <Providers>
      <html lang="en">
        <body
          className={`bg-brand-bg ${dmSans.className} tracking-wide antialiased`}
        >
          <main className="mx-auto">
            <Suspense>{children}</Suspense>
          </main>
        </body>
      </html>
    </Providers>
  );
}

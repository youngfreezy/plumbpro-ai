import type { Metadata } from "next";
import { GeistSans } from "geist/font/sans";
import { GeistMono } from "geist/font/mono";
import NextTopLoader from "nextjs-toploader";
import { Toaster } from "sonner";
import "./globals.css";

export const metadata: Metadata = {
  title: "PlumbPro AI",
  description: "AI-powered plumbing business management",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={`${GeistSans.variable} ${GeistMono.variable}`}>
      <body className="min-h-screen bg-background font-sans antialiased">
        <NextTopLoader color="hsl(187, 65%, 38%)" height={2} showSpinner={false} />
        {children}
        <Toaster position="top-right" richColors closeButton />
      </body>
    </html>
  );
}

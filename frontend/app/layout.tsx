import type { Metadata } from "next";

import "./globals.css";

export const metadata: Metadata = {
  title: "StreetShow",
  description: "StreetShow AI virtual try-on & styling platform",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="zh-CN">
      <body className="min-h-screen bg-black text-white antialiased">
        {children}
      </body>
    </html>
  );
}

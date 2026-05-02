import type { Metadata } from "next";

import { LangProvider } from "../components/LangProvider";
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
    <html lang="en">
      <body className="min-h-screen bg-black text-white antialiased">
        <LangProvider>{children}</LangProvider>
      </body>
    </html>
  );
}

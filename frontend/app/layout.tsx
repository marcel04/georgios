import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Georgios | Online Ordering",
  description: "A restaurant online-ordering portfolio project.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}

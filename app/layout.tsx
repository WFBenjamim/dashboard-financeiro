import type { Metadata } from "next";
import { Fira_Sans } from "next/font/google";
import "./globals.css";

const firaSans = Fira_Sans({
  subsets: ["latin"],
  weight: ["300", "400", "500", "600", "700", "800", "900"],
  variable: "--font-fira-sans",
});

export const metadata: Metadata = {
  title: "Dashboard Financeiro Executivo",
  description: "Dashboard Financeiro - Gondim",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="pt-BR" className={`dark ${firaSans.variable}`}>
      <body className={firaSans.className}>
        {children}
      </body>
    </html>
  );
}

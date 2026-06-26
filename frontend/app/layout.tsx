import type { Metadata } from "next";
import "./globals.css";
import Navbar from "@/components/Navbar";

export const metadata: Metadata = {
  title: "InfokanSaham ",
  description: "Platform prediksi saham IDX",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="id">
      <body>
        <Navbar />
        <main className="max-w-container mx-auto px-6 py-8">
          {children}
        </main>
      </body>
    </html>
  );
}
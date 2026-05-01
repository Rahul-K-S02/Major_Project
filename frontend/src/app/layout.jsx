import "./globals.css";
import { Toaster } from "react-hot-toast";

export const metadata = {
  title: "GeneRisk — AI Genomic Risk Intelligence",
  description: "AI-powered genomic disease risk prediction. JNNCE Batch B13.",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>
        <Toaster position="top-right" />
        {children}
      </body>
    </html>
  );
}

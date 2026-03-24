import "./globals.css";
import { Lato } from "next/font/google";
import { Providers } from "./providers";
import { Sidebar } from "./components/Sidebar";
import { TopBar } from "./components/TopBar";

const lato = Lato({
  subsets: ["latin"],
  weight: ["100", "300", "400", "700", "900"],
  display: "swap",
});

export const metadata = {
  title: "Kartavya",
  description: "Kartavya — intelligent course generation platform",  // Fix P4: was "AI course generation platform"
};

// Fix P3: viewport must be a separate export in Next.js 13+ app router
export const viewport = {
  width: "device-width",
  initialScale: 1,
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={lato.className}>
      <body className="aurora-bg">
        <Providers>
          <div className="app-shell">
            <Sidebar />
            <div className="content-area">
              <TopBar />
              <main className="main">{children}</main>
            </div>
          </div>
        </Providers>
      </body>
    </html>
  );
}

import type { Metadata } from "next";
import "./globals.css";

const SITE_URL = "https://bitling.dev";

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: "Bitling • Free Open-Source Desktop Pets for Developers",
  description:
    "Download free open-source desktop pets for your Mac. Bitling lives on your dock, watches your commits, hunts your failing test bugs with lasers, and cheers your Claude Code sessions.",
  openGraph: {
    title: "Bitling • Free Open-Source Desktop Pets for Developers",
    description:
      "A desktop companion that lives on your git commits, hunts test bugs across your desktop, and cheers your Claude Code sessions.",
    url: SITE_URL,
    images: ["/media/hero.png"],
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "Bitling • Free Open-Source Desktop Pets for Developers",
    description:
      "A desktop companion that lives on your git commits, hunts test bugs across your desktop, and cheers your Claude Code sessions.",
    images: ["/media/hero.png"],
  },
  icons: {
    icon: "data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16'><text y='14' font-size='14'>%F0%9F%A4%96</text></svg>",
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}

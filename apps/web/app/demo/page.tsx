import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Live Demo • Bitling",
  description: "Play with Bitling's full desktop pet engine in your browser — switch species, fire git events, and watch it react.",
  openGraph: {
    title: "Live Demo • Bitling",
    description: "Play with Bitling's full desktop pet engine in your browser.",
    images: ["/media/hero.png"],
  },
};

export default function DemoPage() {
  return (
    <div style={{ height: "100dvh", width: "100%", display: "flex", flexDirection: "column" }}>
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "0.6rem 1rem",
          background: "var(--bg-dark)",
          borderBottom: "2px solid var(--border-color)",
          flex: "0 0 auto",
        }}
      >
        <Link
          href="/"
          className="font-pixel"
          style={{
            color: "#FFFFFF",
            fontSize: "0.65rem",
            textTransform: "uppercase",
            padding: "0.6rem 0.25rem",
            margin: "-0.6rem -0.25rem",
            display: "inline-flex",
            alignItems: "center",
          }}
        >
          &larr; Bitling
        </Link>
        <span className="font-pixel" style={{ color: "var(--text-light)", fontSize: "0.65rem" }}>
          Live Demo
        </span>
      </div>
      <iframe
        src="/demo.html"
        title="Bitling Live Interactive Canvas Stage"
        style={{ flex: "1 1 auto", width: "100%", border: "none" }}
      />
    </div>
  );
}

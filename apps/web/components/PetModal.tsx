"use client";

import type { Pet } from "@/data/pets";

export function PetModal({
  pet,
  onClose,
  onTry,
  onCopy,
}: {
  pet: Pet | null;
  onClose: () => void;
  onTry: (id: string) => void;
  onCopy: (text: string) => void;
}) {
  return (
    <div
      className={`modal-backdrop${pet ? " open" : ""}`}
      role="dialog"
      aria-modal="true"
      aria-label="Pet Details"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div className="modal-dialog">
        <button type="button" className="modal-close-btn" aria-label="Close dialog" onClick={onClose}>
          ✕
        </button>
        <div className="modal-content">
          {pet && (
            <>
              <div style={{ textAlign: "center", marginBottom: "1.5rem" }}>
                <div
                  style={{
                    width: 120,
                    height: 120,
                    margin: "0 auto 1rem",
                    background: `radial-gradient(circle, ${pet.accentLight} 0%, #FFFFFF 80%)`,
                    border: "2px solid var(--border-color)",
                    borderRadius: 12,
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    boxShadow: "4px 4px 0px var(--border-color)",
                  }}
                >
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img
                    src={pet.avatar}
                    alt={pet.name}
                    style={{ width: 90, height: 90, objectFit: "contain", imageRendering: "pixelated" }}
                  />
                </div>
                <h2 className="font-pixel" style={{ fontSize: "1.3rem", color: pet.accent, marginBottom: "0.35rem" }}>
                  {pet.name}
                </h2>
                <p style={{ fontSize: "0.95rem", fontWeight: 600, color: "var(--text-muted)" }}>
                  {pet.title} • {pet.species}
                </p>
                <div style={{ display: "flex", gap: "0.5rem", justifyContent: "center", marginTop: "0.75rem" }}>
                  <span
                    className="pixel-badge"
                    style={{
                      background: pet.kind === "walker" ? "#E0F2FE" : "#FEF3C7",
                      color: pet.kind === "walker" ? "#0369A1" : "#B45309",
                    }}
                  >
                    {pet.kind === "walker" ? "🐾 Ground Walker" : "☁️ Air Floater"}
                  </span>
                  <span className="pixel-badge" style={{ background: "var(--bg-dark)", color: "#FFF" }}>
                    {pet.attack.name}
                  </span>
                </div>
              </div>

              <div style={{ display: "flex", flexDirection: "column", gap: "1.25rem", fontSize: "0.92rem" }}>
                <div>
                  <h4 className="font-pixel" style={{ fontSize: "0.72rem", marginBottom: "0.4rem", color: "var(--text-primary)" }}>
                    About {pet.name}
                  </h4>
                  <p style={{ color: "var(--text-secondary)", lineHeight: 1.6 }}>{pet.blurb}</p>
                </div>

                <div
                  style={{
                    background: "var(--bg-secondary)",
                    border: "1.5px solid var(--border-subtle)",
                    borderRadius: 6,
                    padding: "1rem",
                  }}
                >
                  <h4 className="font-pixel" style={{ fontSize: "0.7rem", color: "var(--accent-blue)", marginBottom: "0.5rem" }}>
                    ⚡ Signature Bug Attack
                  </h4>
                  <p style={{ color: "var(--text-primary)", fontWeight: 600 }}>
                    {pet.attack.icon} {pet.attack.name}
                  </p>
                  <p style={{ color: "var(--text-secondary)", fontSize: "0.85rem", marginTop: "0.25rem" }}>{pet.attack.desc}</p>
                </div>

                <div>
                  <h4 className="font-pixel" style={{ fontSize: "0.72rem", marginBottom: "0.4rem", color: "var(--text-primary)" }}>
                    🌟 Growth & Evolution
                  </h4>
                  <p
                    style={{
                      fontFamily: "var(--font-mono)",
                      fontSize: "0.8rem",
                      background: "var(--bg-dark)",
                      color: "#38BDF8",
                      padding: "0.65rem 0.85rem",
                      borderRadius: 4,
                    }}
                  >
                    {pet.evolution}
                  </p>
                </div>

                <div>
                  <h4 className="font-pixel" style={{ fontSize: "0.72rem", marginBottom: "0.5rem", color: "var(--text-primary)" }}>
                    💬 Iconic Voice Quotes
                  </h4>
                  <ul style={{ listStyle: "none", display: "flex", flexDirection: "column", gap: "0.4rem" }}>
                    {pet.quotes.map((q) => (
                      <li
                        key={q}
                        style={{
                          padding: "0.45rem 0.75rem",
                          background: "#F8FAFC",
                          borderLeft: `3px solid ${pet.accent}`,
                          fontStyle: "italic",
                          fontSize: "0.85rem",
                          color: "var(--text-secondary)",
                        }}
                      >
                        &quot;{q}&quot;
                      </li>
                    ))}
                  </ul>
                </div>

                <div style={{ paddingTop: "0.5rem", display: "flex", gap: "0.75rem" }}>
                  <button
                    type="button"
                    className="pixel-btn"
                    style={{ flex: 1, background: pet.accent }}
                    onClick={() => {
                      onClose();
                      onTry(pet.id);
                    }}
                  >
                    ⚡ Play in Stage
                  </button>
                  <button
                    type="button"
                    className="pixel-btn pixel-btn-light"
                    style={{ flex: 1 }}
                    onClick={() => onCopy(`bitling pet ${pet.id}`)}
                  >
                    📋 Copy CLI Command
                  </button>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

"use client";

import type { Pet } from "@/data/pets";

export function PetCard({
  pet,
  onTry,
  onInspect,
  onCopy,
}: {
  pet: Pet;
  onTry: (id: string) => void;
  onInspect: (id: string) => void;
  onCopy: (text: string) => void;
}) {
  return (
    <article
      className="pixel-card pixel-card-hover pet-card"
      onClick={() => onInspect(pet.id)}
    >
      <div
        className="pet-card-media"
        style={{ background: `radial-gradient(circle at center, ${pet.accentLight} 0%, #FFFFFF 75%)` }}
      >
        <div className="pet-card-bg-gradient" style={{ background: pet.accent }} />
        <span
          className="pixel-badge pet-tag-badge"
          style={{ background: "#FFFFFF", borderColor: pet.accent, color: pet.accent }}
        >
          {pet.species}
        </span>
        <span
          className="pixel-badge pet-kind-badge"
          style={{
            background: pet.kind === "walker" ? "#E0F2FE" : "#FEF3C7",
            color: pet.kind === "walker" ? "#0369A1" : "#B45309",
          }}
        >
          {pet.kind === "walker" ? "🐾 Walker" : "☁️ Floater"}
        </span>
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src={pet.avatar} alt={pet.name} className="pet-avatar-img" loading="lazy" />
      </div>

      <div className="pet-card-body">
        <div className="pet-card-title-row">
          <h3 className="pet-name" style={{ color: pet.accent }}>
            {pet.name}
          </h3>
          <span className="pet-species-subtitle">{pet.title}</span>
        </div>

        <p className="pet-blurb">{pet.blurb}</p>

        <div className="pet-attack-box">
          <span className="attack-icon">{pet.attack.icon}</span>
          <div>
            <div className="attack-name">{pet.attack.name}</div>
            <div className="attack-desc">{pet.attack.desc}</div>
          </div>
        </div>

        <div className="pet-quote-box" style={{ borderLeftColor: pet.accent }}>
          &quot;{pet.quotes[0]}&quot;
        </div>

        <div className="pet-card-actions">
          <button
            type="button"
            className="pixel-btn pixel-btn-sm pet-action-btn"
            style={{ background: pet.accent }}
            onClick={(e) => {
              e.stopPropagation();
              onTry(pet.id);
            }}
          >
            ⚡ Test in Stage
          </button>
          <button
            type="button"
            className="pixel-btn pixel-btn-sm pixel-btn-light pet-action-btn"
            onClick={(e) => {
              e.stopPropagation();
              onInspect(pet.id);
            }}
          >
            🔍 Info
          </button>
          <button
            type="button"
            className="pixel-btn pixel-btn-sm pixel-btn-light pet-action-btn"
            title="Copy CLI switch command"
            onClick={(e) => {
              e.stopPropagation();
              onCopy(`bitling pet ${pet.id}`);
            }}
          >
            📋 CLI
          </button>
        </div>
      </div>
    </article>
  );
}

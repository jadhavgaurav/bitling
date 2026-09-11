"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { PETS_DATA, type Pet } from "@/data/pets";
import { PetCard } from "@/components/PetCard";
import { PetModal } from "@/components/PetModal";
import { Toast } from "@/components/Toast";

const FILTERS = [
  { id: "all", label: "All Pets (11)" },
  { id: "anime", label: "Anime & Manga" },
  { id: "heroes", label: "Superheroes" },
  { id: "gaming", label: "Gaming & Sports" },
  { id: "mech", label: "Mechanical & Mythic" },
  { id: "walkers", label: "🐾 Walkers" },
  { id: "floaters", label: "☁️ Floaters" },
];

const FAQS = [
  {
    q: "How do I bypass the macOS Gatekeeper warning?",
    a: (
      <>
        <p>
          Bitling is signed ad hoc rather than with an expensive Apple Developer ID. If macOS displays{" "}
          <em>&quot;Apple could not verify Bitling is free of malware&quot;</em>, simply run this command once in
          your terminal:
        </p>
        <div className="faq-code">xattr -dr com.apple.quarantine /Applications/Bitling.app</div>
        <p>
          Alternatively, go to <strong>System Settings → Privacy &amp; Security</strong>, scroll to{" "}
          <em>&quot;Bitling was blocked&quot;</em>, and click <strong>Open Anyway</strong>. Using the one-line curl
          installer does this automatically!
        </p>
      </>
    ),
  },
  {
    q: "Does Bitling consume heavy CPU or drain laptop battery?",
    a: (
      <p>
        No! Bitling is engineered in lightweight Swift and WebKit. When idle, CPU consumption is ~0.1%. When you
        hide the pet or let it sleep, background rendering halts completely to preserve your MacBook battery life.
      </p>
    ),
  },
  {
    q: "How does Bitling track Git commits without asking for a token?",
    a: (
      <p>
        Bitling reads the local <code>.git/logs/HEAD</code> reflog file on your own hard drive. It never
        communicates with GitHub, requires no personal access tokens, and works on repositories that have never
        been pushed to the cloud.
      </p>
    ),
  },
  {
    q: "How do I switch pets or send events from my terminal?",
    a: (
      <>
        <p>
          Bitling ships with a global CLI linked to <code>/usr/local/bin/bitling</code>. You can switch companions
          or fire events anytime:
        </p>
        <pre className="faq-code faq-code-block">
          <code>{`bitling pet mario       # Switch companion to Super Mario
bitling pet goku        # Switch companion to Son Goku
bitling pet pikachu     # Switch companion to Pikachu
bitling panel           # Open the native control room
bitling say "lunch?"    # Make your pet speak a speech bubble`}</code>
        </pre>
      </>
    ),
  },
  {
    q: "Can I add custom pets or contribute?",
    a: (
      <p>
        Yes! Bitling is 100% open source under the MIT license. You can declare your own species using the{" "}
        <code>defineSpecies</code> API in <code>apps/macos/web/bitling.html</code>, measure its proportions with{" "}
        <code>node tools/check_bubble_gap.mjs</code>, and submit a pull request on GitHub!
      </p>
    ),
  },
];

const QUICK_BAR_IDS = ["mario", "goku", "pikachu", "ronaldo", "spiderman", "ironman", "thor", "naruto", "kaiju", "robot", "dragon"];

const SIM_ACTION_MESSAGES: Record<string, string> = {
  commit: "Fired event: git commit (catching node & eating)",
  push: "Fired event: git push (rocket launched!)",
  fail: "Fired event: tests failed (beetles crawled out!)",
  pass: "Fired event: tests passed (vaporizing beetles!)",
  boss: "Fired event: Boss Bug emerged with HP bar!",
  pat: "Patted pet! (Hearts & purr)",
};

const DEMO_COMMITS = [
  "fix: stop the widget eating cookies",
  "feat: add parafoil physics",
  "wip",
  "typo in the README",
  "refactor the whole rendering pipeline",
];

const DEMO_TESTS = ["test_webhook_signature", "test_invoice_total", "test_retry_backoff", "test_login_redirect", "test_cache_expiry"];

function pickRandomQuote(pet: Pet): string {
  return pet.quotes[Math.floor(Math.random() * pet.quotes.length)];
}

function pickOne<T>(arr: T[]): T {
  return arr[Math.floor(Math.random() * arr.length)];
}

function makeRandomCommitEvent() {
  return {
    kind: "commit",
    message: pickOne(DEMO_COMMITS),
    hash: Math.random().toString(16).slice(2, 9),
    insertions: Math.floor(Math.random() * 500) + 5,
    deletions: Math.floor(Math.random() * 60),
  };
}

function makeRandomFailEvent() {
  const n = Math.floor(Math.random() * 3) + 2;
  return { kind: "test-failed", count: n, name: "api", tests: DEMO_TESTS.slice(0, n) };
}

// The engine (apps/macos/web/bitling.html) always exposes this on window, regardless of
// desktop/demo mode — it's the same handle the test suite and screenshot tooling use, so
// it's the one stable way to drive the embedded iframe from this same-origin outer page.
interface BitlingEngine {
  selectSpecies: (id: string) => void;
  event: (ev: Record<string, unknown>) => void;
  act: (name: "pat" | "feed" | "play" | "sleep" | "reset") => void;
  spawnBoss: (label?: string) => void;
  triggerSpecial: () => void;
}

export default function Home() {
  const [mobileNavOpen, setMobileNavOpen] = useState(false);
  const [filter, setFilter] = useState("all");
  const [activePetId, setActivePetId] = useState("mario");
  const [modalPetId, setModalPetId] = useState<string | null>(null);
  const [faqOpen, setFaqOpen] = useState(0);
  const [toast, setToast] = useState<string | null>(null);
  const [copiedInstall, setCopiedInstall] = useState(false);
  const toastTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const iframeRef = useRef<HTMLIFrameElement>(null);

  const activePet = useMemo(() => PETS_DATA.find((p) => p.id === activePetId) ?? PETS_DATA[0], [activePetId]);
  const modalPet = useMemo<Pet | null>(() => PETS_DATA.find((p) => p.id === modalPetId) ?? null, [modalPetId]);

  useEffect(() => {
    if (!modalPetId) return;
    function onKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape") setModalPetId(null);
    }
    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, [modalPetId]);
  const filteredPets = useMemo(
    () => (filter === "all" ? PETS_DATA : PETS_DATA.filter((p) => p.categories.includes(filter))),
    [filter]
  );

  function showToast(message: string) {
    setToast(message);
    if (toastTimer.current) clearTimeout(toastTimer.current);
    toastTimer.current = setTimeout(() => setToast(null), 3200);
  }

  async function copyToClipboard(text: string, successMsg?: string) {
    try {
      await navigator.clipboard.writeText(text);
    } catch {
      // clipboard API unavailable, nothing more we can safely do here
    }
    showToast(successMsg ?? "Copied to clipboard!");
  }

  function getEngine(): BitlingEngine | null {
    const win = iframeRef.current?.contentWindow as (Window & { __bitling?: BitlingEngine }) | undefined;
    return win?.__bitling ?? null;
  }

  function switchSimulatorPet(id: string) {
    setActivePetId(id);
    const pet = PETS_DATA.find((p) => p.id === id);
    if (!pet) return;
    getEngine()?.selectSpecies(id);
    showToast(`Switched active companion to ${pet.name}!`);
  }

  function triggerSimulatorAction(action: string) {
    if (action === "voice") {
      showToast(`"${pickRandomQuote(activePet)}"`);
      return;
    }
    const engine = getEngine();
    if (!engine) return;
    switch (action) {
      case "commit":
        engine.event(makeRandomCommitEvent());
        showToast(SIM_ACTION_MESSAGES.commit);
        break;
      case "push":
        engine.event({ kind: "push", branch: "main" });
        showToast(SIM_ACTION_MESSAGES.push);
        break;
      case "fail":
        engine.event(makeRandomFailEvent());
        showToast(SIM_ACTION_MESSAGES.fail);
        break;
      case "pass":
        engine.event({ kind: "test-passed", name: "api" });
        showToast(SIM_ACTION_MESSAGES.pass);
        break;
      case "boss":
        engine.spawnBoss("BOSS BUG");
        showToast(SIM_ACTION_MESSAGES.boss);
        break;
      case "pat":
        engine.act("pat");
        showToast(SIM_ACTION_MESSAGES.pat);
        break;
      default:
        break;
    }
  }

  function goToSimulator() {
    document.getElementById("simulator")?.scrollIntoView({ behavior: "smooth" });
  }

  function copyInstall() {
    copyToClipboard(
      "curl -fsSL https://raw.githubusercontent.com/jadhavgaurav/bitling/main/install.sh | bash",
      "Install command copied to clipboard!"
    );
    setCopiedInstall(true);
    setTimeout(() => setCopiedInstall(false), 2200);
  }

  return (
    <>
      <header className="site-header">
        <div className="container header-inner">
          <div className="brand-group">
            <a href="#hero" className="brand-logo" aria-label="Bitling Home">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src="/avatars/robot.png" alt="Bitling" className="brand-avatar" />
              <span>BITLING</span>
              <span className="brand-version-tag">v2.0</span>
            </a>
          </div>

          <nav className="desktop-nav" aria-label="Primary Navigation">
            <a href="#simulator" className="nav-link">Stage</a>
            <a href="#pets" className="nav-link">Pet Roster</a>
            <a href="#superpowers" className="nav-link">Dev Stack</a>
            <a href="#control-room" className="nav-link">Control Room</a>
            <a href="#sdk" className="nav-link">Build a Pet</a>
            <a href="#faq" className="nav-link">FAQ</a>
          </nav>

          <div className="header-actions">
            <a
              href="https://github.com/jadhavgaurav/bitling"
              target="_blank"
              rel="noopener noreferrer"
              className="github-btn"
              aria-label="Bitling GitHub Repository"
            >
              <svg width="15" height="15" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
                <path
                  fillRule="evenodd"
                  clipRule="evenodd"
                  d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.53 1.032 1.53 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z"
                />
              </svg>
              <span>Star</span>
            </a>
            <button type="button" className="mobile-menu-toggle" aria-label="Toggle Menu" onClick={() => setMobileNavOpen((v) => !v)}>
              <span style={{ fontSize: "1.2rem" }}>☰</span>
            </button>
          </div>
        </div>

        <div className={`mobile-nav-panel${mobileNavOpen ? " open" : ""}`}>
          {[
            ["#simulator", "Stage Playground"],
            ["#pets", "Pet Roster (11 Pets)"],
            ["#superpowers", "Developer Stack"],
            ["#control-room", "macOS Control Room"],
            ["#sdk", "Build a Pet SDK"],
            ["#faq", "FAQ & Install"],
          ].map(([href, label]) => (
            <a key={href} href={href} className="nav-link" onClick={() => setMobileNavOpen(false)}>
              {label}
            </a>
          ))}
          <a
            href="https://github.com/jadhavgaurav/bitling/releases/latest"
            className="pixel-btn pixel-btn-sm"
            style={{ marginTop: "0.5rem", textAlign: "center" }}
          >
            Download for macOS
          </a>
        </div>
      </header>

      <section className="hero-section" id="hero">
        <div className="container hero-content">
          <div className="hero-tag">
            <span className="hero-tag-dot" />
            <span>v2.0 Live • 11 Legendary Pets • 100% Free &amp; Local</span>
          </div>

          <h1 className="hero-title">
            The Open-Source Desktop Pet for <span className="highlight-blue">Developers</span>
          </h1>

          <p className="hero-subtitle">
            A small companion that stands on your dock, lives on your git commits, hunts failing test bugs across
            your desktop, launches rockets on push, and cheers your Claude Code sessions.
          </p>

          <div className="hero-ctas">
            <a
              href="https://github.com/jadhavgaurav/bitling/releases/latest"
              className="pixel-btn"
              style={{ padding: "1rem 1.6rem", fontSize: "0.78rem" }}
            >
              Download for macOS (Universal)
            </a>
            <a href="#simulator" className="pixel-btn pixel-btn-light" style={{ padding: "1rem 1.6rem", fontSize: "0.78rem" }}>
              ▶ Try Live in Browser
            </a>
          </div>

          <div className="terminal-command-box">
            <div className="command-code">
              <span className="cmd-prompt">$ </span>curl -fsSL https://raw.githubusercontent.com/jadhavgaurav/bitling/main/install.sh | bash
            </div>
            <button type="button" className={`copy-btn${copiedInstall ? " copied" : ""}`} onClick={copyInstall}>
              {copiedInstall ? "COPIED!" : "COPY INSTALL"}
            </button>
          </div>

          <div className="hero-trust-row">
            <div className="trust-item"><span className="trust-icon">✓</span><span>Free & Open Source (MIT)</span></div>
            <div className="trust-item"><span className="trust-icon">🔒</span><span>100% Local (Zero Telemetry)</span></div>
            <div className="trust-item"><span className="trust-icon">⚡</span><span>Universal (Apple Silicon & Intel)</span></div>
            <div className="trust-item"><span className="trust-icon">🌱</span><span>0.1% CPU (Battery Friendly)</span></div>
          </div>
        </div>
      </section>

      <section className="simulator-section" id="simulator">
        <div className="container">
          <div className="section-header">
            <span className="section-pill">Interactive Stage</span>
            <h2 className="section-title">Play With Bitling In Your Browser</h2>
            <p className="section-subtitle">
              No install or signup required. Click to pat, drag to throw with ram-air parafoils, switch between 11
              species, and fire real developer events!
            </p>
          </div>

          <div className="sim-window">
            <div className="sim-titlebar">
              <div className="sim-dots">
                <span className="sim-dot dot-red" />
                <span className="sim-dot dot-yellow" />
                <span className="sim-dot dot-green" />
              </div>
              <div className="sim-title">
                {activePet.name} ({activePet.species}) • Stage 3
              </div>
              <div className="sim-status">
                <span
                  className="pulse-dot"
                  style={{ display: "inline-block", width: 6, height: 6, background: "#10B981", borderRadius: "50%" }}
                />
                <span>Live 60 FPS</span>
              </div>
            </div>

            <div className="pet-quick-bar">
              {QUICK_BAR_IDS.map((id) => {
                const pet = PETS_DATA.find((p) => p.id === id)!;
                return (
                  <button
                    key={id}
                    type="button"
                    className={`quick-pet-btn${activePetId === id ? " active" : ""}`}
                    onClick={() => switchSimulatorPet(id)}
                  >
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img src={pet.avatar} alt={pet.name} />
                    <span>{pet.name}</span>
                  </button>
                );
              })}
            </div>

            <div className="sim-stage-container">
              <iframe
                ref={iframeRef}
                src="/demo.html?embedded=1"
                className="sim-iframe"
                title="Bitling Live Interactive Canvas Stage"
              />
            </div>

            <div className="sim-controls-dock">
              <div style={{ display: "flex", alignItems: "center" }}>
                <span className="controls-label">Trigger Event:</span>
                <div className="sim-actions-row">
                  <button type="button" className="sim-trigger-btn sim-trigger-commit" onClick={() => triggerSimulatorAction("commit")}>+ Commit Code</button>
                  <button type="button" className="sim-trigger-btn sim-trigger-push" onClick={() => triggerSimulatorAction("push")}>🚀 Git Push</button>
                  <button type="button" className="sim-trigger-btn sim-trigger-fail" onClick={() => triggerSimulatorAction("fail")}>🪲 Test Fail</button>
                  <button type="button" className="sim-trigger-btn sim-trigger-pass" onClick={() => triggerSimulatorAction("pass")}>🎯 Fix Tests</button>
                  <button type="button" className="sim-trigger-btn sim-trigger-boss" onClick={() => triggerSimulatorAction("boss")}>👑 Boss Bug</button>
                </div>
              </div>

              <div className="sim-actions-row">
                <button
                  type="button"
                  className="sim-trigger-btn"
                  style={{ borderColor: "#EC4899", color: "#F472B6" }}
                  onClick={() => triggerSimulatorAction("pat")}
                >
                  💖 Pat Pet
                </button>
                <button
                  type="button"
                  className="sim-trigger-btn"
                  style={{ borderColor: "#F59E0B", color: "#FCD34D" }}
                  onClick={() => triggerSimulatorAction("voice")}
                >
                  💬 Voice Quote
                </button>
                <a href="/demo.html" target="_blank" className="sim-trigger-btn" style={{ borderColor: "#38BDF8", color: "#38BDF8", textDecoration: "none" }}>
                  ⤢ Fullscreen
                </a>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="gallery-section" id="pets">
        <div className="container">
          <div className="section-header">
            <span className="section-pill">The Companion Roster</span>
            <h2 className="section-title">Adopt Your Desktop Companion</h2>
            <p className="section-subtitle">
              11 unique species with distinct walk cycles, attack animations, sound effects, and commit-based
              evolution.
            </p>
          </div>

          <div className="gallery-filter-bar">
            {FILTERS.map((f) => (
              <button
                key={f.id}
                type="button"
                className={`filter-btn${filter === f.id ? " active" : ""}`}
                onClick={() => setFilter(f.id)}
              >
                {f.label}
              </button>
            ))}
          </div>

          <div className="pets-grid">
            {filteredPets.map((pet) => (
              <PetCard
                key={pet.id}
                pet={pet}
                onTry={(id) => {
                  switchSimulatorPet(id);
                  goToSimulator();
                }}
                onInspect={setModalPetId}
                onCopy={(text) => copyToClipboard(text, `Copied "${text}" to clipboard!`)}
              />
            ))}
          </div>
        </div>
      </section>

      <section className="superpowers-section" id="superpowers">
        <div className="container">
          <div className="section-header">
            <span className="section-pill">Built For Your Terminal</span>
            <h2 className="section-title">Developer Superpowers</h2>
            <p className="section-subtitle">
              Bitling doesn&apos;t sit idle. It connects directly to your daily development tools and turns your
              workspace into an interactive stage.
            </p>
          </div>

          <div className="superpowers-grid">
            <article className="feature-card">
              <div className="feature-header">
                <div className="feature-icon-box">📦</div>
                <div>
                  <h3 className="feature-title">Real-Time Git Activity</h3>
                  <p style={{ fontSize: "0.8rem", color: "var(--accent-blue)", fontWeight: 600 }}>ZERO-CONFIG REFLOG WATCHER</p>
                </div>
              </div>
              <p className="feature-desc">
                Bitling automatically scans your home directory and tails your repositories&apos; <code>.git/logs</code>{" "}
                reflog. No tokens, no GitHub account required, and no polling.
              </p>
              <div className="feature-media-box">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img src="/media/commit.png" alt="Bitling catching a commit node" loading="lazy" />
              </div>
              <ul style={{ fontSize: "0.85rem", color: "var(--text-secondary)", listStyle: "square", paddingLeft: "1.25rem" }}>
                <li><strong>Git commit:</strong> Drops a glowing node stamped with the short hash that your pet eats.</li>
                <li><strong>Git push:</strong> Launches a multi-stage rocket ascending into the clouds.</li>
                <li><strong>Git merge:</strong> Confetti explosion and celebratory merge feast.</li>
              </ul>
            </article>

            <article className="feature-card">
              <div className="feature-header">
                <div className="feature-icon-box">🪲</div>
                <div>
                  <h3 className="feature-title">Failing Test Bug Hunting</h3>
                  <p style={{ fontSize: "0.8rem", color: "var(--accent-red)", fontWeight: 600 }}>SCREEN-WIDE FAILING TEST NAMES</p>
                </div>
              </div>
              <p className="feature-desc">
                When tests fail in Pytest or CI, beetles crawl out across your entire desktop.{" "}
                <strong>Each beetle wears the actual name of the failing test</strong> so you know what broke
                instantly!
              </p>
              <div className="feature-media-box">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img src="/media/desktop-stage.png" alt="Beetles wearing test names and laser beam sniper strike" loading="lazy" />
              </div>
              <ul style={{ fontSize: "0.85rem", color: "var(--text-secondary)", listStyle: "square", paddingLeft: "1.25rem" }}>
                <li><strong>Laser sniper:</strong> When you re-run tests, your pet vaporizes <em>only the ones you actually fixed</em>!</li>
                <li><strong>Boss bugs:</strong> Major failures spawn an armored boss beetle with a health bar equal to the failure count.</li>
                <li><strong>Click-through:</strong> The overlay never intercepts mouse clicks or steals editor focus.</li>
              </ul>
            </article>

            <article className="feature-card">
              <div className="feature-header">
                <div className="feature-icon-box">🤖</div>
                <div>
                  <h3 className="feature-title">Claude Code AI Assistant</h3>
                  <p style={{ fontSize: "0.8rem", color: "var(--accent-yellow-dark)", fontWeight: 600 }}>LIVE SESSION TRANSCRIPT MONITOR</p>
                </div>
              </div>
              <p className="feature-desc">
                Bitling tails transcripts under <code>~/.claude/projects</code>. While Claude Code researches, edits
                files, and executes commands, your pet stays in lockstep.
              </p>
              <div className="feature-media-box">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img src="/media/claude.png" alt="Bitling displaying typing dots for Claude Code" loading="lazy" />
              </div>
              <ul style={{ fontSize: "0.85rem", color: "var(--text-secondary)", listStyle: "square", paddingLeft: "1.25rem" }}>
                <li><strong>Thinking dots:</strong> Antenna glows amber with animated dots while Claude reasons.</li>
                <li><strong>Permission wave:</strong> Waves both arms with a &quot;?&quot; chime when Claude needs your confirmation.</li>
                <li><strong>Task celebration:</strong> Arms up and sparkles when your agent finishes a turn.</li>
              </ul>
            </article>

            <article className="feature-card">
              <div className="feature-header">
                <div className="feature-icon-box">🪂</div>
                <div>
                  <h3 className="feature-title">Physics &amp; Ram-Air Parafoil</h3>
                  <p style={{ fontSize: "0.8rem", color: "var(--accent-green)", fontWeight: 600 }}>RAGDOLL THROW &amp; FLOATER FLIGHT</p>
                </div>
              </div>
              <p className="feature-desc">
                Pick up your pet with your mouse: its legs dangle naturally. Throw it across your desktop, and it
                tumbles, opens a ram-air parafoil, and lands upright on its feet!
              </p>
              <div className="feature-media-box">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img src="/media/parafoil.png" alt="Bitling descending under a ram-air parafoil" loading="lazy" />
              </div>
              <ul style={{ fontSize: "0.85rem", color: "var(--text-secondary)", listStyle: "square", paddingLeft: "1.25rem" }}>
                <li><strong>Walkers:</strong> Patrol the bottom edge of your screen and dock.</li>
                <li><strong>Floaters:</strong> Hover anywhere in mid-air and stay where you release them.</li>
                <li><strong>Needs meters:</strong> Pet, feed batteries/chips, or let your companion sleep at night.</li>
              </ul>
            </article>
          </div>
        </div>
      </section>

      <section className="control-room-section" id="control-room">
        <div className="container">
          <div className="control-room-grid">
            <div className="room-visual-card">
              <div className="pixel-card" style={{ padding: "1rem", background: "#0B0F17" }}>
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src="/media/hero.png"
                  alt="Bitling Native macOS Control Room"
                  style={{ width: "100%", borderRadius: 4, border: "1.5px solid #334155" }}
                />
              </div>
            </div>

            <div>
              <span className="section-pill">The Native Control Room</span>
              <h2 className="section-title">Everything Your Companion Sees, In One Place</h2>
              <p className="section-subtitle" style={{ marginBottom: "2rem" }}>
                Click Bitling&apos;s Dock icon or run <code>bitling panel</code> to open the native control room.
                Zero telemetry, zero network tracking.
              </p>

              <div className="room-features-list">
                {[
                  ["Live Activity Stream & 12-Hour Timeline", "See every commit hash, push, merge, and Claude turn logged in real time with color-coded event ticks."],
                  ["Three Needs Gauges & Growth Stage", "Check your companion's Energy, Hunger, and Happiness levels. Watch them grow into Overclocked and Ultra forms!"],
                  ["Setup & Optional Global Git Hooks", "Configure repo watchers, toggle screen-wide bug swarms, set sound preferences, or enable one-step global git hooks."],
                ].map(([title, desc], i) => (
                  <div className="room-feature-item" key={title}>
                    <div className="room-feature-num">{i + 1}</div>
                    <div className="room-feature-text">
                      <h4>{title}</h4>
                      <p>{desc}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="sdk-section" id="sdk">
        <div className="container">
          <div className="section-header">
            <span className="section-pill" style={{ color: "#60A5FA" }}>Developer Extension Guide</span>
            <h2 className="section-title">Create Your Own Pet in 50 Lines</h2>
            <p className="section-subtitle">
              Adding a species to Bitling is a pure drawing and a voice definition, not a complex fork. Needs,
              physics, and speech bubbles are shared.
            </p>
          </div>

          <div className="sdk-code-window">
            <div className="code-titlebar">
              <span className="code-filename">apps/macos/web/bitling.html — defineSpecies() API</span>
              <span style={{ fontSize: "0.7rem", color: "#79C0FF", fontFamily: "var(--font-mono)" }}>JavaScript</span>
            </div>
            <pre className="code-content">
              <code>{`// Register a new species in Bitling
defineSpecies({
  id: 'newt',
  name: 'Newt',
  kind: 'ground',                  // or 'float'
  blurb: 'A speedy salamander with elemental flame breath.',
  accent: '#7ee7d7',
  radius: [46, 44, 52, 60],          // body radius per growth stage
  reach: () => 3.4,                 // speech bubble clearance (measured)
  half: (r) => r * 1.8,             // window boundary width
  draw: () => drawNewt(),           // your canvas drawing function
  trail: null,                      // 'thruster' or 'flamejet'
  attack: {
    style: 'beam',
    charge: 0.3,
    origin: (r) => [{ x: pet.x, y: pet.y }],
    draw(r, k) { /* custom canvas laser / projectile */ }
  },
  voice: {
    hello: ['Ready to code!', 'Newt is on watch.'],
    zapped: ['Bug squashed!', 'Clean hit!'],
    testPass: ['All green! Clean build.']
  }
});`}</code>
            </pre>
          </div>
        </div>
      </section>

      <section className="comparison-section" id="comparison">
        <div className="container">
          <div className="section-header">
            <span className="section-pill">Feature Comparison</span>
            <h2 className="section-title">Why Developers Love Bitling</h2>
            <p className="section-subtitle">How Bitling compares to OpenPets and traditional desktop pets.</p>
          </div>

          <div className="table-wrapper">
            <table className="comp-table">
              <thead>
                <tr>
                  <th>Feature</th>
                  <th className="col-bitling">Bitling</th>
                  <th>OpenPets</th>
                  <th>Generic Desktop Pets</th>
                </tr>
              </thead>
              <tbody>
                {[
                  ["In-Browser Live Simulation", "✓ Full 60 FPS Canvas Engine", "✓ Spritesheet Preview", "✗ Video / Mockups only"],
                  ["Real-Time Git Reflog Tracking", "✓ Native zero-config watcher", "✗ Plugin required", "✗ None"],
                  ["Failing Test Bug Swarms", "✓ Screen-wide bugs with test names", "✗ None", "✗ None"],
                  ["Fixed-Test Sniper Lasers", "✓ Snipes only tests you fixed", "✗ None", "✗ None"],
                  ["Claude Code AI Session Hooks", "✓ Built-in transcript tailer", "✗ Plugin required", "✗ None"],
                  ["Ragdoll Drag & Parachute Physics", "✓ Real ram-air ram parafoil", "✗ Spritesheet frames", "✗ None"],
                  ["Boss Bug Battles", "✓ Armored bosses with health bars", "✗ None", "✗ None"],
                  ["Privacy & Zero Telemetry", "✓ 100% Local-first, zero telemetry", "✓ Local-first", "Varies"],
                ].map(([feature, bitling, openpets, generic]) => (
                  <tr key={feature}>
                    <td><strong>{feature}</strong></td>
                    <td className="col-bitling">
                      <span className={bitling.startsWith("✓") ? "comp-check" : "comp-cross"}>{bitling}</span>
                    </td>
                    <td><span className={openpets.startsWith("✓") ? "comp-check" : "comp-cross"}>{openpets}</span></td>
                    <td><span className={generic.startsWith("✓") ? "comp-check" : "comp-cross"}>{generic}</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>

      <section className="faq-section" id="faq">
        <div className="container">
          <div className="section-header">
            <span className="section-pill">Got Questions?</span>
            <h2 className="section-title">Frequently Asked Questions</h2>
            <p className="section-subtitle">Everything you need to know about installing, running, and configuring Bitling.</p>
          </div>

          <div className="faq-list">
            {FAQS.map((item, i) => (
              <div className={`faq-item${faqOpen === i ? " active" : ""}`} key={item.q}>
                <button type="button" className="faq-question" onClick={() => setFaqOpen(faqOpen === i ? -1 : i)}>
                  <span>{item.q}</span>
                  <span className="faq-icon">+</span>
                </button>
                <div className="faq-answer">{item.a}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      <footer className="site-footer">
        <div className="container">
          <div className="footer-top">
            <div className="footer-brand">
              <h3>🤖 BITLING</h3>
              <p>
                The open-source desktop pet for developers. Built for macOS, living on your dev activity, and
                tracking git, pytest, and Claude Code.
              </p>
              <div style={{ marginTop: "1.25rem" }}>
                <a href="https://github.com/jadhavgaurav/bitling/releases/latest" className="pixel-btn pixel-btn-sm pixel-btn-yellow">
                  Download Latest Release
                </a>
              </div>
            </div>

            <div className="footer-col">
              <h4>Navigation</h4>
              <ul>
                <li><a href="#simulator">Stage Playground</a></li>
                <li><a href="#pets">Companion Gallery</a></li>
                <li><a href="#superpowers">Developer Stack</a></li>
                <li><a href="#control-room">Control Room</a></li>
                <li><a href="#sdk">Build a Pet</a></li>
                <li><a href="#faq">FAQ</a></li>
              </ul>
            </div>

            <div className="footer-col">
              <h4>Resources</h4>
              <ul>
                <li><a href="/demo.html" target="_blank">Full Demo Stage</a></li>
                <li><a href="https://github.com/jadhavgaurav/bitling" target="_blank">GitHub Repository</a></li>
                <li><a href="https://github.com/jadhavgaurav/bitling/releases" target="_blank">Release Notes</a></li>
                <li><a href="https://github.com/jadhavgaurav/bitling/blob/main/LICENSE" target="_blank">MIT License</a></li>
              </ul>
            </div>

            <div className="footer-col">
              <h4>Quick Install</h4>
              <p style={{ fontSize: "0.8rem", marginBottom: "0.5rem", color: "#94A3B8" }}>Run in Terminal:</p>
              <div
                style={{
                  background: "#161B22",
                  border: "1px solid #334155",
                  padding: "0.5rem",
                  borderRadius: 4,
                  fontFamily: "var(--font-mono)",
                  fontSize: "0.72rem",
                  color: "#38BDF8",
                  wordBreak: "break-all",
                }}
              >
                curl -fsSL https://raw.githubusercontent.com/jadhavgaurav/bitling/main/install.sh | bash
              </div>
            </div>
          </div>

          <div className="footer-bottom">
            <div>© 2026 Bitling Project. Open source under the MIT License.</div>
            <div>Crafted with 💖 for developers worldwide.</div>
          </div>
        </div>
      </footer>

      <PetModal
        pet={modalPet}
        onClose={() => setModalPetId(null)}
        onTry={(id) => {
          switchSimulatorPet(id);
          goToSimulator();
        }}
        onCopy={(text) => copyToClipboard(text, `Copied "${text}" to clipboard!`)}
      />

      <Toast message={toast} />
    </>
  );
}

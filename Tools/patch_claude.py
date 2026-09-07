#!/usr/bin/env python3
"""One-off migration: Claude Code session reactions (working face, prompts, tools, done, notify).

Applied to web/bitling.html. Idempotent-guarded, asserts every anchor.
"""
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent / "web" / "bitling.html"
s = SRC.read_text(encoding="utf-8")
if "claude-prompt" in s:
    raise SystemExit("already applied")


def patch(old: str, new: str) -> None:
    global s
    if s.count(old) != 1:
        raise SystemExit(f"anchor found {s.count(old)}x, expected 1:\n{old[:160]}")
    s = s.replace(old, new)


# ---------------------------------------------------------------- copy + state
patch("    deployFail: ['deploy failed. rollback?', 'prod said no', 'abort abort'],",
      "    deployFail: ['deploy failed. rollback?', 'prod said no', 'abort abort'],\n"
      "    onIt: ['on it', 'thinking…', 'reading the code', 'let me look', 'hmm, okay'],\n"
      "    working: ['still thinking…', 'crunching…', 'almost there', 'lots of files…'],\n"
      "    done: ['done! check it', 'finished, human', 'your turn', 'ready for review', 'ta-da'],\n"
      "    needsYou: ['Claude needs you!', 'permission? over here!', 'psst, it is waiting'],")
patch("      commits: 0, pushes: 0, bugs: 0, lastCommitAt: 0,\n    };",
      "      commits: 0, pushes: 0, bugs: 0, lastCommitAt: 0, prompts: 0,\n    };")
patch("    screenText: '', screenTint: '', screenT: 0, shake: 0, deploying: false, deployProgress: 0,\n  };",
      "    working: false, workT: 0, wave: 0, chatterAt: 0,\n"
      "    screenText: '', screenTint: '', screenT: 0, shake: 0, deploying: false, deployProgress: 0,\n  };")

# ---------------------------------------------------------------- timers
patch("    for (const k of ['chew', 'happy', 'surprise', 'yawn', 'dizzy', 'glance', 'shake', 'screenT']) pet[k] = Math.max(0, pet[k] - dt);",
      "    for (const k of ['chew', 'happy', 'surprise', 'yawn', 'dizzy', 'glance', 'shake', 'screenT', 'wave', 'workT']) pet[k] = Math.max(0, pet[k] - dt);\n"
      "    if (pet.working && pet.workT <= 0) pet.working = false;")

# ---------------------------------------------------------------- look: thinking gaze after cursor, before wander
patch("""        } else if (pointer.over && pet.t - pointer.lastT < 3) {
          pet.lookT.x = clamp((pointer.x - pet.x) / (r * 3), -1, 1);
          pet.lookT.y = clamp((pointer.y - (pet.y - r)) / (r * 3), -1, 1);
        } else {""", """        } else if (pointer.over && pet.t - pointer.lastT < 3) {
          pet.lookT.x = clamp((pointer.x - pet.x) / (r * 3), -1, 1);
          pet.lookT.y = clamp((pointer.y - (pet.y - r)) / (r * 3), -1, 1);
        } else if (pet.working) {
          pet.lookT.x = -0.5 + 0.25 * Math.sin(pet.t * 0.7);
          pet.lookT.y = -0.5;
        } else {""")

# ---------------------------------------------------------------- idle: no strolling while Claude works
patch("    if (state.asleep || pet.held) return;\n    const r = Math.random();",
      "    if (state.asleep || pet.held) return;\n"
      "    if (pet.working) { if (Math.random() < 0.35) say(pick(LINES.working), 2400); return; }\n"
      "    const r = Math.random();")

# ---------------------------------------------------------------- drawing: antenna, arms, thinking dots, spinner
patch("    else if (state.full < 30) tipColor = 'hsl(40, 95%, 60%)';\n    else if (asleep) tipColor = `hsl(${hue}, 20%, 55%)`;",
      "    else if (pet.wave > 0) tipColor = `hsl(200, 95%, ${55 + 20 * Math.abs(Math.sin(t * 12))}%)`;\n"
      "    else if (pet.working) tipColor = `hsl(25, 95%, ${52 + 14 * Math.sin(t * 5)}%)`;\n"
      "    else if (state.full < 30) tipColor = 'hsl(40, 95%, 60%)';\n"
      "    else if (asleep) tipColor = `hsl(${hue}, 20%, 55%)`;")
patch("      if (carried) theta = 2.9;\n      else if (pet.happy > 0) theta = 2.2 + Math.sin(t * 12) * 0.35;",
      "      if (carried) theta = 2.9;\n"
      "      else if (pet.wave > 0) theta = 2.5 + Math.sin(t * 14) * 0.5 * (sgn === 1 ? 1 : 0.3);\n"
      "      else if (pet.happy > 0) theta = 2.2 + Math.sin(t * 12) * 0.35;")
patch("""    const my = ey + r * 0.38;
    if (pet.chew > 0) {""", """    const my = ey + r * 0.38;
    if (pet.wave > 0 && !f.asleep) {
      ctx.font = `700 ${Math.round(r * 0.34)}px ui-monospace, Menlo, monospace`;
      ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
      ctx.fillText('?', 0, my);
    } else if (pet.working && !f.asleep && pet.chew <= 0 && pet.yawn <= 0 && pet.surprise <= 0 && !erroring) {
      for (let i = -1; i <= 1; i++) {
        const phase = Math.sin(t * 6 - i * 1.1);
        ctx.globalAlpha = 0.45 + 0.55 * (phase * 0.5 + 0.5);
        ctx.beginPath(); ctx.arc(i * r * 0.16, my - phase * r * 0.02, r * 0.045, 0, Math.PI * 2); ctx.fill();
      }
      ctx.globalAlpha = 1;
    } else if (pet.chew > 0) {""")
patch("""    if (pet.deploying) {
      const bw = sw * 0.72, bh = r * 0.13, by = hy + sh / 2 - r * 0.24;""", """    if (pet.working && !asleep) {
      const cx = sw / 2 - r * 0.17, cy = hy - sh / 2 + r * 0.17;
      ctx.lineWidth = Math.max(1, r * 0.04);
      ctx.beginPath(); ctx.arc(cx, cy, r * 0.08, t * 6, t * 6 + 4.2); ctx.stroke();
    }
    if (pet.deploying) {
      const bw = sw * 0.72, bh = r * 0.13, by = hy + sh / 2 - r * 0.24;""")

# ---------------------------------------------------------------- events
patch("    const loud = ['commit', 'push', 'merge', 'test-failed', 'deploy-started', 'deploy-finished', 'deploy-failed'].includes(kind);",
      "    const loud = ['commit', 'push', 'merge', 'test-failed', 'deploy-started', 'deploy-finished', 'deploy-failed', 'claude-prompt', 'claude-notify'].includes(kind);")
patch("""      case 'say':
        say(shortMessage(msg) || 'hi', 3000);
        break;
      default:
        break;
    }""", """      case 'say':
        say(shortMessage(msg) || 'hi', 3000);
        break;
      case 'claude-session-start': {
        const project = String(ev.name || ev.repo || '').trim();
        pet.glance = 1.2;
        say(project ? `new session in ${project}` : 'new Claude session', 2800);
        break;
      }
      case 'claude-prompt': {
        state.prompts += 1;
        pet.working = true; pet.workT = 120; pet.wave = 0;
        pet.happy = 0.5;
        say(pick(LINES.onIt), 2200);
        break;
      }
      case 'claude-tool': {
        pet.working = true; pet.workT = 90;
        const tool = String(ev.name || '');
        const detail = String(ev.message || '').toLowerCase();
        if (pet.t - pet.chatterAt > 12 && Math.random() < 0.5) {
          pet.chatterAt = pet.t;
          let line = 'working…';
          if (/^(Edit|Write|MultiEdit|NotebookEdit)$/.test(tool)) line = 'editing files…';
          else if (tool === 'Bash') line = /pytest|jest|vitest|npm (run )?test|go test|cargo test/.test(detail) ? 'running tests…' : /git /.test(detail) ? 'git things…' : 'running commands…';
          else if (/^(Read|Grep|Glob)$/.test(tool)) line = 'reading around…';
          else if (tool === 'Agent') line = 'sent a helper';
          else if (/^(WebSearch|WebFetch)$/.test(tool)) line = 'searching the web…';
          else if (tool === 'Artifact') line = 'publishing something';
          say(line, 2000);
        }
        break;
      }
      case 'claude-tool-error': {
        if (Math.random() < 0.35) {
          pet.screenTint = 'error'; pet.screenText = '!'; pet.screenT = 0.7; pet.shake = 0.25;
          say(pick(['hmm, that errored', 'oops', 'retrying, probably']), 1800);
        }
        break;
      }
      case 'claude-done': {
        pet.working = false; pet.workT = 0;
        pet.happy = 1.4;
        state.joy = clamp(state.joy + 2);
        spawn('spark', pet.x, pet.y - petR() * 1.8, 6, { spread: petR() * 0.6, vx: 70, vy: -80, size: 7, hue: 25, dur: 0.9 });
        say(pick(LINES.done), 3000);
        break;
      }
      case 'claude-notify': {
        pet.working = false;
        pet.wave = 4;
        audio.ok();
        say(shortMessage(msg) || pick(LINES.needsYou), 4200);
        break;
      }
      case 'claude-idle':
        pet.working = false;
        say('waiting on you…', 2600);
        break;
      case 'claude-session-end':
        pet.working = false;
        say('session over. nap?', 2600);
        break;
      default:
        break;
    }""")

SRC.write_text(s, encoding="utf-8")
print("patched", SRC)

import base64
from pathlib import Path

def main():
    final_dir = Path('/tmp/pika_final')
    sound_files = {
        'pikaPika': final_dir / 'pika_pika.mp3',
        'pikaChuuu': final_dir / 'pika_chuuu.mp3',
        'pikaChu': final_dir / 'pikachu.mp3',
        'pikaQuestion': final_dir / 'pika_question.mp3',
        'pikaSad': final_dir / 'pika_sad.mp3',
        'pikaThunder': final_dir / 'pika_thunder.mp3',
    }

    b64_dict = {}
    for key, path in sound_files.items():
        with open(path, 'rb') as f:
            b64 = base64.b64encode(f.read()).decode('ascii')
            b64_dict[key] = f"data:audio/mp3;base64,{b64}"
            print(f"{key}: {len(b64)} chars")

    bitling_path = Path("web/bitling.html")
    content = bitling_path.read_text(encoding="utf-8")

    # Build the audio definition
    audio_obj_code = """  const PIKA_AUDIO = {
"""
    for key, uri in b64_dict.items():
        audio_obj_code += f"    {key}: '{uri}',\n"
    audio_obj_code += """  };
  const pikaBuffers = {};
  function getPikaBuffer(key) {
    if (pikaBuffers[key]) return Promise.resolve(pikaBuffers[key]);
    if (!PIKA_AUDIO[key]) return Promise.resolve(null);
    audio.ensure();
    if (!audio.ctx) return Promise.resolve(null);
    try {
      const b64 = PIKA_AUDIO[key].split(',')[1];
      const binary = atob(b64);
      const len = binary.length;
      const bytes = new Uint8Array(len);
      for (let i = 0; i < len; i++) bytes[i] = binary.charCodeAt(i);
      const arrayBuf = bytes.buffer.slice(0);
      return new Promise((resolve) => {
        const p = audio.ctx.decodeAudioData(
          arrayBuf,
          (buf) => { pikaBuffers[key] = buf; resolve(buf); },
          () => resolve(null)
        );
        if (p && typeof p.then === 'function') {
          p.then((buf) => { pikaBuffers[key] = buf; resolve(buf); }).catch(() => resolve(null));
        }
      });
    } catch (_) {
      return Promise.resolve(null);
    }
  }

  // ---------------------------------------------------------------- audio
  const audio = {
    ctx: null,
    ensure() {
      if (!this.ctx) {
        try { this.ctx = new (window.AudioContext || window.webkitAudioContext)(); } catch (_) { this.ctx = null; }
      }
      if (this.ctx && this.ctx.state === 'suspended') this.ctx.resume().catch(() => {});
    },
    playPika(key, vol = 0.88) {
      if (!state.sound) return;
      this.ensure();
      getPikaBuffer(key).then((buf) => {
        if (buf && this.ctx) {
          try {
            const src = this.ctx.createBufferSource();
            src.buffer = buf;
            const g = this.ctx.createGain();
            g.gain.setValueAtTime(vol, this.ctx.currentTime);
            src.connect(g).connect(this.ctx.destination);
            src.start(0);
            return;
          } catch (_) {}
        }
        try {
          if (PIKA_AUDIO[key]) {
            const snd = new Audio(PIKA_AUDIO[key]);
            snd.volume = vol;
            snd.play().catch(() => {});
          }
        } catch (_) {}
      });
    },
    preloadPika() {
      if (typeof window !== 'undefined' && window.atob) {
        Object.keys(PIKA_AUDIO).forEach((k) => getPikaBuffer(k));
      }
    },"""

    # Replace audio object declaration
    old_audio_start = "  // ---------------------------------------------------------------- audio\n  const audio = {\n    ctx: null,\n    ensure() {\n      if (!this.ctx) {\n        try { this.ctx = new (window.AudioContext || window.webkitAudioContext)(); } catch (_) { this.ctx = null; }\n      }\n      if (this.ctx && this.ctx.state === 'suspended') this.ctx.resume().catch(() => {});\n    },"
    if old_audio_start not in content:
        raise SystemExit("Could not find old_audio_start in bitling.html")

    content = content.replace(old_audio_start, audio_obj_code, 1)

    # Now replace pikaPika and other audio methods
    old_audio_methods = """    pikaPika() {
      this.tone(920, 1280, 0.09, 'triangle', 0.12);
      setTimeout(() => this.tone(1180, 780, 0.11, 'sine', 0.10), 95);
      setTimeout(() => this.tone(960, 1320, 0.09, 'triangle', 0.12), 230);
      setTimeout(() => this.tone(1220, 820, 0.13, 'sine', 0.10), 330);
    },
    pikaChuuu() {
      this.tone(860, 1180, 0.13, 'triangle', 0.12);
      setTimeout(() => this.tone(1000, 1450, 0.19, 'sine', 0.13), 150);
      setTimeout(() => {
        this.tone(1720, 560, 0.40, 'sawtooth', 0.14);
        this.tone(1220, 400, 0.42, 'triangle', 0.11);
      }, 370);
      setTimeout(() => this.thunderbolt(), 690);
    },
    pikaChu() {
      this.tone(920, 1220, 0.09, 'triangle', 0.12);
      setTimeout(() => this.tone(1120, 1380, 0.08, 'sine', 0.11), 100);
      setTimeout(() => this.tone(1380, 680, 0.16, 'sawtooth', 0.09), 190);
    },
    pikaQuestion() {
      this.tone(850, 1420, 0.18, 'triangle', 0.11);
    },"""

    new_audio_methods = """    pikaPika() {
      this.playPika('pikaPika', 0.92);
    },
    pikaChuuu() {
      this.playPika('pikaChuuu', 0.95);
    },
    pikaChu() {
      this.playPika('pikaChu', 0.90);
    },
    pikaQuestion() {
      this.playPika('pikaQuestion', 0.88);
    },
    pikaSad() {
      this.playPika('pikaSad', 0.85);
    },
    pikaThunder() {
      this.playPika('pikaThunder', 0.95);
    },"""

    if old_audio_methods not in content:
        raise SystemExit("Could not find old_audio_methods in bitling.html")

    content = content.replace(old_audio_methods, new_audio_methods, 1)

    # Update say() handling
    old_say = """    if (state.species === 'pikachu') {
      if (text.includes('CHUU') || text.includes('100,000')) audio.pikaChuuu();
      else if (text.includes('?')) audio.pikaQuestion();
      else if (text.includes('Pikachu')) audio.pikaChu();
      else audio.pikaPika();
    }"""

    new_say = """    if (state.species === 'pikachu') {
      const up = (text || '').toUpperCase();
      if (up.includes('CHUU') || up.includes('THUNDER') || up.includes('100,000') || up.includes('ATTACK')) audio.pikaChuuu();
      else if (up.includes('?')) audio.pikaQuestion();
      else if (up.includes('PIKACHU') || up.includes('PIKA CHU')) audio.pikaChu();
      else if (up.includes('SAD') || up.includes('OUCH') || up.includes('CRY') || up.includes('HURT')) audio.pikaSad();
      else audio.pikaPika();
    }"""

    if old_say not in content:
        raise SystemExit("Could not find old_say in bitling.html")

    content = content.replace(old_say, new_say, 1)

    # Update boot to preload pika buffers
    old_boot = "  audio.ensure();\n  resize();"
    new_boot = "  audio.ensure();\n  audio.preloadPika();\n  resize();"
    if old_boot in content:
        content = content.replace(old_boot, new_boot, 1)

    bitling_path.write_text(content, encoding="utf-8")
    print("Successfully patched web/bitling.html with authentic Pikachu anime voices!")

if __name__ == '__main__':
    main()

from pathlib import Path

bitling_path = Path("web/bitling.html")
content = bitling_path.read_text(encoding="utf-8")

# 1. Update playPika in audio object to include debouncing and cleanly stopping previous buffers
old_play_pika = """    playPika(key, vol = 0.88) {
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
    },"""

new_play_pika = """    playPika(key, vol = 0.92) {
      if (!state.sound) return;
      this.ensure();
      const now = performance.now();
      if (this._lastPikaKey === key && now - (this._lastPikaTime || 0) < 350) return;
      this._lastPikaKey = key;
      this._lastPikaTime = now;
      getPikaBuffer(key).then((buf) => {
        if (buf && this.ctx) {
          try {
            if (this._pikaSrc) {
              try { this._pikaSrc.stop(); } catch (_) {}
              this._pikaSrc = null;
            }
            const src = this.ctx.createBufferSource();
            src.buffer = buf;
            const g = this.ctx.createGain();
            g.gain.setValueAtTime(vol, this.ctx.currentTime);
            src.connect(g).connect(this.ctx.destination);
            src.start(0);
            this._pikaSrc = src;
            src.onended = () => { if (this._pikaSrc === src) this._pikaSrc = null; };
            return;
          } catch (_) {}
        }
        try {
          if (PIKA_AUDIO[key]) {
            if (this._pikaAudio) {
              try { this._pikaAudio.pause(); } catch (_) {}
              this._pikaAudio = null;
            }
            const snd = new Audio(PIKA_AUDIO[key]);
            snd.volume = vol;
            this._pikaAudio = snd;
            snd.play().catch(() => {});
          }
        } catch (_) {}
      });
    },"""

if old_play_pika not in content:
    raise SystemExit("old_play_pika not found in bitling.html")
content = content.replace(old_play_pika, new_play_pika, 1)

# 2. Update Pikachu voice lines to include bossDown and squash
old_voice_lines = """    voice: {
      hello: ['Pika-pika!', 'Pikachu!', 'Pika?'],
      happy: ['Pikachu!!', 'Pika-chuu!', 'Pika! (wagging tail)', 'Pi-ka!'],
      hungry: ['Pika... (hungry)', 'Chuuu...', 'Pika pika berry!'],
      sleepy: ['Chuuu... (yawn)', 'Pika... zzz', 'curling into tail'],
      bored: ['Pika? (ear twitch)', 'Chuu...', 'sparking cheeks quietly'],
      petted: ['Pikaaa! (blushing)', 'Chuuu~', 'Pika-pi! (happy wiggles)'],
      eat: ['Chomp! Pika!', 'munch munch', 'delish! Pika!'],
      zapped: ['Pika-CHUUU! 100,000 Volts!', 'Zapped! Pika!', 'Bug fainted!'],
      play: ['Pika-pika! (running in circles)', 'Catch me! Pika!', 'Cheeks sparking!'],
      working: ['Pika... (charging electric focus)', 'Chuuu...', 'steady sparks'],
      done: ['Pikachu!!', 'All bugs fainted!', 'Build cleared, Pika!'],
      testFail: ['Pika?! Failing tests!', 'Cheeks glowing red!', 'Pika... CHUU!'],
      testPass: ['Pikachu!! All green!', 'Pika-pika green build!'],
      shipped: ['Pika-CHUUU! Deployed to the stars!', 'Rocket away, Pika!'],
      held: ['Pikaaa! Put me down!', 'Watch the tail! Pika!', 'Static tingling!'],
      landed: ['Pika! Landed on four paws!', 'Pikachu! Safe on the ground.'],
      night: ['Pika... (tail glowing gently)', 'quiet night in Kanto', 'sweet dreams, Pika'],
    },"""

new_voice_lines = """    voice: {
      hello: ['Pika-pika!', 'Pikachu!', 'Pika?'],
      happy: ['Pikachu!!', 'Pika-chuu!', 'Pika! (wagging tail)', 'Pi-ka!'],
      hungry: ['Pika... (hungry)', 'Chuuu...', 'Pika pika berry!'],
      sleepy: ['Chuuu... (yawn)', 'Pika... zzz', 'curling into tail'],
      bored: ['Pika? (ear twitch)', 'Chuu...', 'sparking cheeks quietly'],
      petted: ['Pikaaa! (blushing)', 'Chuuu~', 'Pika-pi! (happy wiggles)'],
      eat: ['Chomp! Pika!', 'munch munch', 'delish! Pika!'],
      zapped: ['Pika-pika! Gotcha!', 'Zapped! Pika!', 'Bug fainted! Pikachu!'],
      bossDown: ['Pika-CHUUU! 100,000 Volts!', 'Thunderbolt! Big bug down!', 'Pika-CHUUU!'],
      squash: ['Pikachu! Gotcha!', 'Pika! Squashed!', 'Pika-pika!'],
      play: ['Pika-pika! (running in circles)', 'Catch me! Pika!', 'Cheeks sparking!'],
      working: ['Pika... (charging electric focus)', 'Chuuu...', 'steady sparks'],
      done: ['Pikachu!!', 'All bugs fainted!', 'Build cleared, Pika!'],
      testFail: ['Pika?! Failing tests!', 'Cheeks glowing red!', 'Pika... CHUU!'],
      testPass: ['Pikachu!! All green!', 'Pika-pika green build!'],
      shipped: ['Pika-CHUUU! Deployed to the stars!', 'Rocket away, Pika!'],
      held: ['Pikaaa! Put me down!', 'Watch the tail! Pika!', 'Static tingling!'],
      landed: ['Pika! Landed on four paws!', 'Pikachu! Safe on the ground.'],
      night: ['Pika... (tail glowing gently)', 'quiet night in Kanto', 'sweet dreams, Pika'],
    },"""

if old_voice_lines not in content:
    raise SystemExit("old_voice_lines not found in bitling.html")
content = content.replace(old_voice_lines, new_voice_lines, 1)

# 3. Update bug attack firing so Pikachu shouts at the EXACT moment of firing & killing the bug
old_combat_firing = """          if (shotStyle === 'kamehameha') audio.kameFire();
          else if (shotStyle === 'kiball') audio.kiBlast();
          else if (shotStyle === 'thunderbolt') audio.thunderbolt();
          else if (shotStyle === 'electroball') audio.electroBall();"""

new_combat_firing = """          if (shotStyle === 'kamehameha') audio.kameFire();
          else if (shotStyle === 'kiball') audio.kiBlast();
          else if (shotStyle === 'thunderbolt') {
            audio.thunderbolt();
            if (state.species === 'pikachu') audio.pikaChuuu();
          } else if (shotStyle === 'electroball') {
            audio.electroBall();
            if (state.species === 'pikachu') audio.pikaPika();
          }"""

if old_combat_firing not in content:
    raise SystemExit("old_combat_firing not found in bitling.html")
content = content.replace(old_combat_firing, new_combat_firing, 1)

# 4. In charging start, don't prematurely shout before killing the bug; play gathering charge sound
old_charge_start = """        if (resolved && resolved.sound === 'kameCharge') audio.kameCharge();
        else if (resolved && resolved.sound === 'pikaChuuu') audio.pikaChuuu();
        else if (resolved && resolved.sound === 'pikaPika') audio.pikaPika();
        else audio.charge();"""

new_charge_start = """        if (resolved && resolved.sound === 'kameCharge') audio.kameCharge();
        else audio.charge();"""

if old_charge_start not in content:
    raise SystemExit("old_charge_start not found in bitling.html")
content = content.replace(old_charge_start, new_charge_start, 1)

# 5. In petPet(), don't double play voice if say(line('petted')) is also called
old_pet_pet = """    if (state.species === 'pikachu') audio.pikaPika();
    else audio.squeak();
    spawn('heart', pet.x, pet.y - petR() * 1.9, 4, { spread: petR() * 0.6, vx: 40, vy: -90, size: 10 });
    if (Math.random() < 0.6) say(line('petted'));"""

new_pet_pet = """    const willSay = Math.random() < 0.6;
    if (state.species === 'pikachu') {
      if (!willSay) audio.pikaPika();
    } else {
      audio.squeak();
    }
    spawn('heart', pet.x, pet.y - petR() * 1.9, 4, { spread: petR() * 0.6, vx: 40, vy: -90, size: 10 });
    if (willSay) say(line('petted'));"""

if old_pet_pet not in content:
    raise SystemExit("old_pet_pet not found in bitling.html")
content = content.replace(old_pet_pet, new_pet_pet, 1)

# 6. In handleGitEvent for 'say', handle ev.message or ev.text cleanly with proper length
old_case_say = """      case 'say':
        say(shortMessage(msg) || 'hi', 3000);
        break;"""

new_case_say = """      case 'say': {
        const text = String(ev.message || ev.text || '').trim().split('\\n')[0].slice(0, 60);
        say(text || 'Pika-pika!', 3000);
        break;
      }"""

if old_case_say not in content:
    raise SystemExit("old_case_say not found in bitling.html")
content = content.replace(old_case_say, new_case_say, 1)

bitling_path.write_text(content, encoding="utf-8")
print("Successfully updated audio timing in web/bitling.html!")

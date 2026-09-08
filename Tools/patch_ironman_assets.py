#!/usr/bin/env python3
"""Process Iron Man sprites and audio, producing base64 assets for bitling.html."""
import os
import base64
from PIL import Image

OUT_DIR = '/tmp/ironman_processed_sprites'
os.makedirs(OUT_DIR, exist_ok=True)

# 1. Process Sprites
# Frames:
# - idle: iron_fly_0 (cropped tightly)
# - fly: iron_fly_1 (flight with thruster pulse)
# - stance: IronManColor1Stance_0 (ready stance)
# - charge: iron_charge_2 (raised palm gathering plasma orb)
# - inspect: iron_powa_10 (gauntlet computer interface)
# - salute: iron_wins_4 (victory salute)

sprites_src = {
    'idle': '/tmp/ironman_assets/extracted/iron_fly_0.png',
    'fly': '/tmp/ironman_assets/extracted/iron_fly_1.png',
    'stance': '/tmp/ironman_assets/extracted/IronManColor1Stance_0.png',
    'charge': '/tmp/ironman_assets/extracted/iron_charge_2.png',
    'inspect': '/tmp/ironman_assets/extracted/iron_powa_10.png',
    'salute': '/tmp/ironman_assets/extracted/iron_wins_4.png'
}

b64_sprites = {}
for name, path in sprites_src.items():
    im = Image.open(path).convert('RGBA')
    bbox = im.getbbox()
    if bbox:
        cropped = im.crop(bbox)
    else:
        cropped = im
    out_path = os.path.join(OUT_DIR, f'{name}.png')
    cropped.save(out_path, format='PNG', optimize=True)
    with open(out_path, 'rb') as f:
        b64 = base64.b64encode(f.read()).decode('ascii')
        b64_sprites[name] = f'data:image/png;base64,{b64}'
    print(f"Processed sprite {name}: {cropped.size}, {os.path.getsize(out_path)} bytes")

# 2. Process Audio
audio_src = {
    'iroRepulsor': '/tmp/ironman_processed_audio/iro_repulsor.mp3',
    'iroUnibeam': '/tmp/ironman_processed_audio/iro_unibeam.mp3',
    'jarvisAsYouWish': '/tmp/ironman_processed_audio/jarvis_as_you_wish.mp3',
    'jarvisOnline': '/tmp/ironman_processed_audio/jarvis_online.mp3',
    'repulsorHum': '/tmp/ironman_processed_audio/repulsor_hum.mp3'
}

b64_audio = {}
for name, path in audio_src.items():
    with open(path, 'rb') as f:
        b64 = base64.b64encode(f.read()).decode('ascii')
        b64_audio[name] = f'data:audio/mp3;base64,{b64}'
    print(f"Processed audio {name}: {os.path.getsize(path)} bytes")

# Save as json for easy embedding
import json
with open('/tmp/ironman_data.json', 'w') as f:
    json.dump({'sprites': b64_sprites, 'audio': b64_audio}, f)

print("Saved /tmp/ironman_data.json successfully!")

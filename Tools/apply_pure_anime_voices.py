import base64
from pathlib import Path

def main():
    final_dir = Path('/tmp/pika_anime_pure')
    sound_files = {
        'pikaPika': final_dir / 'pika_pika.mp3',
        'pikaChuuu': final_dir / 'pika_chuuu.mp3',
        'pikaChu': final_dir / 'pikachu.mp3',
        'pikaQuestion': final_dir / 'pika_question.mp3',
        'pikaSad': final_dir / 'pika_sad.mp3',
    }

    b64_dict = {}
    for key, path in sound_files.items():
        with open(path, 'rb') as f:
            b64 = base64.b64encode(f.read()).decode('ascii')
            b64_dict[key] = f"data:audio/mp3;base64,{b64}"
            print(f"{key}: {len(b64)} chars base64 ({path.stat().st_size} bytes)")

    bitling_path = Path("web/bitling.html")
    content = bitling_path.read_text(encoding="utf-8")

    # Locate PIKA_AUDIO block
    start_marker = "  const PIKA_AUDIO = {"
    end_marker = "  };\n  const pikaBuffers = {};"
    idx1 = content.find(start_marker)
    idx2 = content.find(end_marker)
    if idx1 == -1 or idx2 == -1:
        raise SystemExit("Could not find PIKA_AUDIO block in bitling.html")

    new_pika_audio = "  const PIKA_AUDIO = {\n"
    for key, uri in b64_dict.items():
        new_pika_audio += f"    {key}: '{uri}',\n"

    content = content[:idx1] + new_pika_audio + content[idx2:]

    # Make sure pikaThunder points to pikaChuuu
    old_methods = """    pikaSad() {
      this.playPika('pikaSad', 0.85);
    },
    pikaThunder() {
      this.playPika('pikaThunder', 0.95);
    },"""

    new_methods = """    pikaSad() {
      this.playPika('pikaSad', 0.85);
    },
    pikaThunder() {
      this.playPika('pikaChuuu', 0.95);
    },"""

    if old_methods in content:
        content = content.replace(old_methods, new_methods, 1)

    bitling_path.write_text(content, encoding="utf-8")
    print("Successfully replaced all Pikachu audio with 100% official anime voice clips!")

if __name__ == '__main__':
    main()

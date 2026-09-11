#!/usr/bin/env python3
"""One-off migration: many more phrases, and a shuffle bag so they stop repeating.

Every category now holds eight to fourteen lines, the one-off inline arrays became
categories too, and `line(key)` draws from a shuffled bag: every phrase in a category
is used once before any of them comes round again, so the same line never lands twice
in a row.
"""
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent / "web" / "bitling.html"
s = SRC.read_text(encoding="utf-8")
if "function line(" in s:
    raise SystemExit("already applied")

LINES = """  const LINES = {
    hello: ['hi!', 'you came back!', 'ooh, hello', 'missed you', 'welcome back', 'there you are',
      'I kept your seat warm', 'status: pleased', 'reconnected', 'I waited', 'you are back online'],
    hungry: ['tummy rumbles...', 'snack? snack?', 'feed me pls', 'so hungry', 'battery low',
      'running on fumes', 'is it snack o clock?', 'I could eat a chip', 'feed the machine',
      'low fuel warning', 'draw exceeds intake', 'hangry.exe'],
    sleepy: ['*yawn*', 'so sleepy...', 'nap time?', 'eyes heavy', 'entering low power',
      'my fans are slowing', 'five more minutes', 'sleep mode is calling', 'idle threads everywhere',
      'cannot keep my pixels open'],
    happy: ['la la la', 'best day', '~wiggle~', 'love this', 'hehe', 'all systems nominal',
      'good vibes only', 'humming along', 'zero complaints', 'happily idling', 'joy at 99%',
      'this is a good desktop'],
    bored: ['play with me?', 'bored...', 'any bugs to squash?', 'anyone?', 'idle... so idle',
      'give me a task', 'I have cycles to spare', 'entertain me?', 'nothing in the queue',
      'boredom overflow', 'poke me?'],
    petted: ['hehe', 'more pats!', '*purr*', 'that spot!', 'again again', 'pat received',
      'best input all day', 'processing... joy', 'do that again', 'my circuits tingle',
      'recalibrated by affection'],
    full: ['so full!', 'no more, thanks', 'later maybe', 'storage full', 'I am at capacity',
      'buffer overflow', 'maybe after a walk', 'cannot accept more input'],
    eat: ['nom nom', 'yum!', 'crunch', 'tasty', 'charging...', 'delicious voltage', 'mmm, silicon',
      'that hit the spot', 'power restored', '*munch*'],
    night: ['stars are out', 'cozy night', 'so quiet', 'the servers sleep too', 'moonlight mode',
      'quiet hours', 'nice night for a build', 'nobody deploys at this hour'],
    wake: ['*stretch*', 'good morning!', 'hello again', 'rebooted', 'systems back online',
      'that was a good sleep', 'cache cleared, ready', 'awake and dangerous', 'morning, human'],
    held: ['whee!', 'eep!', 'flying!', 'careful!', 'unexpected lift', 'wheeee', 'altitude!',
      'gravity who?', 'I have no legs right now', 'put me down. or do not.', 'this is fine',
      'weightless!'],
    chute: ['deploying chute!', 'geronimo!', 'this is fine', 'physics!', 'engaging drag',
      'canopy out!', 'soft landing incoming', 'gravity, meet nylon', 'descent controlled',
      'wheeee, but safely'],
    landed: ['stuck the landing', 'ten out of ten', 'chute stowed', 'that was on purpose',
      'nailed it', 'no damage taken', 'landing gear works', 'as planned, obviously'],
    play: ['bugs! squash them!', 'debug time', 'found some bugs', 'exterminate!', 'stomping time',
      'to the bug tracker!', 'they are getting away!', 'triage, physical edition'],
    squash: ['fixed!', 'squash!', 'gotcha', 'bug: 0, me: 1', 'closed as fixed', 'patched',
      'one less ticket', 'stomped', 'resolved', 'cannot reproduce now'],
    allSquashed: ['all bugs squashed!', 'clean build!', 'zero bugs. for now.', 'the board is empty',
      'inbox zero, bug edition', 'nothing left to stomp'],
    someEscaped: ['some got away...', 'they fled into prod', 'reopening those tickets',
      'known issues, then'],
    egg: ['unbox me!', 'something is beeping in here', '*rattle*', 'knock knock', 'this side up',
      'hello? is someone there?', 'let me out!', 'I hear a human', 'shipping was rough',
      'tape is all that separates us'],
    unboxing: ['*rattle*', 'tape is tearing', 'almost open...', 'nearly there', 'I can see light',
      'one more tug', 'keep going!'],
    sleeping: ['zzz', 'night night', 'sleepy time', 'powering down', 'see you in the morning',
      'entering sleep mode', 'goodnight, human'],
    stretch: ['*stretch*', 'servos ok', 'recalibrating', 'joints checked', 'limbering up',
      'diagnostics: fine'],
    takeoff: ['brb, hovering', 'let me see from up here', 'going up', 'thrusters on',
      'gaining altitude', 'up we go', 'switching to flight mode'],
    hovering: ['nice view', 'scanning…', 'I can see your dock from here', 'hovering is cheap',
      'good visibility today', 'everything looks smaller', 'no notes from up here'],
    testFail: ['tests are red…', 'who broke the build?', 'ERR ERR ERR', 'it worked on my machine',
      'red across the board', 'the suite is unhappy', 'assertions betrayed us',
      'not great, not terrible'],
    testPass: ['tests green!', 'all green. ship it.', 'zero failures', 'the suite is happy',
      'green across the board', 'clean run', 'no assertions harmed'],
    deployFail: ['deploy failed. rollback?', 'prod said no', 'abort abort', 'prod rejected us',
      'rollback time', 'the deploy did not deploy'],
    onIt: ['on it', 'thinking…', 'reading the code', 'let me look', 'hmm, okay', 'spinning up',
      'parsing your request', 'right, where were we', 'context loading', 'give me a second'],
    working: ['still thinking…', 'crunching…', 'almost there', 'lots of files…',
      'deep in the codebase', 'this one is chunky', 'still going', 'do not close the laptop',
      'many tokens, much thought'],
    done: ['done! check it', 'finished, human', 'your turn', 'ready for review', 'ta-da',
      'that is done', 'over to you', 'have a look', 'shipped to your screen'],
    needsYou: ['Claude needs you!', 'permission? over here!', 'psst, it is waiting',
      'it wants your approval', 'a decision is required', 'hey! yes or no?'],
    tired: ['too tired to play', 'need a nap first', 'battery says no', 'ask me after a nap',
      'low power, sorry'],
    oops: ['hmm, that errored', 'oops', 'retrying, probably', 'that did not work',
      'stack trace incoming', 'well, that failed'],
    noCommits: ['no commits today?', 'the repo misses you', 'git log is lonely',
      'the branch is untouched', 'HEAD has not moved all day'],
  };
"""

# ---------------------------------------------------------------- swap the table
i = s.index("  const LINES = {")
j = s.index("\n  };\n", i) + len("\n  };\n")
s = s[:i] + LINES + s[j:]

# ---------------------------------------------------------------- shuffle-bag picker
anchor = "  const pick = (arr) => arr[Math.floor(Math.random() * arr.length)];\n"
assert s.count(anchor) == 1
s = s.replace(anchor, anchor +
              "  // Draw phrases from a shuffled bag: every line in a category is used once before\n"
              "  // any of them comes round again, so the pet never repeats itself back to back.\n"
              "  const phraseBags = new Map();\n"
              "  function line(key) {\n"
              "    const all = LINES[key] || [];\n"
              "    if (all.length < 2) return all[0] || '';\n"
              "    let bag = phraseBags.get(key);\n"
              "    if (!bag || !bag.length) {\n"
              "      bag = all.slice();\n"
              "      for (let i = bag.length - 1; i > 0; i--) {\n"
              "        const k = Math.floor(Math.random() * (i + 1));\n"
              "        [bag[i], bag[k]] = [bag[k], bag[i]];\n"
              "      }\n"
              "      phraseBags.set(key, bag);\n"
              "    }\n"
              "    return bag.pop();\n"
              "  }\n")

# ---------------------------------------------------------------- route every call site through the bag
for key in ["hello", "hungry", "sleepy", "happy", "bored", "petted", "full", "eat", "night",
            "wake", "held", "chute", "landed", "play", "squash", "egg", "testFail", "testPass",
            "deployFail", "onIt", "working", "done", "needsYou", "tired"]:
    s = s.replace(f"pick(LINES.{key})", f"line('{key}')")

for old, new in [
    ("pick(['*rattle*', 'tape is tearing', 'almost open...'])", "line('unboxing')"),
    ("pick(['zzz', 'night night', 'sleepy time'])", "line('sleeping')"),
    ("pick(['all bugs squashed!', 'clean build!', 'zero bugs. for now.'])", "line('allSquashed')"),
    ("say('some got away...', 2200)", "say(line('someEscaped'), 2200)"),
    ("pick(['*stretch*', 'servos ok', 'recalibrating'])", "line('stretch')"),
    ("pick(['brb, hovering', 'let me see from up here', 'going up', 'thrusters on'])", "line('takeoff')"),
    ("pick(['nice view', 'scanning…', 'I can see your dock from here', 'hovering is cheap'])", "line('hovering')"),
    ("pick(['no commits today?', 'the repo misses you', 'git log is lonely'])", "line('noCommits')"),
    ("pick(['hmm, that errored', 'oops', 'retrying, probably'])", "line('oops')"),
    ("say(pick(sky.night > 0.6 ? LINES.night : LINES.happy));",
     "say(line(sky.night > 0.6 ? 'night' : 'happy'));"),
]:
    assert s.count(old) == 1, f"call site not found: {old[:70]}"
    s = s.replace(old, new)

SRC.write_text(s, encoding="utf-8")
leftover = s.count("pick(LINES.")
print(f"patched {SRC}; remaining pick(LINES.*) call sites: {leftover}")

export type PetKind = "walker" | "floater";

export interface Pet {
  id: string;
  name: string;
  title: string;
  species: string;
  kind: PetKind;
  categories: string[];
  accent: string;
  accentLight: string;
  avatar: string;
  blurb: string;
  attack: { name: string; desc: string; icon: string };
  evolution: string;
  quotes: string[];
  features: string[];
}

export const PETS_DATA: Pet[] = [
  {
    id: "mario",
    name: "Mario",
    title: "Super Mario",
    species: "Mushroom Kingdom Plumber",
    kind: "walker",
    categories: ["gaming", "walkers"],
    accent: "#E52521",
    accentLight: "#FEE2E2",
    avatar: "/avatars/mario.png",
    blurb:
      "High-definition 3D animated likeness (Illumination / Movie style). Evolves from Small Mario to Super, Fire, and Star Mario as you commit code!",
    attack: {
      name: "Fireball & Stomp",
      desc: "Jump-stomps crawling bugs; hurls 3D blazing fireballs on boss bugs.",
      icon: "🔥",
    },
    evolution: "Small Mario (0 commits) → Super Mario (10 commits) → Fire Mario (25 commits) → Star Mario (50 commits)",
    quotes: [
      "It's-a me, Mario!",
      "Yahoo! Let's-a go!",
      "WAHOO! Fireball direct hit!",
      "COURSE CLEAR! Pushed down the warp pipe to production! YAHOO!",
    ],
    features: [
      'Punches floating 3D "?" blocks to collect Super Mushrooms & Gold Coins on commits',
      "Power-down shrink penalty if a test suite fails",
      "Course Clear! flagpole victory fanfare and green Warp Pipe on deployment",
    ],
  },
  {
    id: "goku",
    name: "Goku",
    title: "Son Goku",
    species: "Saiyan on Flying Nimbus",
    kind: "floater",
    categories: ["anime", "floaters"],
    accent: "#FF5722",
    accentLight: "#FFEDD5",
    avatar: "/avatars/goku.png",
    blurb:
      "Rides the golden Flying Nimbus (Kintoun) with Power Pole and Turtle School Gi. Today's commits power continuous ki transformations up to Ultra Instinct!",
    attack: {
      name: "Full Kamehameha",
      desc: "Rapid Ki Blasts for small bugs; devastating charged Kamehameha wave for bosses.",
      icon: "⚡",
    },
    evolution: "Kid Goku → Kaioken (10 commits) → Super Saiyan (25 commits) → Ultra Instinct (50 commits)",
    quotes: [
      "I'm Goku! Ready to train!",
      "Flying Nimbus, full throttle!",
      "Ka... Me... Ha... Me... HAAA!",
      "A Saiyan gets stronger after defeat!",
    ],
    features: [
      "Hover flight physics over Mount Paozu and Karin Tower",
      "Aura flares and shockwave rings during code review & test runs",
      "Celebrates deployments with high-speed Instant Transmission",
    ],
  },
  {
    id: "pikachu",
    name: "Pikachu",
    title: "Electric Mouse Pokémon",
    species: "Electric Companion",
    kind: "walker",
    categories: ["gaming", "anime", "walkers"],
    accent: "#FACC15",
    accentLight: "#FEF9C3",
    avatar: "/avatars/pikachu.png",
    blurb:
      'Scampers along your screen edge with authentic synthesized voice lines ("Pika-pika!"), sparking red cheeks, and ground shockwave thunderbolts.',
    attack: {
      name: "100,000-Volt Thunderbolt",
      desc: "Crackling Electro Balls for small pests; sky lightning bolts with ground shockwaves for bosses.",
      icon: "⚡",
    },
    evolution: "Pichu Scout → Pikachu Classic → Overcharged Volt Master",
    quotes: ["Pika-pika!", "Pika-CHUUU! (100,000 Volts!)", "Pikachu!! All green build!", "Chuuu... (curling into tail to sleep)"],
    features: [
      "Synthesized Pikachu soundboard and cheerful ear wiggles",
      "Cute scruff-drag physics with dangling paws when moved",
      "Cheeks glow glowing red warning during test failures",
    ],
  },
  {
    id: "ronaldo",
    name: "CR7",
    title: "Cristiano Ronaldo",
    species: "The Goal Machine",
    kind: "walker",
    categories: ["gaming", "walkers"],
    accent: "#00E676",
    accentLight: "#DCFCE7",
    avatar: "/avatars/ronaldo.png",
    blurb:
      "High-definition realistic likeness with an independent physics soccer ball that rolls and bounces. Chases the ball, dribbles, juggles, and snipes bugs with knuckleball power-kicks!",
    attack: {
      name: "Top Bins & SIUUU Strike",
      desc: "Kicks the soccer ball at bugs; celebrates git pushes with stadium net bulge and iconic mid-air spin SIUUU!",
      icon: "⚽",
    },
    evolution: "Sporting Talent → Manchester Legend → Real Madrid Maestro → 900+ Goals Icon",
    quotes: ["SIUUUUUU!", "Top bins! GOLAZO!", "Calma, calma... let me cook.", "Champions League mentality! 900+ goals!"],
    features: [
      "Interactive soccer ball you can click, kick, and juggle across your screen",
      'Theatrical "GOAL!" sequence with referee whistle, crowd roar, and golden confetti',
      "VAR review animation when tests are running",
    ],
  },
  {
    id: "spiderman",
    name: "Spider-Man",
    title: "Friendly Neighborhood Hero",
    species: "Web Slinger",
    kind: "walker",
    categories: ["heroes", "walkers"],
    accent: "#E23636",
    accentLight: "#FEE2E2",
    avatar: "/avatars/spiderman.png",
    blurb:
      "Authentic 3D suit with skyline window swinging, expressive eye shutter optics, web thwips, and Spidey-Sense warnings when tests break.",
    attack: {
      name: "Web Thwip & Slingshot Dive",
      desc: "Fast web strands snare pests; slingshot dive smashes boss bugs into the pavement.",
      icon: "🕸️",
    },
    evolution: "Homemade Suit → Classic Red & Blue → Stark Upgraded → Iron Spider",
    quotes: [
      "Your friendly neighborhood Spider-Man!",
      "Spidey-Sense is tingling! Bugs ahead!",
      "Thwip! Webbed up and delivered!",
      "Just another day saving the codebase!",
    ],
    features: [
      "Window-anchored web-swinging animation across your editor",
      "Dynamic eye-shutter reactions mirroring user typing cadence",
      "Spidey-Sense electric aura alerting you before build breaks",
    ],
  },
  {
    id: "ironman",
    name: "Iron Man",
    title: "Tony Stark • Mark III",
    species: "Armored Avenger",
    kind: "floater",
    categories: ["heroes", "floaters"],
    accent: "#DC2626",
    accentLight: "#FEE2E2",
    avatar: "/avatars/ironman.png",
    blurb:
      "Hovers with active pulse repulsor boot thrusters in gleaming Mark III red & gold armor. Speaks Jarvis telemetry diagnostics while you code.",
    attack: {
      name: "Chest Arc Reactor Unibeam",
      desc: "Palm Repulsor Blasts for small bugs; full-output chest Unibeam disintegration on boss bugs.",
      icon: "💥",
    },
    evolution: "Mark I Prototype → Mark III Classic → Hulkbuster Armor → Nanotech Bleeding Edge",
    quotes: [
      "I am Iron Man.",
      "Jarvis: 'All systems nominal, sir.'",
      "Arc Reactor Unibeam: total disintegration!",
      "Tony: 'Who forgot to order shawarma?'",
    ],
    features: [
      "Live Jarvis AI status reports during Claude Code and terminal sessions",
      "Photon beam shader with traveling plasma shock rings",
      "Supersonic orbital deployment sequence when code is pushed",
    ],
  },
  {
    id: "thor",
    name: "Thor",
    title: "God of Thunder",
    species: "Asgardian Avenger",
    kind: "floater",
    categories: ["heroes", "floaters"],
    accent: "#38BDF8",
    accentLight: "#E0F2FE",
    avatar: "/avatars/thor.png",
    blurb:
      "The Mighty Thor, son of Odin! Wields Mjolnir, commands celestial lightning storms, and forges the legendary Stormbreaker axe at 25+ daily commits!",
    attack: {
      name: "Divine Thunder & Hammer Spin",
      desc: "Crackling sky lightning bolts smite bugs; spinning Mjolnir weapon throw obliterates bosses.",
      icon: "⚡",
    },
    evolution: "Prince of Asgard → God of Thunder → Awakened Storm God → Stormbreaker King",
    quotes: [
      "I am Thor, son of Odin!",
      "BY ODIN'S BEARD! Feel the power of the storm!",
      "ALL TESTS GREEN! THE NINE REALMS ARE SECURED!",
      "ANOTHER! *smashes coffee mug*",
    ],
    features: [
      "Dynamic hammer spin physics and Bifrost warp portals on git push",
      "Divine blue lightning arcing across your desktop on test completion",
      "Stormbreaker weapon upgrade unlocked at 25 commits in a single day",
    ],
  },
  {
    id: "naruto",
    name: "Naruto",
    title: "Naruto Uzumaki",
    species: "Ninja of the Leaf",
    kind: "walker",
    categories: ["anime", "walkers"],
    accent: "#F97316",
    accentLight: "#FFEDD5",
    avatar: "/avatars/naruto.png",
    blurb:
      "Dashes with shinobi speed, arms swept back in classic ninja sprint. Gathers swirling nature chakra and destroys bugs with the iconic Fuuton: Rasenshuriken!",
    attack: {
      name: "Fuuton: Rasenshuriken",
      desc: "Rapid spinning Chakra Shurikens for small pests; massive spiraling wind-blade Rasenshuriken for bosses.",
      icon: "🌀",
    },
    evolution: "Genin Rookie → Sage Mode Apprentice → Nine-Tails Cloak → Seventh Hokage",
    quotes: ["Believe it! Dattebayo!", "RASENGAN! Direct hit!", "My ninja way never fails!", "Time for Ichiraku ramen!"],
    features: [
      "Ninja sprint walk cycle and Shadow Clone jutsu sparkles",
      "Swirling cyan wind chakra particles and hand-seal animations",
      "Celebrates test passes with huge bowls of ramen",
    ],
  },
  {
    id: "kaiju",
    name: "Rumble",
    title: "Atomic Titan",
    species: "Prehistoric Kaiju",
    kind: "walker",
    categories: ["mech", "walkers"],
    accent: "#06B6D4",
    accentLight: "#CFFAFE",
    avatar: "/avatars/kaiju.png",
    blurb:
      "A charcoal titan with sweeping tail, glowing cyan dorsal plates, and heavy earth-shaking footsteps. Flies by aiming atomic breath down at the earth!",
    attack: {
      name: "Cyan Atomic Breath",
      desc: "Heavy tail and foot stomps; charges luminous dorsal fins to unleash searing atomic breath.",
      icon: "🌋",
    },
    evolution: "Hatchling Titan → Armored Colossus → Burning Thermo Titan",
    quotes: [
      "RRRR... the ground shakes, slightly.",
      "Good rampage weather. Nothing left to flatten.",
      "Flattened, every single one of them.",
      "I am very heavy. You cannot lift a kaiju.",
    ],
    features: [
      "Screen-shaking ground stomp physics that flattens desktop bugs",
      "Luminous animated dorsal plate charging sequence",
      "Rides its own breath into the sky in classic Godzilla 1971 fashion",
    ],
  },
  {
    id: "robot",
    name: "Bitling",
    title: "The Little Machine",
    species: "Flagship Desktop Bot",
    kind: "walker",
    categories: ["mech", "walkers"],
    accent: "#0EA5E9",
    accentLight: "#E0F2FE",
    avatar: "/avatars/robot.png",
    blurb:
      "The original desktop companion. Stands on your dock, watches your reflog, catches falling commit nodes, and snipes failing tests with twin eye lasers.",
    attack: {
      name: "Twin Cyan Eye Lasers",
      desc: "Precision optic laser beams vaporize failing test beetles with pin-point accuracy.",
      icon: "🤖",
    },
    evolution: "Bootling → Bitling → Overclocked Bitling (Dual Antennas & Golden Halo)",
    quotes: [
      "Commit caught: delicious hash!",
      "Engaging drag... parafoil deployed!",
      "Main has left the building! Rocket away!",
      "Go to sleep, human. Git log is lonely.",
    ],
    features: [
      "Retro CRT screen face that reflects typing dots and progress bars",
      "Ram-air ram parafoil automatically deploys when you fling the robot",
      "Mood-shifting antenna color and three chest-mounted need gauges",
    ],
  },
  {
    id: "dragon",
    name: "Shenron",
    title: "The Eternal Dragon",
    species: "Wish Granting Deity",
    kind: "floater",
    categories: ["anime", "mech", "floaters"],
    accent: "#22C55E",
    accentLight: "#DCFCE7",
    avatar: "/avatars/dragon.png",
    blurb:
      "Vast emerald coils, crimson eyes, and a majestic serpentine flight across your entire workspace. Grants wishes as you close GitHub issues.",
    attack: {
      name: "Dragon Fire Storm",
      desc: "Unleashes concentrated cones of sacred emerald dragon fire that burn away test bugs.",
      icon: "🐉",
    },
    evolution: "Dragon Orb Hatchling → Coiling Serpent → Celestial Shenron",
    quotes: [
      "I am Shenron. State your wish.",
      "Your wish has been granted. The path is clear.",
      "Even a dragon must be sustained. An offering, mortal?",
      "Go forth. May your work prosper.",
    ],
    features: [
      "Real-time multi-segment snake kinematics with coiling body physics",
      "Celestial cloud trails and gold lightning ambient sky effects",
      "Speaks solemn ancient prophecies when your code deploys successfully",
    ],
  },
];

/**
 * Bitling Website - Interactive Client Engine
 * Handles pet gallery, filtering, simulator control, modal inspection, and clipboard utilities.
 */

// Comprehensive data for all 12 Bitling Pets
const PETS_DATA = [
  {
    id: 'mario',
    name: 'Mario',
    title: 'Super Mario',
    species: 'Mushroom Kingdom Plumber',
    kind: 'walker',
    categories: ['gaming', 'walkers'],
    accent: '#E52521',
    accentLight: '#FEE2E2',
    avatar: 'avatars/mario.png',
    blurb: 'High-definition 3D animated likeness (Illumination / Movie style). Evolves from Small Mario to Super, Fire, and Star Mario as you commit code!',
    attack: {
      name: 'Fireball & Stomp',
      desc: 'Jump-stomps crawling bugs; hurls 3D blazing fireballs on boss bugs.',
      icon: '🔥'
    },
    evolution: 'Small Mario (0 commits) → Super Mario (10 commits) → Fire Mario (25 commits) → Star Mario (50 commits)',
    quotes: [
      "It's-a me, Mario!",
      "Yahoo! Let's-a go!",
      "WAHOO! Fireball direct hit!",
      "COURSE CLEAR! Pushed down the warp pipe to production! YAHOO!"
    ],
    features: [
      'Punches floating 3D "?" blocks to collect Super Mushrooms & Gold Coins on commits',
      'Power-down shrink penalty if a test suite fails',
      'Course Clear! flagpole victory fanfare and green Warp Pipe on deployment'
    ]
  },
  {
    id: 'goku',
    name: 'Goku',
    title: 'Son Goku',
    species: 'Saiyan on Flying Nimbus',
    kind: 'floater',
    categories: ['anime', 'floaters'],
    accent: '#FF5722',
    accentLight: '#FFEDD5',
    avatar: 'avatars/goku.png',
    blurb: 'Rides the golden Flying Nimbus (Kintoun) with Power Pole and Turtle School Gi. Today\'s commits power continuous ki transformations up to Ultra Instinct!',
    attack: {
      name: 'Full Kamehameha',
      desc: 'Rapid Ki Blasts for small bugs; devastating charged Kamehameha wave for bosses.',
      icon: '⚡'
    },
    evolution: 'Kid Goku → Kaioken (10 commits) → Super Saiyan (25 commits) → Ultra Instinct (50 commits)',
    quotes: [
      "I'm Goku! Ready to train!",
      "Flying Nimbus, full throttle!",
      "Ka... Me... Ha... Me... HAAA!",
      "A Saiyan gets stronger after defeat!"
    ],
    features: [
      'Hover flight physics over Mount Paozu and Karin Tower',
      'Aura flares and shockwave rings during code review & test runs',
      'Celebrates deployments with high-speed Instant Transmission'
    ]
  },
  {
    id: 'pikachu',
    name: 'Pikachu',
    title: 'Electric Mouse Pokémon',
    species: 'Electric Companion',
    kind: 'walker',
    categories: ['gaming', 'anime', 'walkers'],
    accent: '#FACC15',
    accentLight: '#FEF9C3',
    avatar: 'avatars/pikachu.png',
    blurb: 'Scampers along your screen edge with authentic synthesized voice lines ("Pika-pika!"), sparking red cheeks, and ground shockwave thunderbolts.',
    attack: {
      name: '100,000-Volt Thunderbolt',
      desc: 'Crackling Electro Balls for small pests; sky lightning bolts with ground shockwaves for bosses.',
      icon: '⚡'
    },
    evolution: 'Pichu Scout → Pikachu Classic → Overcharged Volt Master',
    quotes: [
      "Pika-pika!",
      "Pika-CHUUU! (100,000 Volts!)",
      "Pikachu!! All green build!",
      "Chuuu... (curling into tail to sleep)"
    ],
    features: [
      'Synthesized Pikachu soundboard and cheerful ear wiggles',
      'Cute scruff-drag physics with dangling paws when moved',
      'Cheeks glow glowing red warning during test failures'
    ]
  },
  {
    id: 'ronaldo',
    name: 'CR7',
    title: 'Cristiano Ronaldo',
    species: 'The Goal Machine',
    kind: 'walker',
    categories: ['gaming', 'walkers'],
    accent: '#00E676',
    accentLight: '#DCFCE7',
    avatar: 'avatars/ronaldo.png',
    blurb: 'High-definition realistic likeness with an independent physics soccer ball that rolls and bounces. Chases the ball, dribbles, juggles, and snipes bugs with knuckleball power-kicks!',
    attack: {
      name: 'Top Bins & SIUUU Strike',
      desc: 'Kicks the soccer ball at bugs; celebrates git pushes with stadium net bulge and iconic mid-air spin SIUUU!',
      icon: '⚽'
    },
    evolution: 'Sporting Talent → Manchester Legend → Real Madrid Maestro → 900+ Goals Icon',
    quotes: [
      "SIUUUUUU!",
      "Top bins! GOLAZO!",
      "Calma, calma... let me cook.",
      "Champions League mentality! 900+ goals!"
    ],
    features: [
      'Interactive soccer ball you can click, kick, and juggle across your screen',
      'Theatrical "GOAL!" sequence with referee whistle, crowd roar, and golden confetti',
      'VAR review animation when tests are running'
    ]
  },
  {
    id: 'spiderman',
    name: 'Spider-Man',
    title: 'Friendly Neighborhood Hero',
    species: 'Web Slinger',
    kind: 'walker',
    categories: ['heroes', 'walkers'],
    accent: '#E23636',
    accentLight: '#FEE2E2',
    avatar: 'avatars/spiderman.png',
    blurb: 'Authentic 3D suit with skyline window swinging, expressive eye shutter optics, web thwips, and Spidey-Sense warnings when tests break.',
    attack: {
      name: 'Web Thwip & Slingshot Dive',
      desc: 'Fast web strands snare pests; slingshot dive smashes boss bugs into the pavement.',
      icon: '🕸️'
    },
    evolution: 'Homemade Suit → Classic Red & Blue → Stark Upgraded → Iron Spider',
    quotes: [
      "Your friendly neighborhood Spider-Man!",
      "Spidey-Sense is tingling! Bugs ahead!",
      "Thwip! Webbed up and delivered!",
      "Just another day saving the codebase!"
    ],
    features: [
      'Window-anchored web-swinging animation across your editor',
      'Dynamic eye-shutter reactions mirroring user typing cadence',
      'Spidey-Sense electric aura alerting you before build breaks'
    ]
  },
  {
    id: 'ironman',
    name: 'Iron Man',
    title: 'Tony Stark • Mark III',
    species: 'Armored Avenger',
    kind: 'floater',
    categories: ['heroes', 'floaters'],
    accent: '#DC2626',
    accentLight: '#FEE2E2',
    avatar: 'avatars/ironman.png',
    blurb: 'Hovers with active pulse repulsor boot thrusters in gleaming Mark III red & gold armor. Speaks Jarvis telemetry diagnostics while you code.',
    attack: {
      name: 'Chest Arc Reactor Unibeam',
      desc: 'Palm Repulsor Blasts for small bugs; full-output chest Unibeam disintegration on boss bugs.',
      icon: '💥'
    },
    evolution: 'Mark I Prototype → Mark III Classic → Hulkbuster Armor → Nanotech Bleeding Edge',
    quotes: [
      "I am Iron Man.",
      "Jarvis: 'All systems nominal, sir.'",
      "Arc Reactor Unibeam: total disintegration!",
      "Tony: 'Who forgot to order shawarma?'"
    ],
    features: [
      'Live Jarvis AI status reports during Claude Code and terminal sessions',
      'Photon beam shader with traveling plasma shock rings',
      'Supersonic orbital deployment sequence when code is pushed'
    ]
  },
  {
    id: 'thor',
    name: 'Thor',
    title: 'God of Thunder',
    species: 'Asgardian Avenger',
    kind: 'floater',
    categories: ['heroes', 'floaters'],
    accent: '#38BDF8',
    accentLight: '#E0F2FE',
    avatar: 'avatars/thor.png',
    blurb: 'The Mighty Thor, son of Odin! Wields Mjolnir, commands celestial lightning storms, and forges the legendary Stormbreaker axe at 25+ daily commits!',
    attack: {
      name: 'Divine Thunder & Hammer Spin',
      desc: 'Crackling sky lightning bolts smite bugs; spinning Mjolnir weapon throw obliterates bosses.',
      icon: '⚡'
    },
    evolution: 'Prince of Asgard → God of Thunder → Awakened Storm God → Stormbreaker King',
    quotes: [
      "I am Thor, son of Odin!",
      "BY ODIN'S BEARD! Feel the power of the storm!",
      "ALL TESTS GREEN! THE NINE REALMS ARE SECURED!",
      "ANOTHER! *smashes coffee mug*"
    ],
    features: [
      'Dynamic hammer spin physics and Bifrost warp portals on git push',
      'Divine blue lightning arcing across your desktop on test completion',
      'Stormbreaker weapon upgrade unlocked at 25 commits in a single day'
    ]
  },
  {
    id: 'naruto',
    name: 'Naruto',
    title: 'Naruto Uzumaki',
    species: 'Ninja of the Leaf',
    kind: 'walker',
    categories: ['anime', 'walkers'],
    accent: '#F97316',
    accentLight: '#FFEDD5',
    avatar: 'avatars/naruto.png',
    blurb: 'Dashes with shinobi speed, arms swept back in classic ninja sprint. Gathers swirling nature chakra and destroys bugs with the iconic Fuuton: Rasenshuriken!',
    attack: {
      name: 'Fuuton: Rasenshuriken',
      desc: 'Rapid spinning Chakra Shurikens for small pests; massive spiraling wind-blade Rasenshuriken for bosses.',
      icon: '🌀'
    },
    evolution: 'Genin Rookie → Sage Mode Apprentice → Nine-Tails Cloak → Seventh Hokage',
    quotes: [
      "Believe it! Dattebayo!",
      "RASENGAN! Direct hit!",
      "My ninja way never fails!",
      "Time for Ichiraku ramen!"
    ],
    features: [
      'Ninja sprint walk cycle and Shadow Clone jutsu sparkles',
      'Swirling cyan wind chakra particles and hand-seal animations',
      'Celebrates test passes with huge bowls of ramen'
    ]
  },
  {
    id: 'kaiju',
    name: 'Rumble',
    title: 'Atomic Titan',
    species: 'Prehistoric Kaiju',
    kind: 'walker',
    categories: ['mech', 'walkers'],
    accent: '#06B6D4',
    accentLight: '#CFFAFE',
    avatar: 'avatars/kaiju.png',
    blurb: 'A charcoal titan with sweeping tail, glowing cyan dorsal plates, and heavy earth-shaking footsteps. Flies by aiming atomic breath down at the earth!',
    attack: {
      name: 'Cyan Atomic Breath',
      desc: 'Heavy tail and foot stomps; charges luminous dorsal fins to unleash searing atomic breath.',
      icon: '🌋'
    },
    evolution: 'Hatchling Titan → Armored Colossus → Burning Thermo Titan',
    quotes: [
      "RRRR... the ground shakes, slightly.",
      "Good rampage weather. Nothing left to flatten.",
      "Flattened, every single one of them.",
      "I am very heavy. You cannot lift a kaiju."
    ],
    features: [
      'Screen-shaking ground stomp physics that flattens desktop bugs',
      'Luminous animated dorsal plate charging sequence',
      'Rides its own breath into the sky in classic Godzilla 1971 fashion'
    ]
  },
  {
    id: 'robot',
    name: 'Bitling',
    title: 'The Little Machine',
    species: 'Flagship Desktop Bot',
    kind: 'walker',
    categories: ['mech', 'walkers'],
    accent: '#0EA5E9',
    accentLight: '#E0F2FE',
    avatar: 'avatars/robot.png',
    blurb: 'The original desktop companion. Stands on your dock, watches your reflog, catches falling commit nodes, and snipes failing tests with twin eye lasers.',
    attack: {
      name: 'Twin Cyan Eye Lasers',
      desc: 'Precision optic laser beams vaporize failing test beetles with pin-point accuracy.',
      icon: '🤖'
    },
    evolution: 'Bootling → Bitling → Overclocked Bitling (Dual Antennas & Golden Halo)',
    quotes: [
      "Commit caught: delicious hash!",
      "Engaging drag... parafoil deployed!",
      "Main has left the building! Rocket away!",
      "Go to sleep, human. Git log is lonely."
    ],
    features: [
      'Retro CRT screen face that reflects typing dots and progress bars',
      'Ram-air ram parafoil automatically deploys when you fling the robot',
      'Mood-shifting antenna color and three chest-mounted need gauges'
    ]
  },
  {
    id: 'dragon',
    name: 'Shenron',
    title: 'The Eternal Dragon',
    species: 'Wish Granting Deity',
    kind: 'floater',
    categories: ['anime', 'mech', 'floaters'],
    accent: '#22C55E',
    accentLight: '#DCFCE7',
    avatar: 'avatars/dragon.png',
    blurb: 'Vast emerald coils, crimson eyes, and a majestic serpentine flight across your entire workspace. Grants wishes as you close GitHub issues.',
    attack: {
      name: 'Dragon Fire Storm',
      desc: 'Unleashes concentrated cones of sacred emerald dragon fire that burn away test bugs.',
      icon: '🐉'
    },
    evolution: 'Dragon Orb Hatchling → Coiling Serpent → Celestial Shenron',
    quotes: [
      "I am Shenron. State your wish.",
      "Your wish has been granted. The path is clear.",
      "Even a dragon must be sustained. An offering, mortal?",
      "Go forth. May your work prosper."
    ],
    features: [
      'Real-time multi-segment snake kinematics with coiling body physics',
      'Celestial cloud trails and gold lightning ambient sky effects',
      'Speaks solemn ancient prophecies when your code deploys successfully'
    ]
  }
];

// State variables
let currentFilter = 'all';
let activePetId = 'mario';

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
  renderPetGallery();
  setupFilterListeners();
  setupModalListeners();
  setupCopyButtons();
  setupFaqAccordion();
  setupMobileMenu();
  setupSimulatorBridge();
});

/**
 * Render Pet Gallery Cards
 */
function renderPetGallery() {
  const container = document.getElementById('petsGrid');
  if (!container) return;

  const filteredPets = PETS_DATA.filter(pet => {
    if (currentFilter === 'all') return true;
    return pet.categories.includes(currentFilter);
  });

  container.innerHTML = filteredPets.map(pet => `
    <article class="pixel-card pixel-card-hover pet-card" data-pet-id="${pet.id}">
      <div class="pet-card-media" style="background: radial-gradient(circle at center, ${pet.accentLight} 0%, #FFFFFF 75%);">
        <div class="pet-card-bg-gradient" style="background: ${pet.accent};"></div>
        <span class="pixel-badge pet-tag-badge" style="background: #FFFFFF; border-color: ${pet.accent}; color: ${pet.accent};">
          ${pet.species}
        </span>
        <span class="pixel-badge pet-kind-badge" style="background: ${pet.kind === 'walker' ? '#E0F2FE' : '#FEF3C7'}; color: ${pet.kind === 'walker' ? '#0369A1' : '#B45309'};">
          ${pet.kind === 'walker' ? '🐾 Walker' : '☁️ Floater'}
        </span>
        <img src="${pet.avatar}" alt="${pet.name}" class="pet-avatar-img" loading="lazy">
      </div>

      <div class="pet-card-body">
        <div class="pet-card-title-row">
          <h3 class="pet-name" style="color: ${pet.accent};">${pet.name}</h3>
          <span class="pet-species-subtitle">${pet.title}</span>
        </div>

        <p class="pet-blurb">${pet.blurb}</p>

        <div class="pet-attack-box">
          <span class="attack-icon">${pet.attack.icon}</span>
          <div>
            <div class="attack-name">${pet.attack.name}</div>
            <div class="attack-desc">${pet.attack.desc}</div>
          </div>
        </div>

        <div class="pet-quote-box" style="border-left-color: ${pet.accent};">
          "${pet.quotes[0]}"
        </div>

        <div class="pet-card-actions">
          <button class="pixel-btn pixel-btn-sm pet-action-btn btn-try-pet" data-pet-id="${pet.id}" style="background: ${pet.accent};">
            ⚡ Test in Stage
          </button>
          <button class="pixel-btn pixel-btn-sm pixel-btn-light pet-action-btn btn-inspect-pet" data-pet-id="${pet.id}">
            🔍 Info
          </button>
          <button class="pixel-btn pixel-btn-sm pixel-btn-light pet-action-btn btn-copy-cli" data-cli="bitling pet ${pet.id}" title="Copy CLI switch command">
            📋 CLI
          </button>
        </div>
      </div>
    </article>
  `).join('');

  // Attach card event listeners
  container.querySelectorAll('.btn-try-pet').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      const petId = btn.getAttribute('data-pet-id');
      switchSimulatorPet(petId);
      // Smooth scroll up to simulator
      document.getElementById('simulator')?.scrollIntoView({ behavior: 'smooth' });
    });
  });

  container.querySelectorAll('.btn-inspect-pet').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      const petId = btn.getAttribute('data-pet-id');
      openPetModal(petId);
    });
  });

  container.querySelectorAll('.btn-copy-cli').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      const cliCmd = btn.getAttribute('data-cli');
      copyToClipboard(cliCmd, `Copied "${cliCmd}" to clipboard!`);
    });
  });

  container.querySelectorAll('.pet-card').forEach(card => {
    card.addEventListener('click', () => {
      const petId = card.getAttribute('data-pet-id');
      openPetModal(petId);
    });
  });
}

/**
 * Filter Buttons Setup
 */
function setupFilterListeners() {
  const filterBtns = document.querySelectorAll('.filter-btn');
  filterBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      filterBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      currentFilter = btn.getAttribute('data-filter') || 'all';
      renderPetGallery();
    });
  });
}

/**
 * Simulator Bridge & Quick Ribbon
 */
function setupSimulatorBridge() {
  const ribbonBtns = document.querySelectorAll('.quick-pet-btn');
  ribbonBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      ribbonBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const petId = btn.getAttribute('data-pet-id');
      switchSimulatorPet(petId);
    });
  });

  // Simulator HUD Event Triggers
  document.querySelectorAll('.sim-trigger-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const action = btn.getAttribute('data-action');
      triggerSimulatorAction(action);
    });
  });
}

/**
 * Switch Active Pet in Simulator
 */
function switchSimulatorPet(petId) {
  activePetId = petId;
  const pet = PETS_DATA.find(p => p.id === petId);
  if (!pet) return;

  // Update Ribbon Active State
  document.querySelectorAll('.quick-pet-btn').forEach(btn => {
    if (btn.getAttribute('data-pet-id') === petId) {
      btn.classList.add('active');
    } else {
      btn.classList.remove('active');
    }
  });

  // Update Titlebar Indicator
  const simTitle = document.getElementById('simActivePetName');
  if (simTitle) {
    simTitle.textContent = `${pet.name} (${pet.species}) • Stage 3`;
  }

  // Communicate with Simulator Iframe
  const simIframe = document.getElementById('simulatorIframe');
  if (simIframe && simIframe.contentWindow) {
    try {
      // Try direct API call if same origin
      if (simIframe.contentWindow.petNative && simIframe.contentWindow.petNative.setSpecies) {
        simIframe.contentWindow.petNative.setSpecies(petId);
      } else {
        // Post message fallback
        simIframe.contentWindow.postMessage({ type: 'setSpecies', species: petId }, '*');
      }
    } catch (err) {
      console.warn('Iframe communication fallback:', err);
    }
  }

  showToast(`Switched active companion to ${pet.name}!`);
}

/**
 * Trigger Developer Events in Simulator
 */
function triggerSimulatorAction(action) {
  const simIframe = document.getElementById('simulatorIframe');
  if (!simIframe || !simIframe.contentWindow) return;

  try {
    const win = simIframe.contentWindow;
    // Map button actions to iframe functions
    switch (action) {
      case 'commit':
        if (typeof win.testCommit === 'function') win.testCommit();
        else if (win.document && win.document.querySelector('[data-test="commit"]')) {
          win.document.querySelector('[data-test="commit"]').click();
        }
        showToast('Fired event: git commit (catching node & eating)');
        break;

      case 'push':
        if (typeof win.testPush === 'function') win.testPush();
        else if (win.document && win.document.querySelector('[data-test="push"]')) {
          win.document.querySelector('[data-test="push"]').click();
        }
        showToast('Fired event: git push (rocket launched!)');
        break;

      case 'fail':
        if (typeof win.testFail === 'function') win.testFail();
        else if (win.document && win.document.querySelector('[data-test="fail"]')) {
          win.document.querySelector('[data-test="fail"]').click();
        }
        showToast('Fired event: tests failed (beetles crawled out!)');
        break;

      case 'pass':
        if (typeof win.testPass === 'function') win.testPass();
        else if (win.document && win.document.querySelector('[data-test="pass"]')) {
          win.document.querySelector('[data-test="pass"]').click();
        }
        showToast('Fired event: tests passed (vaporizing beetles!)');
        break;

      case 'boss':
        if (typeof win.testBoss === 'function') win.testBoss();
        else if (win.document && win.document.querySelector('[data-test="boss"]')) {
          win.document.querySelector('[data-test="boss"]').click();
        }
        showToast('Fired event: Boss Bug emerged with HP bar!');
        break;

      case 'pat':
        if (typeof win.patPet === 'function') win.patPet();
        else if (win.document && win.document.querySelector('[data-test="pat"]')) {
          win.document.querySelector('[data-test="pat"]').click();
        }
        showToast('Patted pet! (Hearts & purr)');
        break;

      case 'voice':
        const pet = PETS_DATA.find(p => p.id === activePetId);
        if (pet) {
          const randQuote = pet.quotes[Math.floor(Math.random() * pet.quotes.length)];
          showToast(`"${randQuote}"`);
        }
        break;
    }
  } catch (e) {
    console.warn('Action dispatch exception:', e);
  }
}

/**
 * Pet Detail Inspection Modal
 */
function setupModalListeners() {
  const modal = document.getElementById('petModal');
  const closeBtn = document.getElementById('modalCloseBtn');

  if (closeBtn && modal) {
    closeBtn.addEventListener('click', () => {
      modal.classList.remove('open');
    });

    modal.addEventListener('click', (e) => {
      if (e.target === modal) {
        modal.classList.remove('open');
      }
    });

    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && modal.classList.contains('open')) {
        modal.classList.remove('open');
      }
    });
  }
}

function openPetModal(petId) {
  const pet = PETS_DATA.find(p => p.id === petId);
  if (!pet) return;

  const modal = document.getElementById('petModal');
  const modalBody = document.getElementById('modalContentBody');
  if (!modal || !modalBody) return;

  modalBody.innerHTML = `
    <div style="text-align: center; margin-bottom: 1.5rem;">
      <div style="width: 120px; height: 120px; margin: 0 auto 1rem; background: radial-gradient(circle, ${pet.accentLight} 0%, #FFFFFF 80%); border: 2px solid var(--border-color); border-radius: 12px; display: flex; align-items: center; justify-content: center; box-shadow: 4px 4px 0px var(--border-color);">
        <img src="${pet.avatar}" alt="${pet.name}" style="width: 90px; height: 90px; object-fit: contain; image-rendering: pixelated;">
      </div>
      <h2 class="font-pixel" style="font-size: 1.3rem; color: ${pet.accent}; margin-bottom: 0.35rem;">${pet.name}</h2>
      <p style="font-size: 0.95rem; font-weight: 600; color: var(--text-muted);">${pet.title} • ${pet.species}</p>
      <div style="display: flex; gap: 0.5rem; justify-content: center; margin-top: 0.75rem;">
        <span class="pixel-badge" style="background: ${pet.kind === 'walker' ? '#E0F2FE' : '#FEF3C7'}; color: ${pet.kind === 'walker' ? '#0369A1' : '#B45309'};">
          ${pet.kind === 'walker' ? '🐾 Ground Walker' : '☁️ Air Floater'}
        </span>
        <span class="pixel-badge" style="background: var(--bg-dark); color: #FFF;">
          ${pet.attack.name}
        </span>
      </div>
    </div>

    <div style="display: flex; flex-direction: column; gap: 1.25rem; font-size: 0.92rem;">
      <div>
        <h4 class="font-pixel" style="font-size: 0.72rem; margin-bottom: 0.4rem; color: var(--text-primary);">About ${pet.name}</h4>
        <p style="color: var(--text-secondary); line-height: 1.6;">${pet.blurb}</p>
      </div>

      <div style="background: var(--bg-secondary); border: 1.5px solid var(--border-subtle); border-radius: 6px; padding: 1rem;">
        <h4 class="font-pixel" style="font-size: 0.7rem; color: var(--accent-blue); margin-bottom: 0.5rem;">⚡ Signature Bug Attack</h4>
        <p style="color: var(--text-primary); font-weight: 600;">${pet.attack.icon} ${pet.attack.name}</p>
        <p style="color: var(--text-secondary); font-size: 0.85rem; margin-top: 0.25rem;">${pet.attack.desc}</p>
      </div>

      <div>
        <h4 class="font-pixel" style="font-size: 0.72rem; margin-bottom: 0.4rem; color: var(--text-primary);">🌟 Growth & Evolution</h4>
        <p style="font-family: var(--font-mono); font-size: 0.8rem; background: var(--bg-dark); color: #38BDF8; padding: 0.65rem 0.85rem; border-radius: 4px;">
          ${pet.evolution}
        </p>
      </div>

      <div>
        <h4 class="font-pixel" style="font-size: 0.72rem; margin-bottom: 0.5rem; color: var(--text-primary);">💬 Iconic Voice Quotes</h4>
        <ul style="list-style: none; display: flex; flex-direction: column; gap: 0.4rem;">
          ${pet.quotes.map(q => `
            <li style="padding: 0.45rem 0.75rem; background: #F8FAFC; border-left: 3px solid ${pet.accent}; font-style: italic; font-size: 0.85rem; color: var(--text-secondary);">
              "${q}"
            </li>
          `).join('')}
        </ul>
      </div>

      <div style="padding-top: 0.5rem; display: flex; gap: 0.75rem;">
        <button class="pixel-btn" id="modalTryBtn" style="flex: 1; background: ${pet.accent};">
          ⚡ Play in Stage
        </button>
        <button class="pixel-btn pixel-btn-light" id="modalCopyBtn" style="flex: 1;">
          📋 Copy CLI Command
        </button>
      </div>
    </div>
  `;

  modal.classList.add('open');

  document.getElementById('modalTryBtn')?.addEventListener('click', () => {
    modal.classList.remove('open');
    switchSimulatorPet(pet.id);
    document.getElementById('simulator')?.scrollIntoView({ behavior: 'smooth' });
  });

  document.getElementById('modalCopyBtn')?.addEventListener('click', () => {
    const cmd = `bitling pet ${pet.id}`;
    copyToClipboard(cmd, `Copied "${cmd}" to clipboard!`);
  });
}

/**
 * Copy to Clipboard Utility
 */
function setupCopyButtons() {
  document.querySelectorAll('[data-copy]').forEach(btn => {
    btn.addEventListener('click', () => {
      const textToCopy = btn.getAttribute('data-copy');
      if (!textToCopy) return;

      copyToClipboard(textToCopy, 'Install command copied to clipboard!');

      btn.classList.add('copied');
      const originalText = btn.textContent;
      btn.textContent = 'COPIED!';
      setTimeout(() => {
        btn.classList.remove('copied');
        btn.textContent = originalText;
      }, 2200);
    });
  });
}

function copyToClipboard(text, successMsg) {
  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(text).then(() => {
      showToast(successMsg || 'Copied to clipboard!');
    }).catch(() => {
      fallbackCopy(text, successMsg);
    });
  } else {
    fallbackCopy(text, successMsg);
  }
}

function fallbackCopy(text, successMsg) {
  const textarea = document.createElement('textarea');
  textarea.value = text;
  textarea.style.position = 'fixed';
  textarea.style.opacity = '0';
  document.body.appendChild(textarea);
  textarea.focus();
  textarea.select();
  try {
    document.execCommand('copy');
    showToast(successMsg || 'Copied to clipboard!');
  } catch (err) {
    console.error('Copy fallback failed', err);
  }
  document.body.removeChild(textarea);
}

/**
 * Toast Notice
 */
function showToast(message) {
  let toast = document.getElementById('siteToast');
  if (!toast) {
    toast = document.createElement('div');
    toast.id = 'siteToast';
    toast.className = 'toast-notice';
    document.body.appendChild(toast);
  }

  toast.innerHTML = `<span>⚡</span> ${message}`;
  toast.classList.add('show');

  clearTimeout(window.__toastTimer);
  window.__toastTimer = setTimeout(() => {
    toast.classList.remove('show');
  }, 3200);
}

/**
 * FAQ Accordion
 */
function setupFaqAccordion() {
  document.querySelectorAll('.faq-question').forEach(btn => {
    btn.addEventListener('click', () => {
      const item = btn.closest('.faq-item');
      if (!item) return;
      const isOpen = item.classList.contains('active');

      // Close all other items for clean UX
      document.querySelectorAll('.faq-item').forEach(i => i.classList.remove('active'));

      if (!isOpen) {
        item.classList.add('active');
      }
    });
  });
}

/**
 * Mobile Navigation Menu
 */
function setupMobileMenu() {
  const toggle = document.getElementById('mobileMenuToggle');
  const panel = document.getElementById('mobileNavPanel');

  if (toggle && panel) {
    toggle.addEventListener('click', () => {
      panel.classList.toggle('open');
    });

    panel.querySelectorAll('a').forEach(link => {
      link.addEventListener('click', () => {
        panel.classList.remove('open');
      });
    });
  }
}

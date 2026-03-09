## Code Organization

### File Structure (ES6 Modules)

```
game/
├── index.html
├── main.js                 # Entry point, config
├── boot.json               # { "module": true }
│
├── scenes/
│   ├── Boot.js
│   ├── Preloader.js
│   ├── MainMenu.js
│   ├── Game.js
│   ├── GameOver.js
│   └── GameUI.js
│
├── gameobjects/
│   ├── Player.js
│   ├── Enemy.js
│   ├── Projectile.js
│   └── Platform.js
│
├── managers/
│   ├── EnemyManager.js
│   ├── LevelManager.js
│   └── ScoreManager.js
│
├── utils/
│   ├── GridUtils.js
│   └── MathUtils.js
│
└── constants/
    ├── SpriteKeys.js
    ├── AnimationKeys.js
    └── AudioKeys.js
```

---

### Module Imports

```javascript
// main.js
import Boot from './scenes/Boot.js';
import Preloader from './scenes/Preloader.js';
import Game from './scenes/Game.js';

const config = {
    type: Phaser.AUTO,
    width: 800,
    height: 600,
    scene: [Boot, Preloader, Game]
};

new Phaser.Game(config);

// Game.js
import Player from '../gameobjects/Player.js';
import EnemyManager from '../managers/EnemyManager.js';
import { SPRITE_KEYS, ANIMATION_KEYS } from '../constants/Keys.js';

export default class Game extends Phaser.Scene {
    // ...
}
```

---

### Constants Management

```javascript
// constants/SpriteKeys.js
export const SPRITE_KEYS = {
    PLAYER: 'player',
    ENEMY: 'enemy',
    PLATFORM: 'platform',
    COIN: 'coin'
};

// constants/AnimationKeys.js
export const ANIMATION_KEYS = {
    PLAYER_WALK: 'player-walk',
    PLAYER_JUMP: 'player-jump',
    PLAYER_IDLE: 'player-idle'
};

// constants/AudioKeys.js
export const AUDIO_KEYS = {
    JUMP: 'jump',
    COIN: 'coin',
    HIT: 'hit',
    MUSIC: 'music'
};

// Usage
import { SPRITE_KEYS, ANIMATION_KEYS } from './constants/Keys.js';

this.player = this.add.sprite(x, y, SPRITE_KEYS.PLAYER);
this.player.play(ANIMATION_KEYS.PLAYER_WALK);
```

**Benefits**:
- Type safety (catches typos)
- Single source of truth
- Easy refactoring
- IDE autocomplete

---

### Separation of Concerns

**Scenes**: Game flow, state management
**Game Objects**: Entity behavior, rendering
**Managers**: System coordination
**Utils**: Reusable helpers
**Constants**: Configuration

---

### Initialization Order

```javascript
create() {
    this.initVariables();      // Reset state
    this.initCamera();         // Camera config
    this.initPhysics();        // Physics world

    this.createBackground();   // Visuals
    this.createGroups();       // Physics groups
    this.createLevel();        // Static objects
    this.createPlayer();       // Dynamic objects
    this.createEnemies();      // Spawned objects

    this.initAnimations();     // Animation setup
    this.initInput();          // Input handlers
    this.setupCollisions();    // Collision rules

    this.createUI();           // HUD overlay
    this.startGame();          // Begin gameplay
}
```

---


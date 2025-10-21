## State Management

### Scene-Level State

```javascript
export default class GameScene extends Phaser.Scene {
    constructor() {
        super('GameScene');

        // Configuration (set once)
        this.gridWidth = 10;
        this.maxEnemies = 5;

        // References (initialized later)
        this.player;
        this.enemies;
    }

    init() {
        // Reset on scene restart
        this.score = 0;
        this.level = 1;
        this.gameOver = false;
    }

    create() {
        // Initialize objects
        this.player = new Player(this);
        this.enemies = [];
    }

    update() {
        if (this.gameOver) return;  // Early exit

        // Game logic
    }
}
```

**Pattern**:
- Constructor: Configuration
- Init: Resettable state
- Create: Object initialization
- Update: Game logic with guards

---

### Registry Pattern (Cross-Scene Persistence)

```javascript
// Boot.js - Initialize
create() {
    this.registry.set('highscore', 0);
    this.registry.set('musicVolume', 1);
}

// Any Scene - Read
this.highscore = this.registry.get('highscore');

// Any Scene - Update
this.registry.set('highscore', this.score);

// Listen for changes
this.registry.events.on('changedata-highscore', (parent, value) => {
    this.highscoreText.setText(`High: ${value}`);
});
```

**Use Case**: High scores, settings, unlocks that persist across scenes.

---

### LocalStorage Persistence

```javascript
// Load
create() {
    const saved = localStorage.getItem('highscore');
    this.highscore = (saved !== null) ? parseInt(saved) : 0;
}

// Save
gameOver() {
    if (this.score > this.highscore) {
        localStorage.setItem('highscore', this.score);
    }
}
```

---

### GameObject Data Component

```javascript
// Initialization
sprite.setData({
    gridX: x,
    gridY: y,
    type: 'enemy',
    health: 100
});

// Fast direct access (performance critical)
sprite.data.values.health -= damage;

// Slower method calls (initialization/infrequent)
sprite.data.set('health', newValue);
const health = sprite.data.get('health');

// Use case: Store current vs correct state
tile.setData({
    currentPosition: { x: 0, y: 0 },
    correctPosition: { x: 2, y: 3 }
});

// Win condition check
isCorrect() {
    return (
        tile.data.values.currentPosition.x ===
        tile.data.values.correctPosition.x
    );
}
```

**Benefits**:
- Type-safe custom properties
- No pollution of sprite namespace
- Event support via DataManager

---

### State Machines with Flags

```javascript
const GameStates = {
    LOADING: 0,
    READY: 1,
    PLAYING: 2,
    PAUSED: 3,
    GAME_OVER: 4
};

constructor() {
    this.state = GameStates.LOADING;
}

update() {
    switch (this.state) {
        case GameStates.PLAYING:
            this.updateGameplay();
            break;
        case GameStates.PAUSED:
            // Skip gameplay updates
            break;
    }
}

// Or simpler boolean flags
constructor() {
    this.isPaused = false;
    this.isGameOver = false;
    this.allowInput = true;
}

update() {
    if (this.isGameOver || this.isPaused) return;
    if (!this.allowInput) return;

    // Process normally
}
```

---

### Entity State Flags

```javascript
constructor() {
    this.isAlive = true;
    this.isInvincible = false;
    this.isGrounded = false;
    this.isFiring = false;
}

preUpdate(time, delta) {
    super.preUpdate(time, delta);

    if (!this.isAlive) return;

    // Ground check
    this.isGrounded = this.body.touching.down;

    // Jump only when grounded
    if (JustDown(this.jumpKey) && this.isGrounded) {
        this.jump();
    }
}
```

---

### Cross-Scene Communication via Events

```javascript
// Emit from one scene
this.registry.events.emit('player-hit', damageAmount);

// Listen in another scene
this.registry.events.on('player-hit', (damage) => {
    this.updateHealthBar(damage);
});

// Cleanup
shutdown() {
    this.registry.events.removeAllListeners();
}
```

---


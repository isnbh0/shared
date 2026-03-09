## Animation System

### Global Animation Creation

**Principle**: Create animations once in Preloader, use everywhere.

```javascript
// Preloader.js - create() method
this.anims.create({
    key: 'player-walk',
    frames: this.anims.generateFrameNumbers('player', {
        start: 0,
        end: 3
    }),
    frameRate: 10,
    repeat: -1  // Infinite loop
});

this.anims.create({
    key: 'player-idle',
    frames: [{ key: 'player', frame: 4 }],  // Single frame
    frameRate: 20
});

// Atlas-based with prefix
this.anims.create({
    key: 'enemy-walk',
    frames: this.anims.generateFrameNames('sprites', {
        prefix: 'enemy-walk-',
        start: 1,
        end: 4,
        zeroPad: 2  // enemy-walk-01, enemy-walk-02, etc.
    }),
    frameRate: 8,
    repeat: -1
});

// Yoyo animation
this.anims.create({
    key: 'idle-breathe',
    frames: this.anims.generateFrameNumbers('player', {
        start: 0,
        end: 3
    }),
    yoyo: true,
    frameRate: 6,
    repeat: -1
});
```

---

### Reverse Animation Technique

```javascript
// Forward animation
this.anims.create({
    key: 'door-open',
    frames: this.anims.generateFrameNames('objects', {
        prefix: 'door-',
        start: 1,
        end: 5
    }),
    frameRate: 20
});

// Reverse the same frames
this.anims.create({
    key: 'door-close',
    frames: this.anims.generateFrameNames('objects', {
        prefix: 'door-',
        start: 5,
        end: 1  // Reverse order
    }),
    frameRate: 20
});
```

**Benefit**: Reuse assets without duplicate frames.

---

### Animation-Driven Game Logic

```javascript
start() {
    this.on('animationcomplete-throw-start', this.releaseProjectile, this);
    this.on('animationcomplete-throw-end', this.throwComplete, this);
    this.on('animationcomplete-die', this.onDeathComplete, this);

    this.play('idle', true);
}

releaseProjectile() {
    this.play('throw-end');
    this.spawnProjectile(this.x, this.y);
}

throwComplete() {
    this.isThrowing = false;
    this.play('idle');
}
```

**Pattern**: Perfect visual-gameplay synchronization via animation events. Chain animations through callbacks.

---

### State-Based Animation Control

```javascript
updateAnimation(newState) {
    // Avoid redundant animation calls
    if (this.prevState !== newState && !this.isBlocking) {
        this.prevState = newState;
        this.anims.play(newState);
    }
}

update() {
    if (this.velocity.x < 0) {
        this.updateAnimation('walk-left');
    } else if (this.velocity.x > 0) {
        this.updateAnimation('walk-right');
    } else {
        this.updateAnimation('idle');
    }
}
```

**Pattern**: Track previous state to prevent redundant animation restarts.

---

### External Animation Data

```javascript
// Load animation JSON
preload() {
    this.load.animation('spriteAnims', 'animations.json');
}

// JSON format
{
    "anims": [
        {
            "key": "walk",
            "type": "frame",
            "frames": [
                { "key": "sprite", "frame": "walk-01" },
                { "key": "sprite", "frame": "walk-02" }
            ],
            "frameRate": 10,
            "repeat": -1
        }
    ]
}
```

**Benefit**: Designer-friendly, no code changes for animation tweaks.

---


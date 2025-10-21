## Game Loop Patterns

### Standard Update Pattern

```javascript
update(time, delta) {
    if (this.gameOver) return;  // Early exit

    // Process input
    this.handleInput();

    // Update entities
    this.player.update(time, delta);
    this.enemies.forEach(enemy => enemy.update(time, delta));

    // Check conditions
    this.checkWinCondition();
}
```

---

### Minimal Update (Event-Driven)

```javascript
// No update() method needed
// Use timers, callbacks, and events instead

create() {
    // Timer-based updates
    this.time.addEvent({
        delay: 1000,
        callback: this.updateScore,
        callbackScope: this,
        loop: true
    });

    // Input events
    this.input.on('pointerdown', this.handleClick, this);

    // Tween callbacks
    this.tweens.add({
        targets: sprite,
        x: 800,
        onComplete: () => this.nextLevel()
    });
}
```

**When to Use**: Turn-based, puzzle games, grid-based games.

---

### PreUpdate for Custom Game Objects

```javascript
class Enemy extends Phaser.Physics.Arcade.Sprite {
    preUpdate(time, delta) {
        super.preUpdate(time, delta);  // ESSENTIAL for animations

        if (!this.active) return;

        // Custom per-frame logic
        this.updateAI(time, delta);
        this.checkBoundaries();
    }
}
```

**Critical**: Must call `super.preUpdate()` for animations to work.

---

### Update Delegation

```javascript
// Scene delegates to systems/managers
update(time, delta) {
    if (this.isPaused) return;

    this.player.update(time, delta);
    this.enemyManager.update(time, delta);
    this.particleSystem.update(time, delta);
}

// Manager updates its entities
class EnemyManager {
    update(time, delta) {
        this.enemies.forEach(enemy => {
            if (enemy.active) {
                enemy.update(time, delta);
            }
        });
    }
}
```

---

### Timer-Based Events

```javascript
// Recurring timer
this.scoreTimer = this.time.addEvent({
    delay: 1000,
    callback: () => {
        this.score++;
        this.scoreText.setText(this.score);
    },
    callbackScope: this,
    repeat: -1  // Infinite
});

// One-shot delay
this.time.delayedCall(2000, () => {
    this.startGame();
}, [], this);

// Variable delay
const delay = Phaser.Math.Between(3000, 6000);
this.time.delayedCall(delay, this.spawnEnemy, [], this);

// Pause/resume
this.timer.paused = true;
this.timer.paused = false;

// Stop and remove
this.timer.remove(false);

// Cleanup
shutdown() {
    if (this.timer) {
        this.timer.destroy();
    }
}
```

---


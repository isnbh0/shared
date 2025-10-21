## Movement Patterns

### Velocity-Based Movement (Continuous)

**For**: Action games, platformers, physics-based gameplay.

```javascript
update() {
    if (this.cursors.left.isDown) {
        this.player.setVelocityX(-speed);
        this.player.anims.play('walk-left', true);
    }
    else if (this.cursors.right.isDown) {
        this.player.setVelocityX(speed);
        this.player.anims.play('walk-right', true);
    }
    else {
        this.player.setVelocityX(0);
        this.player.anims.play('idle');
    }

    // Jump with ground check
    if (this.cursors.up.isDown && this.player.body.touching.down) {
        this.player.setVelocityY(-jumpForce);
    }
}
```

**Pattern**:
- Set velocity, physics handles position
- Immediate stop when released
- Animation tied to movement
- Ground check via `body.touching.down`

---

### Time-Based Discrete Movement (Grid/Turn-Based)

**For**: Grid-based games, turn-based, puzzle games.

```javascript
create() {
    this.moveTime = 0;
    this.moveDelay = 200;  // Milliseconds between moves
}

update(time) {
    if (time >= this.moveTime) {
        this.move(time);
    }
}

move(time) {
    // Update position based on direction
    this.position.x += this.direction.x;
    this.position.y += this.direction.y;

    // Update visual
    this.sprite.x = this.position.x * GRID_SIZE;
    this.sprite.y = this.position.y * GRID_SIZE;

    // Schedule next move
    this.moveTime = time + this.moveDelay;
}
```

**Benefits**:
- Frame-rate independent
- Easy speed adjustment
- Natural for turn-based mechanics
- Better performance than continuous updates

---

### Timer-Based Movement (No Update Loop)

```javascript
create() {
    this.timer = this.time.addEvent({
        delay: 250,
        callback: this.moveEntities,
        callbackScope: this,
        loop: true
    });
}

moveEntities() {
    this.entities.forEach(entity => {
        entity.x += GRID_SIZE * entity.direction;
    });
}

// Stop/restart pattern
pause() {
    this.timer.paused = true;
}

resume() {
    this.timer.paused = false;
}

changeSpeed(newDelay) {
    this.timer.remove();
    this.timer = this.time.addEvent({
        delay: newDelay,
        callback: this.moveEntities,
        callbackScope: this,
        loop: true
    });
}
```

**Use Case**: Snake, falling block games, discrete movement without update polling.

---

### Pursuit/Follow Pattern

```javascript
// Mouse/pointer following
create() {
    this.target = new Phaser.Math.Vector2();

    this.input.on('pointermove', (pointer) => {
        this.target.x = pointer.x;
        this.target.y = pointer.y;
    });
}

update() {
    if (this.isActive) {
        // moveToObject returns angle
        const angle = this.physics.moveToObject(
            this.sprite,
            this.target,
            this.speed
        );

        // Adjust rotation (π/2 if sprite faces up)
        this.sprite.rotation = angle + Math.PI / 2;

        // Stop when close enough
        const distance = Phaser.Math.Distance.Between(
            this.sprite.x, this.sprite.y,
            this.target.x, this.target.y
        );

        if (distance < 6) {
            this.sprite.body.reset(this.target.x, this.target.y);
        }
    }
}
```

---

### Direction Validation Pattern

**Problem**: Allowing invalid 180-degree turns in Snake-like games.

**Solution**: Dual direction properties.

```javascript
constructor() {
    this.heading = RIGHT;    // Intended direction (input)
    this.direction = RIGHT;  // Current direction (validated)
}

faceLeft() {
    // Only allow perpendicular turns
    if (this.direction === UP || this.direction === DOWN) {
        this.heading = LEFT;
    }
}

move() {
    // Apply validated direction
    this.direction = this.heading;

    switch (this.direction) {
        case UP:
            this.position.y -= 1;
            break;
        // ... other directions
    }
}
```

---

### Screen Wrapping

```javascript
// Manual wrapping
if (this.x < 0) this.x = gameWidth;
if (this.x > gameWidth) this.x = 0;
if (this.y < 0) this.y = gameHeight;
if (this.y > gameHeight) this.y = 0;

// Using Phaser.Math.Wrap
this.x = Phaser.Math.Wrap(this.x, 0, gameWidth);
this.y = Phaser.Math.Wrap(this.y, 0, gameHeight);
```

**Creates**: Toroidal topology, eliminates boundary collision detection.

---

### Projectile Motion (Arc)

```javascript
fire(x, y) {
    this.setVelocityX(-600);
    this.setAccelerationX(-1400);  // Creates arc
}
```

**Technique**: Initial velocity + continuous acceleration = curved path.

---


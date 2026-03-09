## Input Handling

### Cursor Keys Setup

```javascript
create() {
    // Auto-creates left, right, up, down, space, shift
    this.cursors = this.input.keyboard.createCursorKeys();
}

update() {
    if (this.cursors.left.isDown) {
        // Handle input
    }
}
```

---

### JustDown Pattern (Single-Press Detection)

**Problem**: Continuous firing while key held.

**Solution**: JustDown only triggers once per press.

```javascript
constructor(scene) {
    this.spacebar = scene.input.keyboard.addKey(
        Phaser.Input.Keyboard.KeyCodes.SPACE
    );
}

preUpdate(time, delta) {
    super.preUpdate(time, delta);

    if (Phaser.Input.Keyboard.JustDown(this.spacebar) && !this.isFiring) {
        this.fire();
    }
}
```

**Use Case**: Jumping, shooting, menu navigation.

---

### Dual Input Support (Keyboard + Pointer)

```javascript
// Setup
this.cursors = this.input.keyboard.createCursorKeys();
this.input.on('pointerdown', this.handlePointerDown, this);

// Keyboard
update() {
    if (this.cursors.left.isDown) {
        this.moveLeft();
    }
}

// Pointer (mouse + touch)
handlePointerDown(pointer) {
    if (pointer.x < this.player.x) {
        this.moveLeft();
    } else {
        this.moveRight();
    }
}
```

**Benefits**: Accessibility, mobile support, player choice.

---

### Event-Driven Pointer Movement

```javascript
create() {
    this.input.on('pointermove', (pointer) => {
        if (this.isActive) {
            // Clamp within boundaries
            this.player.x = Phaser.Math.Clamp(
                pointer.x,
                minBound,
                maxBound
            );

            // Update dependent objects
            if (this.attachedObject) {
                this.attachedObject.x = this.player.x;
            }
        }
    }, this);
}
```

**Technique**: Event-driven vs polling in update() for better performance.

---

### Interactive Objects

```javascript
// Individual object interaction
sprite.setInteractive();
sprite.on('pointerdown', () => {
    this.handleClick(sprite);
});

// Hover effects
sprite.on('pointerover', () => {
    sprite.setTint(0xffff00);
    this.input.setDefaultCursor('pointer');
});

sprite.on('pointerout', () => {
    sprite.clearTint();
    this.input.setDefaultCursor('default');
});

// Scene-wide delegation
this.input.on('gameobjectdown', (pointer, gameObject) => {
    this.handleClick(gameObject);
});
```

---

### Input Gating/Locking

```javascript
onClick() {
    if (!this.allowClick) return;  // Gate check
    if (this.gameOver) return;

    this.allowClick = false;  // Disable during processing

    this.processAction();

    // Re-enable after animation
    this.time.delayedCall(duration, () => {
        this.allowClick = true;
    }, [], this);
}
```

**Purpose**: Prevent rapid clicking, double-triggers during animations.

---

### One-Time Input

```javascript
// Auto-cleanup after firing
this.input.once('pointerdown', () => {
    this.scene.start('NextScene');
});

this.input.keyboard.once('keydown-SPACE', this.start, this);

// Multiple triggers for same action
this.input.keyboard.once('keydown-SPACE', this.start, this);
this.input.keyboard.once('keydown-UP', this.start, this);
this.input.keyboard.once('keydown-DOWN', this.start, this);
this.input.once('pointerdown', this.start, this);
```

**Use Case**: Scene transitions, "click to continue", prevent double-triggers.

---

### Input Cleanup Pattern

```javascript
cleanup() {
    // Remove event listeners
    this.input.off('gameobjectdown', this.onClick);
    this.input.keyboard.off('keydown-SPACE', this.action);

    // Remove timers
    if (this.timer) {
        this.timer.remove(false);
    }
}
```

**Critical**: Prevents memory leaks and duplicate listeners.

---

### Context Menu Disabling

```javascript
create() {
    // For custom right-click handling
    this.input.mouse.disableContextMenu();
}

onPointerDown(pointer) {
    if (pointer.rightButtonDown()) {
        this.handleRightClick();
    }
}
```

---


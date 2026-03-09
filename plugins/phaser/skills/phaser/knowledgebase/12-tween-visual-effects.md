## Tween & Visual Effects

### Basic Tween Patterns

```javascript
// Simple property animation
this.tweens.add({
    targets: sprite,
    y: 400,
    duration: 1000,
    ease: 'Power2'
});

// Multiple properties
this.tweens.add({
    targets: sprite,
    x: 400,
    y: 300,
    alpha: 0,
    duration: 1000,
    ease: 'Cubic.easeInOut'
});

// Relative values
this.tweens.add({
    targets: sprite,
    x: '+=100',   // Move 100 pixels right
    y: '-=50',    // Move 50 pixels up
    duration: 500
});

// Yoyo (bounce back)
this.tweens.add({
    targets: sprite,
    y: '-=20',
    duration: 200,
    ease: 'Quad.easeOut',
    yoyo: true
});

// Loop
this.tweens.add({
    targets: sprite,
    angle: 360,
    duration: 2000,
    repeat: -1  // Infinite
});
```

---

### Multi-Property Synchronized Tweens

```javascript
this.tweens.add({
    targets: sprite,
    props: {
        scaleX: { value: 1.2, duration: 250 },
        scaleY: { value: 0.8, duration: 250 },
        angle: { value: 360, duration: 500, delay: 250 }
    },
    ease: 'Sine.easeInOut',
    yoyo: true,
    repeat: -1
});
```

**Pattern**: Each property can have independent duration and delay.

---

### Tween Callbacks

```javascript
this.tweens.add({
    targets: sprite,
    x: 800,
    duration: 1000,
    ease: 'Power2',
    onStart: () => {
        this.sound.play('slide');
    },
    onUpdate: (tween) => {
        const progress = tween.progress;
        sprite.alpha = progress;
    },
    onComplete: () => {
        sprite.destroy();
        this.spawnNext();
    }
});
```

---

### Staggered Animations

```javascript
// Cascade effect
items.forEach((item, index) => {
    this.tweens.add({
        targets: item,
        y: finalY,
        duration: 800,
        delay: index * 100,  // Stagger
        ease: 'Bounce.out'
    });
});

// Grid stagger (from center)
this.tweens.add({
    targets: this.tiles.getChildren(),
    scale: { from: 0, to: 1 },
    ease: 'bounce.out',
    duration: 600,
    delay: this.tweens.stagger(100, {
        grid: [4, 4],
        from: 'center'
    })
});
```

---

### Choreographed Sequences

```javascript
createIntroSequence() {
    let delay = 0;

    // Title drops in
    this.tweens.add({
        targets: this.title,
        y: 200,
        duration: 1000,
        delay: delay,
        ease: 'Bounce.out'
    });
    delay += 1200;

    // Menu items fade in sequentially
    this.menuItems.forEach((item, i) => {
        this.tweens.add({
            targets: item,
            alpha: 1,
            duration: 300,
            delay: delay + (i * 100)
        });
    });
    delay += 500;

    // Enable input after sequence
    this.time.delayedCall(delay, () => {
        this.enableInput();
    });

    return delay;  // Return for composition
}
```

**Pattern**: Accumulating delay variable for complex choreography.

---

### Tween Chaining

```javascript
this.tweens.chain({
    targets: sprite,
    tweens: [
        { x: 200, duration: 500 },
        { y: 300, duration: 500 },
        { scale: 2, duration: 500 },
        { alpha: 0, duration: 500 }
    ]
});
```

---

### Tweening Non-GameObjects

```javascript
// Tween arbitrary objects
const shaderController = new CustomShader.Controller();

this.tweens.add({
    targets: shaderController,
    progress: 1,
    intensity: 0,
    duration: 2000
});

// Tween counters
this.tweens.addCounter({
    from: 0,
    to: 100,
    duration: 1000,
    onUpdate: (tween) => {
        const value = tween.getValue();
        this.updateDisplay(value);
    }
});
```

---

### Camera Effects

```javascript
// Shake
this.cameras.main.shake(duration, intensity);

// Flash
this.cameras.main.flash(duration, r, g, b);

// Fade
this.cameras.main.fadeOut(duration, r, g, b);
this.cameras.main.fadeIn(duration, r, g, b);

// Fade with callback
this.cameras.main.fadeOut(1000);
this.cameras.main.once('camerafadeoutcomplete', () => {
    this.scene.start('NextScene');
});

// Zoom
this.cameras.main.zoomTo(2, 1000);
```

---

### Particle Effects

```javascript
// Create emitter
this.particles = this.add.particles(0, 0, 'particle', {
    speed: { min: 200, max: 400 },
    lifespan: 1000,
    scale: { start: 1, end: 0 },
    alpha: { start: 1, end: 0 },
    rotate: { start: 0, end: 360 },
    blendMode: 'ADD',
    emitting: false  // Manual control
});

// One-shot effect
this.particles.explode(particleCount, x, y);

// Continuous effect
this.particles.emitParticleAt(x, y, count);

// Follow object
this.particles.startFollow(sprite);
this.particles.stopFollow();
```

---


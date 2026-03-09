## Physics & Collision

### Physics Configuration Levels

**Global Configuration**:
```javascript
const config = {
    physics: {
        default: 'arcade',
        arcade: {
            gravity: { y: 300 },
            debug: false
        }
    }
};
```

**World-Level Configuration**:
```javascript
create() {
    // Extended bounds for spawning outside view
    this.physics.world.setBounds(0, -400, width, height + 400);

    // Selective wall collision
    this.physics.world.setBoundsCollision(
        true,   // left
        true,   // right
        true,   // top
        false   // bottom - disable for fall detection
    );
}
```

**Object-Level Configuration**:
```javascript
// Moving object with bouncing
sprite.setCollideWorldBounds(true);
sprite.setBounce(1);  // 1 = perfect elastic collision
sprite.setVelocity(vx, vy);

// Immovable object
sprite.setImmovable();

// Custom gravity per object
sprite.setGravityY(-offset);  // Offset global gravity

// Circular hitbox
sprite.setCircle(radius, offsetX, offsetY);

// Custom rectangular hitbox
sprite.setSize(width, height);
sprite.setOffset(x, y);
```

---

### Collision vs Overlap

**Collider** - Physical collision with bounce/blocking:
```javascript
this.physics.add.collider(
    playerGroup,
    platformGroup
);
```

**Overlap** - Trigger-based detection without physics response:
```javascript
this.physics.add.overlap(
    player,
    collectibles,
    this.onCollect,      // Callback
    null,                 // Process callback
    this                  // Context
);
```

**Collision with Callback**:
```javascript
this.physics.add.collider(
    player,
    enemies,
    (player, enemy) => {
        if (player.isAlive && enemy.alpha === 1) {
            this.handleHit(player, enemy);
        }
    },
    null,
    this
);
```

**Pattern**: Use collider for physical interactions, overlap for triggers/pickups.

---

### Position-Based Dynamic Response

**Problem**: Boring, predictable collisions.

**Solution**: Vary response based on collision position.

```javascript
hitPaddle(ball, paddle) {
    const diff = ball.x - paddle.x;

    if (Math.abs(diff) < 10) {
        // Center hit - add randomness
        ball.setVelocityX(
            Phaser.Math.Between(-100, 100)
        );
    } else {
        // Side hit - angle based on distance
        ball.setVelocityX(diff * multiplier);
    }
}
```

**Benefits**:
- Player skill expression
- Prevents monotonous gameplay
- Breaks edge cases

---

### State-Gated Collision

```javascript
onCollision(player, enemy) {
    // Multiple validation gates
    if (!player.isAlive) return;
    if (player.invincible) return;
    if (enemy.alpha < 1) return;  // Fading in/out
    if (!enemy.active) return;

    // Process collision
    this.handleDamage(player, enemy);
}
```

**Principle**: Validate all relevant states before processing collision.

---

### Per-Track/Layer Collision Isolation

```javascript
class Track {
    constructor(scene, id, y) {
        // Each track has isolated physics groups
        this.playerProjectiles = scene.physics.add.group();
        this.enemyProjectiles = scene.physics.add.group();
        this.enemies = scene.physics.add.group();

        // Collisions only within this track
        scene.physics.add.overlap(
            this.playerProjectiles,
            this.enemies,
            this.hitEnemy,
            null,
            this
        );
    }
}
```

**Use Case**: Multi-lane games, layered gameplay (like Duck Hunt).

---


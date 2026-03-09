## Object Pooling & Memory

### Group-Based Object Pooling

**Problem**: Creating/destroying objects causes GC pauses.

**Solution**: Pre-create objects, recycle via enable/disable.

```javascript
create() {
    // Pre-create pool
    this.projectiles = this.physics.add.group({
        classType: Projectile,
        frameQuantity: 20,      // Pre-create 20 instances
        key: 'projectile',
        active: false,
        visible: false,
        maxSize: 20             // Pool won't grow beyond this
    });
}

// Get from pool
fire() {
    const projectile = this.projectiles.getFirstDead(false);
    if (projectile) {
        projectile.fire(this.x, this.y);
    }
}

// Projectile class
fire(x, y) {
    this.body.reset(x, y);
    this.setActive(true);
    this.setVisible(true);
    this.setVelocity(vx, vy);
}

stop() {
    this.setActive(false);
    this.setVisible(false);
    this.body.enable = false;
}

// Auto-recycling in preUpdate
preUpdate(time, delta) {
    super.preUpdate(time, delta);

    if (this.x < -64 || this.x > width + 64) {
        this.stop();
    }
}
```

**Benefits**:
- No object creation/destruction during gameplay
- Fixed pool size prevents GC spikes
- `getFirstDead()` auto-manages recycling
- Better performance

---

### Enable/Disable Pattern

```javascript
// Disable (hide and deactivate)
collect(item) {
    item.disableBody(true, true);  // (disableGameObject, hideGameObject)
}

// Re-enable (show and reactivate)
reset(item) {
    item.enableBody(
        true,      // resetX
        item.x,    // x position
        item.startY,  // y position
        true,      // enableGameObject
        true       // showGameObject
    );
}

// Check if all collected
if (this.items.countActive(true) === 0) {
    this.respawnAll();
}
```

**Pattern**: For collectibles, respawning enemies, anything that cycles.

---

### Object Reuse (Reset Pattern)

```javascript
// Instead of destroy/create
restart() {
    // Reset global state
    this.score = 0;
    this.gameOver = false;

    // Reset all entities
    this.entities.forEach(entity => entity.reset());

    // Reset UI
    this.scoreText.setText('0');
}

// Entity reset method
reset() {
    this.x = this.startX;
    this.y = this.startY;
    this.setVelocity(0, 0);
    this.clearTint();
    this.setAlpha(1);
    this.isAlive = true;
}
```

**Benefit**: More efficient than destroying and recreating, maintains references.

---

### Dynamic Texture Cleanup

```javascript
create() {
    this.dynamicTextures = [];
}

createDynamicTexture(key, width, height) {
    const texture = this.textures.addDynamicTexture(key, width, height);
    this.dynamicTextures.push(texture);
    return texture;
}

cleanup() {
    // Essential for preventing memory leaks
    this.dynamicTextures.forEach(tex => tex.destroy());
    this.dynamicTextures = [];
}
```

**Critical**: Dynamic textures must be explicitly destroyed.

---


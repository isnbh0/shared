## Performance Optimization

### Object Pooling (Detailed)

See [Object Pooling & Memory](#object-pooling--memory) section.

**Key Benefits**:
- Eliminates GC pauses during gameplay
- Fixed memory footprint
- Better frame stability

---

### Texture Caching

```javascript
createTexture(key, width, height) {
    // Check before generating
    if (!this.textures.exists(key)) {
        const texture = this.textures.addDynamicTexture(key, width, height);
        // Generate texture
        return texture;
    }
    return this.textures.get(key);
}
```

---

### Minimize Update Logic

```javascript
// BAD - Processes every frame
update() {
    this.objects.forEach(obj => {
        if (obj.y > 600) {
            obj.destroy();
        }
    });
}

// GOOD - Auto-recycle in object's preUpdate
preUpdate(time, delta) {
    super.preUpdate(time, delta);

    if (this.y > 600) {
        this.stop();  // Return to pool
    }
}
```

---

### Event-Driven Over Polling

```javascript
// BAD - Checks every frame
update() {
    if (this.player.x > this.goal.x) {
        this.handleWin();
    }
}

// GOOD - Event-driven
this.physics.add.overlap(this.player, this.goal, () => {
    this.handleWin();
});
```

---

### Static Groups for Immovable Objects

```javascript
// Better performance for platforms, walls, etc.
this.platforms = this.physics.add.staticGroup();

this.platforms.create(x, y, 'platform')
    .setScale(2)
    .refreshBody();  // Essential after scaling static bodies
```

---

### Texture Atlas Usage

See [Asset Management](#asset-management) section.

**Benefits**:
- Single draw call for multiple sprites
- Better GPU memory usage
- Faster rendering

---

### Depth Management

```javascript
// Set once instead of sorting every frame
this.background.setDepth(0);
this.player.setDepth(10);
this.enemies.setDepth(5);
this.hud.setDepth(100);
```

---

### Physics Debugging

```javascript
// Development only
const config = {
    physics: {
        default: 'arcade',
        arcade: {
            debug: true  // Disable in production
        }
    }
};
```

---


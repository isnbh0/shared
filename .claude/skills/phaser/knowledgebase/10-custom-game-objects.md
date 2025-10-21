## Custom Game Objects

### Extending Phaser.Sprite

```javascript
export default class Player extends Phaser.Physics.Arcade.Sprite {
    constructor(scene, x, y) {
        super(scene, x, y, 'player');

        // Self-registration
        scene.add.existing(this);
        scene.physics.add.existing(this);

        // Configuration
        this.setCollideWorldBounds(true);
        this.setSize(24, 32);
        this.setOffset(4, 0);

        // Custom properties
        this.speed = 160;
        this.jumpForce = -330;
        this.isAlive = true;

        // Input references
        this.cursors = scene.input.keyboard.createCursorKeys();
    }

    // Custom update logic
    preUpdate(time, delta) {
        super.preUpdate(time, delta);  // ESSENTIAL for animations

        if (!this.isAlive) return;

        this.handleMovement();
    }

    handleMovement() {
        if (this.cursors.left.isDown) {
            this.setVelocityX(-this.speed);
            this.anims.play('walk-left', true);
        } else if (this.cursors.right.isDown) {
            this.setVelocityX(this.speed);
            this.anims.play('walk-right', true);
        } else {
            this.setVelocityX(0);
            this.anims.play('idle');
        }
    }

    jump() {
        if (this.body.touching.down) {
            this.setVelocityY(this.jumpForce);
        }
    }
}
```

**Pattern**: Extend sprite when entity needs physics and rendering.

---

### Extending Phaser.Image

```javascript
export default class Pickup extends Phaser.Physics.Arcade.Image {
    constructor(scene, x, y) {
        super(scene, x, y, 'coin');

        scene.add.existing(this);
        scene.physics.add.existing(this);

        this.setCircle(12);
        this.setBounce(0.5);
        this.points = 10;
    }

    collect() {
        this.disableBody(true, true);
        return this.points;
    }
}
```

**When to Use**: Static sprites that need physics but no animations.

---

### Composition Pattern (Non-Visual)

```javascript
export default class Track {
    constructor(scene, id, y) {
        this.scene = scene;
        this.id = id;
        this.y = y;

        // Contains physics groups but isn't a sprite
        this.enemies = scene.physics.add.group();
        this.projectiles = scene.physics.add.group();

        // Setup collisions
        scene.physics.add.overlap(
            this.enemies,
            this.projectiles,
            this.onHit,
            null,
            this
        );
    }

    update() {
        // Update managed objects
        this.enemies.children.iterate(enemy => {
            enemy.update();
        });
    }

    onHit(enemy, projectile) {
        enemy.hit();
        projectile.stop();
    }
}
```

**When to Use**: Managers, systems, groups that don't need visual representation.

---

### Extending Groups

```javascript
export default class EnemyWave extends Phaser.Physics.Arcade.Group {
    constructor(world, scene) {
        super(world, scene);

        this.classType = Enemy;  // Group creates Enemy instances

        this.config = [
            { type: 'small', speed: 60 },
            { type: 'medium', speed: 90 },
            { type: 'large', speed: 120 }
        ];
    }

    spawn() {
        const config = Phaser.Math.RND.pick(this.config);
        const x = Phaser.Math.Between(0, 800);

        let enemy = this.getFirstDead(false);
        if (!enemy) {
            enemy = new Enemy(this.scene, x, 0, config);
            this.add(enemy);
        } else {
            enemy.reset(x, 0, config);
        }
    }

    update() {
        this.children.iterate(enemy => {
            if (enemy.active) {
                enemy.update();
            }
        });
    }
}
```

---


## UI/HUD Patterns

### Text Styling

```javascript
const textStyle = {
    fontFamily: 'Arial Black',
    fontSize: 32,
    color: '#ffffff',
    stroke: '#000000',
    strokeThickness: 6,
    shadow: {
        offsetX: 2,
        offsetY: 2,
        color: '#000',
        blur: 4,
        fill: true
    }
};

this.scoreText = this.add.text(32, 32, 'Score: 0', textStyle);
```

---

### Text Positioning

```javascript
// Top-left
this.add.text(16, 16, 'Score: 0', style);

// Top-right
this.add.text(width - 16, 16, 'Time: 60', style)
    .setOrigin(1, 0);  // Anchor to top-right

// Center
this.add.text(width / 2, height / 2, 'GAME OVER', style)
    .setOrigin(0.5);  // Center both axes

// Multiline centered
const lines = ['Line 1', 'Line 2', '', 'Line 4'];
this.add.text(centerX, centerY, lines, style)
    .setAlign('center')
    .setOrigin(0.5);
```

---

### Dynamic Text Updates

```javascript
// Simple update
this.scoreText.setText('Score: ' + this.score);

// With padding
this.scoreText.setText(
    Phaser.Utils.String.Pad(this.score, 6, '0', 1)
);

// Animated counter
this.tweens.addCounter({
    from: 0,
    to: targetValue,
    duration: 1000,
    onUpdate: (tween) => {
        const value = Math.floor(tween.getValue());
        this.scoreText.setText('Score: ' + value);
    }
});
```

---

### Bitmap Font (Seven-Segment Display)

```javascript
// Setup
this.digit1 = this.add.image(x, y, 'digits', 0).setOrigin(0);
this.digit2 = this.add.image(x + 13, y, 'digits', 0).setOrigin(0);
this.digit3 = this.add.image(x + 26, y, 'digits', 0).setOrigin(0);

updateDigits(value) {
    const padded = Phaser.Utils.String.Pad(value.toString(), 3, '0', 1);

    this.digit1.setFrame(parseInt(padded[0]));
    this.digit2.setFrame(parseInt(padded[1]));
    this.digit3.setFrame(parseInt(padded[2]));
}
```

---

### Icon-Based Counters

```javascript
// Lives counter
createLives() {
    this.hearts = this.add.group({
        key: 'heart',
        repeat: this.lives - 1,
        setXY: {
            x: startX,
            y: startY,
            stepX: spacing
        }
    });
}

loseLife() {
    const lastHeart = this.hearts.getChildren()[this.hearts.getLength() - 1];

    this.tweens.add({
        targets: lastHeart,
        y: -100,
        alpha: 0,
        duration: 500,
        onComplete: () => {
            lastHeart.destroy();
        }
    });

    this.lives--;
}
```

---

### Layered UI (Z-Ordering)

```javascript
create() {
    // Order of creation = z-order
    this.add.image(0, 0, 'background');           // Layer 0

    // Gameplay objects
    this.createPlayer();                          // Layer 1
    this.createEnemies();                         // Layer 2

    // UI overlay
    this.add.image(0, 0, 'ui-frame').setDepth(10);      // Layer 10
    this.scoreText = this.add.text(32, 32, '0').setDepth(11);  // Layer 11
}

// Manual z-ordering
this.hudText.setDepth(100);

// Container for grouping
this.hud = this.add.container(0, 0);
this.hud.add([this.scoreText, this.livesIcon, this.timerText]);
this.hud.setDepth(10);
```

---

### Semi-Transparent Overlay

```javascript
// Pause menu background
this.pauseOverlay = this.add.rectangle(
    width / 2,
    height / 2,
    width,
    height,
    0x000000,  // Black
    0.7        // 70% opacity
).setDepth(50);

this.pauseText = this.add.text(centerX, centerY, 'PAUSED', style)
    .setDepth(51);
```

---


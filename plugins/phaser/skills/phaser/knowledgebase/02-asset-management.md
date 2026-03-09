## Asset Management

### Two-Stage Loading Strategy

**Problem**: Long loading times create poor initial experience.

**Solution**: Load in two stages - minimal bootstrap, then full assets.

```javascript
// Stage 1: Boot Scene - Preloader UI assets only
preload() {
    this.load.image('background', 'assets/bg.png');
    this.load.image('logo', 'assets/logo.png');
}

// Stage 2: Preloader Scene - Full game assets
preload() {
    // Show loading screen with pre-loaded assets
    this.add.image(400, 300, 'background');
    const loadText = this.add.text(400, 300, 'Loading...', style);

    // Progress bar
    const bar = this.add.rectangle(x, y, 4, height, 0xffffff);
    this.load.on('progress', (progress) => {
        bar.width = minWidth + (maxWidth * progress);
    });

    // Load main assets
    this.load.setPath('assets/game/');
    this.load.atlas('sprites', 'sprites.png', 'sprites.json');
    this.load.audio('music', ['music.ogg', 'music.m4a', 'music.mp3']);
}
```

**Benefits**:
- Fast initial feedback
- Visual progress indication
- Better perceived performance

---

### Texture Atlas Pattern

**Problem**: Multiple HTTP requests, poor memory usage.

**Solution**: Combine sprites into single atlas.

```javascript
// Load atlas
preload() {
    this.load.atlas('gameSprites',
        'sprites.png',      // Texture
        'sprites.json'      // Frame data
    );
}

// Use frames
create() {
    this.add.sprite(x, y, 'gameSprites', 'player-idle-01');
    sprite.setFrame('enemy-small');
}
```

**Benefits**:
- Single HTTP request
- Reduced draw calls
- Better GPU memory usage
- Easier asset management

---

### Multi-Format Audio Loading

**Problem**: Different browsers support different audio formats.

**Solution**: Provide multiple formats, browser auto-selects.

```javascript
this.load.audio('music', [
    'assets/audio/music.ogg',  // Firefox, Chrome
    'assets/audio/music.m4a',  // Safari
    'assets/audio/music.mp3'   // Fallback
]);
```

---

### Centralized Asset Path Management

```javascript
preload() {
    this.load.setBaseURL('https://cdn.phaserfiles.com/v385');
    this.load.setPath('assets/games/my-game/');

    // All subsequent loads use this path
    this.load.image(['bg', 'logo', 'tiles']);

    // Change path for different asset types
    this.load.setPath('assets/audio/');
    this.load.audio('sfx', 'effect.mp3');
}
```

---

### Custom Font Loading Synchronization

```javascript
// Add font via DOM in init()
init() {
    const element = document.createElement('style');
    document.head.appendChild(element);
    element.sheet.insertRule(
        '@font-face { font-family: "CustomFont"; src: url("font.ttf"); }',
        0
    );
}

// Wait for font before proceeding
create() {
    WebFont.load({
        custom: { families: ['CustomFont'] },
        active: () => {
            this.scene.start('NextScene');
        }
    });
}
```

**Prevents**: FOUT (Flash of Unstyled Text), layout shifts.

---


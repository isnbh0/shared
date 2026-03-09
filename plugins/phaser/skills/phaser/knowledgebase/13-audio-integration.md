## Audio Integration

### Sound Management

```javascript
// Preload
preload() {
    this.load.audio('music', ['music.ogg', 'music.m4a', 'music.mp3']);
    this.load.audio('jump', 'jump.wav');
}

// Background music
create() {
    this.music = this.sound.play('music', {
        loop: true,
        volume: 0.7
    });
}

// Sound effects
jump() {
    this.sound.play('jump');
}

// With volume
this.sound.play('explosion', { volume: 1.2 });

// Stop all
gameOver() {
    this.sound.stopAll();
    this.sound.play('gameover');
}
```

---

### Audio Lock Handling

```javascript
// Check for browser audio restrictions
create() {
    if (this.sound.locked) {
        this.loadText.setText('Click to Start');
        this.input.once('pointerdown', () => {
            this.scene.start('MainMenu');
        });
    } else {
        this.scene.start('MainMenu');
    }
}
```

---

### Centralized Audio Management

```javascript
// UI Scene manages all audio
const AUDIO_KEYS = {
    JUMP: 'jump',
    COIN: 'coin',
    HIT: 'hit',
    MUSIC: 'music'
};

class GameUI extends Phaser.Scene {
    create() {
        this.audio = {};
        for (let key in AUDIO_KEYS) {
            this.audio[AUDIO_KEYS[key]] = this.sound.add(AUDIO_KEYS[key]);
        }
    }

    playAudio(key, allowOverlap = true) {
        if (!allowOverlap && this.audio[key].isPlaying) {
            return;
        }
        this.audio[key].play();
    }
}

// Game scene triggers sounds
this.uiScene.playAudio(AUDIO_KEYS.JUMP);
this.uiScene.playAudio(AUDIO_KEYS.STEP, false);  // No overlap
```

---

### Delayed/Sequenced Audio

```javascript
// Delay sound
this.sound.play('countdown', { delay: 27 });

// Multiple sounds with delays
this.sound.play('shot');
this.sound.play('shot', { delay: 0.25 });
this.sound.play('shot', { delay: 0.5 });
```

---

### Persistent Music Across Scenes

```javascript
// Preloader
create() {
    if (!this.music) {
        this.music = this.sound.play('music', { loop: true });
    }
    this.scene.start('MainMenu');
}

// Subsequent scenes don't restart music
```

---


## Scene Architecture

### Multi-Scene Flow Pattern

**Problem**: Managing different game states (loading, menu, gameplay, game over).

**Solution**: Dedicated scenes for each major state.

```javascript
const config = {
    scene: [ Boot, Preloader, MainMenu, Game, GameOver ]
};

// Scene progression
// Boot → Preloader → MainMenu → Game → GameOver → MainMenu
```

**Scene Responsibilities**:
- **Boot**: Minimal initialization, registry setup, load critical assets for preloader UI
- **Preloader**: Full asset loading with progress feedback, global animation creation
- **MainMenu**: Navigation, settings, high score display
- **Game**: Core gameplay logic
- **GameOver**: Results display, retry/exit options

**When to Use**: Any game with distinct phases beyond pure gameplay.

---

### Parallel Scene Pattern (UI Overlay)

**Problem**: Separating HUD from gameplay logic.

**Solution**: Run UI scene in parallel with game scene.

```javascript
// In Game scene
create() {
    this.scene.launch('GameUI');  // Launch parallel scene
    this.uiScene = this.scene.get('GameUI');
}

// Cross-scene communication
updateScore(points) {
    this.uiScene.updateScore(points);
}

// In GameUI scene
init() {
    this.scene.moveUp();  // Ensure UI stays on top
}
```

**Benefits**:
- Clean separation of concerns
- Independent update cycles
- Easier UI iteration
- Reusable UI scenes

**When to Use**: Games with complex HUD elements, multiple game modes sharing UI.

---

### Scene Transitions with Visual Effects

```javascript
// Simple transition
this.scene.start('NextScene');

// Fade transition
this.cameras.main.fadeOut(duration);
this.cameras.main.once('camerafadeoutcomplete', () => {
    this.scene.start('NextScene');
});

// With shader effects
this.tweens.add({
    targets: shaderController,
    progress: 1,
    duration: 2500,
    onComplete: () => this.scene.start('NextScene')
});

// Pause/overlay pattern
this.scene.pause();           // Pause current scene
this.scene.run('PauseMenu');  // Run overlay on top
```

**Principle**: Coordinate transitions with visual feedback for professional feel.

---

### Scene Data Passing

```javascript
// Send data during transition
this.scene.start('NextScene', {
    score: this.score,
    level: this.level
});

// Receive data
init(data) {
    if (Object.keys(data).length !== 0) {
        this.score = data.score;
        this.level = data.level;
    }
}
```

---


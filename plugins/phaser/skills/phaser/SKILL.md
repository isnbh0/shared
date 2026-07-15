---
name: phaser
description: Provides battle-tested patterns, best practices, and code examples for building Phaser 3 games. Use when writing game code, implementing game mechanics, setting up scenes, handling physics, animations, input, or any Phaser-related development. Covers architecture, performance, algorithms, and common pitfalls.
---

# Phaser 3 Game Development

## Quick Start

```javascript
const config = {
    scene: [Boot, Preloader, MainMenu, Game, GameOver]
};

create() {
    this.projectiles = this.physics.add.group({
        classType: Projectile,
        frameQuantity: 20,
        active: false,
        visible: false
    });
}

fire() {
    const projectile = this.projectiles.getFirstDead(false);
    if (projectile) projectile.fire(x, y);
}
```

Create global animations once in the preloader, use `Phaser.Input.Keyboard.JustDown` for edge-triggered input, and pool frequently created game objects.

## Knowledge Base

Read only the files relevant to the current task. `knowledgebase/TOC.md` is the complete index.

- `01-scene-architecture.md`
- `02-asset-management.md`
- `03-physics-collision.md`
- `04-movement-patterns.md`
- `05-animation-system.md`
- `06-input-handling.md`
- `07-state-management.md`
- `08-object-pooling-memory.md`
- `09-grid-systems.md`
- `10-custom-game-objects.md`
- `11-ui-hud-patterns.md`
- `12-tween-visual-effects.md`
- `13-audio-integration.md`
- `14-game-loop-patterns.md`
- `15-algorithm-implementations.md`
- `16-performance-optimization.md`
- `17-code-organization.md`
- `18-development-philosophy.md`

Search the bundled files when the relevant topic is unclear, for example `rg -i "collision|overlap" knowledgebase/`.

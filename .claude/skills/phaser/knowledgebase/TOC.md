# Phaser 3 Development Patterns & Best Practices - Table of Contents

A comprehensive, game-agnostic reference library of patterns, techniques, and architectural approaches for building high-quality Phaser 3 games.

## How to Use This Knowledge Base

- Start with the TOC below to find relevant topics
- Each section is in its own file for easy searching and reference
- Use grep/search to find specific patterns or techniques
- Sections are cross-referenced where patterns relate to each other

## Sections

1. [Scene Architecture](01-scene-architecture.md)
   - Multi-scene flow, parallel scenes, transitions, data passing

2. [Asset Management](02-asset-management.md)
   - Loading strategies, texture atlases, audio, fonts

3. [Physics & Collision](03-physics-collision.md)
   - Configuration, collision vs overlap, dynamic responses

4. [Movement Patterns](04-movement-patterns.md)
   - Velocity-based, discrete, timer-based, pursuit, screen wrapping

5. [Animation System](05-animation-system.md)
   - Global animations, state-based control, animation-driven logic

6. [Input Handling](06-input-handling.md)
   - Keyboard, pointer, touch, input gating, cleanup

7. [State Management](07-state-management.md)
   - Scene state, registry, localStorage, data components

8. [Object Pooling & Memory](08-object-pooling-memory.md)
   - Group-based pooling, enable/disable patterns, cleanup

9. [Grid Systems](09-grid-systems.md)
   - Dual coordinates, 2D arrays, adjacency, alignment

10. [Custom Game Objects](10-custom-game-objects.md)
    - Extending sprites, images, composition, groups

11. [UI/HUD Patterns](11-ui-hud-patterns.md)
    - Text styling, positioning, counters, layering

12. [Tween & Visual Effects](12-tween-visual-effects.md)
    - Basic tweens, choreography, camera effects, particles

13. [Audio Integration](13-audio-integration.md)
    - Sound management, audio lock, centralized audio

14. [Game Loop Patterns](14-game-loop-patterns.md)
    - Update patterns, event-driven, preUpdate, timers

15. [Algorithm Implementations](15-algorithm-implementations.md)
    - Flood fill, random placement, puzzle generation, AI

16. [Performance Optimization](16-performance-optimization.md)
    - Object pooling, texture caching, event-driven, static groups

17. [Code Organization](17-code-organization.md)
    - File structure, modules, constants, separation of concerns

18. [Development Philosophy](18-development-philosophy.md)
    - Architecture principles, when to use physics, workflow, pitfalls

## Quick Reference

### Common Patterns
- **Multi-scene flow**: Boot → Preloader → MainMenu → Game → GameOver
- **Object pooling**: Pre-create with groups, recycle with enable/disable
- **Animation creation**: Global in Preloader, use everywhere
- **Input handling**: JustDown for single-press, dual keyboard + pointer
- **State management**: Scene properties + Registry for persistence

### Performance Tips
- Use texture atlases for multiple sprites
- Static groups for immovable objects
- Event-driven over polling in update()
- Object pools for frequently created/destroyed objects
- Minimal update logic - only what's necessary

### Common Pitfalls
- Forgetting `super.preUpdate()` in custom sprites
- Not calling `refreshBody()` after scaling static groups
- Creating objects in update() instead of pooling
- Missing bounds checks on grid access
- Not cleaning up listeners/timers

---

*Based on analysis of multiple production Phaser 3 games. Patterns are game-agnostic and adaptable to any genre.*

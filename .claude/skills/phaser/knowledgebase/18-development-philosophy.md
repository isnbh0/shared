## Development Philosophy

### Architecture Principles

1. **Separation of Concerns**: Scenes, objects, managers have clear roles
2. **Composition Over Inheritance**: Use managers and systems
3. **Event-Driven**: Prefer events over polling when possible
4. **Data-Driven**: Use configuration objects, not hard-coded values
5. **Explicit State**: Clear state management, avoid hidden state
6. **Resource Lifecycle**: Explicit creation and cleanup
7. **Progressive Enhancement**: Build complexity incrementally

---

### When to Use Physics

**Use Physics When**:
- Continuous collision detection needed
- Velocity/acceleration/gravity required
- Complex physical interactions
- Realistic bouncing/friction

**Skip Physics When**:
- Grid-based movement (use grid logic)
- Discrete state changes (use flags)
- Binary collision (just touching/not touching)
- Complete control desired (manual calculations)

---

### Scene Architecture Decisions

**Single Scene**:
- Simple games (< 1000 lines)
- Arcade games, endless runners
- Minimal state transitions

**Multi-Scene**:
- Multiple game modes
- Complex state flow
- Reusable components

**Parallel Scenes**:
- Separate HUD from gameplay
- Multiple camera views
- Complex UI overlays

---

### Update vs Event-Driven

**Use update() when**:
- Continuous motion/animation
- Frame-by-frame checks needed
- Physics-based gameplay
- Real-time reactions

**Use events when**:
- Turn-based mechanics
- Discrete state changes
- Fixed interval updates
- Simpler logic flow

---

### Performance Philosophy

1. **Premature optimization is the root of all evil** - Make it work, then optimize
2. **Measure first** - Use debug mode to identify bottlenecks
3. **Object pooling** for frequently created/destroyed objects
4. **Event-driven** reduces polling overhead
5. **Atlas everything** for rendering performance
6. **Static groups** for immovable objects
7. **Minimal update logic** - do only what's necessary

---

### Code Quality Practices

1. **Consistent naming** - Use descriptive names
2. **Method chaining** - Leverage Phaser's fluent API
3. **Early returns** - Guard clauses reduce nesting
4. **Comments for why, not what** - Code should be self-documenting
5. **Extract magic numbers** - Use named constants
6. **Small functions** - Single responsibility
7. **Clean up resources** - Remove listeners, destroy objects

---

### Progressive Difficulty Patterns

**Milestone-Based**:
```javascript
if (this.level === 5 || this.level === 10) {
    this.speed -= 50;
}
```

**Continuous Scaling**:
```javascript
this.enemySpeed = baseSpeed + (this.level * increment);
```

**Complexity Changes**:
```javascript
if (this.level >= 10) {
    this.maxProjectiles = 2;  // Reduce player capability
}
```

**Parametric Tuning**:
```javascript
nextLevel() {
    if (this.level < 5) {
        this.dangerDelay -= 0.1;
    }
    if (this.level < 10) {
        this.durationLow -= 100;
        this.durationHigh -= 200;
    }
    this.level++;
}
```

---

### Development Workflow

1. **Plan**: Sketch architecture, identify patterns
2. **Prototype**: Build simplest version that works
3. **Iterate**: Add features incrementally
4. **Polish**: Animations, sound, juice
5. **Optimize**: Profile and improve bottlenecks
6. **Test**: Play, break, fix
7. **Refactor**: Clean up as you go

---

### Common Pitfalls to Avoid

1. **Forgetting `super.preUpdate()`** - Animations won't work
2. **Not calling `refreshBody()` on static groups** - After scaling
3. **Memory leaks** - Not removing listeners/timers
4. **Creating objects in update()** - Use object pools
5. **Polling in update()** - Use events when possible
6. **Hard-coded values** - Use constants
7. **Missing bounds checks** - Always validate grid access
8. **Not handling scene restart** - Reset state in init()
9. **Ignoring context binding** - Use arrow functions or bind
10. **Over-engineering** - Start simple, add complexity as needed

---


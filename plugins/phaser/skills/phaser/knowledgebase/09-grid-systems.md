## Grid Systems

### Dual Coordinate System

**Pattern**: Separate logical grid positions from pixel positions.

```javascript
// Grid coordinates for logic
this.gridX = 5;  // Column
this.gridY = 3;  // Row

// Pixel coordinates for rendering
this.sprite.x = this.gridX * TILE_SIZE;
this.sprite.y = this.gridY * TILE_SIZE;

// Conversion helpers
getGridX(sprite) {
    return Math.floor((sprite.x - this.offset.x) / TILE_SIZE);
}

getGridY(sprite) {
    return Math.floor((sprite.y - this.offset.y) / TILE_SIZE);
}

getPixelX(gridX) {
    return this.offset.x + (gridX * TILE_SIZE);
}

getPixelY(gridY) {
    return this.offset.y + (gridY * TILE_SIZE);
}
```

---

### 2D Grid Array

```javascript
// Creation
create() {
    this.grid = [];
    for (let y = 0; y < this.height; y++) {
        this.grid[y] = [];
        for (let x = 0; x < this.width; x++) {
            this.grid[y][x] = 0;  // 0 = empty, 1 = occupied
        }
    }
}

// Access
getCellXY(x, y) {
    if (x < 0 || x >= this.width || y < 0 || y >= this.height) {
        return null;  // Bounds check
    }
    return this.grid[y][x];
}

setCellXY(x, y, value) {
    if (this.isValid(x, y)) {
        this.grid[y][x] = value;
    }
}

isValid(x, y) {
    return x >= 0 && x < this.width && y >= 0 && y < this.height;
}

// Iteration
for (let y = 0; y < this.height; y++) {
    for (let x = 0; x < this.width; x++) {
        const cell = this.grid[y][x];
        // Process cell
    }
}
```

---

### Grid-Aligned Group Creation

```javascript
this.tiles = this.add.group({
    key: 'tile',
    frameQuantity: 1,
    repeat: 15,  // Creates 16 total
    gridAlign: {
        width: 4,
        height: 4,
        cellWidth: 80,
        cellHeight: 80,
        x: startX,
        y: startY
    }
});

// Or manual with loop
for (let y = 0; y < rows; y++) {
    for (let x = 0; x < cols; x++) {
        const px = baseX + (x * cellWidth);
        const py = baseY + (y * cellHeight);

        const tile = this.add.image(px, py, 'tile');
        tile.setData({ gridX: x, gridY: y });
    }
}
```

---

### Adjacency Helpers (8-Direction)

```javascript
getAdjacentCells(x, y) {
    return [
        this.getCellXY(x - 1, y - 1),  // Top-Left
        this.getCellXY(x,     y - 1),  // Top
        this.getCellXY(x + 1, y - 1),  // Top-Right
        this.getCellXY(x - 1, y    ),  // Left
        this.getCellXY(x + 1, y    ),  // Right
        this.getCellXY(x - 1, y + 1),  // Bottom-Left
        this.getCellXY(x,     y + 1),  // Bottom
        this.getCellXY(x + 1, y + 1)   // Bottom-Right
    ].filter(cell => cell !== null);   // Remove out-of-bounds
}

// 4-Direction (cardinal)
getCardinalCells(x, y) {
    return [
        this.getCellXY(x,     y - 1),  // Top
        this.getCellXY(x - 1, y    ),  // Left
        this.getCellXY(x + 1, y    ),  // Right
        this.getCellXY(x,     y + 1)   // Bottom
    ].filter(cell => cell !== null);
}
```

---

### Grid Visualization

```javascript
create() {
    this.add.grid(
        x, y,              // Position
        width, height,     // Total size
        cellW, cellH,      // Cell dimensions
        0x999999,          // Fill color
        1,                 // Fill alpha
        0x666666           // Outline color
    ).setOrigin(0);
}
```

---


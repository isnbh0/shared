# Example: Initialized Protocol for Web/UI Project

This file shows what `SKILL.md` looks like after initialization for a **React + TypeScript + Tailwind** web application project.

**Purpose**: Use this as a reference when initializing the protocol for your own project.

---

## Status Section (Updated)

```markdown
## 🚨 INITIALIZATION REQUIRED 🚨

**CURRENT STATUS**: ✅ **INITIALIZED on 2025-01-15**

This protocol has been customized for: **React/TypeScript Web Application**
```

---

## Initialized Domain Configuration

```markdown
### Domain Configuration

PRIMARY DOMAIN: Web/UI Development (React, TypeScript, Tailwind CSS)

LANGUAGES/FRAMEWORKS:
- React 18
- TypeScript 5.x
- Tailwind CSS
- Vite (build tool)
- Playwright (testing/automation)

CODEBASE DEFINITION OF "CORRECT":
- UI renders pixel-perfect to Figma designs
- No console errors or warnings
- All interactive elements accessible via keyboard
- Responsive across viewport sizes (mobile/tablet/desktop)
- Page load performance <3s on 3G
```

---

## Initialized Measurement Tools

```markdown
### Measurement Tools

AVAILABLE TOOLS:
1. Playwright (browser automation and measurement)
2. Chrome DevTools (computed styles, layout inspection)
3. Lighthouse (performance and accessibility scores)
4. React DevTools (component hierarchy, props, state)
5. Tailwind Play (CSS debugging)
6. Visual regression testing (Percy)

PRIMARY MEASUREMENT METHOD:
Playwright browser automation for computed styles and element measurements

TOOL USAGE INSTRUCTIONS:

**For Layout/Styling Issues:**
1. Start dev server: `npm run dev`
2. Navigate to problematic page: `http://localhost:5173/path`
3. Run measurement script: `npx playwright test measure-layout.spec.ts`
4. Capture computed styles:
   ```javascript
   const element = await page.locator('[data-testid="container"]');
   const height = await element.evaluate(el => {
     const computed = window.getComputedStyle(el);
     return {
       height: computed.height,
       display: computed.display,
       flexDirection: computed.flexDirection
     };
   });
   ```
5. Take screenshots: `await page.screenshot({ path: 'before.png' })`

**For Performance Issues:**
1. Run Lighthouse: `npm run lighthouse`
2. Capture metrics: FCP, LCP, CLS, TBT
3. Compare against targets (see metrics below)

**For Interaction Issues:**
1. Use Playwright to simulate user actions
2. Verify state changes via React DevTools
3. Check accessibility tree via DevTools
```

---

## Initialized Success Metrics

```markdown
### Success Metrics

PROJECT-SPECIFIC METRICS:

**Layout/Styling:**
- Element dimensions in pixels (e.g., "height: 385px")
- Computed CSS properties (e.g., "display: flex")
- Responsive breakpoint behavior (mobile: 375px, tablet: 768px, desktop: 1280px)
- Visual diff score (Percy: <5% difference threshold)

**Performance:**
- First Contentful Paint (FCP): <1.8s
- Largest Contentful Paint (LCP): <2.5s
- Cumulative Layout Shift (CLS): <0.1
- Time to Interactive (TTI): <3.8s
- Lighthouse Performance score: >90

**Accessibility:**
- Lighthouse Accessibility score: 100
- All WCAG 2.1 AA criteria passing
- Keyboard navigation functional
- Screen reader compatibility verified

**Functionality:**
- Zero console errors
- Zero console warnings
- Expected state updates occur
- API calls return expected data
- User flows complete successfully

TYPICAL MEASUREMENT VALUES:
- Button height: 44px (touch target)
- Container padding: 16px (mobile), 24px (desktop)
- Font size: 14px (body), 24px (h1)
- Animation duration: 200ms (hover), 300ms (page transitions)
- API response time: <200ms
```

---

## Initialized Phase Details

### Phase 1: Problem Definition (Web/UI)

```markdown
**1.1 Quantify the Issue**

DOMAIN: Web/UI (React + TypeScript + Tailwind)

MEASUREMENT TOOLS: Playwright browser automation

QUANTIFICATION METHOD:

**For layout issues:**
1. Start dev server: `npm run dev`
2. Open Playwright: `npx playwright test --headed`
3. Navigate to problem page
4. Run measurement script:
   ```javascript
   const measurements = await page.evaluate(() => {
     const elements = {
       container: document.querySelector('[data-testid="container"]'),
       header: document.querySelector('[data-testid="header"]'),
       main: document.querySelector('[data-testid="main"]')
     };

     return Object.fromEntries(
       Object.entries(elements).map(([key, el]) => [
         key,
         {
           height: window.getComputedStyle(el).height,
           width: window.getComputedStyle(el).width,
           display: window.getComputedStyle(el).display
         }
       ])
     );
   });

   console.log(JSON.stringify(measurements, null, 2));
   ```
5. Take screenshot: `await page.screenshot({ path: 'baseline.png', fullPage: true })`
6. Document exact values

**For interaction issues:**
1. Use Playwright to simulate user actions
2. Capture state before and after
3. Verify expected vs actual behavior
4. Screenshot each state

**For performance issues:**
1. Run Lighthouse: `npm run lighthouse`
2. Capture all Core Web Vitals
3. Identify metrics outside targets
4. Profile with Chrome DevTools Performance tab

**1.2 Establish Success Criteria**

SUCCESS METRICS:
- [Specific height/width in pixels for layout issues]
- [Specific Lighthouse score for performance issues]
- [Specific interaction behavior for functional issues]

Example:
- Container height: >900px
- Lighthouse Performance: >90
- Button click triggers modal open within 100ms
```

### Phase 2: Systematic Investigation (Web/UI)

```markdown
**2.1 Map the System**

MAPPING APPROACH: Trace React component hierarchy and CSS cascade

**For layout issues:**
1. Identify problem component in React DevTools
2. Trace parent hierarchy: Component → Parent → Root
3. For each level, capture:
   - Component props affecting layout
   - CSS classes applied (Tailwind)
   - Computed styles (height, width, display, flex properties)
4. Identify where layout breaks
5. Document CSS cascade and specificity

**For interaction issues:**
1. Map event handler chain: UI Element → onClick → State Update → Re-render
2. Trace state management: Component State / Zustand / Context
3. Identify where expected behavior diverges

**For performance issues:**
1. Profile component render times (React DevTools Profiler)
2. Identify expensive operations
3. Check for unnecessary re-renders
4. Review bundle size (Vite build analysis)

Example mapping output:
```
<div id="root" className="h-full">           // height: 100vh ✅
  └─ <ThemeProvider className="???">         // height: 385px ❌ PROBLEM HERE
      └─ <MainContainer className="h-full">  // height: 304px ❌ CONSTRAINED BY PARENT
          └─ <ChatArea className="h-full">   // height: 240px ❌ CONSTRAINED BY PARENT
```

Missing `h-full` class on ThemeProvider breaks height inheritance chain.
```

### Phase 3: Controlled Testing (Web/UI)

```markdown
**3.2 Measurement Protocol**

MEASUREMENT TOOL: Playwright browser automation

MEASUREMENT PROCEDURE:

**For layout/styling changes:**

1. **Start dev server**:
   ```bash
   npm run dev
   ```

2. **Navigate to test page**:
   ```bash
   http://localhost:5173/problematic-page
   ```

3. **Run Playwright measurement script**:
   ```bash
   npx playwright test measure.spec.ts
   ```

4. **Capture computed styles**:
   ```javascript
   // measure.spec.ts
   import { test, expect } from '@playwright/test';

   test('measure layout', async ({ page }) => {
     await page.goto('http://localhost:5173/problematic-page');

     const measurements = await page.evaluate(() => {
       const getStyles = (selector) => {
         const el = document.querySelector(selector);
         if (!el) return null;
         const computed = window.getComputedStyle(el);
         return {
           height: computed.height,
           width: computed.width,
           display: computed.display,
           flexDirection: computed.flexDirection,
           padding: computed.padding
         };
       };

       return {
         themeProvider: getStyles('[data-testid="theme-provider"]'),
         mainContainer: getStyles('[data-testid="main-container"]'),
         chatArea: getStyles('[data-testid="chat-area"]')
       };
     });

     console.log(JSON.stringify(measurements, null, 2));
   });
   ```

5. **Take screenshots**:
   ```javascript
   await page.screenshot({
     path: 'screenshots/before-fix.png',
     fullPage: true
   });
   ```

6. **Record exact numerical values** in spreadsheet or JSON file

**For performance changes:**

1. Run Lighthouse audit:
   ```bash
   npm run lighthouse -- --output=json --output-path=./lighthouse-before.json
   ```

2. Extract Core Web Vitals:
   ```bash
   cat lighthouse-before.json | jq '.audits | {fcp, lcp, cls, tbt}'
   ```

3. Capture bundle size:
   ```bash
   npm run build
   ls -lh dist/assets/*.js
   ```
```

---

## Project-Specific Example (Filled In)

```markdown
### Project-Specific Example

## Example: ThemeProvider Height Collapse Bug

**Context**: React application with full-height chat interface. Chat area not filling available viewport height.

**PHASE 1: PROBLEM DEFINITION**

**Quantification (via Playwright):**

```javascript
// Measurements captured at http://localhost:5173/chat
{
  "themeProvider": {
    "height": "385px",
    "display": "block",
    "expectedHeight": "~1000px"
  },
  "mainContainer": {
    "height": "304px",
    "display": "flex",
    "expectedHeight": "~950px"
  },
  "chatArea": {
    "height": "240px",
    "display": "flex",
    "expectedHeight": "~900px"
  }
}
```

Screenshot: `screenshots/chat-height-collapsed.png`

**Success Criteria:**
- ThemeProvider height: >1000px
- MainContainer height: >950px
- ChatArea height: >900px
- No console errors
- Matches Figma design visually

---

**PHASE 2: SYSTEMATIC INVESTIGATION**

**Component Hierarchy:**
```
root (h-full ✅) → 100vh
  ThemeProvider (NO h-full ❌) → height collapses to content (385px)
    MainContainer (h-full ⚠️) → constrained by parent (304px)
      ChatArea (h-full ⚠️) → constrained by parent (240px)
```

**CSS Analysis:**
- `h-full` in Tailwind = `height: 100%`
- `100%` requires parent to have explicit height
- ThemeProvider missing explicit height → collapses to auto
- Children can't inherit height from collapsed parent

**Hypothesis Generation:**

**Hypothesis A (Primary)**: Missing `h-full` class on ThemeProvider
- **Prediction**: Adding `h-full` will restore heights to >1000px
- **Likelihood**: High (clear missing class in hierarchy)
- **Test complexity**: Low (1-line change)

**Hypothesis B (Alternative)**: CSS specificity issue overriding height
- **Prediction**: Adding `!important` or higher specificity will fix
- **Likelihood**: Low (no conflicting styles observed)
- **Test complexity**: Medium

**Hypothesis C (Alternative)**: Flexbox configuration issue
- **Prediction**: Changing flex properties will fix
- **Likelihood**: Low (flexbox working in children)
- **Test complexity**: Medium

**Ranking**: Test A first.

---

**PHASE 3: CONTROLLED TESTING**

**Testing Hypothesis A:**

**HYPOTHESIS**: Missing `h-full` class in ThemeProvider component causes container height collapse from expected ~1000px to actual 385px

**PREDICTION**: Adding `h-full` className to ThemeProvider will:
- Increase ThemeProvider height from 385px to >1000px
- Increase MainContainer height from 304px to >950px
- Increase ChatArea height from 240px to >900px
- Maintain all other layout properties
- Introduce zero console errors

**TESTING**: Adding `h-full` to className in `src/contexts/ThemeContext.tsx:122`

```diff
  export const ThemeProvider: React.FC<ThemeProviderProps> = ({ children }) => {
    const [theme, setTheme] = useState<Theme>('light');

    return (
-     <div className="theme-provider" data-theme={theme} data-testid="theme-provider">
+     <div className="theme-provider h-full" data-theme={theme} data-testid="theme-provider">
        <ThemeContext.Provider value={{ theme, setTheme }}>
          {children}
        </ThemeContext.Provider>
      </div>
    );
  };
```

**MEASUREMENT BEFORE** (baseline):
```javascript
// Via Playwright at http://localhost:5173/chat
{
  "themeProvider": { "height": "385px" },
  "mainContainer": { "height": "304px" },
  "chatArea": { "height": "240px" }
}
```
Screenshot: `screenshots/before-h-full-fix.png`
Console: 0 errors

**MEASUREMENT AFTER** (with h-full added):
```javascript
// Via Playwright at http://localhost:5173/chat (hard refresh)
{
  "themeProvider": { "height": "1080px" },
  "mainContainer": { "height": "999px" },
  "chatArea": { "height": "935px" }
}
```
Screenshot: `screenshots/after-h-full-fix.png`
Console: 0 errors

**RESULT**: Predictions matched exactly
- ThemeProvider: 385px → 1080px (Δ +695px) ✅ Exceeds >1000px target
- MainContainer: 304px → 999px (Δ +695px) ✅ Exceeds >950px target
- ChatArea: 240px → 935px (Δ +695px) ✅ Exceeds >900px target
- Console errors: 0 → 0 ✅ No new errors introduced
- Visual comparison: Matches Figma design ✅

**CONCLUSION**: Hypothesis A is **STRONGLY SUPPORTED** by evidence. The missing `h-full` class was the root cause of the height collapse.

---

**PHASE 4: VERIFICATION AND DOCUMENTATION**

**Independent Verification:**

✅ **Hard refresh test** (Cmd+Shift+R): Heights persist at 1080/999/935px
✅ **Cross-browser test**:
  - Safari 17: 1080/999/935px ✅
  - Firefox 121: 1080/999/935px ✅
  - Chrome 120: 1080/999/935px ✅
✅ **Console errors**: 0 errors in all browsers
✅ **Visual regression**: Percy diff score: 0.8% (acceptable)
✅ **Responsive test**:
  - Mobile (375px): Heights scale correctly ✅
  - Tablet (768px): Heights scale correctly ✅
  - Desktop (1280px): Heights scale correctly ✅
✅ **Lighthouse scores**: Performance 94 (unchanged), Accessibility 100 (unchanged)
✅ **User testing**: Chat interface usable, fills viewport ✅

**Evidence Documentation:**

**Screenshots:**
- Before: `screenshots/2025-01-15-before-h-full-fix.png`
- After: `screenshots/2025-01-15-after-h-full-fix.png`

**Measurements:**
- Before: `measurements/before-h-full.json`
- After: `measurements/after-h-full.json`

**Code Changes:**
- File: `src/contexts/ThemeContext.tsx`
- Line: 122
- Change: Added `h-full` to className
- Diff: 1 line modified

**Commit:**
```
commit 7a4f9e2b1c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f
Author: Developer <dev@example.com>
Date: 2025-01-15 14:32:18 -0800

    fix: Add h-full class to ThemeProvider to restore container heights

    PROBLEM:
    - ThemeProvider height collapsed to 385px (expected: ~1000px)
    - MainContainer constrained to 304px (expected: ~950px)
    - ChatArea constrained to 240px (expected: ~900px)

    ROOT CAUSE:
    - Missing h-full class on ThemeProvider broke height inheritance chain
    - Children (MainContainer, ChatArea) have h-full but parent didn't

    SOLUTION:
    - Added h-full class to ThemeProvider (ThemeContext.tsx:122)

    VERIFICATION:
    - ThemeProvider: 385px → 1080px ✅
    - MainContainer: 304px → 999px ✅
    - ChatArea: 240px → 935px ✅
    - Cross-browser tested (Chrome/Safari/Firefox) ✅
    - Responsive breakpoints verified ✅

    Evidence: screenshots/2025-01-15-before-after-h-full-fix.png
```

**Quality Control Checklist:**

- [x] Problem was measured objectively (Playwright: 385/304/240px)
- [x] Hypothesis stated explicitly ("Missing h-full causes collapse")
- [x] Only one variable changed (added h-full class only)
- [x] Before/after measurements identical conditions (same browser, same viewport)
- [x] Results compared quantitatively (695px increase across all elements)
- [x] Fix verified through multiple methods (Playwright, manual testing, cross-browser)
- [x] No assumptions made (all claims backed by measurements)
- [x] All evidence documented (screenshots, measurements, code diff)
- [x] Success criteria met (all heights >target values)
- [x] No regressions (console errors = 0, Lighthouse scores unchanged)

**Fix Status**: ✅ **VERIFIED AND DEPLOYED**
```

---

## Summary

This initialized protocol is now **ready to use** for debugging issues in this React/TypeScript/Tailwind web application.

**Key customizations made:**
1. ✅ Domain: Web/UI (React + TypeScript + Tailwind)
2. ✅ Tools: Playwright, Chrome DevTools, Lighthouse
3. ✅ Metrics: Pixel dimensions, Lighthouse scores, computed styles
4. ✅ Example: Real ThemeProvider height collapse bug
5. ✅ Procedures: Exact commands for measurement and verification

**When to use:**
- Layout bugs that resist normal debugging
- Performance regressions that need root cause analysis
- Interaction bugs with subtle timing or state issues
- Any bug where previous "fixes" haven't actually worked

**How to use:**
1. Read the problem description
2. Jump to Phase 1: Problem Definition
3. Follow the process step-by-step
4. Use the exact measurement procedures defined above
5. Complete the quality control checklist before claiming success

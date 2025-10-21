# Domain-Specific Debugging Examples

This document shows how the Rigorous Scientific Debugging Protocol applies across different domains. Each example demonstrates the same core methodology with domain-appropriate tools and metrics.

---

## Table of Contents

1. [Web/UI Debugging](#webui-debugging)
2. [Backend/API Debugging](#backendapi-debugging)
3. [Data Processing Debugging](#data-processing-debugging)
4. [Performance Debugging](#performance-debugging)
5. [Algorithm Correctness Debugging](#algorithm-correctness-debugging)

---

## Web/UI Debugging

### Domain Context
- **Technology**: React, TypeScript, Tailwind CSS
- **Tools**: Playwright browser automation, Chrome DevTools
- **Metrics**: Pixel dimensions, computed styles, visual rendering
- **Definition of "correct"**: UI matches design specifications exactly

### Example Bug: Container Height Collapse

**Phase 1: Problem Definition**

**Quantification:**
```bash
# Measurement script using Playwright
npx playwright test --headed measurements.spec.ts
```

Captured measurements:
- ThemeProvider container: 385px (expected: ~1000px)
- MainContainer: 304px (expected: ~950px)
- ChatArea: 240px (expected: ~900px)

**Success Criteria:**
- ThemeProvider height: >1000px
- MainContainer height: >950px
- ChatArea height: >900px
- No console errors
- Visual match to design spec

**Phase 2: Systematic Investigation**

**System Mapping:**
```
<div id="root">
  └─ <ThemeProvider> (385px ❌)
      └─ <div className="main-container"> (304px ❌)
          └─ <ChatArea> (240px ❌)
```

**Hypothesis Generation:**

1. **Hypothesis A**: Missing `h-full` class on ThemeProvider prevents height inheritance
2. **Hypothesis B**: CSS flexbox configuration incorrect in parent
3. **Hypothesis C**: Z-index or positioning issue causing collapse

Ranking: Test A first (most likely, easiest to verify)

**Phase 3: Controlled Testing**

**Testing Hypothesis A:**

**HYPOTHESIS**: Missing h-full class in ThemeProvider causes container height collapse from expected 1035px to actual 385px

**PREDICTION**: Adding h-full class will increase ThemeProvider height to >1000px, MainContainer to >950px, and ChatArea to >900px

**TESTING**: Adding 'h-full' to className in `src/contexts/ThemeContext.tsx:122`

```diff
- <div className="theme-provider">
+ <div className="theme-provider h-full">
```

**MEASUREMENT BEFORE**:
```javascript
// Via Playwright: await page.evaluate(() => ...)
{
  "ThemeProvider": "385px",
  "MainContainer": "304px",
  "ChatArea": "240px"
}
```

**MEASUREMENT AFTER**:
```javascript
{
  "ThemeProvider": "1080px",
  "MainContainer": "999px",
  "ChatArea": "935px"
}
```

**RESULT**: Predictions matched exactly
- ThemeProvider increased 695px (385→1080px) ✅
- MainContainer increased 695px (304→999px) ✅
- ChatArea increased 695px (240→935px) ✅
- All values exceed success criteria ✅

**CONCLUSION**: Hypothesis SUPPORTED by evidence. The missing h-full class was the root cause.

**Phase 4: Verification and Documentation**

**Independent Verification:**
- ✅ Hard refresh (Cmd+Shift+R): Heights persist
- ✅ Test in Safari: 1080px/999px/935px confirmed
- ✅ Test in Firefox: 1080px/999px/935px confirmed
- ✅ Console: No errors
- ✅ Visual comparison: Matches design spec

**Evidence:**
- Before screenshot: `screenshots/before-height-collapse.png`
- After screenshot: `screenshots/after-height-fixed.png`
- Code change: `src/contexts/ThemeContext.tsx:122` (1 line)
- Commit: `a3f7e92 - Fix: Add h-full class to ThemeProvider to restore proper container heights`

---

## Backend/API Debugging

### Domain Context
- **Technology**: Node.js, Express, PostgreSQL
- **Tools**: Application Performance Monitoring (APM), request logging, load testing (k6)
- **Metrics**: Response time (p50/p95/p99), error rate, throughput
- **Definition of "correct"**: p95 latency <200ms, error rate <0.1%

### Example Bug: API Response Time Regression

**Phase 1: Problem Definition**

**Quantification:**
```bash
# Load test to measure current performance
k6 run --vus 50 --duration 60s load-test.js
```

Captured measurements:
- p50 latency: 145ms (expected: ~80ms)
- p95 latency: 420ms (expected: <200ms) ❌
- p99 latency: 890ms (expected: <300ms) ❌
- Error rate: 0.05% ✅

**Success Criteria:**
- p95 latency: <200ms
- p99 latency: <300ms
- Error rate: <0.1%
- No degradation in p50

**Phase 2: Systematic Investigation**

**System Mapping:**
```
Client Request
  → Express Route Handler
    → Authentication Middleware (traced: 5ms)
    → Business Logic (traced: 35ms)
    → Database Query (traced: 380ms) ❌ SUSPICIOUS
    → Response Serialization (traced: 12ms)
  ← Response
```

**Hypothesis Generation:**

1. **Hypothesis A**: Missing database index on frequently queried column
2. **Hypothesis B**: N+1 query problem in ORM
3. **Hypothesis C**: Database connection pool exhaustion

Ranking: Test A first (DB query time is 380ms, likely culprit)

**Phase 3: Controlled Testing**

**Testing Hypothesis A:**

**HYPOTHESIS**: Missing index on `users.email` column causes table scan, increasing p95 latency from <200ms to 420ms

**PREDICTION**: Adding B-tree index on `users.email` will reduce p95 latency to <200ms and p99 to <300ms

**TESTING**: Adding database index via migration `migrations/20250115_add_users_email_index.sql`

```sql
CREATE INDEX CONCURRENTLY idx_users_email ON users(email);
```

**MEASUREMENT BEFORE**:
```bash
# k6 load test results
{
  "p50": "145ms",
  "p95": "420ms",
  "p99": "890ms",
  "error_rate": "0.05%"
}

# Database query plan
EXPLAIN ANALYZE SELECT * FROM users WHERE email = 'test@example.com';
Seq Scan on users (cost=0.00..1845.00 rows=1) (actual time=375.234..375.234)
```

**MEASUREMENT AFTER**:
```bash
# k6 load test results
{
  "p50": "82ms",
  "p95": "165ms",
  "p99": "245ms",
  "error_rate": "0.04%"
}

# Database query plan
Index Scan using idx_users_email on users (cost=0.42..8.44 rows=1) (actual time=2.156..2.156)
```

**RESULT**: Predictions matched
- p95 latency decreased 255ms (420→165ms) ✅
- p99 latency decreased 645ms (890→245ms) ✅
- p50 improved as bonus (145→82ms) ✅
- Database query time: 375ms→2ms (173x improvement) ✅

**CONCLUSION**: Hypothesis SUPPORTED. Missing index was the root cause.

**Phase 4: Verification and Documentation**

**Independent Verification:**
- ✅ Sustained load test (10 min): p95=168ms, stable
- ✅ Production-like dataset: p95=172ms
- ✅ Cold cache test: p95=185ms
- ✅ Integration tests: All passing
- ✅ No regression in other endpoints

**Evidence:**
- Before APM trace: `traces/pre-index-trace.json`
- After APM trace: `traces/post-index-trace.json`
- Database migration: `migrations/20250115_add_users_email_index.sql`
- Load test results: `reports/k6-before-after-comparison.json`

---

## Data Processing Debugging

### Domain Context
- **Technology**: Python, Pandas, data pipeline
- **Tools**: pytest, statistical validation, data profiling
- **Metrics**: Accuracy, completeness, statistical properties (mean, std, distributions)
- **Definition of "correct"**: Aggregations match expected distributions, no data loss

### Example Bug: Incorrect Revenue Aggregation

**Phase 1: Problem Definition**

**Quantification:**
```python
# Data validation test
pytest tests/test_revenue_aggregation.py -v

# Statistical comparison
python scripts/compare_revenue_distributions.py
```

Captured measurements:
- Input records: 125,430
- Output records: 125,430 ✅ (no data loss)
- Total revenue (input): $4,892,156.32
- Total revenue (output): $4,845,091.18 ❌ (difference: -$47,065.14)
- Mean revenue (input): $39.01
- Mean revenue (output): $38.63 ❌ (difference: -$0.38)

**Success Criteria:**
- Total revenue matches input (tolerance: ±$1 for rounding)
- Mean revenue matches input (tolerance: ±$0.01)
- All records present
- Distribution properties preserved

**Phase 2: Systematic Investigation**

**System Mapping:**
```
Raw Data (CSV)
  → read_csv() with dtype specifications
    → filter_invalid_transactions() (traced: 0 rows removed ✅)
    → aggregate_by_customer() (SUSPICIOUS: revenue delta here)
      → Group by customer_id
      → Sum revenue per customer
    → write_output()
  → Aggregated Data
```

**Hypothesis Generation:**

1. **Hypothesis A**: Floating point precision loss during summation
2. **Hypothesis B**: Incorrect data type causing truncation (e.g., int instead of float)
3. **Hypothesis C**: Filter removing valid transactions incorrectly

Ranking: Test B first (type issues common in aggregations)

**Phase 3: Controlled Testing**

**Testing Hypothesis B:**

**HYPOTHESIS**: Using int32 instead of float64 for revenue column truncates decimal values, causing $47,065.14 total revenue loss

**PREDICTION**: Changing revenue dtype from int32 to float64 will restore total revenue to within ±$1 of input value ($4,892,156.32)

**TESTING**: Modifying dtype specification in `src/etl/revenue_aggregator.py:45`

```diff
- dtype={'revenue': 'int32', 'customer_id': 'str'}
+ dtype={'revenue': 'float64', 'customer_id': 'str'}
```

**MEASUREMENT BEFORE**:
```python
# Test output from pytest
{
  "input_total_revenue": 4892156.32,
  "output_total_revenue": 4845091.18,
  "difference": -47065.14,
  "percentage_error": -0.96,
  "sample_truncation": [
    {"input": 49.99, "output": 49},  # Lost $0.99
    {"input": 129.95, "output": 129}, # Lost $0.95
  ]
}
```

**MEASUREMENT AFTER**:
```python
# Test output from pytest
{
  "input_total_revenue": 4892156.32,
  "output_total_revenue": 4892156.32,
  "difference": 0.00,
  "percentage_error": 0.00,
  "sample_truncation": [
    {"input": 49.99, "output": 49.99},  # Preserved ✅
    {"input": 129.95, "output": 129.95}, # Preserved ✅
  ]
}
```

**RESULT**: Predictions matched exactly
- Total revenue difference: -$47,065.14 → $0.00 ✅
- Mean revenue restored: $38.63 → $39.01 ✅
- All decimal values preserved ✅
- Statistical tests pass ✅

**CONCLUSION**: Hypothesis SUPPORTED. Integer dtype was truncating decimal values.

**Phase 4: Verification and Documentation**

**Independent Verification:**
- ✅ Rerun on different dataset (Q4 data): Revenue matches within $0.50
- ✅ Statistical distribution tests: Kolmogorov-Smirnov p=0.92 (distributions match)
- ✅ Manual spot check: 50 random records verified
- ✅ Integration test suite: All passing
- ✅ Historical data reprocessing: Previous quarters now match source

**Evidence:**
- Before/after test output: `test_results/revenue_aggregation_comparison.txt`
- Code change: `src/etl/revenue_aggregator.py:45` (1 line)
- Validation report: `reports/revenue_fix_validation.pdf`
- Statistical comparison: `analysis/distribution_comparison.png`

---

## Performance Debugging

### Domain Context
- **Technology**: Node.js application
- **Tools**: Chrome DevTools profiler, memory snapshots, flamegraphs
- **Metrics**: Memory usage, garbage collection frequency, heap size
- **Definition of "correct"**: Memory usage stable over time, no memory leaks

### Example Bug: Memory Leak in Long-Running Process

**Phase 1: Problem Definition**

**Quantification:**
```bash
# Memory monitoring script
node --expose-gc --inspect monitor-memory.js

# Run application for 2 hours with load
artillery run --duration 7200 load-profile.yml
```

Captured measurements (samples every 10 minutes):
- T+0min: Heap size: 45MB
- T+30min: Heap size: 128MB
- T+60min: Heap size: 215MB ❌ (linear growth)
- T+90min: Heap size: 301MB ❌ (continuing growth)
- T+120min: Heap size: 389MB ❌ (out of memory imminent)

**Success Criteria:**
- Heap size stabilizes <150MB after warmup
- No linear growth over 2-hour period
- Garbage collection reclaims memory effectively
- Application runs 24+ hours without restart

**Phase 2: Systematic Investigation**

**System Mapping:**
```
Request Handler
  → Cache Layer (global Map) ❌ SUSPICIOUS (never clears)
    → Store parsed data
  → Business Logic
  → Response
```

**Heap snapshot analysis:**
```javascript
// Top memory consumers
{
  "parseCache Map": "287MB (74% of heap)", // ❌ GROWING UNBOUNDED
  "other": "102MB (26% of heap)"
}
```

**Hypothesis Generation:**

1. **Hypothesis A**: Cache Map grows unbounded because no eviction policy exists
2. **Hypothesis B**: Event listener memory leak (listeners not removed)
3. **Hypothesis C**: Circular references preventing garbage collection

Ranking: Test A first (parseCache is 74% of heap and growing)

**Phase 3: Controlled Testing**

**Testing Hypothesis A:**

**HYPOTHESIS**: Unbounded parseCache Map accumulates entries indefinitely, causing heap to grow linearly from 45MB to 389MB over 2 hours

**PREDICTION**: Implementing LRU cache with 1000-entry limit will stabilize heap <150MB after warmup and prevent linear growth

**TESTING**: Replacing Map with LRU cache in `src/cache/parse-cache.js:12`

```diff
- const parseCache = new Map();
+ const LRU = require('lru-cache');
+ const parseCache = new LRU({ max: 1000, maxAge: 1000 * 60 * 30 });
```

**MEASUREMENT BEFORE**:
```javascript
// Heap measurements over 2 hours
{
  "T+0min": "45MB",
  "T+30min": "128MB",
  "T+60min": "215MB",
  "T+90min": "301MB",
  "T+120min": "389MB",
  "trend": "linear growth (+2.87MB/min)",
  "cache_entries": 284750 // unbounded
}
```

**MEASUREMENT AFTER**:
```javascript
// Heap measurements over 2 hours
{
  "T+0min": "47MB",
  "T+30min": "93MB", // warmup
  "T+60min": "98MB", // stabilizing
  "T+90min": "95MB", // stable
  "T+120min": "97MB", // stable
  "trend": "stable after warmup",
  "cache_entries": 1000 // bounded by LRU
}
```

**RESULT**: Predictions matched
- Heap size stabilized at ~96MB (within <150MB target) ✅
- No linear growth after T+30min warmup ✅
- Memory reclaimed by GC effectively ✅
- Cache entries bounded at 1000 ✅

**CONCLUSION**: Hypothesis SUPPORTED. Unbounded cache was the memory leak source.

**Phase 4: Verification and Documentation**

**Independent Verification:**
- ✅ 24-hour sustained load test: Heap stable 94-102MB
- ✅ Garbage collection frequency: Normalized (was every 30s, now every 5min)
- ✅ Production deployment: No OOM errors over 7 days
- ✅ Performance impact: Response time unchanged (p95: 85ms before, 87ms after)
- ✅ Cache hit rate: 89% (acceptable with 1000 entry limit)

**Evidence:**
- Before heap timeline: `profiling/heap-before-unbounded.png`
- After heap timeline: `profiling/heap-after-lru.png`
- Flamegraph comparison: `profiling/flamegraph-comparison.svg`
- Code change: `src/cache/parse-cache.js:12-14` (3 lines)
- Long-run test results: `monitoring/24hr-load-test-report.json`

---

## Algorithm Correctness Debugging

### Domain Context
- **Technology**: Python, numerical computation
- **Tools**: pytest, property-based testing (Hypothesis), numerical validation
- **Metrics**: Correctness assertions, edge case coverage, numerical accuracy
- **Definition of "correct"**: Algorithm produces mathematically correct results for all inputs

### Example Bug: Incorrect Binary Search Implementation

**Phase 1: Problem Definition**

**Quantification:**
```python
# Test suite execution
pytest tests/test_binary_search.py -v

# Property-based testing
pytest tests/test_binary_search_properties.py --hypothesis-show-statistics
```

Captured measurements:
- Basic tests (sorted arrays): 12/12 passing ✅
- Edge case tests: 4/6 passing ❌
  - Empty array: PASS ✅
  - Single element: PASS ✅
  - Duplicate elements: FAIL ❌
  - Target not in array: FAIL ❌
- Property-based tests: 89/100 examples passed ❌
- Failure rate: 13.3%

**Success Criteria:**
- All unit tests passing (100%)
- All property-based tests passing (100%)
- Handles all edge cases correctly
- O(log n) time complexity maintained

**Phase 2: Systematic Investigation**

**System Mapping:**
```python
def binary_search(arr, target):
    left, right = 0, len(arr) - 1

    while left <= right:
        mid = (left + right) // 2

        if arr[mid] == target:
            return mid  # ❌ SUSPICIOUS: What if duplicates?
        elif arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1

    return -1  # Not found
```

**Failing test case analysis:**
```python
# Input: arr = [1, 2, 2, 2, 3], target = 2
# Expected: Any valid index (1, 2, or 3)
# Actual: AssertionError on target not in array check ❌

# Input: arr = [1, 3, 5, 7], target = 4
# Expected: -1 (not found)
# Actual: Returns 2 (index of 5) ❌
```

**Hypothesis Generation:**

1. **Hypothesis A**: Off-by-one error in loop termination condition
2. **Hypothesis B**: Incorrect return value when element not found
3. **Hypothesis C**: Mid calculation causes integer overflow (unlikely in Python)

Ranking: Test B first (failing test shows wrong return for "not found")

**Phase 3: Controlled Testing**

**Testing Hypothesis B:**

**HYPOTHESIS**: Function returns wrong index when target not in array due to logic error in termination condition

**PREDICTION**: Fixing loop condition will result in 100% test pass rate (18/18 tests) and 100% property test pass rate

**TESTING**: Investigation reveals issue is in final return location logic. Modified `src/algorithms/search.py:15-18`

```diff
def binary_search(arr, target):
    left, right = 0, len(arr) - 1

    while left <= right:
        mid = (left + right) // 2

        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1

    return -1
```

Wait, that looks correct. Re-examining failed test output...

**REVISED HYPOTHESIS**: Tests are actually failing because test assertions are incorrect (checking wrong behavior)

**Re-testing with corrected hypothesis:**

Actually, reviewing test file `tests/test_binary_search.py:45`:

```python
# Incorrect test assertion
def test_target_not_in_array():
    arr = [1, 3, 5, 7]
    result = binary_search(arr, 4)
    assert arr[result] == 4  # ❌ BUG: This asserts arr[result] == 4, but result should be -1
```

**ACTUAL HYPOTHESIS**: Test code has bug - it's checking `arr[result]` when `result=-1`, causing `arr[-1]` to return last element (7), and `7 == 4` fails

**ACTUAL TESTING**: Fixing test assertion in `tests/test_binary_search.py:47`

```diff
def test_target_not_in_array():
    arr = [1, 3, 5, 7]
    result = binary_search(arr, 4)
-   assert arr[result] == 4  # Wrong: checks arr[-1]
+   assert result == -1  # Correct: checks return value
```

**MEASUREMENT BEFORE** (with buggy test):
```python
{
  "total_tests": 18,
  "passed": 14,
  "failed": 4,
  "pass_rate": "77.8%",
  "property_tests_passed": "89/100"
}
```

**MEASUREMENT AFTER** (with fixed test):
```python
{
  "total_tests": 18,
  "passed": 18,
  "failed": 0,
  "pass_rate": "100%",
  "property_tests_passed": "100/100"
}
```

**RESULT**: Prediction matched
- All unit tests passing: 14/18 → 18/18 ✅
- All property tests passing: 89/100 → 100/100 ✅
- Algorithm implementation was correct all along ✅
- Tests had incorrect assertions ✅

**CONCLUSION**: Hypothesis SUPPORTED. The bug was in the test code, not the algorithm.

**LESSON**: Evidence-only approach revealed the REAL bug. Initial assumption (algorithm wrong) was incorrect. Measurements forced investigation of actual failure mechanism.

**Phase 4: Verification and Documentation**

**Independent Verification:**
- ✅ Property-based testing with 10,000 examples: All pass
- ✅ Edge cases manually verified: All correct
- ✅ Performance test: O(log n) complexity confirmed
- ✅ Code review: Implementation matches specification
- ✅ Comparison with reference implementation: Behavior identical

**Evidence:**
- Test output before: `test_results/before-test-fix.txt`
- Test output after: `test_results/after-test-fix.txt`
- Code change: `tests/test_binary_search.py:47` (test fix)
- Algorithm code: `src/algorithms/search.py` (unchanged - was correct)
- Property test statistics: `hypothesis-statistics.txt`

---

## Common Patterns Across Domains

Despite different tools and metrics, notice the **universal patterns**:

1. **Quantify First**: Every example starts with exact measurements
2. **System Mapping**: Understanding structure before hypothesizing
3. **Testable Hypotheses**: Specific, measurable predictions
4. **One Variable**: Only one change tested at a time
5. **Objective Measurement**: Tools, not intuition, provide answers
6. **Evidence-Based Conclusions**: Results compared to predictions
7. **Independent Verification**: Multiple methods confirm the fix

**The scientific method works the same way regardless of domain.**

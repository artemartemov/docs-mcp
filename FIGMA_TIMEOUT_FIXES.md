# Figma Adapter Timeout Fixes

## Problem
The Figma adapter was hanging for 5+ minutes during page load, causing ingestion to freeze.

## Root Causes
1. **Long page load timeouts**: Original 30s timeout was too aggressive for Figma's React SPA
2. **No fallback strategies**: Single timeout failure killed the entire extraction
3. **Blocking operations**: All operations were blocking without timeout protection
4. **Bot detection**: Figma likely detected automated browser behavior

## Solutions Implemented

### 1. Enhanced SPA Base Class (`spa_base.py`)

#### Multiple Timeout Strategies
- **Strategy 1**: Quick load with `domcontentloaded` (10s timeout)
- **Strategy 2**: Fallback with `commit` wait condition (8s timeout)  
- **Graceful degradation**: Falls back to traditional HTTP extraction if both fail

#### Comprehensive Timeout Protection
```python
# All operations now have individual timeouts
await asyncio.wait_for(self._wait_for_spa_content(page, url), timeout=12.0)
await asyncio.wait_for(page.title(), timeout=3.0)
await asyncio.wait_for(self._extract_main_content(page, url), timeout=8.0)
```

#### Anti-Bot Detection Headers
```python
await page.set_extra_http_headers({
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Cache-Control': 'no-cache',
    'Pragma': 'no-cache',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Upgrade-Insecure-Requests': '1'
})
```

#### Timeout-Protected Cleanup
- Page close: 2s timeout
- Context close: 2s timeout  
- Browser close: 2s timeout
- Prevents hanging during cleanup

### 2. Figma-Specific Improvements (`figma_docs.py`)

#### Reduced Content Thresholds
- Selector wait timeout: 3s → 2s
- Content load timeout: 12s → 5s
- Basic content threshold: 1000 chars → 500 chars
- Minimum content threshold: 300 chars → 200 chars

#### Multiple Content Extraction Strategies
```python
# Strategy 1: Quick selector-based extraction (3s timeout)
content = await asyncio.wait_for(page.text_content(selector), timeout=3.0)

# Strategy 2: Advanced DOM manipulation (4s timeout)  
content = await asyncio.wait_for(page.evaluate("..."), timeout=4.0)

# Strategy 3: Minimal content extraction (2s timeout)
content = await asyncio.wait_for(page.evaluate("..."), timeout=2.0)
```

#### Non-Blocking Wait Strategy
- Reduced sleep from 2s → 1s
- All waits are wrapped in try/catch with timeouts
- Never blocks entire process

## Expected Results

### Before Fixes
- Figma ingestion hanging for 5+ minutes
- Process killed due to timeouts
- No content extracted

### After Fixes  
- Maximum page load time: ~20s (10s + 8s fallback)
- Maximum content extraction time: ~15s (12s + 3s + 8s operations)
- **Total maximum time per URL: ~35s**
- Graceful fallback to HTTP extraction if browser fails
- Process never hangs indefinitely

## Usage

The fixes are automatically applied when using the Figma adapter:

```bash
# Test with a single URL (should complete in <35s)
make test-figma

# Full Figma ingestion with timeout protection
make ingest-figma
```

## Monitoring

Watch for these log messages indicating the fixes are working:

```
⚠️  Quick load failed, trying fallback load: ...
⚠️  SPA content loading timeout for {url}, proceeding with available content
⚠️  Content extraction timeout for {url}
✅ Successfully extracted {X} chars from {url}
```

## Fallback Behavior

If browser automation continues to have issues:
1. Adapter automatically falls back to HTTP + BeautifulSoup
2. Provides informative message about SPA limitations
3. Still creates document entry with metadata
4. Process continues without hanging

This ensures the ingestion process is robust and never gets stuck on problematic URLs.
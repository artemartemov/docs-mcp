# Claude Accessibility Instructions

## IMPORTANT: Always Check Accessibility When Writing Code

When reviewing or writing code, ALWAYS:

### 1. **Search Cached Patterns First**
Before writing any UI code, search for existing accessibility patterns:
```python
# For FastAPI endpoints/forms
search_accessibility_patterns('form validation', framework='fastapi')

# For iOS/SwiftUI code
search_accessibility_patterns('VoiceOver', framework='swift_ios')

# For React/Web components
search_accessibility_patterns('ARIA', framework='react')
```

### 2. **Apply WCAG Standards Automatically**
- **Default to WCAG AA compliance** for all new code
- Check patterns for the specific framework being used
- Apply accessibility attributes proactively

### 3. **Code Review Checklist**
When reviewing code, ALWAYS check:
- [ ] Form labels and ARIA attributes
- [ ] Alt text for images
- [ ] Color contrast ratios (4.5:1 minimum)
- [ ] Keyboard navigation support
- [ ] Screen reader compatibility
- [ ] Error message accessibility

### 4. **Proactive Pattern Application**
```python
# BEFORE writing any form code:
patterns = search_accessibility_patterns('forms', framework='[current_framework]')

# BEFORE writing any image handling:
patterns = search_accessibility_patterns('images alt text')

# BEFORE writing navigation:
patterns = search_accessibility_patterns('navigation ARIA')
```

### 5. **Integration Workflow**
1. **Identify UI Element** → Search patterns
2. **Apply Pattern** → Use cached examples
3. **Validate** → Check against WCAG level
4. **Document** → Note accessibility features

## Example Usage in Practice

### When Writing FastAPI Form Endpoint:
```python
# First, search for patterns
search_accessibility_patterns('form validation', framework='fastapi', wcag_level='AA')

# Then apply the patterns found to ensure:
# - Proper error messages with ARIA
# - Descriptive field validation
# - Accessible response formats
```

### When Writing SwiftUI View:
```swift
// First, search for patterns
search_accessibility_patterns('SwiftUI VoiceOver', framework='swift_ios')

// Then apply patterns for:
// - accessibilityLabel
// - accessibilityHint
// - accessibilityTraits
// - Dynamic Type support
```

### When Writing React Component:
```jsx
// First, search for patterns
search_accessibility_patterns('React form', framework='react', wcag_level='AA')

// Then ensure:
// - Proper ARIA attributes
// - Focus management
// - Error announcement
// - Keyboard navigation
```

## Automated Reminders

### Add to Every Code Review:
"I've checked accessibility patterns for this code using `search_accessibility_patterns()` and applied WCAG AA standards."

### Include in Code Comments:
```python
# Accessibility: Following WCAG AA pattern from search_accessibility_patterns('forms', 'fastapi')
```

## Performance Benefits
- **80% reduction** in accessibility-related API calls
- **Instant** pattern lookup from local cache
- **Consistent** accessibility across all code
- **Proactive** compliance instead of reactive fixes

## Remember: Accessibility First, Not Last!
Always search and apply accessibility patterns BEFORE writing code, not as an afterthought.
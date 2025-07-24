# Pull Request

## Description
<!-- Provide a brief description of the changes in this PR -->

## Type of Change
<!-- Mark the relevant option with an "x" -->
- [ ] 🐛 Bug fix (non-breaking change which fixes an issue)
- [ ] ✨ New feature (non-breaking change which adds functionality)
- [ ] 💥 Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] 📚 Documentation update
- [ ] 🔧 Maintenance (dependencies, CI/CD, etc.)
- [ ] 🎨 Style/formatting changes
- [ ] ♻️ Refactoring (no functional changes)

## Related Issues
<!-- Link to any related issues -->
Fixes #(issue_number)
Closes #(issue_number)
Related to #(issue_number)

## Changes Made
<!-- List the main changes made in this PR -->
- 
- 
- 

## Testing
<!-- Describe the tests you ran and how to reproduce them -->

### Test Environment
- [ ] All existing tests pass
- [ ] New tests added for new functionality
- [ ] Manual testing completed
- [ ] Integration tests pass

### Test Commands
```bash
# Commands used to test these changes
make test
make lint
make security
```

## Security Considerations
<!-- Mark the relevant options with an "x" -->
- [ ] This change does not introduce security vulnerabilities
- [ ] Security review requested (if applicable)
- [ ] Dependencies updated and scanned for vulnerabilities
- [ ] No sensitive data exposed in logs or code

## Accessibility
<!-- For UI/frontend changes -->
- [ ] Changes follow WCAG AA standards
- [ ] Accessibility patterns searched and applied: `search_accessibility_patterns()`
- [ ] Screen reader compatibility verified
- [ ] Keyboard navigation works properly
- [ ] Color contrast ratios meet requirements

## Documentation
- [ ] Code is self-documenting with clear variable and function names
- [ ] Complex logic is commented appropriately
- [ ] README updated (if applicable)
- [ ] CLAUDE.md updated (if applicable)
- [ ] API documentation updated (if applicable)

## Checklist
<!-- Mark all completed items with an "x" -->
- [ ] My code follows the project's style guidelines
- [ ] I have performed a self-review of my own code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] I have made corresponding changes to the documentation
- [ ] My changes generate no new warnings
- [ ] I have added tests that prove my fix is effective or that my feature works
- [ ] New and existing unit tests pass locally with my changes
- [ ] Any dependent changes have been merged and published

## Screenshots/Demo
<!-- If applicable, add screenshots or demo links -->

## Additional Context
<!-- Add any other context about the pull request here -->

---

## For Reviewers

### Review Checklist
- [ ] Code quality and style
- [ ] Test coverage and quality
- [ ] Security implications
- [ ] Performance impact
- [ ] Documentation completeness
- [ ] Accessibility compliance (if applicable)

### Testing Instructions
1. Check out this branch
2. Run `make install-dev`
3. Run `make all-checks`
4. Test the specific functionality described above

---

**Note**: This PR will be automatically tested by our CI/CD pipeline. All checks must pass before merging.
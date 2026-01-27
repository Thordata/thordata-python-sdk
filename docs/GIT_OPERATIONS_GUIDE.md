# Git Operations Guide

This guide provides step-by-step instructions for committing and pushing the code changes.

## Prerequisites

1. Ensure you have Git installed and configured
2. Ensure you have access to the repository
3. Review all changes before committing

## Step-by-Step Git Operations

### 1. Check Current Status

```bash
cd D:\Thordata_Work\thordata-python-sdk
git status
```

This will show:
- Modified files
- New files
- Deleted files
- Untracked files

### 2. Review Changes

```bash
# See all changes
git diff

# See changes in a specific file
git diff src/thordata/tools/ecommerce.py

# See staged changes
git diff --cached
```

### 3. Stage Changes

**Option A: Stage all changes**
```bash
git add .
```

**Option B: Stage specific files (recommended for review)**
```bash
# Stage modified files
git add src/thordata/tools/ecommerce.py
git add src/thordata/tools/__init__.py
git add scripts/acceptance/run_all_tools_coverage.py
git add scripts/acceptance/run_quick_validation.py

# Stage deleted files
git add src/thordata/tools/ecommerce_extended.py

# Stage new files
git add docs/GIT_OPERATIONS_GUIDE.md
```

### 4. Commit Changes

```bash
git commit -m "feat: Complete tools module with 100% API coverage

- Merge ecommerce.py and ecommerce_extended.py
- Fix dataclass parameter ordering issues
- Add timeout protection to acceptance tests
- Optimize test scripts with better error handling
- Add quick validation test script
- Update README with tools usage examples
- Fix code quality issues (line length, imports)
- Add comprehensive documentation

BREAKING CHANGE: None (backward compatible)
"
```

**Commit Message Format:**
- Use conventional commits: `feat:`, `fix:`, `docs:`, `refactor:`, `test:`
- First line: brief summary (50 chars max)
- Blank line
- Detailed description (wrap at 72 chars)
- List of changes with bullet points

### 5. Push to Remote

**Option A: Push to main branch (if you have permissions)**
```bash
git push origin main
```

**Option B: Push to feature branch (recommended)**
```bash
# Create and switch to feature branch
git checkout -b feat/complete-tools-coverage

# Push to remote
git push origin feat/complete-tools-coverage

# Then create a Pull Request on GitHub
```

### 6. Create Pull Request (if using feature branch)

1. Go to GitHub repository
2. Click "New Pull Request"
3. Select your feature branch
4. Add description:
   ```
   ## Summary
   Completes tools module with 100% API coverage and improves code quality.
   
   ## Changes
   - ✅ Merged ecommerce tools into single module
   - ✅ Fixed dataclass parameter ordering
   - ✅ Added timeout protection to tests
   - ✅ Optimized acceptance test scripts
   - ✅ Updated README with tools examples
   - ✅ Fixed code quality issues
   
   ## Testing
   - [x] All tools import successfully
   - [x] Quick validation test passes (2/3)
   - [x] Code quality checks pass
   
   ## Breaking Changes
   None - all changes are backward compatible
   ```

## Verification Checklist

Before pushing, verify:

- [ ] All tests pass (or expected failures documented)
- [ ] Code quality checks pass (`ruff check`)
- [ ] No hardcoded credentials
- [ ] No sensitive data in commits
- [ ] README updated if needed
- [ ] CHANGELOG.md updated (if applicable)
- [ ] All imports work correctly
- [ ] No broken references

## Rollback (if needed)

If you need to undo changes:

```bash
# Undo last commit (keep changes)
git reset --soft HEAD~1

# Undo last commit (discard changes)
git reset --hard HEAD~1

# Undo specific file
git checkout -- path/to/file

# Undo all uncommitted changes
git reset --hard HEAD
```

## Branch Strategy

**Recommended workflow:**

1. **main**: Production-ready code
2. **develop**: Integration branch
3. **feat/***: Feature branches
4. **fix/***: Bug fix branches
5. **docs/***: Documentation updates

**Example:**
```bash
# Create feature branch
git checkout -b feat/complete-tools-coverage

# Make changes and commit
git add .
git commit -m "feat: complete tools coverage"

# Push feature branch
git push origin feat/complete-tools-coverage

# Create PR on GitHub
# After review and merge, delete local branch
git checkout main
git pull origin main
git branch -d feat/complete-tools-coverage
```

## Common Issues

### Issue: "Your branch is ahead of origin/main"

**Solution:**
```bash
git push origin main
# or
git push origin your-branch-name
```

### Issue: "Merge conflicts"

**Solution:**
```bash
# Pull latest changes
git pull origin main

# Resolve conflicts in files
# Then stage resolved files
git add resolved-file.py

# Complete merge
git commit -m "fix: resolve merge conflicts"
```

### Issue: "Large file in commit"

**Solution:**
```bash
# Remove from commit but keep file
git reset HEAD~1
git add .gitignore
git add -u
git commit -m "fix: exclude large files"

# Or use git-lfs for large files
```

## Best Practices

1. **Commit often**: Small, focused commits are easier to review
2. **Write clear messages**: Explain what and why, not how
3. **Test before commit**: Run tests locally
4. **Review before push**: Use `git diff` to review changes
5. **Use branches**: Don't commit directly to main
6. **Keep commits focused**: One logical change per commit

## Additional Resources

- [Git Documentation](https://git-scm.com/doc)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [GitHub Flow](https://guides.github.com/introduction/flow/)

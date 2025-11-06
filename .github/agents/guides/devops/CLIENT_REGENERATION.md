# Client Regeneration Guide

Guide for regenerating the OpenAPI client from the specification.

## Quick Reference

```bash
# Validate OpenAPI spec
uv run poe validate-openapi

# Regenerate client (2+ minutes)
uv run poe regenerate-client

# Verify regeneration
uv run poe check
```

**NEVER CANCEL** `regenerate-client` - it takes 2+ minutes but must complete!

______________________________________________________________________

## When to Regenerate

### Required Regeneration

**OpenAPI spec changes:**

- New endpoints added to `docs/katana-openapi.yaml`
- Existing endpoints modified
- New models/schemas added
- Model properties changed

**Generator updates:**

- `openapi-python-client` package updated
- Generator configuration changed

### Verify Need

```bash
# Check if spec changed since last generation
git log --oneline docs/katana-openapi.yaml

# Check generated code timestamp
ls -l katana_public_api_client/api/
```

______________________________________________________________________

## Regeneration Process

### Step 1: Validate OpenAPI Spec

```bash
# Validate with openapi-spec-validator
uv run poe validate-openapi

# Expected output:
# ✓ OpenAPI spec is valid
```

**If validation fails:**

- Fix errors in `docs/katana-openapi.yaml`
- Common issues: invalid references, missing required fields
- Use Redocly for detailed errors: `uv run poe validate-openapi-redocly`

### Step 2: Backup Current State (Optional)

```bash
# Create backup
cp -r katana_public_api_client katana_public_api_client.backup

# Or commit current state
git add katana_public_api_client
git commit -m "chore: snapshot before regeneration"
```

### Step 3: Regenerate Client

```bash
# Run regeneration (2+ minutes, DO NOT CANCEL)
uv run poe regenerate-client

# What happens:
# 1. Validates OpenAPI spec
# 2. Runs openapi-python-client via npx
# 3. Auto-fixes 6,589+ lint issues with ruff
# 4. Moves generated code to package
# 5. Runs final formatting
```

**Expected output:**

```
Validating OpenAPI specification...
✓ Spec valid

Generating client code...
✓ Client generated

Applying auto-fixes...
✓ Fixed 6589 issues

Moving files...
✓ Files moved

Final formatting...
✓ Formatted

Client regeneration complete!
```

### Step 4: Verify Regeneration

```bash
# Check git status
git status

# Should show changes in:
# - katana_public_api_client/api/
# - katana_public_api_client/models/
# - katana_public_api_client/client.py
# - etc.

# Run full validation
uv run poe check

# Should pass all checks
```

### Step 5: Review Changes

```bash
# View generated changes
git diff katana_public_api_client/

# Focus on API changes
git diff katana_public_api_client/api/

# Focus on model changes
git diff katana_public_api_client/models/
```

### Step 6: Commit Changes

```bash
# Add all generated files
git add katana_public_api_client/

# Use appropriate commit message
git commit -m "feat(client): regenerate client for new endpoints"
# or
git commit -m "chore(client): regenerate client after spec fixes"
# or
git commit -m "build(client): regenerate with updated generator"
```

______________________________________________________________________

## What Gets Regenerated

### Generated Files (Overwritten)

**API endpoints:**

```
katana_public_api_client/api/**/*.py
```

- All endpoint modules
- Request/response handling
- DO NOT EDIT - will be overwritten

**Models:**

```
katana_public_api_client/models/**/*.py
```

- All data models
- Serialization code
- DO NOT EDIT - will be overwritten

**Base client:**

```
katana_public_api_client/client.py
katana_public_api_client/client_types.py
katana_public_api_client/errors.py
katana_public_api_client/py.typed
```

### Preserved Files (Not Regenerated)

**Custom code:**

```
katana_public_api_client/katana_client.py  ✅ Preserved
katana_public_api_client/log_setup.py      ✅ Preserved
```

**Tests:**

```
tests/**/*.py  ✅ Preserved
```

**Documentation:**

```
docs/**/*.md  ✅ Preserved
```

______________________________________________________________________

## Auto-Fix Process

### What Gets Auto-Fixed

The regeneration process uses `ruff --unsafe-fixes` to automatically fix **6,589+ lint
issues**:

**Import issues:**

- Unused imports removed
- Imports sorted
- Duplicate imports merged

**Code style:**

- Line length violations
- Whitespace issues
- Quote style normalized

**Type issues:**

- Type annotations fixed
- Optional types corrected

**Unicode:**

- Multiplication signs (× → \*)
- Other special characters

### Why Auto-Fix

**Without auto-fix:**

- Manual fixes needed across 226+ files
- Hours of work
- Easy to miss issues
- Inconsistent styling

**With auto-fix:**

- Automatic correction
- Consistent style
- No manual intervention
- Reliable, repeatable

______________________________________________________________________

## Common Issues

### Regeneration Fails

**Symptom:**

```
error: Failed to generate client
```

**Debug:**

```bash
# Check OpenAPI spec validity
uv run poe validate-openapi

# Try Redocly for detailed errors
uv run poe validate-openapi-redocly

# Check generator is installed
npx openapi-python-client --version
```

**Fix:**

- Correct OpenAPI spec errors
- Ensure npx is available
- Check internet connection (downloads generator)

### Tests Fail After Regeneration

**Symptom:**

```
Tests passed before, fail after regeneration
```

**Common causes:**

- API signature changed
- Model fields changed
- Response format changed

**Fix:**

```bash
# Identify failing tests
uv run poe test

# Review API changes
git diff katana_public_api_client/api/

# Update test expectations
# Commit test fixes separately:
git commit -m "test(client): update tests for API changes"
```

### Type Errors After Regeneration

**Symptom:**

```
mypy error: Incompatible types
```

**Fix:**

```bash
# Run type check
uv run poe agent-check

# Review type changes
git diff katana_public_api_client/models/

# Update custom code (katana_client.py) if needed
```

### Import Errors After Regeneration

**Symptom:**

```
ImportError: cannot import name 'OldModel'
```

**Cause:** Model renamed or removed in OpenAPI spec

**Fix:**

1. Check what changed: `git diff katana_public_api_client/models/`
1. Update imports in custom code
1. Update imports in tests
1. Commit fixes

______________________________________________________________________

## OpenAPI Spec Management

### Editing the Spec

**File:** `docs/katana-openapi.yaml`

**Common changes:**

**Add new endpoint:**

```yaml
paths:
  /api/v1/new-endpoint:
    get:
      operationId: get_new_endpoint
      summary: Get new resource
      responses:
        '200':
          description: Success
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/NewResource'
```

**Add new model:**

```yaml
components:
  schemas:
    NewResource:
      type: object
      properties:
        id:
          type: integer
        name:
          type: string
      required:
        - id
        - name
```

### Spec Validation

**Validate before committing:**

```bash
uv run poe validate-openapi
```

**Common validation errors:**

**Missing $ref:**

```
error: Reference not found: #/components/schemas/Missing
```

Fix: Add missing schema or correct reference

**Invalid type:**

```
error: Invalid type: 'stringg'
```

Fix: Correct typo

**Required field missing:**

```
error: Required field 'responses' missing
```

Fix: Add missing required field

______________________________________________________________________

## Generator Configuration

### Configuration File

**File:** `.openapi-generator/config.yaml` (if exists)

**Common settings:**

```yaml
packageName: katana_public_api_client
projectName: katana-openapi-client
packageVersion: 0.30.0
```

### Customizing Generation

Most customization is **not needed** - the generator produces good defaults.

**If customization needed:**

1. Create `.openapi-generator/config.yaml`
1. Document reason for customization
1. Test thoroughly after changes

______________________________________________________________________

## Integration with CI/CD

### Pre-Commit Checks

**Regeneration is NOT automatic** - it's manual when needed.

**CI validates:**

- OpenAPI spec is valid (on spec changes)
- Generated code compiles
- Tests pass
- No linting errors

### Workflow

```
Developer modifies spec
    ↓
Runs validate-openapi locally
    ↓
Runs regenerate-client locally
    ↓
Runs poe check locally
    ↓
Commits changes
    ↓
CI validates everything
    ↓
Merge
```

______________________________________________________________________

## Performance Considerations

### Generation Time

**Typical duration:** 2-3 minutes

**Breakdown:**

- Validation: 5-10 seconds
- Code generation: 60-90 seconds
- Auto-fix: 30-45 seconds
- Final formatting: 10-15 seconds

**Why slow?**

- 76+ endpoints to generate
- 150+ models to generate
- 6,589+ lint issues to fix
- npx downloads generator if not cached

### Optimization

**Already optimized:**

- Uses npx caching
- Parallel auto-fixing where possible
- Incremental formatting

**Don't:**

- Cancel early (wastes time)
- Run unnecessarily (only when spec changes)
- Skip validation (causes failures)

______________________________________________________________________

## Best Practices

### DO ✅

- **Validate spec before regenerating**
- **Let regeneration complete** (2+ minutes)
- **Run full tests after**
- **Review generated changes**
- **Commit with descriptive message**
- **Never edit generated files**

### DON'T ❌

- **Don't cancel regeneration early**
- **Don't edit generated files manually**
- **Don't skip validation**
- **Don't regenerate without reason**
- **Don't commit without testing**

______________________________________________________________________

## Emergency Rollback

**If regeneration breaks everything:**

```bash
# Option 1: Restore from backup
rm -rf katana_public_api_client
mv katana_public_api_client.backup katana_public_api_client

# Option 2: Git revert
git restore katana_public_api_client/

# Verify
uv run poe check

# Investigate issue before retrying
```

______________________________________________________________________

## Summary

**Regeneration workflow:**

1. `uv run poe validate-openapi` - Validate spec
1. `uv run poe regenerate-client` - Regenerate (2+ min)
1. `uv run poe check` - Verify
1. Review changes with `git diff`
1. Commit with appropriate message

**Key points:**

- Takes 2+ minutes - DO NOT CANCEL
- Auto-fixes 6,589+ lint issues
- Overwrites generated files
- Preserves custom code
- Always test after regeneration

**Remember:** Generated code is read-only. Customizations go in `katana_client.py`!

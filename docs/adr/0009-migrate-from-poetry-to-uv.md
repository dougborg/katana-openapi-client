# ADR-009: Migrate from Poetry to uv Package Manager

## Status

Accepted

Date: 2025-10-17

## Context

This project currently uses Poetry as its package and dependency manager. While Poetry
has served the project well, there are compelling reasons to consider migrating to uv, a
modern Python package manager written in Rust.

### Current State

- **Package Manager**: Poetry 1.x
- **Build Backend**: poetry-core
- **Task Runner**: poethepoet (poe)
- **Dependencies**: 13 core + 30+ dev dependencies
- **Python Versions**: 3.11, 3.12, 3.13
- **Configuration**: pyproject.toml with Poetry-specific sections

### Forces at Play

**Performance Issues:**

- Poetry dependency resolution can be slow (25+ minutes in CI/CD pipelines for complex
  projects)
- Installation times are slower compared to modern alternatives
- Lock file generation is time-consuming

**Ecosystem Evolution:**

- uv has become the de facto modern Python package manager in 2025
- Written in Rust, offering 10-100x speed improvements over pip/Poetry
- Actively developed by Astral (creators of ruff)
- Growing adoption in the Python community

**Tool Consolidation:**

- uv aims to replace pip, pip-tools, pipx, poetry, pyenv, twine, virtualenv in a single
  tool
- Reduces toolchain complexity
- Better integration with modern Python tooling ecosystem

**Standards Compliance:**

- uv strictly complies with Python PEPs
- Uses standard pyproject.toml format (PEP 621)
- This project already uses PEP 621 format, making migration easier

## Decision

We will migrate from Poetry to uv as the primary package and dependency manager for this
project.

The migration will:

1. **Preserve existing functionality**: All development workflows, testing, and CI/CD
   processes will continue to work
1. **Use uv for dependency management**: Replace `poetry install`, `poetry add`, etc.
   with uv equivalents
1. **Keep poethepoet as task runner**: Continue using `poe` for task automation (uv
   doesn't replace this)
1. **Maintain pyproject.toml structure**: Minimal changes needed since we already use
   PEP 621 format
1. **Update documentation**: Update CLAUDE.md, README.md, and CONTRIBUTING.md with new
   commands

### Migration Approach

We will use a **manual migration** approach with validation at each step:

1. Install uv and verify it works with current pyproject.toml
1. Generate uv.lock from existing dependencies
1. Update build-system to use standard build backend (hatchling or setuptools)
1. Test all workflows (dev, test, build, docs)
1. Update CI/CD configuration
1. Update documentation and contributor guides
1. Remove Poetry-specific configuration

### Transition Period

- Keep Poetry configuration temporarily for one release cycle
- Document both Poetry and uv commands during transition
- Fully remove Poetry dependencies after successful migration validation

## Consequences

### Positive Consequences

**Performance Improvements:**

- **10-100x faster** dependency resolution and installation
- **Faster CI/CD pipelines**: Reduced build times
- **Lower memory usage**: More efficient resource utilization
- **Parallel downloads**: Faster package installation

**Developer Experience:**

- **Simpler toolchain**: One tool for multiple purposes
- **Better lockfile**: More reliable dependency resolution
- **Modern features**: Override dependencies, platform-independent resolution
- **Active development**: Regular updates and improvements from Astral

**Project Health:**

- **Future-proof**: Align with modern Python ecosystem direction
- **Better compatibility**: Strict PEP compliance
- **Reduced maintenance**: Less configuration to maintain
- **Easier onboarding**: More familiar to new contributors

### Negative Consequences

**Migration Effort:**

- Time investment to perform migration (estimated 4-8 hours)
- Need to update documentation and guides
- Need to update CI/CD workflows
- Need to communicate changes to contributors

**Learning Curve:**

- Contributors familiar with Poetry need to learn uv commands
- Different command syntax (though generally simpler)
- May encounter edge cases during migration

**Potential Risks:**

- Different dependency resolution may select different versions
- Need to validate all existing functionality works
- Pre-commit hooks may need updates
- Integration with semantic-release needs verification

### Neutral Consequences

**No Impact Areas:**

- Core client functionality remains unchanged
- Generated API code unaffected
- Test suite remains the same
- Documentation build process unchanged (mkdocs)
- Code quality tools unchanged (ruff, mypy)

**Build System:**

- Need to switch from poetry-core to hatchling or setuptools
- Build outputs should be identical
- PyPI publishing process may need minor adjustments

## Alternatives Considered

### Alternative 1: Stay with Poetry

**Description**: Continue using Poetry as the package manager

**Pros:**

- No migration effort required
- Well-understood by current contributors
- Stable and mature tooling
- Works fine for current project size

**Cons:**

- Slower performance, especially as dependencies grow
- Missing modern features available in uv
- Against ecosystem trends (fewer new projects choosing Poetry)
- Larger CI/CD times and costs

**Why Rejected**: While Poetry works, the performance benefits and ecosystem alignment
of uv make migration worthwhile, especially given our already-standard pyproject.toml
format.

### Alternative 2: PDM

**Description**: Migrate to PDM instead of uv

**Pros:**

- Modern tool with good PEP 621 support
- Better than Poetry in performance
- Can act as bridge between Poetry and uv

**Cons:**

- Less performance improvement than uv
- Smaller community compared to uv
- Additional migration step if we want uv later
- Not as actively developed as uv

**Why Rejected**: PDM is a good tool, but uv offers better performance and has stronger
momentum in the ecosystem. Since we're migrating anyway, go with the best option.

### Alternative 3: pip-tools

**Description**: Use pip-tools for dependency management

**Pros:**

- Lightweight and simple
- Based on standard pip
- Minimal learning curve

**Cons:**

- Less feature-rich than uv
- Slower than uv
- Doesn't consolidate other tools (virtualenv, etc.)
- Manual workflow compared to uv's automation

**Why Rejected**: Pip-tools doesn't offer the same level of performance or convenience
as uv, and lacks features like automatic virtualenv management.

## Implementation Plan

### Phase 1: Preparation (1-2 hours)

1. **Install uv**: `curl -LsSf https://astral.sh/uv/install.sh | sh`
1. **Backup current state**: Commit all changes, create backup branch
1. **Document current Poetry commands**: List all `poetry` commands used in project
1. **Verify current functionality**: Run full test suite, build docs, generate client

### Phase 2: Migration (2-3 hours)

1. **Initialize uv project**:
   - Run `uv init` to verify pyproject.toml compatibility
   - Generate `uv.lock` with `uv lock`
1. **Update build system**:
   - Change `build-backend` from `poetry.core.masonry.api` to `hatchling.build`
   - Update `requires` to `["hatchling"]`
   - Remove `[tool.poetry]` section (or keep temporarily)
1. **Test dependency installation**:
   - `uv sync --all-extras` (equivalent to `poetry install --all-extras`)
   - Verify all dependencies installed correctly
1. **Update task runner**:
   - Change all scripts to use `uv run poe` instead of `poetry run poe`
   - Test all poe tasks work correctly

### Phase 3: Validation (1-2 hours)

1. **Run test suite**: `uv run poe test`
1. **Run linting**: `uv run poe lint`
1. **Build documentation**: `uv run poe docs-build`
1. **Test client regeneration**: `uv run poe regenerate-client`
1. **Build distribution**: `uv build`
1. **Test in fresh environment**: Clone repo, run `uv sync`, test

### Phase 4: CI/CD Updates (1 hour)

1. **Update GitHub Actions workflows**:
   - Replace Poetry installation with uv installation
   - Update cache keys from Poetry to uv
   - Change commands from `poetry run` to `uv run`
1. **Test CI/CD**: Push to test branch, verify all workflows pass

### Phase 5: Documentation (1 hour)

1. **Update CLAUDE.md**: Replace Poetry commands with uv equivalents
1. **Update README.md**: Update installation and quick start
1. **Update CONTRIBUTING.md**: Update developer setup instructions
1. **Create migration guide**: Document for contributors on transition

### Phase 6: Cleanup (30 minutes)

1. **Remove Poetry files**: Delete `poetry.lock` after confirming `uv.lock` works
1. **Remove Poetry-specific config**: Clean up `[tool.poetry]` sections
1. **Update .gitignore**: Remove Poetry cache entries, add uv cache entries
1. **Final testing**: Complete test pass on all platforms

## Command Mapping

### Common Operations

| Poetry                                      | uv                                 |
| ------------------------------------------- | ---------------------------------- |
| `poetry install`                            | `uv sync`                          |
| `poetry install --extras "dev docs"`        | `uv sync --all-extras`             |
| `poetry add httpx`                          | `uv add httpx`                     |
| `poetry add --group dev pytest`             | `uv add --dev pytest`              |
| `poetry remove httpx`                       | `uv remove httpx`                  |
| `poetry update`                             | `uv lock --upgrade`                |
| `poetry run pytest`                         | `uv run pytest`                    |
| `poetry run poe test`                       | `uv run poe test`                  |
| `poetry build`                              | `uv build`                         |
| `poetry shell`                              | `uv run $SHELL` (or activate venv) |
| `poetry env info`                           | `uv venv` (shows venv info)        |
| `poetry lock`                               | `uv lock`                          |
| `poetry show`                               | `uv pip list`                      |
| `poetry show --tree`                        | `uv tree`                          |
| `poetry check`                              | (built into uv operations)         |
| `poetry version`                            | (edit pyproject.toml directly)     |
| `poetry publish`                            | `uv publish`                       |
| `poetry config virtualenvs.in-project true` | (default behavior in uv)           |

### Task Runner (Unchanged)

All `poe` tasks work the same, just replace `poetry run poe` with `uv run poe`:

- `uv run poe test`
- `uv run poe lint`
- `uv run poe format`
- `uv run poe check`
- etc.

## Success Criteria

Migration is considered successful when:

1. ✅ All tests pass with uv-managed dependencies
1. ✅ Documentation builds successfully
1. ✅ Client regeneration works
1. ✅ CI/CD pipelines pass
1. ✅ Build artifacts are identical to Poetry builds
1. ✅ All poe tasks execute correctly
1. ✅ Installation from PyPI works (after test release)
1. ✅ Developer setup time is reduced
1. ✅ CI/CD pipeline is faster than before

## Rollback Plan

If migration encounters insurmountable issues:

1. Revert to backup branch
1. Document issues encountered
1. Create GitHub issue with detailed analysis
1. Reassess migration timeline
1. Continue with Poetry until issues resolved

## References

- [uv Official Documentation](https://docs.astral.sh/uv/)
- [migrate-to-uv Tool](https://github.com/mkniewallner/migrate-to-uv)
- [Poetry to uv Migration Guide](https://pratikpathak.com/migrating-poetry-to-uv-package-manager/)
- [Astral Blog: uv Announcement](https://astral.sh/blog/uv)
- [PEP 621: Storing project metadata in pyproject.toml](https://peps.python.org/pep-0621/)
- [Poetry vs uv Comparison](https://www.loopwerk.io/articles/2024/python-poetry-vs-uv/)
- [Stack Overflow: Poetry to uv Migration](https://stackoverflow.com/questions/79118841/how-can-i-migrate-from-poetry-to-uv-package-manager)

## Related ADRs

- ADR-002: Generate Client from OpenAPI Specification (build system dependency)
- ADR-004: Defer Observability to httpx (dependency management)

## Notes

- This migration aligns with the project's philosophy of using modern, efficient tooling
  (as seen with ruff, mypy, httpx)
- The project's existing use of PEP 621 format makes this migration lower-risk than it
  would be for projects using legacy Poetry-only format
- Performance gains will be most noticeable in CI/CD and for new contributors setting up
  the project

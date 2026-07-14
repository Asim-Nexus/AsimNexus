# Contributing to AsimNexus

## Code Standards

### Docstrings
- Every module file MUST have a module-level docstring describing its purpose.
- `__init__.py` files should have a concise docstring describing the package.
- Class and method docstrings follow Google-style conventions.

### `__init__.py` Conventions
- Package `__init__.py` files should export the public API via `__all__`.
- Use lazy imports inside functions (e.g., `get_*()` factory functions) to avoid circular imports.
- Docstring-only `__init__.py` is acceptable for packages that are purely submodule collections.

### Imports
- Use absolute imports (`from core.consensus import CloneConsensusVoting`).
- Group imports: standard library → third-party → local.
- Use `try/except ImportError` for optional dependencies with graceful fallbacks.

### Error Handling
- Use `try/except` with specific exception types, never bare `except:`.
- Log errors with `logger.exception()` or `logger.error()`.
- Return standardized API responses via [`routes/response.py`](routes/response.py) helpers: `ok()`, `error()`, `paginated()`.

### API Response Format
All endpoints MUST return the standardized format:

```python
# Success
{"status": "ok", "data": {...}, "timestamp": "..."}

# Error
{"status": "error", "detail": "...", "code": 400, "timestamp": "..."}

# Paginated
{"status": "ok", "data": [...], "pagination": {"page": 1, "per_page": 20, "total": 100}, "timestamp": "..."}
```

## Testing

### Test Suites

| Suite | Location | Purpose |
|-------|----------|---------|
| Real | `tests/real/` | Full system integration tests (88 tests) |
| E2E | `tests/e2e/` | End-to-end workflow tests (28 tests) |
| Integration | `tests/integration/` | Component integration tests (470 tests) |
| Unit | `tests/unit/` | Unit tests |
| Performance | `tests/performance/` | Performance and load tests |
| Security | `tests/security/` | Security-focused tests |

### Running Tests

```bash
# Run all real tests
pytest tests/real/ -v

# Run all E2E tests
pytest tests/e2e/ -v

# Run all integration tests
pytest tests/integration/ -v

# Run full suite
pytest tests/real/ tests/e2e/ tests/integration/ -v
```

### Test Requirements
- New features MUST include tests in the appropriate suite.
- Real tests (`tests/real/`) should test the actual implementation, not mocks.
- Integration tests should verify component interactions.
- All tests MUST pass before merging.

## PR Checklist

Before submitting PR:
- [ ] Code follows docstring and import conventions
- [ ] Tests added for new logic
- [ ] `pytest tests/real/ tests/e2e/ tests/integration/` passes
- [ ] No `print()` statements in production code (use `logging`)
- [ ] API endpoints use standardized response format
- [ ] No forbidden patterns (bare except, wildcard imports)

## Forbidden Patterns

- ❌ Bare `except:` — always specify exception type
- ❌ `from module import *` — use explicit imports
- ❌ `print()` in production code — use `logging`
- ❌ Hardcoded secrets or tokens
- ❌ `# TODO` without an associated issue or ticket

## Architecture Notes

- **`app.py`**: FastAPI application entry point with 684+ routes. All route modules are registered via [`routes/__init__.py`](routes/__init__.py) `register_routes()`.
- **`core/`**: Core subsystems — each in its own package with `__init__.py` exporting the public API.
- **`routes/`**: API route modules — each has an `init_*()` function receiving `app_globals` dict.
- **`routes/response.py`**: Standardized response helpers used by all route modules.
- **`core/security/auth_middleware.py`**: Global `AuthMiddleware` for JWT Bearer token validation.
- **`core/security_layer.py`**: `ZKPBridge` for zero-knowledge proofs.
- **`knowledge/rag_engine.py`**: `RAGEngine` with ChromaDB vector store.
- **`mesh/`**: Mesh networking — offline sync, multi-mesh routing, auto-discovery.

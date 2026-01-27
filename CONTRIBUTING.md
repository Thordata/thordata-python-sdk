# Contributing to Thordata Python SDK

Thank you for your interest in contributing! This document provides guidelines and instructions for contributing.

---

## 📋 Code of Conduct

Please be respectful and constructive in all interactions.

---

## 🚀 Getting Started

### 1. Fork and Clone

```bash
git clone https://github.com/YOUR_USERNAME/thordata-python-sdk.git
cd thordata-python-sdk
```

### 2. Set Up Development Environment

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install with dev dependencies
pip install -e ".[dev]"
```

### 3. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bug-fix
```

---

## 💻 Development Workflow

### Code Style

We use the following tools to maintain code quality:

```bash
# Format code with Black
black src tests

# Lint with Ruff
ruff check src tests --fix

# Type check with MyPy
mypy src
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage (recommended: use coverage CLI for reliable results)
python -m coverage run -m pytest -p no:cov -v tests
python -m coverage report -m

# Optional: HTML report
python -m coverage run -m pytest -p no:cov tests && python -m coverage html

# From repo root with script (Git Bash / Linux / macOS)
bash scripts/run_coverage.sh

# Run specific test
pytest tests/test_client.py -v -k test_serp
```

### Pre-commit Checks

Before committing, ensure:

- ✅ All tests pass
- ✅ Code is formatted (black)
- ✅ No linting errors (ruff)
- ✅ Type checks pass (mypy)

---

## 📝 Pull Request Process

1. Update documentation if you've changed APIs
2. Add tests for new functionality
3. Update CHANGELOG.md with your changes
4. Ensure CI passes on your PR
5. Request review from maintainers

### PR Title Convention

- `feat:` Add new feature
- `fix:` Fix bug description
- `docs:` Update documentation
- `refactor:` Refactor code
- `test:` Add tests
- `chore:` Update dependencies

---

## 📁 Project Structure

```
src/thordata/
├── __init__.py           # Public API exports
├── client.py             # Sync client (main)
├── async_client.py       # Async client
├── unlimited.py          # Sync Unlimited Proxy namespace
├── async_unlimited.py    # Async Unlimited Proxy namespace
├── models.py             # Re-exports (ProxyConfig, etc.)
├── enums.py              # Engine, TaskStatus, ProxyType, etc.
├── exceptions.py         # Exception hierarchy
├── retry.py              # Retry decorator and RetryConfig
├── serp_engines.py       # SERP namespace (sync/async)
├── _utils.py             # Internal: auth headers, parse_json, etc.
├── core/
│   ├── http_client.py    # Sync HTTP session + retry
│   ├── async_http_client.py
│   └── tunnel.py         # Proxy tunneling (HTTP/HTTPS/SOCKS5)
├── types/                # Request/response types (SerpRequest, ProxyConfig, etc.)
│   ├── common.py, proxy.py, serp.py, task.py, universal.py
└── tools/                # Pre-built scrapers (Amazon, YouTube, etc.)
    ├── base.py, code.py, ecommerce.py, search.py, social.py, video.py
```

---

## 🧪 Testing Guidelines

- Write tests for all new features
- Use pytest fixtures for common setups
- Mock external API calls for unit tests
- Aim for >80% coverage on new code

### Unit tests (no network, no proxy)

Default `pytest` runs only unit tests. No `.env` or Clash needed.

```bash
pytest
# or with coverage
python -m coverage run -m pytest -p no:cov -v tests
python -m coverage report -m
```

### Integration tests (live API / proxy)

Integration tests are **skipped** unless explicitly enabled. They require a real `.env` with credentials.

| Env | Meaning |
|-----|--------|
| `THORDATA_INTEGRATION=true` | Enable integration tests (e.g. proxy protocol test) |
| `THORDATA_INTEGRATION_STRICT=true` | Fail on any proxy error; if unset, skip on likely local interference |
| `THORDATA_INTEGRATION_HTTP=true` | Include HTTP (in addition to HTTPS/SOCKS5h) in proxy test |
| `THORDATA_UPSTREAM_PROXY` | Optional. Set if you are behind GFW/corporate proxy (e.g. Clash Verge `http://127.0.0.1:7897`, or Clash `http://127.0.0.1:7890`). Unit tests do **not** use this. |

**When to use Clash/upstream proxy**

- **Unit tests**: No. They mock HTTP; no proxy needed.
- **Integration tests** (e.g. `test_integration_proxy_protocols.py`): Only if your network blocks Thordata. Set `THORDATA_UPSTREAM_PROXY=http://127.0.0.1:7897` (Clash Verge) or `http://127.0.0.1:7890` (Clash) in `.env` and run with `THORDATA_INTEGRATION=true`.

```bash
# Run only unit tests (default)
pytest -m "not integration"

# Run integration tests (requires .env + THORDATA_INTEGRATION=true)
THORDATA_INTEGRATION=true pytest -m integration
```

### Example Test

```python
import pytest
from thordata import ThordataClient, ProxyConfig

def test_proxy_config_validation():
    """Test that ProxyConfig validates parameters correctly."""
    with pytest.raises(ValueError, match="session_duration"):
        ProxyConfig(
            username="user",
            password="pass",
            session_duration=100  # Invalid: max is 90
        )
```

---

## 📖 Documentation

- Update docstrings for API changes
- Follow Google-style docstrings
- Include examples in docstrings

### Example Docstring

```python
def serp_search(
    self,
    query: str,
    *,
    engine: str = "google",
) -> dict[str, Any]:
    """
    Execute a SERP search.
    
    Args:
        query: The search keywords.
        engine: Search engine to use.
    
    Returns:
        Parsed JSON results from the search.
    
    Raises:
        ThordataAuthError: If authentication fails.
        ThordataRateLimitError: If rate limited.
    
    Example:
        >>> results = client.serp_search("python tutorial")
        >>> print(len(results.get("organic", [])))
    """
```

---

## ❓ Questions?

- Open an issue for bugs or feature requests
- Email support@thordata.com for other questions

---

Thank you for contributing! 🎉
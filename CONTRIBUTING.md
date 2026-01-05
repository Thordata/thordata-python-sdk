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

# Run with coverage
pytest --cov=thordata --cov-report=html

# Run specific test
pytest tests/test_client.py::test_serp_search -v
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
├── __init__.py         # Public exports
├── client.py           # Sync client (main)
├── async_client.py     # Async client
├── models.py           # Dataclass models
├── enums.py            # Enumerations
├── exceptions.py       # Exception classes
├── retry.py            # Retry logic
└── _utils.py           # Internal utilities
```

---

## 🧪 Testing Guidelines

- Write tests for all new features
- Use pytest fixtures for common setups
- Mock external API calls
- Aim for >80% coverage on new code

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
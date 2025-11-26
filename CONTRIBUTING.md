# Contributing to Thordata Python SDK

Thank you for your interest in contributing to the **Thordata Python SDK**.
Your help makes it easier for AI developers and data teams to access high-quality web data.

---

## How can I contribute?

- Bug reports
- Feature requests
- Documentation improvements
- Pull Requests (bug fixes, new features, examples)

---

## Development Workflow

### 1. Clone and Branch

```bash
git clone https://github.com/Thordata/thordata-python-sdk.git
cd thordata-python-sdk

git checkout main
git pull origin main
git checkout -b feature/your-feature-name
# Example: git checkout -b feature/add-yandex-support
```

### 2. Set Up Environment

We recommend using a virtual environment:

```bash
python -m venv venv
# On Linux / macOS:
source venv/bin/activate
# On Windows:
venv\Scripts\activate
```

Install runtime and development dependencies:

```bash
pip install -e .
pip install -r requirements.txt  # pytest, requests-mock, aioresponses, etc.
```

### 3. Run Tests

```bash
python -m pytest
```

All tests should pass before submitting a PR.

### 4. Submit a Pull Request

Push your branch and open a Pull Request against main.
Please include:

- A clear description of the change
- Any relevant issue numbers
- Screenshots or logs if applicable

Thank you for building with Thordata.
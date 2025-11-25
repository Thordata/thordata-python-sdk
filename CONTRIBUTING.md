# ✍️ Contributing to Thordata Python SDK

Welcome to the **Thordata Python SDK** community! We believe in the power of open source, and your contributions help AI developers access data more efficiently.

Please read this guide before submitting any code.

---

## 🤝 How can I contribute?

We welcome all forms of contributions, including but not limited to:

1.  **Bug Reports**: Report errors you encounter.
2.  **Feature Requests**: Suggest new features or improvements.
3.  **Code Submissions**: Submit PRs for bug fixes, new features, or documentation updates.

## 🚀 Contribution Workflow

### 1. Clone and Branch

Before coding, please pull the latest code from the `main` branch and create a new feature branch.

```bash
git checkout main
git pull origin main
git checkout -b feature/your-feature-name
# Example: git checkout -b feature/add-yandex-support
```

### 2. Install Dependencies

We recommend using a virtual environment:

**Bash**

```bash
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
pip install -r requirements.txt
pip install -e .          # Install the package in editable mode
```

### 3. Run Tests

Ensure all tests pass before submitting:

**Bash**

```bash
pytest
```

### 4. Submit a Pull Request (PR)

Push your changes to your fork and submit a Pull Request to our main branch. Please provide a clear description of your changes.

Thank you for building with Thordata! 🚀
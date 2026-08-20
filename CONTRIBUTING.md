# Contributing to DemandPulse

Thank you for your interest in contributing to **DemandPulse**. We welcome high-quality contributions in forecasting algorithms, causal inference estimators, inventory decision rules, API performance, and MLOps tooling.

---

## Development Setup

### 1. Requirements
- Python 3.10+ (Python 3.11 recommended)
- Git
- Docker & Docker Compose (optional for containerized testing)

### 2. Local Installation
Clone the repository and install the package in editable mode with development extras:

```bash
git clone https://github.com/waqaszahoor2/DemandPulse.git
cd DemandPulse
python -m pip install -e ".[dev]"
```

---

## Quality Standards & CI Gates

DemandPulse enforces strict code quality and testing standards. Before submitting a pull request, ensure all local checks pass:

### 1. Run Unit & Integration Tests
```bash
make test
```
*Equivalent command:* `python -m pytest tests -v`

### 2. Linting & Formatting
```bash
make lint
make format
```
*Tools used:* `ruff check src tests` and `ruff format --check src tests`

### 3. Type Checking
```bash
make typecheck
```
*Tool used:* `mypy src`

### 4. Dependency Security Audit
```bash
make security
```
*Tool used:* `pip-audit`

---

## Pull Request Guidelines

1. **Feature Branches**: Create a descriptive branch name (e.g., `feature/add-conformal-interval`, `fix/leakage-lag-computation`).
2. **Commit Messages**: Write concise, imperative commit messages (e.g., `feat: implement AIPW doubly robust estimator`).
3. **Test Coverage**: Every new feature or bug fix must include corresponding pytest test cases under `tests/`.
4. **Documentation**: Update docstrings and relevant markdown files (`README.md`, `MODEL_CARD.md`, `RESULTS.md`) when modifying API routes or model capabilities.

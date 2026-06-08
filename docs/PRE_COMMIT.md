# Pre-commit configuration for AIPY-VN

This repository uses pre-commit hooks to ensure code quality and consistency.

## Installation

1. Install pre-commit:
```bash
pip install pre-commit
```

2. Install the hooks:
```bash
pre-commit install
```

3. Run hooks on all files:
```bash
pre-commit run --all-files
```

## Available Hooks

### Python (Backend)
- **ruff**: Fast Python linter and formatter
- **black**: Code formatter
- **isort**: Import sorting
- **mypy**: Static type checking
- **bandit**: Security linter

### TypeScript/JavaScript (Frontend)
- **eslint**: Linter for TS/JS
- **prettier**: Code formatter

### General
- **trailing-whitespace**: Remove trailing whitespace
- **end-of-file-fixer**: Ensure files end with newline
- **check-yaml**: Validate YAML files
- **check-json**: Validate JSON files
- **check-toml**: Validate TOML files
- **detect-private-key**: Detect private keys
- **check-merge-conflict**: Detect merge conflicts

### Security
- **bandit**: Python security linter
- **detect-secrets**: Detect secrets in code

### Docker
- **hadolint**: Dockerfile linter

### Custom Hooks
- **pytest-backend**: Run backend tests
- **typecheck-frontend**: Type check frontend apps

## Usage

### Automatic Hooks
Hooks run automatically on `git commit`. If a hook fails, the commit will be blocked.

### Manual Hooks
Run hooks manually:
```bash
# Run all hooks
pre-commit run --all-files

# Run specific hook
pre-commit run ruff --all-files

# Run hooks on staged files only
pre-commit run
```

### Skip Hooks
Skip hooks (not recommended):
```bash
git commit --no-verify -m "message"
```

## Configuration

Hooks are configured in `.pre-commit-config.yaml`. To add or modify hooks:

1. Edit `.pre-commit-config.yaml`
2. Update hooks: `pre-commit autoupdate`
3. Reinstall: `pre-commit install`

## Troubleshooting

### Hook Fails
If a hook fails:
1. Fix the reported issues
2. Run `pre-commit run --all-files` to verify
3. Commit again

### Hook Timeout
If a hook times out, increase timeout in `.pre-commit-config.yaml`:
```yaml
  - id: mypy
    args: [--ignore-missing-imports]
    additional_dependencies: [...]
    timeout: 300  # 5 minutes
```

### Update Hooks
Update to latest versions:
```bash
pre-commit autoupdate
```

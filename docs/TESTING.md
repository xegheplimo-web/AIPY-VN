# Testing Guide

## Required Checks

### JavaScript / TypeScript

```bash
npm run lint
npm run test
npm run build
```

### Python

```bash
cd apps/api-server
python -m pytest
```

### Docker

```bash
docker compose ps
```

## AI Testing Rules

1. Run relevant tests after code changes
2. Report exact failing command if test fails
3. Identify root cause before changing code again
4. Avoid random fixes
5. Add/update tests for new features

## Definition of Done

A task is done only when:

- Code compiles/builds
- Lint passes or exceptions explained
- Tests pass or failures documented
- App starts
- UI/API behavior verified
- Files changed reported

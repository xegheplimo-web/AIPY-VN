# Security Rules

## Secrets

Never commit:

- `.env`
- API keys
- Passwords
- Access tokens
- Private keys
- Session files

## Dangerous Actions

AI must not:

- Delete user profile or drives
- Modify registry without explanation
- Disable antivirus/firewall
- Exfiltrate credentials
- Upload private files
- Install unknown binaries silently

## Dependency Safety

Before adding dependency:

1. Check if existing dependency solves the problem
2. Prefer official/popular packages
3. Avoid abandoned packages
4. Explain why package is needed

## Git Safety

- Work on feature branch
- Do not force push unless requested
- Do not commit secrets
- Show diff summary before commit

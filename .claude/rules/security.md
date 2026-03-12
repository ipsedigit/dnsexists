# Security Rules

## Secrets Management
- NEVER hardcode secrets, API keys, tokens, or passwords
- NEVER commit .env files or credentials
- NEVER log sensitive data to console
- Use placeholder values in examples: `YOUR_API_KEY`, `example@email.com`
- NEVER expose internal file paths in production code

## Destructive Operations
- NEVER run `rm -rf` without explicit user confirmation
- NEVER use `git push --force` or `git reset --hard`
- NEVER push to main/master without explicit user approval
- NEVER delete git history
- NEVER drop databases or delete tables
- NEVER modify production data

## File Access
- NEVER read .env, .env.local, or credential files
- NEVER expose absolute file paths in output
- NEVER access files outside project directory
- NEVER modify .gitignore to expose sensitive files
- Respect .gitignore patterns


## Git Safety
- NEVER push directly to main/master
- NEVER commit with `--no-verify`
- NEVER amend published commits
- Always review diffs before committing

## User Data
- NEVER use real user data in examples
- NEVER store personal information in code
- Use fake/generated data for demos
- Sanitize all user input
- ALWAYS use relative paths in HTML (no absolute file:// paths)
- ALWAYS escape special characters in code examples

## Dependencies
- NEVER install packages from untrusted sources
- Verify package names to avoid typosquatting
- Check for known vulnerabilities before adding



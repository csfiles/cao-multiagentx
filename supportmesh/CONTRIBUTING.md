# Contributing to SupportMesh

Thank you for your interest in contributing! SupportMesh is an open-source reference implementation and welcomes contributions of all kinds.

## Ways to Contribute

- Bug reports and fixes
- New MCP tools or AWS backend integrations
- Additional agent profiles
- Documentation improvements
- Test coverage expansion
- Performance improvements

## Development Setup

```bash
git clone https://github.com/your-org/supportmesh.git
cd supportmesh
cp .env.example .env
uv pip install -e ".[dev]"
make test
```

## Workflow

1. **Fork** the repository on GitHub
2. **Create a branch** from `main`:
   ```bash
   git checkout -b feat/your-feature-name
   ```
3. **Make changes** — write code, add tests, update docs
4. **Run checks** before committing:
   ```bash
   make format
   make lint
   make test
   ```
5. **Commit** with a clear message (see commit style below)
6. **Push** and open a **Pull Request** against `main`

## Commit Message Style

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add DynamoDB backend for order storage
fix: handle missing customer_id in refund eligibility check
docs: add AWS Bedrock integration guide
test: add parallel policy retrieval test
chore: bump mcp dependency to 1.1.0
```

Types: `feat`, `fix`, `docs`, `test`, `refactor`, `chore`, `perf`

## Code Style

- **Formatter**: `ruff format` (line length 100)
- **Linter**: `ruff check` with `E, F, I, UP` rules
- **Type hints**: required for all public functions
- **Docstrings**: required for all public modules, classes, and functions
- **No secrets**: never commit credentials, API keys, or `.env` files

## Testing Requirements

- All new features must have tests in `tests/`
- Tests must pass without AWS credentials (use local data)
- Mutation tests must verify safety guards are respected
- Use `pytest-asyncio` for async tests

## Pull Request Guidelines

- Keep PRs focused — one feature or fix per PR
- Include tests for all new functionality
- Update documentation if you change behavior
- Reference any related issues: `Closes #123`
- PRs require at least one approving review

## Issue Templates

When filing a bug, include:
- SupportMesh version (`supportmesh --version`)
- Python version (`python --version`)
- CAO CLI version (`cao --version`)
- Steps to reproduce
- Expected vs. actual behavior
- Relevant log output (redact any credentials)

## Code of Conduct

This project follows the [Contributor Covenant Code of Conduct](https://www.contributor-covenant.org/version/2/1/code_of_conduct/).
Be respectful, inclusive, and constructive.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

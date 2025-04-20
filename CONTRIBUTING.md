# Contributing to Klavis AI

Thank you for your interest in contributing to Klavis AI! This document outlines the process and conventions we use for contributions, pull requests, and commit messages.

## Contributor License Agreement (CLA)

Before we can accept your contributions, we require all contributors to sign our Contributor License Agreement (CLA). This is a one-time process.

[Contributor License Agreement](https://cla-assistant.io/Klavis-AI/klavis)

The CLA helps ensure that everyone who submits a contribution has the legal right to do so and agrees to the terms under which the contribution is accepted. Without this agreement, we cannot review or accept your contributions.

## Table of Contents

- [Contributor License Agreement (CLA)](#contributor-license-agreement-cla)
- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Commit Message Convention](#commit-message-convention)
- [Pull Request Process](#pull-request-process)
- [Code Style Guidelines](#code-style-guidelines)
- [Testing Guidelines](#testing-guidelines)
- [License](#license)

## Code of Conduct

We expect all contributors to follow our Code of Conduct. Please be respectful and inclusive in all interactions.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/yourusername/klavisAi.git`
3. Add the upstream remote: `git remote add upstream https://github.com/Klavis-AI/klavis.git`
4. Create a new branch for your feature or bug fix
5. Make your changes
6. Submit a pull request

## Development Workflow

### Monorepo Structure

The project is organized as a monorepo with multiple MCP servers and clients:

- `mcp_servers/` - Contains individual Model Context Protocol servers
- `mcp_clients/` - Contains clients that connect to MCP servers

When making changes, be mindful of the scope of your change and any potential impacts on other components.

## Commit Message Convention

We follow a simplified version of the [Conventional Commits](https://www.conventionalcommits.org/) specification for commit messages.

Format:

```
<type>(<scope>): <subject>
```

### Type

Must be one of the following:

- `feat`: A new feature
- `fix`: A bug fix
- `docs`: Documentation only changes
- `style`: Changes that do not affect the meaning of the code (formatting, etc.)
- `refactor`: A code change that neither fixes a bug nor adds a feature
- `perf`: A code change that improves performance
- `test`: Adding missing or correcting existing tests
- `chore`: Changes to the build process or auxiliary tools
- `ci`: Changes to CI configuration files and scripts

### Scope

The scope is optional and can be anything specifying the place of the commit change. For example: `slack`, `github`, `supabase`, etc.

### Subject

The subject contains a succinct description of the change:
- Use the imperative, present tense: "change" not "changed" nor "changes"
- Don't capitalize the first letter
- No period (.) at the end

### Examples

```
feat(slack): add user profile lookup functionality
```

```
fix(github): resolve PR comment retrieval issue
```

```
docs(core): update installation instructions
```

```
refactor(supabase): simplify authentication flow
```

## Pull Request Process

1. **Create a descriptive PR title** following the commit message format:
   ```
   <type>(<scope>): <subject>
   ```

2. **Fill in the PR template** with:
   - A clear description of the changes
   - The motivation for the changes
   - Any additional context that might be helpful
   - Screenshots if applicable

3. **Link related issues** using GitHub keywords like "Closes #123" or "Fixes #456"

4. **Keep PRs focused and reasonably sized** - Split large changes into smaller, more manageable PRs when possible

5. **Update documentation** if your changes affect the public API or user experience

6. **Add tests** for new features or bug fixes

7. **Make sure all tests pass** and code style checks complete successfully

8. **Request reviews** from appropriate team members

9. **Address review feedback** promptly and thoroughly

10. **Rebase your branch** on the latest main branch before merging


## Testing Guidelines

- Write tests for all new features and bug fixes
- Maintain or improve code coverage
- Test across multiple Node.js/Python/go versions when appropriate

## License

By contributing to Klavis AI, you agree that your contributions will be licensed under the project's [MIT License](LICENSE).
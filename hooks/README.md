# Git Hooks

This directory contains Git hook templates for the qontinui-devtools repository.

## Available Hooks

### commit-msg

Prevents commit messages from containing the word "Claude" (case-insensitive).

## Installation

To install the hooks, run the following commands from the repository root:

```bash
# Install commit-msg hook
cp hooks/commit-msg .git/hooks/commit-msg
chmod +x .git/hooks/commit-msg

# On Windows/WSL, you may also need to convert line endings
sed -i 's/\r$//' .git/hooks/commit-msg
```

## Automatic Installation

You can install all hooks at once with:

```bash
# Copy all hooks
cp hooks/* .git/hooks/
chmod +x .git/hooks/*

# Fix line endings on Windows/WSL
find .git/hooks -type f -exec sed -i 's/\r$//' {} \;
```

## Testing

To test if the hook is working:

```bash
# This should fail
git commit --allow-empty -m "Test with Claude"

# This should succeed
git commit --allow-empty -m "Test without the forbidden word"
```

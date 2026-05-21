from pathlib import Path
import os

# Canonical purge targets (heavy project build artifacts)
PURGE_TARGETS = {
    "node_modules",
    "target",        # Rust, Maven
    "build",         # Gradle, various
    "dist",          # JS builds
    "venv",          # Python
    ".venv",         # Python
    ".pytest_cache", # Python (pytest)
    ".mypy_cache",   # Python (mypy)
    ".tox",          # Python (tox virtualenvs)
    ".nox",          # Python (nox virtualenvs)
    ".ruff_cache",   # Python (ruff)
    ".gradle",       # Gradle local
    "__pycache__",   # Python
    ".next",         # Next.js
    ".nuxt",         # Nuxt.js
    ".output",       # Nuxt.js
    "vendor",        # PHP Composer
    "bin",           # .NET build output (guarded)
    "obj",           # C# / Unity
    ".turbo",        # Turborepo cache
    ".parcel-cache" # Parcel bundler
    ".dart_tool",    # Flutter/Dart build cache
    ".zig-cache",    # Zig
    "zig-out",       # Zig
    ".angular",      # Angular
    ".svelte-kit",   # SvelteKit
    ".astro",        # Astro
    "coverage",      # Code coverage reports
    ".cxx",          # React Native Android NDK build cache
    ".expo",         # Expo
    ".build",        # Swift Package Manager
}

# Monorepo indicators (higher priority)
MONOREPO_INDICATORS = {
    "lerna.json",
    "pnpm-workspace.yaml",
    "nx.json",
    "rush.json",
}

# Project indicators for container detection
PROJECT_INDICATORS = {
    "package.json",
    "Cargo.toml",
    "go.mod",
    "pyproject.toml",
    "requirements.txt",
    "pom.xml",
    "build.gradle",
    "Gemfile",
    "composer.json",
    "pubspec.yaml",
    "Package.swift",
    "Makefile",
    "build.zig",
    "build.zig.zon",
    ".git",
}

# Default search paths for Linux
DEFAULT_PURGE_SEARCH_PATHS = [
    str(Path.home() / "Documents"),
    str(Path.home() / "Projects"),
    str(Path.home() / "Code"),
    str(Path.home() / "Development"),
    str(Path.home() / "src"),
    str(Path.home() / "repos"),
    str(Path.home() / "workspace"),
]

# Config file for custom purge paths
PURGE_CONFIG_FILE = Path.home() / ".config" / "lmole" / "purge_paths"

# Minimum age in days before considering for cleanup
MIN_AGE_DAYS = 7

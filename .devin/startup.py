#!/usr/bin/env python3
"""
.devin/startup.py - AI Coding Auto-Startup System
Auto-detect project type, init CodeGraph, apply optimal AI configuration
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# Colors for terminal output
RESET = "\033[0m"
BOLD = "\033[1m"
GREEN = "\033[32m"
CYAN = "\033[36m"
YELLOW = "\033[33m"
RED = "\033[31m"
DIM = "\033[2m"
MAGENTA = "\033[35m"
WHITE = "\033[37m"


def print_step(icon: str, message: str, color: str = CYAN) -> None:
    print(f"{color}{icon}{RESET} {message}")


def print_sub(message: str, color: str = DIM) -> None:
    print(f"   {color}-> {message}{RESET}")


def print_done(message: str = "Done") -> None:
    print(f"   {GREEN}[OK] {message}{RESET}")


def print_skip(message: str) -> None:
    print(f"   {DIM}[SKIP] {message}{RESET}")


def print_warn(message: str) -> None:
    print(f"   {YELLOW}[WARN] {message}{RESET}")


def print_error(message: str) -> None:
    print(f"   {RED}[ERR] {message}{RESET}")


class ProjectDetector:
    """Detects project type by scanning files."""

    SKIP_DIRS = {
        "node_modules",
        ".git",
        "__pycache__",
        ".venv",
        ".env",
        "venv",
        "dist",
        "build",
        ".next",
        ".nuxt",
        "target",
        "coverage",
        ".turbo",
        "playwright-report",
        "test-results",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        "*.egg-info",
        ".devin",
    }

    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        self.fingerprint: dict[str, bool] = {}

    def _exists(self, pattern: str) -> bool:
        return any(self.root.glob(pattern))

    def _find_files(self, pattern: str, max_files: int = 10) -> list[Path]:
        """Find files matching pattern, skipping heavy directories."""
        return list(self._walk_filtered(self.root, pattern, max_files))

    def _walk_filtered(
        self, start: Path, pattern: str, max_files: int = 10
    ) -> list[Path]:
        """Walk from start, skipping heavy directories, yielding matches."""
        results: list[Path] = []
        for dirpath, dirnames, filenames in os.walk(start, topdown=True):
            dirnames[:] = [d for d in dirnames if d not in self.SKIP_DIRS]
            for fn in filenames:
                if Path(fn).match(pattern):
                    results.append(Path(dirpath) / fn)
                    if len(results) >= max_files:
                        return results
        return results

    def detect(self) -> dict[str, bool]:
        r = self.root
        fp = self.fingerprint

        # Python
        fp["python"] = any(
            [
                (r / "pyproject.toml").exists(),
                (r / "requirements.txt").exists(),
                (r / "setup.py").exists(),
                (r / "Pipfile").exists(),
                len(self._find_files("*.py", max_files=1)) > 0,
            ]
        )

        # Node.js / TypeScript
        fp["javascript"] = (r / "package.json").exists()
        fp["typescript"] = (
            (r / "tsconfig.json").exists()
            or len(self._find_files("*.ts", max_files=1)) > 0
            or len(self._find_files("*.tsx", max_files=1)) > 0
        )
        fp["react"] = (
            len(self._find_files("*.tsx", max_files=1)) > 0
            or len(self._find_files("*.jsx", max_files=1)) > 0
        )

        # Rust
        fp["rust"] = (r / "Cargo.toml").exists()

        # Go
        fp["go"] = (r / "go.mod").exists()

        # Java
        fp["java"] = (r / "pom.xml").exists() or (r / "build.gradle").exists()

        # Docker
        fp["docker"] = (r / "docker-compose.yml").exists() or (
            r / "Dockerfile"
        ).exists()

        # Database
        fp["database"] = len(self._find_files("*.sql", max_files=1)) > 0

        # Monorepo / workspace
        fp["monorepo"] = (
            (r / "pnpm-workspace.yaml").exists()
            or (r / "turbo.json").exists()
            or (r / "nx.json").exists()
        )
        fp["pnpm"] = (r / "pnpm-workspace.yaml").exists() or (
            r / "pnpm-lock.yaml"
        ).exists()
        fp["turbo"] = (r / "turbo.json").exists()
        fp["nx"] = (r / "nx.json").exists()

        # Testing
        fp["vitest"] = len(self._find_files("vitest.config.*", max_files=1)) > 0
        fp["jest"] = len(self._find_files("jest.config.*", max_files=1)) > 0
        fp["playwright"] = len(self._find_files("playwright.config.*", max_files=1)) > 0
        fp["pytest"] = (r / "pytest.ini").exists() or (r / "pyproject.toml").exists()
        fp["has_tests"] = (
            len(self._find_files("*.test.ts", max_files=1)) > 0
            or len(self._find_files("*.test.tsx", max_files=1)) > 0
            or len(self._find_files("*.test.js", max_files=1)) > 0
            or len(self._find_files("test_*.py", max_files=1)) > 0
        )

        # Package managers
        fp["yarn"] = (r / "yarn.lock").exists()
        fp["npm"] = (r / "package-lock.json").exists()
        fp["uv"] = (r / "uv.lock").exists()

        # CI/CD
        fp["github_actions"] = (r / ".github").is_dir()

        # Framework specifics from all package.json files
        for pkg_path in self._find_files("package.json", max_files=20):
            try:
                data = json.loads(pkg_path.read_text(encoding="utf-8"))
                deps = list(data.get("dependencies", {}).keys())
                deps += list(data.get("devDependencies", {}).keys())
                for dep in deps:
                    dep_lower = dep.lower()
                    if dep_lower == "react":
                        fp["react"] = True
                    if dep_lower == "next":
                        fp["nextjs"] = True
                    if dep_lower == "vue":
                        fp["vue"] = True
                    if dep_lower == "svelte":
                        fp["svelte"] = True
                    if dep_lower == "tailwindcss":
                        fp["tailwind"] = True
                    if dep_lower == "@tanstack/react-query":
                        fp["react_query"] = True
                    if dep_lower == "zustand":
                        fp["zustand"] = True
                    if dep_lower == "express":
                        fp["express"] = True
                    if dep_lower == "fastify":
                        fp["fastify"] = True
                    if dep_lower == "prisma":
                        fp["prisma"] = True
                    if dep_lower == "drizzle-orm":
                        fp["drizzle"] = True
                    if dep_lower == "vite":
                        fp["vite"] = True
            except Exception:
                pass

        # Python framework specifics (sample first 50 .py files)
        if fp.get("python"):
            py_files = self._find_files("*.py", max_files=50)
            for f in py_files:
                try:
                    content = f.read_text(encoding="utf-8", errors="ignore")
                    lines = content.splitlines()
                    for line in lines:
                        stripped = line.strip()
                        if stripped.startswith("from fastapi") or stripped.startswith(
                            "import fastapi"
                        ):
                            fp["fastapi"] = True
                        if stripped.startswith("from flask") or stripped.startswith(
                            "import flask"
                        ):
                            fp["flask"] = True
                        if stripped.startswith("from django") or stripped.startswith(
                            "import django"
                        ):
                            fp["django"] = True
                        if stripped.startswith(
                            "from sqlalchemy"
                        ) or stripped.startswith("import sqlalchemy"):
                            fp["sqlalchemy"] = True
                        if stripped.startswith(
                            "import pydantic"
                        ) or stripped.startswith("from pydantic"):
                            fp["pydantic"] = True
                except Exception:
                    pass

        # Frontend E2E detection
        web_dirs = [
            "apps/web-customer",
            "apps/web-owner",
            "apps/web-admin",
            "web",
            "frontend",
            "client",
        ]
        for d in web_dirs:
            p = r / d
            if p.is_dir():
                for _ in self._walk_filtered(p, "playwright.config.*", max_files=1):
                    fp["playwright"] = True
                    break
                for ext in ("ts", "tsx", "js", "jsx"):
                    for _ in self._walk_filtered(p, f"*.test.{ext}", max_files=1):
                        fp["has_tests"] = True
                        break
                    if fp.get("has_tests"):
                        break

        return fp


class ConfigBuilder:
    """Builds optimal project configuration from fingerprint."""

    def __init__(self, root: Path, fingerprint: dict[str, bool]) -> None:
        self.root = root
        self.fp = fingerprint

    def build(self) -> dict[str, Any]:
        fp = self.fp

        main_types = []
        if fp.get("python"):
            main_types.append("python")
        if fp.get("typescript"):
            main_types.append("typescript")
        if fp.get("javascript") and not fp.get("typescript"):
            main_types.append("javascript")
        if fp.get("rust"):
            main_types.append("rust")
        if fp.get("go"):
            main_types.append("go")
        if fp.get("java"):
            main_types.append("java")

        frameworks = []
        if fp.get("fastapi"):
            frameworks.append("fastapi")
        if fp.get("flask"):
            frameworks.append("flask")
        if fp.get("django"):
            frameworks.append("django")
        if fp.get("react"):
            frameworks.append("react")
        if fp.get("nextjs"):
            frameworks.append("nextjs")
        if fp.get("vue"):
            frameworks.append("vue")
        if fp.get("svelte"):
            frameworks.append("svelte")
        if fp.get("express"):
            frameworks.append("express")

        databases = []
        if fp.get("sqlalchemy") or fp.get("prisma") or fp.get("drizzle"):
            databases.append("orm")
        if fp.get("database"):
            databases.append("sql")

        testing = []
        if fp.get("pytest"):
            testing.append("pytest")
        if fp.get("vitest"):
            testing.append("vitest")
        if fp.get("jest"):
            testing.append("jest")
        if fp.get("playwright"):
            testing.append("playwright")

        package_manager = "npm"
        if fp.get("pnpm"):
            package_manager = "pnpm"
        elif fp.get("yarn"):
            package_manager = "yarn"

        python_manager = "pip"
        if fp.get("uv"):
            python_manager = "uv"

        # Exclude patterns
        exclude = [
            "**/node_modules/**",
            "**/dist/**",
            "**/build/**",
            "**/.git/**",
            "**/target/**",
            "**/__pycache__/**",
            "**/.venv/**",
            "**/.next/**",
            "**/.nuxt/**",
            "**/coverage/**",
            "**/*.min.js",
            "**/*.min.css",
            "**/*.map",
            "**/.turbo/**",
            "**/playwright-report/**",
            "**/test-results/**",
        ]

        if fp.get("docker"):
            exclude += ["**/postgres_data/**", "**/redis_data/**"]
        if fp.get("python"):
            exclude += [
                "**/.pytest_cache/**",
                "**/*.egg-info/**",
                "**/.mypy_cache/**",
                "**/.ruff_cache/**",
            ]
        if fp.get("rust"):
            exclude += ["**/Cargo.lock"]

        settings = {
            "contextWindow": "maximum",
            "codeUnderstanding": "deep",
            "enableParallelQueries": True,
            "maxParallelCalls": 10,
            "enableCaching": True,
            "smartContextSelection": True,
            "autoDetectProjectType": True,
            "preferCodegraphOverGrep": True,
        }

        if fp.get("python"):
            settings["python"] = {
                "linter": "ruff",
                "formatter": "ruff",
                "typeChecker": "mypy",
                "testRunner": "pytest" if fp.get("pytest") else "unittest",
                "importSorting": "ruff",
                "docstringStyle": "google",
                "strictTypeHints": True,
            }

        if fp.get("typescript"):
            settings["typescript"] = {
                "strictMode": True,
                "linter": "eslint",
                "formatter": "prettier",
                "typeChecker": "tsc",
                "testRunner": (
                    "vitest"
                    if fp.get("vitest")
                    else ("jest" if fp.get("jest") else "node")
                ),
                "bundler": (
                    "vite"
                    if fp.get("vite")
                    else ("next" if fp.get("nextjs") else "unknown")
                ),
            }

        ai_config = {
            "preferStructuralSearch": True,
            "useCodeGraphFirst": True,
            "aggressiveOptimization": True,
            "cacheSymbolReferences": True,
            "cacheFileRelationships": True,
            "prefetchRelatedFiles": True,
            "lazyLoadLargeFiles": True,
            "enableAutoVerification": True,
            "verification": {
                "autoRunTests": True,
                "autoRunLint": True,
                "autoRunTypecheck": True,
                "autoRunBuild": False,
                "failFast": True,
                "maxRetries": 3,
            },
        }

        skills_auto_invoke = {
            "gitnexus-exploring": {
                "enabled": True,
                "triggers": [
                    "how does",
                    "explain",
                    "architecture",
                    "flow",
                    "trace",
                    "cach hoat dong",
                ],
            },
            "gitnexus-impact-analysis": {
                "enabled": True,
                "triggers": [
                    "impact",
                    "break",
                    "affect",
                    "change",
                    "refactor",
                    "rename",
                    "anh huong",
                ],
            },
            "gitnexus-debugging": {
                "enabled": True,
                "triggers": [
                    "bug",
                    "error",
                    "fail",
                    "debug",
                    "fix",
                    "why",
                    "loi",
                    "sua",
                ],
            },
            "gitnexus-refactoring": {
                "enabled": True,
                "triggers": [
                    "refactor",
                    "extract",
                    "rename",
                    "move",
                    "split",
                    "tai cau truc",
                ],
            },
            "gitnexus-pr-review": {
                "enabled": True,
                "triggers": ["review", "pr", "pull request", "merge", "danh gia"],
            },
        }

        return {
            "version": "2.0",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "projectPath": str(self.root),
            "projectName": self.root.name,
            "projectTypes": main_types,
            "frameworks": frameworks,
            "databases": databases,
            "testing": testing,
            "packageManager": package_manager,
            "pythonManager": python_manager,
            "isMonorepo": fp.get("monorepo", False),
            "hasDocker": fp.get("docker", False),
            "hasCI": fp.get("github_actions", False),
            "excludePatterns": sorted(set(exclude)),
            "settings": settings,
            "aiConfig": ai_config,
            "skillsAutoInvoke": skills_auto_invoke,
            "detectedFingerprint": sorted(fp.keys()),
        }


def init_codegraph(root: Path) -> bool:
    """Initialize CodeGraph if not already present."""
    codegraph_dir = root / ".codegraph"
    if codegraph_dir.exists():
        print_skip("CodeGraph already initialized (.codegraph exists)")
        return True

    print_step(">>", "CodeGraph not initialized. Running init...", YELLOW)
    try:
        result = subprocess.run(
            ["codegraph", "init", "-i"],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode == 0:
            print_done("CodeGraph initialized")
            return True
        else:
            print_warn("CodeGraph init returned non-zero exit code")
            for line in result.stderr.splitlines()[:10]:
                print_sub(line, DIM)
            return False
    except FileNotFoundError:
        print_warn("codegraph CLI not found in PATH. Skipping auto-init.")
        return False
    except subprocess.TimeoutExpired:
        print_warn("CodeGraph init timed out after 120s")
        return False
    except Exception as e:
        print_warn(f"CodeGraph init failed: {e}")
        return False


def update_codegraphignore(root: Path, patterns: list[str]) -> None:
    """Update or create .codegraphignore with optimized patterns."""
    ignore_file = root / ".codegraphignore"
    existing = set()
    if ignore_file.exists():
        for line in ignore_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                existing.add(line)

    merged = sorted(existing | set(patterns))
    header = [
        "# ============================================================================",
        f"# .codegraphignore - Auto-generated by .devin/startup.py",
        f"# Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "# ============================================================================",
        "",
    ]
    content = "\n".join(header + merged)
    ignore_file.write_text(content + "\n", encoding="utf-8")
    print_done(f".codegraphignore updated ({len(merged)} patterns)")


def save_project_config(root: Path, config: dict[str, Any]) -> None:
    """Save project-config.json."""
    config_dir = root / ".devin"
    config_dir.mkdir(exist_ok=True)
    config_path = config_dir / "project-config.json"
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print_done("project-config.json saved")


def verify_tools() -> None:
    """Verify development tools are available."""
    tools = [
        ("node", ["--version"]),
        ("pnpm", ["--version"]),
        ("python", ["--version"]),
        ("uv", ["--version"]),
        ("docker", ["--version"]),
        ("codegraph", ["--version"]),
        ("gitnexus", ["--version"]),
    ]
    for name, args in tools:
        try:
            result = subprocess.run(
                [name, *args],
                capture_output=True,
                text=True,
                timeout=5,
            )
            ver = (result.stdout or result.stderr).strip().splitlines()[0]
            print_sub(f"{name}: {ver}", GREEN)
        except (FileNotFoundError, subprocess.TimeoutExpired):
            print_sub(f"{name}: not installed", DIM)
        except Exception as e:
            print_sub(f"{name}: error ({e})", YELLOW)


def print_summary(config: dict[str, Any], elapsed: float) -> None:
    """Print final summary."""
    print()
    print(f"{CYAN}{'=' * 67}{RESET}")
    print(f"{CYAN}  AI Coding Environment Ready{RESET}")
    print(f"{CYAN}{'=' * 67}{RESET}")
    print()
    print(f"  Project:   {WHITE}{config['projectName']}{RESET}")
    print(f"  Types:     {GREEN}{', '.join(config['projectTypes'])}{RESET}")
    print(f"  Frameworks: {GREEN}{', '.join(config['frameworks'])}{RESET}")
    print(f"  Testing:   {GREEN}{', '.join(config['testing'])}{RESET}")
    print(f"  Package:   {GREEN}{config['packageManager']}{RESET}")
    print(f"  Python:    {GREEN}{config['pythonManager']}{RESET}")
    print(
        f"  Monorepo:  {GREEN if config['isMonorepo'] else DIM}{'Yes' if config['isMonorepo'] else 'No'}{RESET}"
    )
    print()
    cg_status = (
        "Initialized OK"
        if (Path(config["projectPath"]) / ".codegraph").exists()
        else "Not initialized"
    )
    cg_color = (
        GREEN if (Path(config["projectPath"]) / ".codegraph").exists() else YELLOW
    )
    print(f"  CodeGraph:      {cg_color}{cg_status}{RESET}")
    print(f"  Config file:    {GREEN}.devin/project-config.json{RESET}")
    print(f"  Ignore file:    {GREEN}.codegraphignore{RESET}")
    print()
    print("  AI Optimizations:")
    print("    - Structural search preferred (CodeGraph > grep)")
    print("    - Parallel queries enabled (10 max)")
    print("    - Smart context selection active")
    print("    - Symbol reference caching on")
    print()
    print(f"  {DIM}Completed in {elapsed:.2f}s{RESET}")
    print(f"{CYAN}{'=' * 67}{RESET}")
    print()


def main() -> int:
    import time

    start_time = time.time()

    # Determine project root
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent

    print()
    print(f"{CYAN}+{'-' * 65}+{RESET}")
    print(
        f"{CYAN}|           Devin AI Auto-Startup System v2.0                   |{RESET}"
    )
    print(f"{CYAN}+{'-' * 65}+{RESET}")
    print()

    # Step 1: Detect
    print_step(">>", "Detecting project fingerprint...")
    detector = ProjectDetector(project_root)
    fingerprint = detector.detect()
    print_done(f"Detected {len(fingerprint)} signals")
    for key, val in sorted(fingerprint.items()):
        print_sub(f"{key} = {val}")

    # Step 2: Build config
    print_step(">>", "Building optimal project configuration...")
    builder = ConfigBuilder(project_root, fingerprint)
    config = builder.build()
    print_done("Configuration built")

    # Step 3: Save config
    print_step(">>", "Saving project-config.json...")
    save_project_config(project_root, config)

    # Step 4: Init CodeGraph
    print_step(">>", "Checking CodeGraph status...")
    init_codegraph(project_root)

    # Step 5: Update .codegraphignore
    print_step(">>", "Updating .codegraphignore...")
    update_codegraphignore(project_root, config["excludePatterns"])

    # Step 6: Summary
    elapsed = time.time() - start_time
    print_summary(config, elapsed)

    # Step 7: Tool verification
    print_step(">>", "Verifying development tools...")
    verify_tools()
    print()

    return 0


if __name__ == "__main__":
    sys.exit(main())

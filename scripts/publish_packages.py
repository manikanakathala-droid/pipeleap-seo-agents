"""
Package Publishing Automation

Generates and publishes npm, PyPI, and crates.io packages (pipeleap-tools).
Each package provides a high-DA backlink to pipeleap.com from its registry page.

Usage:
    # Generate only (no publish)
    python scripts/publish_packages.py

    # Generate and publish (requires tokens in env)
    python scripts/publish_packages.py --publish

    # Publish only specified packages
    python scripts/publish_packages.py --publish --packages npm,pypi

Environment variables for publishing:
    NPM_TOKEN                  — npm automation token (npmjs.com → Access Tokens)
    PYPI_TOKEN                 — PyPI API token (pypi.org → Account → API tokens)
    CARGO_REGISTRY_TOKEN       — crates.io API token (crates.io → Account Settings)

Output:
    outputs/backlinks/packages_report.json
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

# Ensure project root is on sys.path
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))

from connectors.api_backlinks import (
    NpmPackagePublisher,
    CratesIoPublisher,
    create_pypi_package,
)


def _run(cmd: list[str], cwd: Path | None = None, env: dict | None = None) -> tuple[int, str]:
    """Run a shell command and return (returncode, output)."""
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            env={**os.environ, **(env or {})},
            capture_output=True,
            text=True,
            timeout=120,
        )
        output = result.stdout + result.stderr
        return result.returncode, output.strip()
    except subprocess.TimeoutExpired:
        return -1, "Command timed out after 120s"
    except FileNotFoundError as exc:
        return -2, f"Command not found: {exc}"
    except Exception as exc:
        return -3, str(exc)


def publish_npm(pkg_path: Path) -> dict:
    """Publish the npm package if NPM_TOKEN is set."""
    token = os.environ.get("NPM_TOKEN", "").strip()
    if not token:
        return {"ok": False, "error": "NPM_TOKEN not set", "published": False}

    npmrc_content = f"//registry.npmjs.org/:_authToken={token}\n"
    npmrc_path = pkg_path / ".npmrc"
    npmrc_path.write_text(npmrc_content, encoding="utf-8")

    rc, out = _run(
        ["npm", "publish", "--access", "public"],
        cwd=pkg_path,
    )

    if rc == 0:
        print(f"  ✓ npm package published: {pkg_path.name}")
        return {
            "ok": True,
            "published": True,
            "package": "pipeleap-tools",
            "registry": "npmjs.com",
            "output": out,
        }
    else:
        # Check if it's already published (version conflict)
        if "cannot publish over existing version" in out.lower():
            print(f"  ~ npm package already published at this version")
            return {"ok": True, "published": False, "reason": "already published", "output": out}
        print(f"  ✗ npm publish failed (rc={rc}): {out[:200]}")
        return {"ok": False, "error": out[:500], "published": False}


def publish_pypi(pkg_path: Path) -> dict:
    """Build and publish the PyPI package if PYPI_TOKEN is set."""
    token = os.environ.get("PYPI_TOKEN", "").strip()
    if not token:
        return {"ok": False, "error": "PYPI_TOKEN not set", "published": False}

    # Build the package
    rc, build_out = _run(
        [sys.executable, "-m", "build"],
        cwd=pkg_path,
    )
    if rc != 0:
        return {"ok": False, "error": f"Build failed: {build_out[:500]}", "published": False}

    # Upload with token auth
    env = {**os.environ, "TWINE_USERNAME": "__token__", "TWINE_PASSWORD": token}
    rc, upload_out = _run(
        [sys.executable, "-m", "twine", "upload", "dist/*", "--skip-existing"],
        cwd=pkg_path,
        env=env,
    )

    if rc == 0:
        print(f"  ✓ PyPI package published")
        return {"ok": True, "published": True, "package": "pipeleap-tools", "registry": "pypi.org"}
    else:
        if "already exists" in upload_out.lower() or "skip" in upload_out.lower():
            print(f"  ~ PyPI package already published")
            return {"ok": True, "published": False, "reason": "already published"}
        print(f"  ✗ PyPI publish failed (rc={rc}): {upload_out[:200]}")
        return {"ok": False, "error": upload_out[:500], "published": False}


def publish_cargo(pkg_path: Path) -> dict:
    """Publish the Rust crate if CARGO_REGISTRY_TOKEN is set."""
    token = os.environ.get("CARGO_REGISTRY_TOKEN", "").strip()
    if not token:
        return {"ok": False, "error": "CARGO_REGISTRY_TOKEN not set", "published": False}

    rc, out = _run(
        ["cargo", "publish", "--token", token],
        cwd=pkg_path,
    )

    if rc == 0:
        print(f"  ✓ Rust crate published: {pkg_path.name}")
        return {"ok": True, "published": True, "package": "pipeleap-tools", "registry": "crates.io"}
    else:
        if "already uploaded" in out.lower() or "already exists" in out.lower():
            print(f"  ~ Rust crate already published at this version")
            return {"ok": True, "published": False, "reason": "already published"}
        # cargo sometimes exits non-zero but still publishes (network issues)
        if "uploading" in out.lower() and "published" in out.lower():
            print(f"  ✓ Rust crate likely published (non-zero exit but upload confirmed)")
            return {"ok": True, "published": True, "warning": out[:300]}
        print(f"  ✗ cargo publish failed (rc={rc}): {out[:200]}")
        return {"ok": False, "error": out[:500], "published": False}


def process_packages(
    output_base: str | Path,
    packages: str = "npm,pypi,cargo",
    publish: bool = False,
) -> dict:
    """Generate (and optionally publish) all three packages.

    Args:
        output_base: Directory to write packages and report.
        packages: Comma-separated list of packages to process.
        publish: If True, attempt to publish after generation.

    Returns:
        Dict with keys: started_at, completed_at, generated, published,
        and per-package results under ``npm``, ``pypi``, ``cargo``.
    """
    from typing import Any

    requested = set(p.strip() for p in packages.split(","))
    results: dict[str, Any] = {
        "started_at": datetime.now(timezone.utc).isoformat(),
        "mode": "publish" if publish else "generate-only",
    }

    output_base = Path(output_base)
    output_base.mkdir(parents=True, exist_ok=True)

    # ── npm package ──────────────────────────────────────────────────────────
    if "npm" in requested:
        print("\n[1/3] npm package (DA92)...")
        npm = NpmPackagePublisher()
        gen = npm.create_package(str(output_base / "npm"))
        results["npm"] = gen
        if gen.get("ok") and publish:
            pkg_path = Path(gen["path"])
            results["npm"] = gen | publish_npm(pkg_path)
        elif not publish:
            print(f"  To publish: cd {gen.get('path', '')} && npm publish --access public")
    else:
        results["npm"] = {"ok": False, "skipped": True}

    # ── PyPI package ─────────────────────────────────────────────────────────
    if "pypi" in requested:
        print("\n[2/3] PyPI package (DA85)...")
        gen = create_pypi_package(str(output_base / "pypi"))
        results["pypi"] = gen
        if gen.get("ok") and publish:
            pkg_path = output_base / "pypi"
            results["pypi"] = gen | publish_pypi(pkg_path)
        elif not publish:
            print(f"  To publish: cd {output_base / 'pypi'} && pip install build twine && python -m build && twine upload dist/*")
    else:
        results["pypi"] = {"ok": False, "skipped": True}

    # ── crates.io crate ──────────────────────────────────────────────────────
    if "cargo" in requested:
        print("\n[3/3] Rust crate / crates.io (DA72)...")
        cr = CratesIoPublisher()
        gen = cr.create_crate(str(output_base / "crates"))
        results["cargo"] = gen
        if gen.get("ok") and publish:
            pkg_path = Path(gen["path"])
            results["cargo"] = gen | publish_cargo(pkg_path)
        elif not publish:
            print(f"  To publish: cd {gen.get('path', '')} && cargo publish")
    else:
        results["cargo"] = {"ok": False, "skipped": True}

    # ── Summary ──────────────────────────────────────────────────────────────
    generated = sum(1 for k in ["npm", "pypi", "cargo"] if results.get(k, {}).get("ok"))
    published = sum(
        1 for k in ["npm", "pypi", "cargo"]
        if results.get(k, {}).get("published") is True
    )
    results["generated"] = generated
    results["published"] = published
    results["completed_at"] = datetime.now(timezone.utc).isoformat()

    # ── Report ───────────────────────────────────────────────────────────────
    report_path = output_base / "packages_report.json"
    report_path.write_text(json.dumps(results, indent=2, default=str), encoding="utf-8")
    print(f"\nReport saved: {report_path}")

    print(f"Summary: {generated}/3 generated, {published}/3 published")
    return results


def main_in_process(output_dir: str = "outputs/backlinks") -> dict:
    """Entry point for in-process call from agent. Generate-only."""
    return process_packages(output_dir, publish=False)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate and publish backlink packages")
    parser.add_argument("--publish", action="store_true", help="Publish packages (requires tokens)")
    parser.add_argument(
        "--packages",
        default="npm,pypi,cargo",
        help="Comma-separated packages to process (npm,pypi,cargo). Default: all",
    )
    parser.add_argument(
        "--output",
        default="outputs/backlinks",
        help="Output directory (default: outputs/backlinks)",
    )
    args = parser.parse_args()
    process_packages(args.output, packages=args.packages, publish=args.publish)


if __name__ == "__main__":
    main()

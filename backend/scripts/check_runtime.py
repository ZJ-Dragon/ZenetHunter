"""CLI wrapper for runtime dependency diagnostics."""

from __future__ import annotations

import argparse
import json
import sys

from app.infrastructure.runtime_checks import collect_runtime_diagnostics


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Inspect the active Python runtime and backend dependencies."
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print diagnostics as JSON.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero if required modules are missing.",
    )
    args = parser.parse_args()

    diagnostics = collect_runtime_diagnostics()
    payload = diagnostics.to_dict()

    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print("ZenetHunter runtime diagnostics")
        print(f"  Python executable : {payload['python_executable']}")
        print(f"  Python version    : {payload['python_version']}")
        print(f"  Platform          : {payload['platform']}")
        print(f"  Environment       : {payload['environment_kind']}")
        if payload["environment_name"]:
            print(f"  Environment name  : {payload['environment_name']}")
        print(f"  Root privileges   : {payload['is_root']}")
        print(f"  Dependencies ok   : {payload['dependencies_ready']}")
        if payload["missing_modules"]:
            print("  Missing modules   :")
            for name in payload["missing_modules"]:
                module = payload["modules"][name]
                print(f"    - {name} ({module['import_name']}): {module['error']}")

    if args.strict and not diagnostics.dependencies_ready:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

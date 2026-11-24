import argparse
import sys

import yaml

from .policies import ConfigError, run


def main() -> int:
    ap = argparse.ArgumentParser(description="Apply Azure DevOps branch policies from a definition file.")
    ap.add_argument("config", help="path to governance YAML")
    ap.add_argument("--apply", action="store_true", help="execute the commands (default: print only)")
    args = ap.parse_args()
    with open(args.config, encoding="utf-8") as f:
        config = yaml.safe_load(f)
    try:
        run(config, apply=args.apply)
    except ConfigError as e:
        print(f"config error: {e}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

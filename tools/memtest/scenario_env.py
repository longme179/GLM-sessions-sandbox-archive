#!/usr/bin/env python3
"""scenario_env.py — run scenario.py with an env-file applied (memtest harness).

Used for runtime-variable experiments, e.g. the SW2 scenario:
  scenario_env.py configs/env-wt2.env -- --config configs/idle0.toml \
      --binary ../target/release/minewrapd --label SW2 --seconds 30

Env-file format: one KEY=VALUE per line; '#' comments allowed.
STANDALONE tool (policy Q8): never commit this into the Minewrap app repo.
"""

from __future__ import annotations

import os
import sys


def load_env_file(path: str) -> dict:
    out = {}
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            out[key.strip()] = val.strip().strip('"').strip("'")
    return out


def main() -> int:
    if len(sys.argv) < 3 or sys.argv[2] != "--":
        print("usage: scenario_env.py ENVFILE -- <scenario.py args...>", file=sys.stderr)
        return 2
    env_file, rest = sys.argv[1], sys.argv[3:]
    envs = load_env_file(env_file)
    os.environ.update(envs)
    print(f"scenario_env: applied {list(envs)} from {env_file}", file=sys.stderr)
    import scenario  # noqa: F401  (shares the directory)
    sys.argv = ["scenario.py"] + rest
    return scenario.main()


if __name__ == "__main__":
    sys.exit(main())

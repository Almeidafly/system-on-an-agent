"""Allow `python -m soa` to run the CLI."""

from soa.cli import main

if __name__ == "__main__":
    raise SystemExit(main())

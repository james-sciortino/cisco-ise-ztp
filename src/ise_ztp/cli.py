import argparse
import json
import logging
from pathlib import Path

from .config import load_config, read_json
from .errors import ProjectError
from .esxi import collect_inventory
from .planning import deployment_plan
from .preflight import run_preflight


def parser():
    root = argparse.ArgumentParser(description="Cisco ISE 3.5 ZTP planning and read-only ESXi preflight", allow_abbrev=False)
    sub = root.add_subparsers(dest="command", required=True)
    preflight = sub.add_parser("preflight", help="Offline by default; live access is explicit", allow_abbrev=False)
    preflight.add_argument("--config", type=Path, required=True)
    modes = preflight.add_mutually_exclusive_group()
    modes.add_argument("--dry-run", action="store_true", help="Validate settings only; no network or credentials")
    modes.add_argument("--inventory", type=Path, help="Evaluate a local inventory fixture; no network")
    modes.add_argument("--live", action="store_true", help="Explicitly connect to ESXi for read-only inventory")
    preflight.add_argument("--format", choices=("text", "json"), default="text")
    deploy = sub.add_parser("deploy", help="Future workflow outline only", allow_abbrev=False)
    deploy.add_argument("--config", type=Path, required=True)
    deploy.add_argument("--dry-run", action="store_true")
    return root


def main(argv=None):
    args = parser().parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    log = logging.getLogger("ise_ztp")
    try:
        if args.command == "deploy" and not args.dry_run:
            raise ProjectError("Deployment is not implemented. Only deploy --dry-run is available.")
        config = load_config(args.config)
        if args.command == "deploy":
            print(json.dumps(deployment_plan(config, args.dry_run), indent=2))
            log.info("Offline deployment outline completed; no operations executed.")
            return 0
        inventory = None
        mode = "offline"
        if args.live:
            log.info("Explicit live read-only preflight selected.")
            inventory = collect_inventory(config)
            mode = "live"
        elif args.inventory:
            inventory = read_json(args.inventory)
            mode = "fixture"
        report = run_preflight(config, inventory, mode)
        if args.format == "json":
            print(json.dumps(report.to_dict(), indent=2))
        else:
            print("Mode: " + mode + "; deployment readiness is NOT certified")
            for check in report.checks:
                print(f"{check.status:4} {check.id}: {check.message}")
        log.info("Preflight completed; failed=%s; no infrastructure modified.", report.failed)
        return 1 if report.failed else 0
    except ProjectError as error:
        log.error("%s", error)
        return 2
    except KeyboardInterrupt:
        log.warning("Operation interrupted.")
        return 130
    except Exception:
        log.error("Unexpected failure; raw exception suppressed to protect sensitive data. Reproduce with synthetic input for debugging.")
        return 2

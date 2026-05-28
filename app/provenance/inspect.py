import argparse
import json
import sys


def parse_args():
    parser = argparse.ArgumentParser(description="Inspect a provenance JSON file.")
    parser.add_argument("path")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    with open(args.path, "r", encoding="utf-8") as f:
        payload = json.load(f)
    if isinstance(payload, dict) and "events" in payload:
        print(json.dumps({"event_count": len(payload.get("events", [])), "path": args.path}, indent=2))
    else:
        keys = sorted(payload.keys()) if isinstance(payload, dict) else []
        summary = {k: payload.get(k) for k in ("timestamp", "backend_name", "runtime_sec", "image_filename", "output_mask_path") if isinstance(payload, dict)}
        summary["keys"] = keys
        print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

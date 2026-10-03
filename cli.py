"""Native ``hermes orbit`` command tree for the ORBIT plugin."""
from __future__ import annotations

import json
from pathlib import Path

from . import tools


def _value(raw: str):
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return raw


def _inputs(args) -> dict:
    values = {}
    if getattr(args, "inputs_json", None):
        values = json.loads(args.inputs_json)
        if not isinstance(values, dict):
            raise ValueError("--inputs-json must be a JSON object")
    for item in getattr(args, "input", []) or []:
        if "=" not in item:
            raise ValueError(f"invalid --input {item!r}; expected NAME=VALUE")
        name, raw = item.split("=", 1)
        if not name:
            raise ValueError("--input name cannot be empty")
        values[name] = _value(raw)
    return values


def _emit(value) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2))


def orbit_command(args):
    try:
        command = getattr(args, "orbit_command", None)
        if command == "status":
            result = tools.get_status_data()
        elif command == "workflows":
            result = tools.api_request("/api/workflows")
        elif command == "run":
            result = tools.api_request("/api/jobs", "POST", {"workflow_id": args.workflow_id, "inputs": _inputs(args)})
            if args.wait:
                result = tools.wait_for_job(result["id"], args.timeout, args.poll)
        elif command == "jobs":
            result = tools.api_request("/api/jobs")
            result["jobs"] = result.get("jobs", [])[:args.limit]
        elif command == "job":
            result = tools.wait_for_job(args.job_id, args.timeout, args.poll) if args.wait else tools.api_request("/api/jobs/" + args.job_id)
        elif command == "cancel":
            result = tools.api_request("/api/jobs/" + args.job_id + "/cancel", "POST", {})
        elif command == "rerun":
            result = tools.api_request("/api/jobs/" + args.job_id + "/rerun", "POST", {})
        elif command == "results":
            result = tools.api_request("/api/jobs/" + args.job_id + "/results")
        elif command == "download":
            target = Path(args.output).expanduser().resolve()
            target.parent.mkdir(parents=True, exist_ok=True)
            content = tools.api_request("/api/results/" + args.result_id + "/download", binary=True)
            target.write_bytes(content)
            result = {"saved_to": str(target), "size_bytes": len(content)}
        elif command == "free-memory":
            result = tools.api_request("/api/hermes/comfy/free", "POST", {})
        else:
            args._orbit_parser.print_help()
            return
        _emit(result)
    except Exception as error:
        _emit({"error": str(error)})
        raise SystemExit(1) from None


def register_cli(parser):
    parser.set_defaults(func=orbit_command, _orbit_parser=parser)
    commands = parser.add_subparsers(dest="orbit_command")
    commands.add_parser("status", help="Check ORBIT and ComfyUI status")
    commands.add_parser("workflows", help="List approved workflows and their inputs")

    run = commands.add_parser("run", help="Run an approved workflow")
    run.add_argument("workflow_id")
    run.add_argument("--input", action="append", default=[], metavar="NAME=VALUE", help="Set one input; JSON values are accepted")
    run.add_argument("--inputs-json", help="Set inputs with one JSON object")
    run.add_argument("--wait", action="store_true", help="Wait for completion")
    run.add_argument("--timeout", type=int, default=300)
    run.add_argument("--poll", type=float, default=2)

    jobs = commands.add_parser("jobs", help="List recent jobs")
    jobs.add_argument("--limit", type=int, default=20, choices=range(1, 101), metavar="1-100")

    job = commands.add_parser("job", help="Show one job")
    job.add_argument("job_id")
    job.add_argument("--wait", action="store_true")
    job.add_argument("--timeout", type=int, default=300)
    job.add_argument("--poll", type=float, default=2)

    for name, help_text in (("cancel", "Cancel a pending or queued job"), ("rerun", "Rerun a saved job"), ("results", "List a job's results")):
        child = commands.add_parser(name, help=help_text)
        child.add_argument("job_id")

    download = commands.add_parser("download", help="Download one result")
    download.add_argument("result_id")
    download.add_argument("output")
    commands.add_parser("free-memory", help="Admin: unload idle ComfyUI models")


def slash_command(raw_args: str) -> str:
    command = raw_args.strip().lower()
    try:
        if command in {"", "help"}:
            return "사용법: /orbit status | workflows | jobs"
        if command == "status":
            return json.dumps(tools.get_status_data(), ensure_ascii=False)
        if command == "workflows":
            return json.dumps(tools.api_request("/api/workflows"), ensure_ascii=False)
        if command == "jobs":
            result = tools.api_request("/api/jobs")
            result["jobs"] = result.get("jobs", [])[:10]
            return json.dumps(result, ensure_ascii=False)
        return "알 수 없는 명령입니다. 사용법: /orbit status | workflows | jobs"
    except Exception as error:
        return json.dumps({"error": str(error)}, ensure_ascii=False)

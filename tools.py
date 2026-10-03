import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path

import keyring


def _base_url():
    return os.environ["ORBIT_DASHBOARD_URL"].rstrip("/")


def _credential():
    service = "orbit-dashboard:" + _base_url()
    installation_id = keyring.get_password(service, "installation-id")
    if not installation_id:
        raise RuntimeError("This Hermes installation is not paired. Use '이 PC Hermes 등록' in ORBIT.")
    token = keyring.get_password(service, installation_id)
    if not token:
        raise RuntimeError("ORBIT credential is missing. Pair this Hermes installation again.")
    return token


def _request(path, method="GET", payload=None, binary=False):
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = urllib.request.Request(
        _base_url() + path,
        data=data,
        method=method,
        headers={"Authorization": "Bearer " + _credential(), **({"Content-Type": "application/json"} if data else {})},
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            return response.read() if binary else json.loads(response.read() or b"{}")
    except urllib.error.HTTPError as error:
        try:
            detail = json.loads(error.read()).get("error", "request failed")
        except Exception:
            detail = "request failed"
        raise RuntimeError(f"ORBIT returned {error.code}: {detail}") from None
    except urllib.error.URLError:
        raise RuntimeError("ORBIT is unavailable. Check VPN and dashboard status.") from None


def _json_result(operation):
    try:
        return json.dumps(operation(), ensure_ascii=False)
    except Exception as error:
        return json.dumps({"error": str(error)}, ensure_ascii=False)


def api_request(path, method="GET", payload=None, binary=False):
    """Public client surface shared by Hermes tools and the native CLI."""
    return _request(path, method, payload, binary)


def get_status_data():
    capabilities = api_request("/api/hermes/capabilities")
    health = api_request("/api/health")
    return {"connection": "ok", **capabilities, "health": health}


def wait_for_job(job_id, timeout_seconds=300, poll_seconds=2):
    timeout_seconds = max(1, min(int(timeout_seconds), 3600))
    poll_seconds = max(0.5, min(float(poll_seconds), 10.0))
    deadline = time.monotonic() + timeout_seconds
    terminal = {"completed", "failed", "cancelled"}
    latest = None
    while time.monotonic() < deadline:
        latest = api_request("/api/jobs/" + str(job_id))
        job = latest.get("job", {}) if isinstance(latest, dict) else {}
        if job.get("state") in terminal:
            if job.get("state") == "completed":
                latest["results"] = api_request("/api/jobs/" + str(job_id) + "/results").get("results", [])
            return latest
        time.sleep(poll_seconds)
    return {"job": (latest or {}).get("job"), "timed_out": True, "timeout_seconds": timeout_seconds}


def list_workflows(args, **kwargs):
    return _json_result(lambda: _request("/api/workflows"))


def create_job(args, **kwargs):
    return _json_result(lambda: _request("/api/jobs", "POST", {"workflow_id": args.get("workflow_id"), "inputs": args.get("inputs", {})}))


def list_jobs(args, **kwargs):
    def operation():
        result = api_request("/api/jobs")
        limit = max(1, min(int(args.get("limit", 20)), 100))
        result["jobs"] = result.get("jobs", [])[:limit]
        return result
    return _json_result(operation)


def get_job(args, **kwargs):
    return _json_result(lambda: _request("/api/jobs/" + str(args.get("job_id", ""))))


def cancel_job(args, **kwargs):
    return _json_result(lambda: _request("/api/jobs/" + str(args.get("job_id", "")) + "/cancel", "POST", {}))


def rerun_job(args, **kwargs):
    return _json_result(lambda: _request("/api/jobs/" + str(args.get("job_id", "")) + "/rerun", "POST", {}))


def list_results(args, **kwargs):
    return _json_result(lambda: _request("/api/jobs/" + str(args.get("job_id", "")) + "/results"))


def download_result(args, **kwargs):
    def operation():
        result_id = str(args.get("result_id", ""))
        target = Path(str(args.get("output_path", ""))).expanduser().resolve()
        if not target.name:
            raise RuntimeError("output_path must name a file")
        target.parent.mkdir(parents=True, exist_ok=True)
        content = _request("/api/results/" + result_id + "/download", binary=True)
        target.write_bytes(content)
        return {"saved_to": str(target), "size_bytes": len(content)}
    return _json_result(operation)


def get_status(args, **kwargs):
    return _json_result(get_status_data)


def wait_job(args, **kwargs):
    return _json_result(lambda: wait_for_job(
        str(args.get("job_id", "")),
        args.get("timeout_seconds", 300),
        args.get("poll_seconds", 2),
    ))


def free_comfy_memory(args, **kwargs):
    return _json_result(lambda: api_request("/api/hermes/comfy/free", "POST", {}))

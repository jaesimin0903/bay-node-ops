"""Measure the assignment's intentional replicas=0 drift and recovery."""
import datetime
import json
from pathlib import Path
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]
BASE = ["kubectl", "--context", "kind-bay"]


def kubectl(*args):
    return subprocess.check_output(BASE + list(args), text=True, timeout=10)


if __name__ == "__main__":
    before = json.loads(kubectl("get", "pod", "geth-dev-0", "-o", "json"))
    started = time.monotonic()
    record = {"startedAt": datetime.datetime.now(datetime.timezone.utc).isoformat(),
              "beforePodUID": before["metadata"]["uid"], "samples": []}
    record["scaleResponse"] = json.loads(kubectl(
        "scale", "statefulset", "geth-dev", "--replicas=0", "-o", "json"))
    while time.monotonic() - started < 180:
        state = json.loads(kubectl("get", "statefulset", "geth-dev", "-o", "json"))
        sample = {"elapsed": round(time.monotonic() - started, 3),
                  "time": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                  "desired": state["spec"]["replicas"],
                  "ready": state.get("status", {}).get("readyReplicas", 0)}
        pods = json.loads(kubectl("get", "pod", "-l", "app=geth-dev", "-o", "json"))
        sample["pods"] = [{"uid": p["metadata"]["uid"],
                           "deleting": p["metadata"].get("deletionTimestamp"),
                           "ready": any(c["type"] == "Ready" and c["status"] == "True"
                                        for c in p["status"].get("conditions", []))}
                          for p in pods["items"]]
        record["samples"].append(sample)
        if sample["desired"] == 1:
            record.setdefault("desiredRestoredSeconds", sample["elapsed"])
        if (sample["desired"] == 1 and sample["ready"] == 1 and sample["pods"]
                and all(p["ready"] and not p["deleting"] for p in sample["pods"])):
            record["readyRestoredSeconds"] = sample["elapsed"]
            record["afterPodUID"] = sample["pods"][0]["uid"]
            break
        time.sleep(0.2)
    (ROOT / "evidence/self-heal.json").write_text(json.dumps(record, indent=2))
    (ROOT / "evidence/self-heal-events.json").write_text(kubectl(
        "-n", "argocd", "get", "events", "--field-selector",
        "involvedObject.name=geth-dev", "-o", "json"))
    print(json.dumps({k: v for k, v in record.items()
                      if k not in ("samples", "scaleResponse")}, indent=2))
    if "readyRestoredSeconds" not in record:
        raise SystemExit("Recovery was not observed within 180 seconds")

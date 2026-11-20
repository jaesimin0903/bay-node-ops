"""Save actual cluster/Prometheus observations every five seconds."""
import datetime
import json
import subprocess
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def get_json(url):
    with urllib.request.urlopen(url, timeout=4) as response:
        return json.load(response)


def resource(kind, name, namespace="default"):
    output = subprocess.check_output(
        ["kubectl", "--context", "kind-bay", "-n", namespace,
         "get", kind, name, "-o", "json"], stderr=subprocess.DEVNULL, timeout=6)
    return json.loads(output)


if __name__ == "__main__":
    output = ROOT / "evidence" / "observations.jsonl"
    while True:
        row = {"time": datetime.datetime.now(datetime.timezone.utc).isoformat()}
        for name, query in {
            "head": 'chain_head_block{job="geth-dev"}',
            "up": 'up{job="geth-dev"}',
            "alerts": 'ALERTS{alertname=~"Geth.*"}',
        }.items():
            try:
                row[name] = get_json("http://127.0.0.1:9090/api/v1/query?" +
                                     urllib.parse.urlencode({"query": query}))["data"]["result"]
            except Exception as error:
                row[name] = {"error": str(error)}
        try:
            pod = resource("pod", "geth-dev-0")
            row["pod"] = {"uid": pod["metadata"]["uid"],
                          "image": pod["spec"]["containers"][0]["image"],
                          "args": pod["spec"]["containers"][0]["args"],
                          "status": pod["status"]}
        except Exception as error:
            row["pod"] = {"error": str(error)}
        try:
            app = resource("application", "geth-dev", "argocd")
            row["application"] = app.get("status", {})
        except Exception as error:
            row["application"] = {"error": str(error)}
        with output.open("a") as stream:
            stream.write(json.dumps(row, ensure_ascii=False) + "\n")
        print(row["time"], flush=True)
        time.sleep(5)

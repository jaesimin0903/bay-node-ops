"""Check saved observations without changing the cluster."""
import json
from pathlib import Path

EVIDENCE = Path(__file__).resolve().parents[1] / "evidence"


def read(name):
    return json.loads((EVIDENCE / name).read_text())


def rpc(name):
    return json.loads(read(name))


before = rpc("before-upgrade.txt")
after = rpc("after-upgrade.txt")
recovered = rpc("after-recovery.txt")
pod = read("pod-final.json")
app = read("application-final.json")
heal = read("self-heal.json")
rules = [r for g in read("rules-recovered.json")["data"]["groups"]
         for r in g["rules"] if r["name"].startswith("Geth")]
fired = {r["metric"]["alertname"] for r in read("raw-alerts-firing.json")["data"]["result"]
         if r["metric"]["alertstate"] == "firing"}
checks = {
    "version upgraded": "v1.17.4" in before["version"] and "v1.17.5" in after["version"],
    "account retained": before["account"] == after["account"] == recovered["account"],
    "block hash retained": before["block1"] == after["block1"] == recovered["block1"],
    "height continued": after["head"] > before["head"] and recovered["head"] > 13,
    "PVC retained": read("pvc-before.json")["metadata"]["uid"] == read("pvc-final.json")["metadata"]["uid"],
    "warning fired": "GethBlockStalled" in fired,
    "critical fired": "GethBlockStalledLong" in fired,
    "alerts resolved": len(rules) == 3 and all(r["state"] == "inactive" and r["health"] == "ok" for r in rules),
    "three PRs merged": all(read(p)["mergedAt"] for p in ["upgrade-geth-1.17.5.json", "incident-stall-blocks.json", "recovery-pr.json"]),
    "period restored": "--dev.period=12" in pod["spec"]["containers"][0]["args"],
    "application synced": app["status"]["sync"]["status"] == "Synced" and app["status"]["health"]["status"] == "Healthy",
    "scale zero accepted": heal["scaleResponse"]["spec"]["replicas"] == 0,
    "selfHeal restored": heal["desiredRestoredSeconds"] > 0 and heal["readyRestoredSeconds"] > 0,
    "pod recreated": heal["beforePodUID"] != heal["afterPodUID"],
}
for name, passed in checks.items():
    print(f"{'PASS' if passed else 'FAIL'} {name}")
if not all(checks.values()):
    raise SystemExit(1)
print(f"{len(checks)} checks passed")

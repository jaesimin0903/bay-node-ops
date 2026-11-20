# BAY 노드 운영 과제 3

Geth를 ArgoCD로 배포하고 Prometheus·Grafana로 상태를 확인한다.

- `k8s/`: Geth, 메트릭 수집, 알람 규칙
- `argocd/geth-app.yaml`: GitHub main → default 네임스페이스 자동 동기화
- `monitoring/`: Helm 설정과 Grafana 대시보드
- `assignment-3.md`: 실습 기록과 리서치 글
- `evidence/`: 실제 관측 원본과 캡처. 공개 저장소에서는 제외

## 다시 설치

```bash
kind create cluster --name bay
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
helm install monitoring prometheus-community/kube-prometheus-stack --version 93.5.0 -n monitoring --create-namespace -f monitoring/values.yaml --wait --timeout 10m
kubectl create namespace argocd
kubectl apply -n argocd --server-side --force-conflicts -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
kubectl apply -f monitoring/dashboard-provision.yaml
kubectl apply -f argocd/geth-app.yaml
```

Geth YAML을 직접 apply하지 않고 Git에 반영한다. 복구도 PR로 진행한다.

```bash
kubectl --context kind-bay -n argocd port-forward svc/argocd-server 8080:443
kubectl --context kind-bay -n monitoring port-forward svc/monitoring-kube-prometheus-prometheus 9090:9090
kubectl --context kind-bay -n monitoring port-forward svc/monitoring-grafana 3300:80
```

각 명령은 별도 터미널에서 실행한다. Grafana: http://127.0.0.1:3300/d/bay-geth/bay-geth
초기 비밀번호는 Kubernetes Secret에서 확인한다. 캡처와 저장소에는 남기지 않는다.

이 구성은 로컬 개발 체인용이다. 게임데이에 쓸 클러스터와 PVC는 유지한다.

# BAY 노드 운영 과제 3

geth를 argocd로 배포하고 프로메테우스·그라파나로 상태를 확인한다.

- `k8s/`: geth, 메트릭 수집, 알람 규칙
- `argocd/geth-app.yaml`: 깃허브 main → default 네임스페이스 자동 동기화
- `monitoring/`: helm 설정과 그라파나 대시보드
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

geth 설정 파일을 직접 적용하지 않고 깃에 반영한다. 복구도 pr로 진행한다.

```bash
kubectl --context kind-bay -n argocd port-forward svc/argocd-server 8080:443
kubectl --context kind-bay -n monitoring port-forward svc/monitoring-kube-prometheus-prometheus 9090:9090
kubectl --context kind-bay -n monitoring port-forward svc/monitoring-grafana 3300:80
```

각 명령은 별도 터미널에서 실행한다. 그라파나: http://127.0.0.1:3300/d/bay-geth/bay-geth
초기 비밀번호는 쿠버네티스 시크릿에서 확인한다. 캡처와 저장소에는 남기지 않는다.

이 구성은 로컬 개발 체인용이다. 게임데이에 쓸 클러스터와 볼륨은 유지한다.

실습 결과: https://app.notion.com/p/41e4790074c881048c97d71dc165dc02

저장된 원본 검증: `python3 scripts/verify_evidence.py` (로컬 evidence 폴더 필요)

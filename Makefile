APP     = scalable-app
CLUSTER = scalable-app-cluster

# ── Build ──────────────────────────────────────────────
build:
	docker build -t $(APP):latest .

# ── Cluster lifecycle ──────────────────────────────────
cluster-up:
	kind create cluster --config k8s/local/kind-config.yaml

cluster-down:
	kind delete cluster --name $(CLUSTER)

# ── Deploy ─────────────────────────────────────────────
load:
	kind load docker-image $(APP):latest --name $(CLUSTER)


metrics:
	kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
	kubectl patch deployment metrics-server -n kube-system --type='json' \
	  -p='[{"op":"add","path":"/spec/template/spec/containers/0/args/-","value":"--kubelet-insecure-tls"}]'
	kubectl rollout status deployment/metrics-server -n kube-system


deploy:
	kubectl apply -f k8s/base/

# ── Full bootstrap (run once) ──────────────────────────
up: build cluster-up load metrics deploy
	@echo "✅ scalable-app is live on Kind"

# ── Dev loop (after first up) ─────────────────────────
reload: build load
	kubectl rollout restart deployment/$(APP)

# ── Observe ────────────────────────────────────────────
status:
	kubectl get pods,svc,hpa

watch-hpa:
	kubectl get hpa scalable-app-hpa --watch

tunnel:
	kubectl port-forward svc/scalable-app-svc 8080:80

# ── Load test ─────────────────────────────────────────
load-test:
	kubectl run load-gen --image=busybox --restart=Never -- \
	  /bin/sh -c "while true; do wget -q -O- http://scalable-app-svc/; done"

clean-load:
	kubectl delete pod load-gen --ignore-not-found

tunnel:
	kubectl port-forward svc/scalable-app-svc 8080:80
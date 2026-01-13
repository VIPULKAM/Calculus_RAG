# Deployment Guide

This guide covers deploying Calculus RAG on a production server using Docker Compose or Kubernetes.

## Option 1: Docker Compose (Simpler)

Best for: Single server deployments, smaller scale (< 100 concurrent users)

### Prerequisites
- Docker 24+ and Docker Compose v2
- 8GB+ RAM (16GB+ recommended for 7B model)
- 50GB+ disk space

### Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/VIPULKAM/Calculus_RAG.git
cd Calculus_RAG

# 2. Create production environment file
cp .env.prod.example .env
# Edit .env and set a strong POSTGRES_PASSWORD

# 3. Build and start services
docker-compose -f docker-compose.prod.yml up -d

# 4. Wait for services to be healthy (2-3 minutes)
docker-compose -f docker-compose.prod.yml ps

# 5. Restore knowledge base
docker-compose -f docker-compose.prod.yml exec app \
  python scripts/restore_db.py backups/starter.dump

# 6. Access the app
# http://your-server-ip:8501
```

### With Nginx Reverse Proxy (SSL)

```bash
# 1. Add SSL certificates to nginx/ssl/
mkdir -p nginx/ssl
cp /path/to/fullchain.pem nginx/ssl/
cp /path/to/privkey.pem nginx/ssl/

# 2. Edit nginx/nginx.conf - uncomment HTTPS section

# 3. Start with nginx profile
docker-compose -f docker-compose.prod.yml --profile with-nginx up -d
```

### GPU Support (NVIDIA)

1. Install [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html)
2. Uncomment GPU section in `docker-compose.prod.yml` under `ollama` service
3. Restart: `docker-compose -f docker-compose.prod.yml up -d ollama`

### Management Commands

```bash
# View logs
docker-compose -f docker-compose.prod.yml logs -f app

# Restart app after config changes
docker-compose -f docker-compose.prod.yml restart app

# Stop all services
docker-compose -f docker-compose.prod.yml down

# Stop and remove volumes (WARNING: deletes data)
docker-compose -f docker-compose.prod.yml down -v

# Pull model manually
docker-compose -f docker-compose.prod.yml exec ollama \
  ollama pull qwen2-math:7b
```

---

## Option 2: Kubernetes (Scalable)

Best for: Multi-node clusters, high availability, university-wide deployment

### Prerequisites
- Kubernetes cluster (1.25+)
- kubectl configured
- NGINX Ingress Controller installed
- (Optional) cert-manager for automatic TLS

### Quick Start

```bash
# 1. Build and push Docker image to your registry
docker build -t your-registry/calculus-rag:latest .
docker push your-registry/calculus-rag:latest

# 2. Update image reference in k8s/app.yaml
# Change: image: calculus-rag:latest
# To: image: your-registry/calculus-rag:latest

# 3. Update secrets (IMPORTANT!)
# Edit k8s/secrets.yaml - change POSTGRES_PASSWORD

# 4. Update ingress hostname
# Edit k8s/ingress.yaml - change calculus-tutor.university.edu

# 5. Deploy with kustomize
kubectl apply -k k8s/

# 6. Wait for pods to be ready
kubectl -n calculus-rag get pods -w

# 7. Pull models (after ollama pod is ready)
kubectl -n calculus-rag wait --for=condition=ready pod -l app=ollama --timeout=300s
kubectl -n calculus-rag create job --from=job/ollama-model-pull ollama-pull-$(date +%s)

# 8. Restore knowledge base
kubectl -n calculus-rag exec -it deploy/calculus-rag-app -- \
  python scripts/restore_db.py backups/starter.dump
```

### Install NGINX Ingress Controller

```bash
# Using Helm
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo update
helm install ingress-nginx ingress-nginx/ingress-nginx \
  --namespace ingress-nginx --create-namespace
```

### Enable TLS with cert-manager

```bash
# 1. Install cert-manager
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.14.0/cert-manager.yaml

# 2. Create ClusterIssuer for Let's Encrypt
cat <<EOF | kubectl apply -f -
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: your-email@university.edu
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
      - http01:
          ingress:
            class: nginx
EOF

# 3. Uncomment TLS section in k8s/ingress.yaml
# 4. Re-apply: kubectl apply -k k8s/
```

### GPU Support in Kubernetes

1. Install [NVIDIA GPU Operator](https://docs.nvidia.com/datacenter/cloud-native/gpu-operator/getting-started.html)
2. Uncomment GPU sections in `k8s/ollama.yaml`
3. Re-apply: `kubectl apply -f k8s/ollama.yaml`

### Scaling

```bash
# Scale app replicas (stateless, can scale horizontally)
kubectl -n calculus-rag scale deployment calculus-rag-app --replicas=5

# Note: ollama and postgres should remain at 1 replica
```

### Monitoring

```bash
# Pod status
kubectl -n calculus-rag get pods

# App logs
kubectl -n calculus-rag logs -f deploy/calculus-rag-app

# Ollama logs
kubectl -n calculus-rag logs -f deploy/ollama

# Resource usage
kubectl -n calculus-rag top pods
```

### Troubleshooting

```bash
# Check pod events
kubectl -n calculus-rag describe pod <pod-name>

# Check ingress
kubectl -n calculus-rag describe ingress calculus-rag-ingress

# Test internal connectivity
kubectl -n calculus-rag run -it --rm debug --image=busybox -- sh
# Then: wget -qO- http://ollama-service:11434/api/tags
```

---

## Architecture Diagram

```
                                    Internet
                                        |
                                   [Ingress/Nginx]
                                        |
                            +-----------+-----------+
                            |                       |
                       [App Pod 1]             [App Pod 2]
                            |                       |
                            +-----------+-----------+
                                        |
                    +-------------------+-------------------+
                    |                                       |
             [PostgreSQL]                             [Ollama]
             (pgvector)                          (LLM + Embeddings)
                    |                                       |
               [PVC: 10Gi]                            [PVC: 20Gi]
```

---

## Security Checklist

- [ ] Change default PostgreSQL password in secrets
- [ ] Enable TLS/HTTPS
- [ ] Configure firewall (only expose 80/443)
- [ ] Set up authentication (university SSO, basic auth, etc.)
- [ ] Regular backups of PostgreSQL data
- [ ] Monitor resource usage
- [ ] Keep images updated

---

## Backup & Restore in Production

### Docker Compose

```bash
# Backup
docker-compose -f docker-compose.prod.yml exec app \
  python scripts/backup_db.py production_backup

# Copy backup out of container
docker cp calculus_rag_app_prod:/app/backups/production_backup.dump ./

# Restore
docker-compose -f docker-compose.prod.yml exec app \
  python scripts/restore_db.py backups/production_backup.dump
```

### Kubernetes

```bash
# Backup
kubectl -n calculus-rag exec deploy/calculus-rag-app -- \
  python scripts/backup_db.py production_backup

# Copy backup to local
kubectl -n calculus-rag cp \
  calculus-rag-app-xxx:/app/backups/production_backup.dump ./

# Restore
kubectl -n calculus-rag exec deploy/calculus-rag-app -- \
  python scripts/restore_db.py backups/production_backup.dump
```

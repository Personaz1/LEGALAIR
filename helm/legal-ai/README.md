# Legal AI Helm Chart

Helm chart for deploying the Legal AI Platform on Kubernetes.

## Description

This chart bootstraps a Legal AI deployment on a Kubernetes cluster using the Helm package manager. It includes:

- FastAPI backend service
- PostgreSQL database
- Redis cache
- Web frontend (Next.js)
- MinIO object storage
- Monitoring stack (Prometheus/Grafana)

## Prerequisites

- Kubernetes 1.19+
- Helm 3.0+
- PV provisioner support in the underlying infrastructure

## Installation

### Quick Start

```bash
# Add the helm chart repository (if hosted)
helm repo add legal-ai https://charts.legal-ai.com
helm repo update

# Install the chart
helm install legal-ai legal-ai/legal-ai --namespace legal-ai-dev --create-namespace
```

### Local Development

```bash
# Clone the repository
git clone https://github.com/org/legal-ai.git
cd legal-ai

# Install from local chart
helm install legal-ai ./helm/legal-ai --namespace legal-ai-dev --create-namespace
```

### Custom Values

```bash
# Install with custom values
helm install legal-ai ./helm/legal-ai \
  --namespace legal-ai-dev \
  --create-namespace \
  --values values-production.yaml
```

## Configuration

The following table lists the configurable parameters and their default values.

### Global Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `global.namespace` | Kubernetes namespace | `legal-ai-dev` |
| `global.imageRegistry` | Global image registry | `docker.io` |
| `global.storageClass` | Global storage class | `standard` |

### API Service Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `api.enabled` | Enable API service | `true` |
| `api.replicaCount` | Number of API replicas | `2` |
| `api.image.repository` | API image repository | `legal-ai/api` |
| `api.image.tag` | API image tag | `latest` |
| `api.service.port` | API service port | `8000` |
| `api.resources.requests.memory` | API memory request | `512Mi` |
| `api.resources.requests.cpu` | API CPU request | `250m` |

### Database Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `postgres.enabled` | Enable PostgreSQL | `true` |
| `postgres.persistence.enabled` | Enable persistence | `true` |
| `postgres.persistence.size` | Storage size | `10Gi` |

### Redis Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `redis.enabled` | Enable Redis | `true` |
| `redis.resources.requests.memory` | Redis memory request | `128Mi` |

## Usage Examples

### Development Environment

```yaml
# values-dev.yaml
app:
  environment: development
  
api:
  replicaCount: 1
  image:
    pullPolicy: Always
    
development:
  enabled: true
  debugMode: true
```

```bash
helm install legal-ai-dev ./helm/legal-ai -f values-dev.yaml
```

### Production Environment

```yaml
# values-prod.yaml
app:
  environment: production
  
api:
  replicaCount: 3
  resources:
    requests:
      memory: "1Gi"
      cpu: "500m"
    limits:
      memory: "4Gi"
      cpu: "2000m"

autoscaling:
  enabled: true
  minReplicas: 3
  maxReplicas: 10
  
postgres:
  persistence:
    size: 100Gi
    
ingress:
  enabled: true
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
  hosts:
    - host: legal-ai.company.com
      paths:
        - path: /api
          service: legal-ai-api
          port: 8000
        - path: /
          service: legal-ai-web
          port: 3000
```

## Upgrading

```bash
# Upgrade to a new version
helm upgrade legal-ai ./helm/legal-ai --namespace legal-ai-dev

# Upgrade with new values
helm upgrade legal-ai ./helm/legal-ai -f values-updated.yaml
```

## Uninstalling

```bash
# Uninstall the chart
helm uninstall legal-ai --namespace legal-ai-dev
```

## Monitoring

The chart includes optional monitoring components:

```yaml
monitoring:
  enabled: true
  prometheus:
    enabled: true
  grafana:
    enabled: true
```

Access monitoring:
- Prometheus: `http://legal-ai.local:9090`
- Grafana: `http://legal-ai.local:3001`

## Troubleshooting

### Common Issues

1. **Pod stuck in Pending state**
   ```bash
   kubectl describe pod <pod-name> -n legal-ai-dev
   # Check for PVC binding issues or resource constraints
   ```

2. **API service not accessible**
   ```bash
   kubectl port-forward svc/legal-ai-api 8000:8000 -n legal-ai-dev
   curl http://localhost:8000/api/v1/health
   ```

3. **Database connection issues**
   ```bash
   kubectl logs deployment/legal-ai-api -n legal-ai-dev
   kubectl exec -it deployment/legal-ai-postgres -n legal-ai-dev -- psql -U legal_ai
   ```

### Validation

Validate the chart before installation:

```bash
# Template validation
helm template legal-ai ./helm/legal-ai --debug

# Lint check
helm lint ./helm/legal-ai

# Dry run
helm install legal-ai ./helm/legal-ai --dry-run --debug
```

## Contributing

1. Update chart version in `Chart.yaml`
2. Update `values.yaml` with new parameters
3. Run validation tests
4. Update this README

## License

This chart is licensed under the MIT License. 
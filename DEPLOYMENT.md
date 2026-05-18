# Deployment Guide

## Overview

This project has two independent release flows:

| Flow | Trigger | System | Produces |
|------|---------|--------|---------|
| **A — PyPI** | GitHub Release | GitHub Actions | Python package on PyPI + updated wheel in ssf-morph |
| **B — Docs/App** | Push to `dev` or git tag | GitLab CI | Docker image on Docker Hub → deployed to K8S via Helm |

---

## Architecture

```
┌──────────────────────────────────────────────────────┐
│  ssf-morph (browser app)          nginx container         │
│    webworker.js loads Pyodide  ──▶ /apps/gwas_sumstats_tools/ │
│    + gwas_sumstats_tools wheel                            │
│                                                           │
│  docs/gwas-sumstats-tools-Documentation                  │
│    docsify static site         ──▶ /apps/gwas_sumstats_tools/docs/      │
└──────────────────────────────────────────────────────┘
         built by Dockerfile.docs
         served by nginx.conf
         deployed via deployment/helm/
```

**Docker Hub images**

| Image | Built from | Purpose |
|-------|-----------|---------|
| `ebispot/gwas-sumstats-tools` | `Dockerfile` | Python CLI app |
| `ebispot/gwas-sumstats-tools-docs` | `Dockerfile.docs` | nginx serving ssf-morph + docs — **this is what K8S runs** |

**Kubernetes — EBI HH cluster (`gwas-depo-hh-config.yml`)**

| Namespace | Environment |
|-----------|-------------|
| `gwas-dev` | Development (auto-deployed on every `dev` push) |
| `gwas` | Production (auto-deployed on every tag) |

**EBI HX cluster (`gwas-depo-hx-config.yml`)** — fallback only, manually triggered.

---

## File inventory

| File | Purpose |
|------|---------|
| `Dockerfile.docs` | Multi-stage build: Poetry builder → nginx server |
| `nginx.conf` | Routes `/apps/gwas_sumstats_tools/` and `/apps/gwas_sumstats_tools/docs/` |
| `ssf-morph/webworker.js` | Loads Pyodide + the versioned wheel file |
| `ssf-morph/wheels/` | Wheel files loaded by the browser app |
| `deployment/helm/Chart.yaml` | Helm chart metadata |
| `deployment/helm/values.yaml` | Default values (image, namespace, resources) |
| `deployment/helm/templates/` | K8S Deployment, Service, Ingress templates |
| `.gitlab-ci.yml` | GitLab CI: test → build → deploy |
| `.github/workflows/publish-pypi.yml` | GitHub Actions: PyPI release + wheel update |
| `.github/workflows/publish-docs.yml` | GitHub Actions: build-only test on PRs |

---

## One-time setup

### 1. Docker Hub — create two public repositories

- `ebispot/gwas-sumstats-tools`
- `ebispot/gwas-sumstats-tools-docs`

### 2. GitLab — CI/CD variables (Settings → CI/CD → Variables)

### 3. GitHub — PyPI trusted publishing

On [pypi.org](https://pypi.org) → your project → Publishing → Add trusted publisher:

- Publisher: **GitHub Actions**
- Owner: `EBISPOT`
- Repository: `gwas-sumstats-tools`
- Workflow filename: `publish-pypi.yml`
- Environment: `publish`

On GitHub → Settings → Environments → create an environment named `publish`.

---

## Flow A — Python library release (GitHub)

**Trigger:** creating a GitHub Release.

### Steps

1. Bump version and push to master:
   ```bash
   poetry version 1.0.25        # update pyproject.toml
   git add pyproject.toml
   git commit -m "chore: bump version to 1.0.25"
   git push origin master
   ```

2. On GitHub → Releases → Draft a new release:
   - Tag: `v1.0.25` (create on `master`)
   - Click **Publish release**

**What `publish-pypi.yml` does automatically:**
```
test (pytest)
  → build wheel: gwas_sumstats_tools-1.0.25-py3-none-any.whl
  → remove old gwas_sumstats_tools-*.whl from ssf-morph/wheels/
  → copy new wheel to ssf-morph/wheels/
  → update webworker.js to reference new wheel filename
  → commit & push changes to master
  → publish to PyPI
```

The commit pushed to `master` then automatically triggers Flow B in GitLab.

---

## Flow B — Docs/app deployment (GitLab)

### On push to `dev`

```
test (pytest)
  ↓
build      → ebispot/gwas-sumstats-tools:<sha>       (CLI image)
build-docs → ebispot/gwas-sumstats-tools-docs:<sha>  (nginx image)
  ↓
deploy-dev → HH cluster, namespace: gwas-dev
             helm install gwas-sumstats-tools-dev
             --set image.tag=<sha>
```

Note: `BUILDKIT_OCI_MEDIA_TYPES=0` and `--provenance=false` are set on the
`build-docs` job to ensure compatibility with EBI's older K8S nodes.

### On push to `master`

Same as `dev` but **no deploy job** — master builds images with the commit SHA
tag only. Deploy to production only happens on a tagged release.

### On a git tag (production release)

```bash
git tag v1.0.25
git push origin v1.0.25    # or push to GitLab remote
```

```
test (pytest)
  ↓
build_release      → ebispot/gwas-sumstats-tools:latest + :v1.0.25
build_release-docs → ebispot/gwas-sumstats-tools-docs:latest + :v1.0.25
  ↓
deploy          (auto)   → PLIVE_KUBECONFIG  → HH cluster, namespace: gwas
deploy-fallback (manual) → PFALLBACK_KUBECONFIG → HX cluster, namespace: gwas
```

`deploy-fallback` only runs when manually clicked in the GitLab pipeline UI.

---

## URL structure after deployment

| URL | Content |
|-----|---------|
| `/apps/gwas_sumstats_tools/` | ssf-morph browser app |
| `/apps/gwas_sumstats_tools/docs/` | docsify documentation |

The K8S Ingress rewrites `/apps/gwas_sumstats_tools/...` → `/apps/gwas_sumstats_tools/...`
before handing off to nginx inside the pod.

---

## Local development

### Test the Docker image locally

```bash
# Build
docker build -f Dockerfile.docs -t gwas-docs:dev .

# Run
docker run --rm -p 8000:80 gwas-docs:dev

# Verify
curl http://localhost:8000/apps/gwas_sumstats_tools/
curl http://localhost:8000/apps/gwas_sumstats_tools/docs/
```

### Dry-run the Helm chart

```bash
# Against your local kubeconfig
helm install gwas-sumstats-tools deployment/helm/ \
  --set image.tag=latest \
  --dry-run --debug
```

---

## Verify after deploy

```bash
# Check rollout
kubectl --namespace gwas rollout status deployment/gwas-sumstats-tools

# Confirm running image tag
kubectl --namespace gwas get pods -l app=gwas-sumstats-tools \
  -o jsonpath='{.items[0].spec.containers[0].image}'

# Check ingress
kubectl --namespace gwas get ingress sumstats-tools-ingress
```

---

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| Image fails to pull on K8S node | OCI media type incompatibility | Ensure `BUILDKIT_OCI_MEDIA_TYPES=0` and `--provenance=false` are set in `build-docs` job |
| `helm init` fails | Wrong helm version in image | Use `dtzar/helm-kubectl:2.13.1` (Helm 2 — required by EBI cluster) |
| `deploy-dev` fails with kubeconfig error | `PLIVE_KUBECONFIG` not set or not base64-encoded | Run `cat gwas-depo-hh-config.yml \| base64 \| tr -d '\n'` and paste into GitLab variable |
| 404 at `/apps/gwas_sumstats_tools/` | nginx misconfiguration or wrong COPY path | `docker exec <container> ls /usr/share/nginx/html/apps/gwas_sumstats_tools/` |
| webworker loads wrong wheel version | `webworker.js` not updated | The `publish-pypi.yml` workflow updates it automatically on each release; check the commit it pushes to master |
| `docker pull` fails on first `build-docs` run | No `latest` tag exists yet | `\|\| true` is already set — safe to ignore on first run |

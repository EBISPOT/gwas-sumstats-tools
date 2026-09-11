# Deployment guide

The browser app and documentation are published together on GitLab Pages.
GitLab hosts the static files; no project nginx server or Kubernetes deployment
is required. Python processing still runs in the browser through Pyodide.

## One-time operator setup

- Enable Pages on the GitLab instance and project. This workflow requires GitLab
  17.10 or later for the Pages syntax and automatic publication of artefacts.
- Development hosting requires GitLab Premium or Ultimate with an available
  parallel Pages deployment slot. Protect the `dev` branch under branch rules;
  the development publication job is excluded when that branch is unprotected.
- Make a runner tagged `gwas` available, with access to Python packages needed
  for the build. The Pages jobs do not require Docker or Kubernetes credentials.
- Enable the group's Dependency Proxy for container images. CI pulls Python,
  Node.js, Docker and Docker-in-Docker images through
  `CI_DEPENDENCY_PROXY_GROUP_IMAGE_PREFIX`. GitLab Runner authenticates these
  pulls automatically using GitLab's predefined credentials.
- Confirm that commits and release tags reach the GitLab project. The GitHub
  remote alone does not run GitLab CI; configure mirroring or push to GitLab.
- Configure Pages access for the intended audience, including anonymous access
  if this is a public site. Protect release tags and restrict who can publish.
- Use the URL shown under **Deploy > Pages**. Group-path and unique-domain URLs
  are supported. No traffic-manager configuration is included.

## Build and publish

| Trigger | Behaviour |
|---------|-----------|
| Default branch push (`main`) | Run tests and build the site, then offer the manual `publish_pages` job |
| Protected `dev` branch push | Run tests and build the site, then automatically run `publish_pages_dev` at the `/dev/` deployment prefix |
| Other branch push (including unprotected `dev`) | Run tests and build the static site as a downloadable `public/` artefact; do not publish |
| Release tag | Run tests and build the site, then offer the manual `publish_pages` job |

To publish the default branch (`main`), open its latest pipeline, or use **Build > Pipelines
> New pipeline** and select that branch. Wait for `test`, `test_worker` and
`build_pages` to succeed, then run **publish_pages**. This publishes the pipeline's
commit, so start a new pipeline if the branch has advanced and you want its latest
state. No release tag is required.

To release a tag, push it to GitLab and run **publish_pages** in that tag's pipeline
after the same checks succeed. Both options replace the production site. The production
environment links to the Pages URL. Publishing jobs are serialised.

`deployment/build_pages.sh` builds a wheel from the checked-out source, copies
SSF-morph to `public/`, copies documentation to `public/docs/`, and adds the wheel
with its full filename (for example,
`public/wheels/gwas_sumstats_tools-2.0.1-py3-none-any.whl`). The generated worker
references that exact filename; the source worker is not changed during builds.
The build checks wheel filenames, archive structure and integrity, and the app's
documentation links. The GitHub pull-request workflow runs this same
build and check. A Node.js regression check verifies that failed worker startup
and retries do not detach uploaded buffers before processing begins.

The publishing job uses `CI_PAGES_URL` to generate a documentation-only rewrite
in `public/_redirects`. This preserves Docsify history routes such as
`docs/UI_format` when opened directly or refreshed. Static files are served
normally; there is no site-wide fallback masking missing scripts or wheels.

The development job publishes a separate Pages deployment with `path_prefix: dev`
and environment name `dev`. For example, production at
`https://group.gitdocs.example/project/` has development at
`https://group.gitdocs.example/project/dev/`. The environment link uses
`CI_PAGES_URL`, which already includes the prefix; do not append `/dev` again.
Documentation rewrites use this same URL, so development deep links also work.
Both deployments have no automatic expiry and use separate publication locks.
Publishing development does not replace production.

Merge the Pages workflow and application changes from `main` into `dev` before
running a development pipeline: GitLab reads CI configuration from that branch.
After its tests and build pass, the development job runs automatically. Open
**Operate > Environments > dev** to follow the site link. Branch protection
controls deployment eligibility, not site visibility; the development site
shares the project's Pages access settings. If environment-level deployment
restrictions are needed, configure the `dev` environment separately in GitLab.

## Local check

From the repository root, with Python 3.13+ and uv installed:

```sh
sh deployment/build_pages.sh
python -m http.server 8000 --directory public
```

Open `http://localhost:8000/`. The build replaces the generated `public/`
directory. Python's simple server does not implement Pages rewrites, so verify
refreshing documentation deep links on GitLab Pages.

After publication, check app startup, wheel loading, formatting, validation and
downloading a result. Check documentation navigation, a direct documentation
link, and the installation-page image. Confirm missing JavaScript returns 404.
A live Pages deployment is required to verify GitLab's routing and access policy.

To roll back, rerun the build and manual publication for a known-good tag that
contains this workflow. Rebuild first if its artefact has expired. Do not run an
old Kubernetes pipeline as a Pages rollback.

## Other release flows and migration

CLI Docker builds in GitLab and PyPI publishing through GitHub Actions are
independent of Pages. The CLI `build` job publishes a commit-SHA image on pushes
to the default branch or `dev`. On release tags, `build_release` publishes
commit-SHA, release-tag and `latest` images to the GitLab project's container
registry (`CI_REGISTRY_IMAGE`). These jobs still require Docker-in-Docker;
the Pages jobs build and publish static files without it.

CLI builds also pull their Python base image through the Dependency Proxy,
passing `PYTHON_IMAGE` to the Dockerfile and authenticating Docker with the
predefined `CI_DEPENDENCY_PROXY_*` credentials. Local Docker builds default to
Docker Hub. The uv image still comes from GHCR; Python packages still come from
their configured package index. The container Dependency Proxy caches Docker Hub
images, not those other dependencies. Published CLI images continue to use the
project's container registry.

The nginx image configuration, Helm chart and their GitLab deployment jobs have
been removed. Existing Kubernetes workloads are not automatically removed;
an operator must retire them and unused Kubernetes credentials after accepting
the Pages deployment.

## References

- [GitLab Pages CI syntax](https://docs.gitlab.com/ci/yaml/#pagespublish)
- [Pages redirects](https://docs.gitlab.com/user/project/pages/redirects/)
- [Parallel Pages deployments](https://docs.gitlab.com/user/project/pages/parallel_deployments/)
- [Container Dependency Proxy](https://docs.gitlab.com/user/packages/dependency_proxy/)

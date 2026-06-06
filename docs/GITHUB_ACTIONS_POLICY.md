# GitHub Actions Security & Pinning Policy

> **Effective Date:** Immediate  
> **Owner:** Security Team  
> **Applies to:** All `.github/workflows/*.yml` files in this repository

---

## 1. Policy Scope

This policy governs **all** GitHub Actions workflow files located under the [`.github/workflows/`](.github/workflows/) directory. Every `uses:` directive in these files **must** comply with the rules below. Exceptions are granted only for actions sourced from `docker://` or local `./.github/actions/` paths, as these are either container-based or version-controlled within this repository.

---

## 2. Mandatory Rules

### 2.1 Action Pinning

All `uses:` directives **MUST** reference a **full 40-character commit SHA** instead of a mutable version tag.

| ❌ Not Allowed | ✅ Allowed |
|---|---|
| `uses: actions/checkout@v4` | `uses: actions/checkout@a12a3e4f1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6` |
| `uses: docker/build-push-action@v5` | `uses: docker/build-push-action@f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9` |
| `uses: azure/login@v2` | `uses: azure/login@a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9` |

### 2.2 Prohibited References

The following mutable references are **strictly prohibited** in `uses:` directives:

- Version tags: `@v1`, `@v2`, `@v3`, `@v4`, `@v5`, etc.
- Branch references: `@master`, `@main`, `@develop`, `@latest`, etc.
- Any tag that can be overwritten by a maintainer.

### 2.3 Special Rules for aquasecurity/trivy-action

The [`aquasecurity/trivy-action`](https://github.com/aquasecurity/trivy-action) MUST **never** use `@master`. It MUST be pinned to a specific semantic version tag (e.g., `@0.29.0`) or, preferably, a full commit SHA.

### 2.4 PR Validation

Any pull request that:

- Adds a new workflow file (`.yml`/`.yaml`) to `.github/workflows/`, **or**
- Modifies an existing workflow file

**MUST** pass a SecureCode or [`actionlint`](https://github.com/rhysd/actionlint) check before merging. This check verifies that all `uses:` directives comply with the pinning rules defined in this policy.

---

## 3. Approved Actions List

The following table catalogs all GitHub Actions currently used across this repository's workflows. Each entry **must** be pinned to a specific commit SHA. The **Pinned Version/SHA** column should be updated as soon as the target commit SHA is resolved.

> **Note:** `<!-- SHA_TBD -->` placeholders indicate the SHA has not yet been resolved and must be filled in before the next policy review.

| Action | Pinned Version/SHA | Purpose | Last Reviewed |
|---|---|---|---|
| [`actions/checkout`](https://github.com/actions/checkout) | `<!-- SHA_TBD -->` | Check out repository source code | 2026-06-01 |
| [`actions/setup-python`](https://github.com/actions/setup-python) | `<!-- SHA_TBD -->` | Configure Python environment | 2026-06-01 |
| [`actions/cache`](https://github.com/actions/cache) | `<!-- SHA_TBD -->` | Cache pip dependencies for faster builds | 2026-06-01 |
| [`actions/upload-artifact`](https://github.com/actions/upload-artifact) | `<!-- SHA_TBD -->` | Upload security reports and build artifacts | 2026-06-01 |
| [`actions/setup-node`](https://github.com/actions/setup-node) | `<!-- SHA_TBD -->` | Configure Node.js environment for npm audit | 2026-06-01 |
| [`docker/setup-qemu-action`](https://github.com/docker/setup-qemu-action) | `<!-- SHA_TBD -->` | Set up QEMU for multi-platform Docker builds | 2026-06-01 |
| [`docker/setup-buildx-action`](https://github.com/docker/setup-buildx-action) | `<!-- SHA_TBD -->` | Configure Docker Buildx for multi-architecture builds | 2026-06-01 |
| [`docker/login-action`](https://github.com/docker/login-action) | `<!-- SHA_TBD -->` | Authenticate to GitHub Container Registry | 2026-06-01 |
| [`docker/metadata-action`](https://github.com/docker/metadata-action) | `<!-- SHA_TBD -->` | Extract Docker image metadata and tags | 2026-06-01 |
| [`docker/build-push-action`](https://github.com/docker/build-push-action) | `<!-- SHA_TBD -->` | Build and push Docker images with caching | 2026-06-01 |
| [`anchore/sbom-action`](https://github.com/anchore/sbom-action) | `<!-- SHA_TBD -->` | Generate Software Bill of Materials (SBOM) for images | 2026-06-01 |
| [`sigstore/cosign-installer`](https://github.com/sigstore/cosign-installer) | `<!-- SHA_TBD -->` | Install Cosign for container image signing | 2026-06-01 |
| [`codecov/codecov-action`](https://github.com/codecov/codecov-action) | `<!-- SHA_TBD -->` | Upload test coverage reports to Codecov | 2026-06-01 |
| [`github/codeql-action/upload-sarif`](https://github.com/github/codeql-action) | `<!-- SHA_TBD -->` | Upload SARIF security scan results to GitHub Security | 2026-06-01 |
| [`aquasecurity/trivy-action`](https://github.com/aquasecurity/trivy-action) | `<!-- SHA_TBD -->` | Run Trivy vulnerability scanner on container images | 2026-06-01 |
| [`aws-actions/configure-aws-credentials`](https://github.com/aws-actions/configure-aws-credentials) | `<!-- SHA_TBD -->` | Configure AWS credentials for ECS deployment | 2026-06-01 |
| [`google-github-actions/auth`](https://github.com/google-github-actions/auth) | `<!-- SHA_TBD -->` | Authenticate to Google Cloud for Cloud Run deployment | 2026-06-01 |
| [`google-github-actions/deploy-cloudrun`](https://github.com/google-github-actions/deploy-cloudrun) | `<!-- SHA_TBD -->` | Deploy container to Google Cloud Run | 2026-06-01 |
| [`azure/login`](https://github.com/azure/login) | `<!-- SHA_TBD -->` | Authenticate to Azure for Container Apps deployment | 2026-06-01 |
| [`azure/CLI`](https://github.com/azure/CLI) | `<!-- SHA_TBD -->` | Run Azure CLI commands for Container Apps management | 2026-06-01 |
| [`pre-commit/action`](https://github.com/pre-commit/action) | `<!-- SHA_TBD -->` | Run pre-commit hooks for code quality | 2026-06-01 |
| [`zricethezav/gitleaks-action`](https://github.com/zricethezav/gitleaks-action) | `<!-- SHA_TBD -->` | Scan for hardcoded secrets and credentials | 2026-06-01 |

### 3.1 Workflow Coverage

The approved actions above cover all three CI/CD workflow files:

| Workflow File | Actions Used |
|---|---|
| [`.github/workflows/docker-publish.yml`](.github/workflows/docker-publish.yml) | `actions/checkout`, `docker/setup-qemu-action`, `docker/setup-buildx-action`, `docker/login-action`, `docker/metadata-action`, `docker/build-push-action`, `anchore/sbom-action`, `sigstore/cosign-installer` |
| [`.github/workflows/ci-cd.yml`](.github/workflows/ci-cd.yml) | `actions/checkout`, `actions/setup-python`, `actions/cache`, `codecov/codecov-action`, `docker/setup-buildx-action`, `docker/login-action`, `docker/metadata-action`, `docker/build-push-action`, `aquasecurity/trivy-action`, `github/codeql-action/upload-sarif`, `actions/upload-artifact`, `aws-actions/configure-aws-credentials`, `google-github-actions/auth`, `google-github-actions/deploy-cloudrun`, `azure/login`, `azure/CLI` |
| [`.github/workflows/security-scan.yml`](.github/workflows/security-scan.yml) | `actions/checkout`, `actions/setup-python`, `pre-commit/action`, `zricethezav/gitleaks-action`, `actions/setup-node`, `actions/upload-artifact` |

---

## 4. Enforcement

### 4.1 Automated CI Check

A CI workflow step **must** be added to the pipeline that references this policy by name. Example step:

```yaml
- name: Check GitHub Actions pinning policy
  run: |
    echo "Validating compliance with GITHUB_ACTIONS_POLICY.md..."
    # Verify all uses: directives use commit SHAs (not tags)
    if grep -rP 'uses:\s+\S+@v?\d+\.\d+' .github/workflows/; then
      echo "ERROR: Unpinned action tag found. See docs/GITHUB_ACTIONS_POLICY.md"
      exit 1
    fi
    echo "All actions are properly pinned."
```

Alternatively, integrate [`actionlint`](https://github.com/rhysd/actionlint) with a custom rule or use the [`step-security/harden-runner`](https://github.com/step-security/harden-runner) action to enforce this policy.

### 4.2 Manual PR Review Checklist

Every pull request that touches `.github/workflows/*.yml` **must** include verification against the checklist in [Section 7](#7-pr-reviewer-checklist).

### 4.3 References

- [GitHub Security Hardening for Actions](https://docs.github.com/en/actions/security-guides/security-hardening-for-github-actions)
- [OpenSSF Scorecard — Pinned Dependencies](https://securityscorecards.dev/viewer/?uri=github.com/AsimNexus/asimnexus)
- [Security Hardening: Using SHA-pinned actions](https://docs.github.com/en/actions/security-guides/security-hardening-for-github-actions#using-third-party-actions)

---

## 5. Renovation / Dependency Update Strategy

### 5.1 Automated Updates via Dependabot or Renovate

To keep pinned SHAs up-to-date without sacrificing security, use **Dependabot** or **Renovate** configured to update GitHub Actions:

**Dependabot** (recommended — native to GitHub):

Create or update `.github/dependabot.yml`:

```yaml
version: 2
updates:
  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
      day: "monday"
    commit-message:
      prefix: "chore"
      include: "scope"
```

**Renovate** (alternative — more configurable):

Add a `renovate.json` configuration:

```json
{
  "$schema": "https://docs.renovatebot.com/renovate-schema.json",
  "extends": ["config:base"],
  "github-actions": {
    "enabled": true,
    "pinDigests": true
  }
}
```

### 5.2 How to Safely Update a Pinned SHA

1. **Check the release notes** of the target action for breaking changes.
2. **Verify the new SHA** — ensure it matches the release tag you intend to use by comparing the tag's commit hash on GitHub.
3. **Update in a dedicated PR** — never bundle action updates with feature work.
4. **Run the full CI pipeline** to confirm the update doesn't break anything.
5. **Update the Approved Actions List** table in this document with the new SHA and date.

### 5.3 Monitoring for Security Advisories

- **GitHub Advisory Database:** Monitor [github.com/advisories](https://github.com/advisories) for advisories affecting your actions.
- **Dependabot alerts:** Enable Dependabot security alerts for this repository (Settings → Security & analysis → Dependabot alerts).
- **OpenSSF Scorecard:** Run `scorecard` to get automatic security ratings for your dependencies.
- **Mailing lists:** Subscribe to [actions@github.com](https://github.com/actions) announcements for critical updates.

---

## 6. Exceptions

The following are **exempt** from the SHA-pinning requirement:

| Source Type | Rationale |
|---|---|
| `docker://` references | These pull container images directly; version pinning is handled via image tags. |
| `./.github/actions/` paths | Local actions are version-controlled within this repository and are inherently pinned to the commit being built. |

All other `uses:` directives, including third-party actions from the GitHub Marketplace, **must** be SHA-pinned.

---

## 7. PR Reviewer Checklist

- [ ] All `uses:` directives use commit SHAs, not version tags
- [ ] No `@master`, `@main`, `@latest` references exist
- [ ] Action versions are the latest available (checked against marketplace)
- [ ] Workflow permissions follow least-privilege principle

---

## 8. Policy Exemption Process

To request an exemption from any part of this policy:

1. Open a GitHub Issue using the **Policy Exemption** template.
2. Include the action name, the reason a SHA pin cannot be used, and a risk assessment.
3. The exemption must be approved by the Security Team lead.
4. Approved exemptions are valid for 90 days and must be renewed.

---

*Document maintained by the Security Team. For questions, open an issue in this repository tagged `security`.*

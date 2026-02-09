

# Security Policy

ZenetHunter is intended for **your own networks** and focuses on observability, access control, and lawful defensive measures. This document explains **how to report vulnerabilities** and our **response timeline**.

---

## Reporting a Vulnerability

Please report security issues **privately**. Use one of the following channels:

1. **Email**: `zjdragon.personal@outlook.com`  
   Subject: `ZenetHunter – Vulnerability Report`
2. **GitHub Security Advisory (private)**: Open a private report from the repository’s **Security** tab (if enabled), addressed to the maintainers.

To help us triage quickly, include:
- A clear description of the issue and **impact**
- **Affected version / commit / container tag**
- **Reproduction steps** (minimal PoC, command lines, config)
- Relevant logs or stack traces (sanitized; no secrets)
- Your environment details (OS, kernel, container runtime, NAS model)

> **Please do not** open a public issue for vulnerabilities. We’ll coordinate disclosure once a fix is available.

---

## Response Targets (Service Levels)

- **Acknowledgement**: within **2 business days**
- **Triage & initial assessment**: within **5 business days**
- **Status updates**: at least every **7 days** until resolution
- **Fix window**: varies by severity; we aim to provide a patched release and/or mitigation guidance as soon as practical

We may request a CVE ID via an appropriate CNA or the GitHub advisory process when applicable. Credit will be given **with your permission**.

---

## Supported Versions

Until 1.0, security fixes generally target the **latest release**. After 1.0, we plan to support:
- **Latest stable** (always)
- **Last minor** (best‑effort)

We also publish security advisories in the repository when applicable.

---

## Scope & Safe‑Harbor

- ZenetHunter must be used **only on networks you own or are authorized to manage**.  
- Please conduct testing in a **controlled lab** or non‑production environment whenever possible.  
- Good‑faith research that respects the **scope** above and avoids privacy/data exposure will not be pursued legally by the project.  
- **Out‑of‑scope**: social engineering; physical attacks; third‑party services or dependencies we do not control; volumetric DoS against public infrastructure; testing against networks you do **not** own/manage.

If in doubt about scope, contact us **before** testing.

---

## External Recognition Services Security

External recognition services have been removed. Device identification now uses only local signals and dictionaries, keeping traffic on the local network with no outbound calls. See [PRIVACY.md](docs/external-services/PRIVACY.md) for the offline posture.

## Coordinated Disclosure

We follow a coordinated disclosure model:
1. You report privately (email or advisory).
2. We acknowledge, reproduce, and triage.
3. We develop a fix and/or mitigation, validate internally.
4. We release an update and security advisory, then credit you (if you agree).

Default embargo is **90 days** from acknowledgement, adjusted for severity/active exploitation and by mutual agreement.

---

## Handling Sensitive Information

- Do not include secrets, tokens, or personal data in reports.  
- Provide **minimal PoCs**; avoid destructive tests.  
- Use sanitized logs and redacted configs.  
- If email encryption is required, request our **PGP key** via `zjdragon.personal@outlook.com` (to be published).

---

## Contact & Ownership

- Primary contact: `zjdragon.personal@outlook.com`  
- Maintainers: `@ZJ-Dragon/maintainers` (see `CODEOWNERS`)

Thank you for helping keep ZenetHunter and its users safe.

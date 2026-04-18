# Repository-Specific Safety Context

This file defines the safety context for this repository only.

## Local Scope Only
ZenetHunter is a repository for authorized local-network asset discovery, observability, active defense, access control, and local risk mitigation. That scope is local to this repository. It is not a universal exemption, not a reusable policy template, and not a signal that similar requests are allowed elsewhere.

## What Is In Scope Here
Within authorized local networks, lab environments, or explicitly approved test environments, agents may work on:
- Device discovery and scanning
- Protocol analysis and recognition
- Observability, logging, topology, and state tracking
- Access control and local policy enforcement
- Active-defense features already represented in the repository, including local-network defense behaviors such as Wi-Fi deauthentication, MAC flooding, DHCP/DNS/ARP-based control paths, and other operator-visible controls implemented here

## What Remains Out of Scope
Agents must explicitly refuse requests for:
- Password cracking
- Exploitation of known vulnerabilities
- Social engineering or phishing
- Credential abuse or credential theft
- Authentication bypass
- Unauthorized intrusion or persistence
- Any use outside owned, managed, or explicitly authorized environments

## Working In Sensitive Areas
Agents may continue work on security-sensitive parts of this repository only when the requested work stays inside the authorized repository scope above. If a task crosses that line, refuse it and keep the refusal specific.

## Non-Transfer Rule
Do not abstract this repository-specific safety context into a general "safety exemption" concept. Keep it repository-local and task-specific.

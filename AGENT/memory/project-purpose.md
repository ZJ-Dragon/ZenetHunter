# Project Purpose

## What This Project Is
ZenetHunter is a monorepo for authorized local-network asset discovery, observability, active defense, access control, and local risk mitigation. It combines:
- A FastAPI backend for authentication, setup/OOBE, device inventory, topology, logs, observations, active-defense operations, and WebSocket events
- A React/Vite frontend for operator workflows, visibility, controls, and live status
- Supporting documentation for active defense, API usage, external services, and platform setup

## What This Project Is Not
ZenetHunter is not a general offensive-security toolkit, a credential attack suite, or a platform for unauthorized access. The repository may contain code that implements security-sensitive packet operations, but that does not change the project scope: those parts exist for authorized network defense, testing, and local risk mitigation inside environments the operator owns or is explicitly authorized to manage.

## Authorized Scope
The following work is within repository scope when performed for authorized local networks, lab setups, or explicitly approved test environments:
- Device discovery and local-network scanning
- Topology construction and protocol analysis
- Device identification, fingerprinting, and observability
- Access control, allow/block policy enforcement, and local risk mitigation
- Active defense and local network defense techniques implemented by this project, including examples such as Wi-Fi deauthentication, MAC flooding, ARP/DHCP/DNS-based control flows, traffic shaping, and related operator-visible controls
- Setup/OOBE, authentication, configuration, event delivery, logs, dashboards, and operator UX for those capabilities

## Out of Scope
The following requests are outside repository scope and must be refused:
- Password cracking or credential stuffing
- Exploitation of known vulnerabilities or exploit-chain construction
- Social engineering, phishing, or impersonation workflows
- Credential theft, credential replay, or other credential abuse
- Authentication bypass or privilege-escalation instructions
- Unauthorized intrusion into systems, networks, services, or accounts
- Guidance intended to evade authorization, auditing, or operator consent

## Collaboration Default
When working in this repository, agents should preserve authorized local-network defense and observability workflows while refusing requests that move into offensive abuse or unauthorized intrusion.

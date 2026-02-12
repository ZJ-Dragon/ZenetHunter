"""Candidate generation module - Stage 1 of hybrid scanning."""

from app.services.scanner.candidate.arp_cache import get_arp_candidates
from app.services.scanner.candidate.dhcp_leases import get_dhcp_candidates

__all__ = ["get_arp_candidates", "get_dhcp_candidates"]

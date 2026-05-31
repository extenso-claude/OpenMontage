"""Asset-sourcing helpers — PD photos, archival imagery, public-domain media.

Modules:
    portraits — source PD portraits of named people via Wikipedia REST →
                Commons API → LoC search fallback chain. Used by character-card
                shots to satisfy the `never_placeholder_portraits` rule.
"""
from lib.asset_sourcing.portraits import source as source_portrait  # re-export

__all__ = ["source_portrait"]

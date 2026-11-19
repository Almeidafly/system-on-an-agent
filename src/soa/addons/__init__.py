"""Add-on interface and loader.

Add-ons are optional. The core (planner, memory, skills, connectors, bus)
does not depend on any concrete add-on. Heatgate and the Lex loop are
documented as future placeholders only; they are not implemented here.
"""

from soa.addons.interface import Addon, AddonManifest, HookContext
from soa.addons.loader import AddonError, AddonLoader, load_addon

__all__ = [
    "Addon",
    "AddonError",
    "AddonLoader",
    "AddonManifest",
    "HookContext",
    "load_addon",
]

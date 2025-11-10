"""
Utility Functions
Helper functions for color generation and type normalization
"""
from typing import Tuple


def generate_random_color(seed_text: str) -> Tuple[int, int, int]:
    """Generate a deterministic random color from text"""
    r = (hash(seed_text) % 200) + 50
    g = ((hash(seed_text) * 2) % 200) + 50
    b = ((hash(seed_text) * 3) % 200) + 50
    return (r, g, b)


def normalize_type(entity_type):
    """Normalize entity/relation type (handle list or string)"""
    if isinstance(entity_type, list):
        return entity_type[0] if entity_type else "Unknown"
    return entity_type

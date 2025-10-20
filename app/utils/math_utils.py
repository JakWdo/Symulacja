"""Mathematical utility functions."""

import math
from typing import List


def cosine_similarity(a: List[float], b: List[float]) -> float:
    """
    Oblicz cosine similarity między dwoma wektorami.

    Cosine similarity to miara podobieństwa wektorów w przestrzeni n-wymiarowej.
    Wartość 1.0 = identyczne, 0.0 = ortogonalne, -1.0 = przeciwne.

    Args:
        a: Pierwszy wektor (lista floatów)
        b: Drugi wektor (lista floatów)

    Returns:
        Cosine similarity w przedziale [-1, 1], zaokrąglone do 4 miejsc po przecinku

    Examples:
        >>> cosine_similarity([1.0, 0.0], [1.0, 0.0])
        1.0
        >>> cosine_similarity([1.0, 0.0], [0.0, 1.0])
        0.0
        >>> cosine_similarity([1.0, 0.0], [-1.0, 0.0])
        -1.0
    """
    dot = sum(x * y for x, y in zip(a, b, strict=False))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return round(dot / (norm_a * norm_b), 4)

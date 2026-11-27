"""Normalization rules for public application feature names."""

from __future__ import annotations

import keyword


def normalize_public_feature_name(raw: str) -> str:
    """Normalize a feature name and reject non-public Python identifiers."""

    feature = raw.strip().lower().replace("-", "_")
    if not feature.isidentifier() or feature.startswith("_") or keyword.iskeyword(feature):
        raise ValueError(f"Invalid public feature name: {raw!r}")
    return feature

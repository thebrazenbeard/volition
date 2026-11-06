"""Source-label syntax only: no provenance authentication or effect authority."""

from __future__ import annotations

import unicodedata


_FORBIDDEN_CATEGORIES = frozenset({'Cc', 'Cf', 'Cs', 'Zl', 'Zp'})
_IGNORABLE_MARK_CATEGORIES = frozenset({'Mn', 'Me', 'Mc'})


def admissible_source(value: object, *, require_explicit: bool = False) -> bool:
    """Check a printable source label without changing the preserved identifier.

    Controls, format characters and surrogates are not stable evidence labels;
    Unicode letters, scripts, spacing and combining accents otherwise survive.
    Combining marks (including spacing marks in Indic scripts) cannot *alone*
    supply a visible identifier or conceal the reserved ``unspecified``
    placeholder in an explicit-source admission.

    This says nothing about whether a named source is authenticated or current.
    """
    if not isinstance(value, str):
        return False
    if any(unicodedata.category(ch) in _FORBIDDEN_CATEGORIES for ch in value):
        return False
    folded = unicodedata.normalize('NFKD', value)
    visible = ''.join(
        ch for ch in folded
        if unicodedata.category(ch) not in _IGNORABLE_MARK_CATEGORIES
        and not ch.isspace()
    )
    return bool(visible) and (not require_explicit or visible.casefold() != 'unspecified')

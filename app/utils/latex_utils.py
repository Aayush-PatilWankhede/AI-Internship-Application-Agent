"""LaTeX escaping and URL sanitization for resume templates."""

from __future__ import annotations

import re
from urllib.parse import urlparse

_LATEX_SPECIALS = {
    "\\": r"\textbackslash{}",
    "{": r"\{",
    "}": r"\}",
    "$": r"\$",
    "&": r"\&",
    "#": r"\#",
    "%": r"\%",
    "_": r"\_",
    "~": r"\textasciitilde{}",
    "^": r"\textasciicircum{}",
    # Unicode punctuation & typography mappings for pdflatex
    "\u2011": "-",  # Non-breaking hyphen (‑)
    "\u2010": "-",  # Hyphen (‐)
    "\u2012": "-",  # Figure dash (‒)
    "\u2013": "--",  # En-dash (–)
    "\u2014": "---",  # Em-dash (—)
    "\u2015": "---",  # Horizontal bar (―)
    "\u2018": "'",  # Left single quote (‘)
    "\u2019": "'",  # Right single quote (’)
    "\u201a": "'",  # Single low-9 quote (‚)
    "\u201b": "'",  # Single high-reversed-9 quote (‛)
    "\u201c": "``",  # Left double quote (“)
    "\u201d": "''",  # Right double quote (”)
    "\u201e": ",,",  # Double low-9 quote („)
    "\u2022": r"\textbullet{}",  # Bullet (•)
    "\u2023": r"\textbullet{}",  # Triangular bullet (‣)
    "\u2043": r"\textbullet{}",  # Hyphen bullet (⁃)
    "\u2026": r"\ldots{}",  # Ellipsis (…)
    "\u00a0": "~",  # Non-breaking space
    "\u202f": "~",  # Narrow no-break space
    "\u200b": "",  # Zero-width space
    "\u200c": "",  # Zero-width non-joiner
    "\u200d": "",  # Zero-width joiner
    "\ufeff": "",  # Byte order mark
    "\u20b9": "Rs.~",  # Indian Rupee (₹)
    "\u20ac": r"\texteuro{}",  # Euro (€)
    "\u00a3": r"\pounds{}",  # Pound (£)
    "\u00a5": r"\textyen{}",  # Yen (¥)
    "\u00b0": r"$^\circ$",  # Degree (°)
    "\u2264": r"$\le$",  # Less than or equal (≤)
    "\u2265": r"$\ge$",  # Greater than or equal (≥)
    "\u2260": r"$\ne$",  # Not equal (≠)
    "\u00b1": r"$\pm$",  # Plus-minus (±)
    "\u00d7": r"$\times$",  # Multiply (×)
    "\u00f7": r"$\div$",  # Divide (÷)
}


def escape_latex(value: str) -> str:
    """Escape characters that are special in LaTeX text mode."""
    return "".join(_LATEX_SPECIALS.get(char, char) for char in value)


def sanitize_url(value: str) -> str:
    """Allow only http(s)/mailto URLs; otherwise return an empty string."""
    cleaned = value.strip()
    if not cleaned:
        return ""
    parsed = urlparse(cleaned)
    if parsed.scheme.lower() in {"http", "https", "mailto"} and (parsed.netloc or parsed.path):
        return cleaned
    if cleaned.startswith("www.") and " " not in cleaned:
        return f"https://{cleaned}"
    return ""


_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def is_email(value: str) -> bool:
    """Return True when ``value`` looks like a simple email address."""
    return bool(_EMAIL_RE.match(value.strip()))

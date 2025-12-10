import re
import hashlib

DEFAULT_REPLACEMENTS = {
    "/": "∕",  # slash
    "\\": "⧵",  # backslash
    "..": "⫻",  # parent directory
}


def safe_filename(name: str, replacements: dict[str, str] | None = None) -> str:
    """
    Convert an unsafe filename into a safe one.
    Applies longest pattern replacement first, then replaces all disallowed characters.
    """
    # Merge defaults + user overrides
    repl = {**DEFAULT_REPLACEMENTS, **(replacements or {})}

    # Sort originals longest -> shortest to avoid partial matches
    sorted_keys = sorted(repl.keys(), key=len, reverse=True)

    # Apply replacements for unsafe sequences
    for key in sorted_keys:
        name = name.replace(key, repl[key])

    # Build an allowlist of characters: A-Z, a-z, 0-9, _ - . and all replacement tokens
    allowed_tokens = "".join(re.escape(t) for t in repl.values())
    pattern = rf"[^A-Za-z0-9_\-\.{allowed_tokens}]"

    # Replace everything not allowed
    name = re.sub(pattern, "_", name)

    return name


def unsafe_filename(safe_name: str, replacements: dict[str, str] | None = None) -> str:
    """
    Reverse the safe filename back to original form.
    Sort by replacement token length (value), longest first, to avoid partial matches.
    """
    repl = {**DEFAULT_REPLACEMENTS, **(replacements or {})}

    # Sort tokens longest -> shortest
    sorted_pairs = sorted(repl.items(), key=lambda kv: len(kv[1]), reverse=True)

    # Replace tokens back to original
    for original, token in sorted_pairs:
        safe_name = safe_name.replace(token, original)

    return safe_name


def safe_filename_hash(name: str) -> str:
    return hashlib.sha256(name.encode()).hexdigest()[:12]

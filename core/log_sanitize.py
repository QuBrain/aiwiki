import re


_SENSITIVE_PATTERNS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"(api[_-]?key\s*[=:]\s*)\S+", re.IGNORECASE), r"\1***"),
    (re.compile(r"(Authorization:\s*Bearer\s*)\S+", re.IGNORECASE), r"\1***"),
    (re.compile(r"(X-API-Key:\s*)\S+", re.IGNORECASE), r"\1***"),
    (re.compile(r"(sk-[a-zA-Z0-9]{20,})"), "sk-***"),
]


def sanitize(msg: str, max_len: int = 2000) -> str:
    for pattern, replacement in _SENSITIVE_PATTERNS:
        msg = pattern.sub(replacement, msg)
    return msg[:max_len]

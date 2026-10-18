from typing import Any, Iterable, Mapping


def message_text(message: Mapping[str, Any]) -> str:
    """Extract text from either plain or multimodal chat message content."""
    content = message.get("content", "")
    if isinstance(content, str):
        return content
    if not isinstance(content, list):
        return ""

    parts = []
    for item in content:
        if isinstance(item, str):
            parts.append(item)
        elif isinstance(item, Mapping):
            text = item.get("text")
            if isinstance(text, str):
                parts.append(text)
    return "\n".join(parts)


def is_termination_message(
    message: Mapping[str, Any],
    accepted: Iterable[str] = ("terminate",),
) -> bool:
    """Return whether a message consists solely of an accepted terminal token."""
    terminal_tokens = {token.strip().casefold() for token in accepted}
    return message_text(message).strip().casefold() in terminal_tokens

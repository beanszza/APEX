"""Security utility functions for input sanitization and prompt injection defense."""

import re
import html

# Disallow control characters, script tags, and common injection signatures
_CONTROL_CHARS = re.compile(r"[\x00-\x1f\x7f]")
_SCRIPT_PATTERN = re.compile(r"<script.*?>.*?</script>|javascript:", re.IGNORECASE)

def sanitize_text(text: str | None, max_length: int = 150) -> str:
    """
    Sanitize text input against prompt injection, script injection, and excessive length.
    Ensures safe incorporation into machine learning models and recommendation text.
    """
    if not text:
        return ""
    
    # Remove control characters and script patterns
    cleaned = _CONTROL_CHARS.sub("", str(text))
    cleaned = _SCRIPT_PATTERN.sub("", cleaned)
    
    # Escape HTML special characters
    cleaned = html.escape(cleaned, quote=True)
    
    # Strip code fences and newlines that could break formatting
    cleaned = cleaned.replace("```", "").replace("\n", " ").replace("\r", " ").strip()
    
    return cleaned[:max_length]

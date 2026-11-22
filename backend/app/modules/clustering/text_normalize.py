import re

_UUID = re.compile(
    r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b",
    re.IGNORECASE,
)
_IP = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
_ISO_TS = re.compile(r"\b\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?\b")
_NUMBER = re.compile(r"\b\d+\b")


def normalize_message_for_clustering(message: str) -> str:
    text = message.strip().lower()
    text = _UUID.sub("<uuid>", text)
    text = _IP.sub("<ip>", text)
    text = _ISO_TS.sub("<ts>", text)
    text = _NUMBER.sub("<num>", text)
    text = re.sub(r"\s+", " ", text)
    return text
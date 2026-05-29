from html.parser import HTMLParser


class _Stripper(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self._parts.append(data)

    def result(self) -> str:
        return " ".join(self._parts).strip()


def strip_html(text: str) -> str:
    s = _Stripper()
    s.feed(text)
    return s.result()


def truncate(text: str, max_chars: int = 4000) -> str:
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "…"

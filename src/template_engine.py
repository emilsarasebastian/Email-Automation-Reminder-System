"""
template_engine.py - Load text templates and fill in {placeholders}.

Example template line:   Hello {name},
Example context:         {"name": "Asha"}
Result:                  Hello Asha,

Unknown placeholders are left as-is (e.g. "{link}") instead of crashing,
so one missing column never stops the whole run.
"""

from pathlib import Path


class _SafeDict(dict):
    def __missing__(self, key):
        return "{" + key + "}"


def load_template(templates_dir: Path, template_name: str) -> str:
    """Read templates/<template_name>.txt"""
    path = Path(templates_dir) / f"{template_name}.txt"
    if not path.exists():
        raise FileNotFoundError(f"Template not found: {path}")
    return path.read_text(encoding="utf-8")


def render(text: str, context: dict) -> str:
    """Replace {placeholders} in `text` with values from `context`."""
    return text.format_map(_SafeDict(context))

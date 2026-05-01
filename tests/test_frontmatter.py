from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from utils import render_template


def test_frontmatter_fields_render():
    template = 'title: "{{ title }}"\nsource_type: video\nsource_url: "{{ source_url }}"\n'
    rendered = render_template(template, {"title": "A", "source_url": "https://x.test"})
    assert 'title: "A"' in rendered
    assert 'source_url: "https://x.test"' in rendered

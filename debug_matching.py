from pathlib import Path
from benennungssoftware.config import load_config
from benennungssoftware.text_extraction import extract_document_text
from benennungssoftware.processor import _matching_projects, _project_match_score

cfg = load_config('examples/config.json')
for p in sorted(Path('examples/demo/unassigned').glob('*.pdf')):
    text = extract_document_text(p, cfg.text_extraction)
    haystack = f'{p.stem} {text}'.casefold()
    matches = _matching_projects(haystack, cfg.projects)
    print('FILE:', p.name)
    if not matches:
        print('UNMATCHED')
        print((text[:1200].replace('\n', ' ')[:1200]))
    else:
        ranked = sorted(matches, key=lambda x: (-_project_match_score(haystack, x), x.code.casefold()))
        print('RANKED:', [(m.code, _project_match_score(haystack, m)) for m in ranked[:8]])
        print('TOP_HITS:', [(m.code, [kw for kw in m.keywords if kw and kw.casefold() in haystack][:10]) for m in ranked[:3]])
    print('---')

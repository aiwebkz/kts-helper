#!/usr/bin/env python3
import hashlib
from pathlib import Path

dist = Path(__file__).resolve().parent / 'dist'
lines = []
for path in sorted(dist.iterdir()):
    if path.is_file() and path.name != 'SHA256SUMS':
        digest = hashlib.sha256()
        with path.open('rb') as source:
            for chunk in iter(lambda: source.read(1024 * 1024), b''):
                digest.update(chunk)
        lines.append(f'{digest.hexdigest()}  {path.name}')
(dist / 'SHA256SUMS').write_text('\n'.join(lines) + '\n', encoding='utf-8')

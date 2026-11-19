#!/usr/bin/env python3
"""Bundle corresponding source, including the pinned hbb_common submodule."""
from pathlib import Path
import subprocess
import tarfile

ROOT = Path(__file__).resolve().parents[1]


def files(path):
    return subprocess.check_output(
        ['git', '-C', str(path), 'ls-files', '--cached', '--others', '--exclude-standard', '-z']
    ).decode('utf-8').split('\0')


def main():
    dist = ROOT / 'kts/dist'
    dist.mkdir(parents=True, exist_ok=True)
    with tarfile.open(dist / 'kts-helper-source.tar.gz', 'w:gz') as archive:
        for base in [ROOT, ROOT / 'libs/hbb_common']:
            for name in sorted(set(files(base))):
                if not name:
                    continue
                path = base / name
                if path.is_file() or path.is_symlink():
                    archive.add(path, arcname='kts-helper/' + path.relative_to(ROOT).as_posix(), recursive=False)
    print('Bundled corresponding source with submodule')


if __name__ == '__main__':
    main()

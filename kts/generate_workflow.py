#!/usr/bin/env python3
"""Derive desktop setup jobs from the pinned upstream workflow, without editing it."""
import copy
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]


def main():
    upstream = yaml.safe_load((ROOT / '.github/workflows/flutter-build.yml').read_text())
    env = copy.deepcopy(upstream['env'])
    # The fork builds artifacts only; upstream publishing/signing services are not used.
    for key in ['TAG_NAME', 'ANDROID_SIGNING_KEY', 'MACOS_P12_BASE64', 'SIGN_BASE_URL']:
        env.pop(key, None)
    env['UPLOAD_ARTIFACT'] = 'true'
    env['PUBLISH_UPDATE_METADATA'] = 'false'
    checkout = {'uses': 'actions/checkout@34e114876b0b11c390a56381ad16ebd13914f8d5',
                'with': {'submodules': 'recursive', 'persist-credentials': False}}
    configure = {'name': 'Configure kts-helper server and branding', 'shell': 'bash',
                 'run': 'python3 kts/configure.py'}
    jobs = {
        'validate': {
            'runs-on': 'ubuntu-22.04',
            'steps': [checkout, {'name': 'Validate release configuration',
                                 'run': 'python3 kts/configure.py --check'},
                      {'name': 'Test configuration validation',
                       'run': 'python3 -m unittest discover -s kts/tests -v'}]
        },
        'generate-bridge': {'needs': ['validate'], 'uses': './.github/workflows/bridge.yml'},
    }
    topmost = copy.deepcopy(upstream['jobs']['build-RustDeskTempTopMostWindow'])
    topmost['needs'] = ['validate']
    topmost['with']['upload-artifact'] = True
    jobs['build-RustDeskTempTopMostWindow'] = topmost
    for job_name in ['build-for-windows-flutter', 'build-for-macOS']:
        job = copy.deepcopy(upstream['jobs'][job_name])
        setup_steps = []
        for step in job['steps']:
            if step.get('name') == 'Build rustdesk':
                build_step = copy.deepcopy(step)
                break
            # No access to upstream's signing service or private Apple credentials.
            if step.get('if') == 'env.MACOS_P12_BASE64 != null':
                continue
            if step.get('name') == 'Run the Dart tests':
                continue
            setup_steps.append(step)
            if step.get('name') == 'Checkout source code':
                setup_steps[-1].setdefault('with', {})['persist-credentials'] = False
                setup_steps.append(copy.deepcopy(configure))
        else:
            raise ValueError(f'Upstream build anchor missing: {job_name}')
        if job_name == 'build-for-windows-flutter':
            build_step['name'] = 'Build kts-helper'
            build_step['run'] = (
                'python3 .\\build.py --portable --flutter --skip-portable-pack --hwcodec ${{ matrix.job.build-args }}\n'
                'if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }\n'
                'Move-Item ./flutter/build/windows/${{ matrix.job.flutter-arch }}/runner/Release ./rustdesk\n'
            )
            setup_steps += [build_step,
                {'name': 'Download window injection library',
                 'uses': 'actions/download-artifact@3e5f45b2cfb9172054b4087a40e8e0b5a5461e7c',
                 'with': {'name': "${{ matrix.job.arch == 'aarch64' && 'topmostwindow-artifacts-ARM64' || 'topmostwindow-artifacts-x64' }}", 'path': './rustdesk'}},
                {'name': 'Package Windows client', 'shell': 'bash', 'run': '''
set -euo pipefail
mv rustdesk/rustdesk.exe rustdesk/kts-helper.exe
cp LICENCE rustdesk/LICENCE
cp kts/NOTICE.txt rustdesk/NOTICE.txt
cp kts/branding/icon.png rustdesk/data/flutter_assets/assets/icon.png
pushd libs/portable
python3 -m pip install -r requirements.txt
python3 generate.py -f ../../rustdesk -o . -e ../../rustdesk/kts-helper.exe
popd
mkdir -p kts/dist
mv target/release/rustdesk-portable-packer.exe kts/dist/kts-helper-${{ env.VERSION }}-${{ matrix.job.arch }}-install.exe
python3 kts/package_source.py
python3 kts/checksums.py
'''.strip()}]
        else:
            # The upstream build still supplies codec/toolchain compatibility for each arch.
            build_step['name'] = 'Build kts-helper'
            setup_steps += [build_step,
                {'name': 'Package unsigned macOS client', 'shell': 'bash', 'run': '''
set -euo pipefail
mkdir -p kts/dist
APP=flutter/build/macos/Build/Products/Release/kts-helper.app
cp LICENCE "$APP/Contents/Resources/LICENCE"
cp kts/NOTICE.txt "$APP/Contents/Resources/NOTICE.txt"
create-dmg --volname "kts-helper" --icon "kts-helper.app" 200 190 --hide-extension "kts-helper.app" --window-size 800 400 --app-drop-link 600 185 "kts/dist/kts-helper-${{ env.VERSION }}-${{ matrix.job.arch }}.dmg" "$APP"
python3 kts/package_source.py
python3 kts/checksums.py
'''.strip()}]
        setup_steps.append({'name': 'Upload kts-helper artifacts',
                            'uses': 'actions/upload-artifact@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a',
                            'with': {'name': 'kts-helper-${{ matrix.job.target }}',
                                     'path': 'kts/dist/*', 'if-no-files-found': 'error',
                                     'retention-days': 14}})
        job['steps'] = setup_steps
        jobs[job_name] = job
    workflow = {'name': 'Build kts-helper desktop',
                'on': {'workflow_dispatch': {}},
                'permissions': {'contents': 'read'},
                'concurrency': {'group': 'kts-build-${{ github.ref }}', 'cancel-in-progress': False},
                'env': env, 'jobs': jobs}
    output = '# Generated by kts/generate_workflow.py from RustDesk 1.5.3.\n'
    output += yaml.safe_dump(workflow, sort_keys=False, width=120)
    (ROOT / '.github/workflows/kts-build.yml').write_text(output)
    print('Generated manual desktop build workflow')


if __name__ == '__main__':
    main()

import base64
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('configure', ROOT / 'kts/configure.py')
configure = importlib.util.module_from_spec(spec)
spec.loader.exec_module(configure)


class ConfigureTests(unittest.TestCase):
    def config(self):
        config = json.loads((ROOT / 'kts/config.json').read_text())
        return dict(config, id_server='support.company.ru:21116',
                    relay_server='support.company.ru:21117',
                    public_key=base64.b64encode(bytes(range(32))).decode())

    def test_release_requires_real_endpoints_and_a_public_key(self):
        config = self.config()
        configure.validate(config)
        for field, values in {
            'id_server': ['', 'remote.invalid', 'https://server.ru', 'server.ru:0',
                          'server.ru:65536', 'server.ru;echo', 'server.ru\n'],
            'relay_server': ['', 'example.com:21117'],
            'public_key': ['', 'not-base64', base64.b64encode(bytes(64)).decode()],
        }.items():
            for value in values:
                with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                    configure.validate(dict(config, **{field: value}))

    def test_host_formats_and_brand_identity(self):
        for host in ['192.168.1.20:21116', '[2001:db8::1]:21116', 'rd.company.ru']:
            configure.validate(dict(self.config(), id_server=host))
        for field, value in [('app_name', '../kts'), ('bundle_id', 'bad/id'), ('accent', "red'")]:
            with self.subTest(field=field), self.assertRaises(ValueError):
                configure.validate(dict(self.config(), **{field: value}))

    def test_preview_blocks_release_and_never_embeds_unchecked_server(self):
        paths = ['flutter/macos/Runner/Configs/AppInfo.xcconfig',
                 'flutter/macos/Runner.xcodeproj/project.pbxproj',
                 'flutter/macos/Runner.xcodeproj/xcshareddata/xcschemes/Runner.xcscheme',
                 'build.py', 'flutter/windows/runner/Runner.rc', 'libs/portable/Cargo.toml', 'flutter/lib/common.dart',
                 'flutter/lib/desktop/pages/desktop_home_page.dart']
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for name in paths:
                (root / name).parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / name, root / name)
            with patch.object(configure, 'ROOT', root):
                configure.apply(self.config(), preview=True)
                source = (root / 'kts/generated/client.rs').read_text()
                self.assertIn('compile_error!', source)
                self.assertIn('unconfigured.invalid:21116', source)
                self.assertNotIn('support.company.ru', source)
                configure.apply(self.config())
                source = (root / 'kts/generated/client.rs').read_text()
                self.assertNotIn('compile_error!', source)
                self.assertIn('support.company.ru:21116', source)
                before = {name: (root / name).read_bytes() for name in paths}
                configure.apply(self.config())
                self.assertEqual(before, {name: (root / name).read_bytes() for name in paths})


if __name__ == '__main__':
    unittest.main()

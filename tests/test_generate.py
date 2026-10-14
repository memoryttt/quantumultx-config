import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

GENERATOR = Path(__file__).resolve().parents[1] / 'scripts' / 'generate.py'

class GenerationTests(unittest.TestCase):
    def run_generator(self, settings=None, domains=None):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        (root / 'config').mkdir()
        cfg = {'repository': 'example/qx', 'branch': 'main', 'path_prefix': '',
               'policy_name': 'AI', 'node_filter': '.*', 'update_interval': 86400,
               'dns': {'mode': 'split', 'default_servers': ['223.5.5.5'],
                       'ai_doh': 'https://1.1.1.1/dns-query'}}
        if settings:
            cfg.update(settings)
        (root / 'config/settings.json').write_text(json.dumps(cfg))
        (root / 'config/ai-domains.json').write_text(json.dumps(domains or [
            {'type': 'suffix', 'domain': 'example.com', 'enabled': True},
            {'type': 'exact', 'domain': 'login.other.net', 'enabled': True},
            {'type': 'suffix', 'domain': 'disabled.net', 'enabled': False}]))
        result = subprocess.run([sys.executable, str(GENERATOR), '--root', str(root)],
                                capture_output=True, text=True)
        return root, result

    def test_suffix_and_exact_dns_share_rule_scope(self):
        root, result = self.run_generator()
        self.assertEqual(result.returncode, 0, result.stderr)
        dns = (root / 'snippets/ai-dns.conf').read_text()
        rules = (root / 'rules/ai.list').read_text()
        self.assertIn('/example.com/', dns)
        self.assertIn('/*.example.com/', dns)
        self.assertIn('/login.other.net/', dns)
        self.assertNotIn('/*.login.other.net/', dns)
        self.assertNotIn('disabled.net', dns + rules)
        self.assertIn('host-suffix, example.com, proxy', rules)
        self.assertIn('host, login.other.net, proxy', rules)

    def test_policy_is_configurable_without_changing_rule_list(self):
        root, result = self.run_generator({'policy_name': '工作AI', 'node_filter': '日本|美国'})
        self.assertEqual(result.returncode, 0, result.stderr)
        profile = (root / 'qx.conf').read_text()
        self.assertIn('static = 工作AI, proxy, server-tag-regex=日本|美国', profile)
        self.assertIn('force-policy=工作AI', profile)
        self.assertNotIn('美国住宅', profile)
        self.assertIn('server = 223.5.5.5', profile)
        self.assertNotIn('token=', profile)

    def test_global_dns_replaces_domestic_default(self):
        root, result = self.run_generator({'dns': {'mode': 'global',
            'default_servers': ['223.5.5.5'], 'ai_doh': 'https://1.1.1.1/dns-query'}})
        self.assertEqual(result.returncode, 0, result.stderr)
        profile = (root / 'qx.conf').read_text()
        self.assertIn('doh-server = https://1.1.1.1/dns-query', profile)
        self.assertNotIn('server = 223.5.5.5', profile)

    def test_rejects_config_injection_before_writing(self):
        root, result = self.run_generator({'policy_name': 'AI\n[server_remote]'})
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((root / 'qx.conf').exists())

    def test_domain_validation_and_stable_output(self):
        root, result = self.run_generator(domains=[{'type': 'suffix', 'domain': 'bad, direct', 'enabled': True}])
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((root / 'rules/ai.list').exists())
        root, result = self.run_generator()
        self.assertEqual(result.returncode, 0, result.stderr)
        before = (root / 'qx.conf').read_bytes()
        subprocess.run([sys.executable, str(GENERATOR), '--root', str(root)], check=True, capture_output=True)
        self.assertEqual(before, (root / 'qx.conf').read_bytes())

if __name__ == '__main__':
    unittest.main()

import importlib.util
from contextlib import closing
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest import mock

MODULE_PATH = Path(__file__).resolve().parents[2] / 'plugins/macros/skills/dredge/scripts/agy_live_export.py'
spec = importlib.util.spec_from_file_location('agy_live_export', MODULE_PATH)
exporter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(exporter)

FAKE_READER = '''#!/usr/bin/env python3
import json,sqlite3,sys
from pathlib import Path
p=Path(sys.argv[-1]); db=sqlite3.connect(p)
value=db.execute('select value from fixture').fetchone()[0]
if value == 'refuse': sys.exit(2)
out=Path(next(x[6:] for x in sys.argv if x.startswith('--out=')))
out.write_text(json.dumps({'cascadeId':p.stem,'steps':[{'text':value}],'agyReader':{'offline':{'sourceDigest':value}}}))
'''


FAKE_SOURCE_READER = """#!/usr/bin/env python3
import json,sqlite3,sys
from pathlib import Path
p=Path(sys.argv[1]); db=sqlite3.connect(p)
value=db.execute('select value from fixture').fetchone()[0]
Path(sys.argv[2]).write_text(json.dumps({'cascadeId':p.stem,'steps':[{'text':value}],'sourceRecovery':{'sourceDigest':value,'omittedExecutors':0}}))
"""


class LiveExportTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.root = self.base / 'root'
        (self.root / 'conversations').mkdir(parents=True)
        self.output = self.base / 'output'
        self.reader = self.base / 'reader'
        self.reader.write_text(FAKE_READER)
        self.reader.chmod(0o700)
        self.ident = '00000000-0000-4000-8000-000000000001'
        self.db = self.root / 'conversations' / (self.ident + '.db')
        with closing(sqlite3.connect(self.db)) as con:
            con.execute('create table fixture(value text)')
            con.execute('insert into fixture values (?)', ('first',))
            con.commit()

    def set_value(self, value):
        with closing(sqlite3.connect(self.db)) as con:
            con.execute('update fixture set value=?', (value,))
            con.commit()

    def state(self):
        return json.loads((self.output / 'status.json').read_text())['sessions'][self.ident]

    def test_new_and_changed_sessions_refresh_atomically(self):
        self.assertEqual(exporter.sync(self.root, self.output, self.reader), 0)
        record = self.state()
        self.assertEqual(record['state'], 'ok')
        self.assertEqual(json.loads((self.output / (self.ident + '.json')).read_text())['steps'][0]['text'], 'first')
        with closing(sqlite3.connect(self.output / 'source' / self.db.name)) as backup:
            self.assertEqual(backup.execute('select value from fixture').fetchone()[0], 'first')
        self.assertEqual(exporter.sync(self.root, self.output, self.reader), 0)
        self.assertEqual(self.state(), record)
        self.set_value('second')
        self.assertEqual(exporter.sync(self.root, self.output, self.reader), 0)
        self.assertEqual(json.loads((self.output / (self.ident + '.json')).read_text())['steps'][0]['text'], 'second')
        self.assertEqual((self.output.stat().st_mode & 0o777), 0o700)
        self.assertEqual(((self.output / (self.ident + '.json')).stat().st_mode & 0o777), 0o600)

    def test_artifact_updates_are_preserved_without_database_changes(self):
        brain = self.root / 'brain' / self.ident
        brain.mkdir(parents=True)
        artifact = brain / 'output.txt'
        artifact.write_text('old output')
        self.assertEqual(exporter.sync(self.root, self.output, self.reader), 0)
        first = self.state()['artifacts']['output.txt']
        self.assertEqual((self.output / 'artifacts' / first).read_text(), 'old output')
        artifact.write_text('new output')
        self.assertEqual(exporter.sync(self.root, self.output, self.reader), 0)
        second = self.state()['artifacts']['output.txt']
        self.assertNotEqual(first, second)
        self.assertEqual((self.output / 'artifacts' / first).read_text(), 'old output')
        self.assertEqual((self.output / 'artifacts' / second).read_text(), 'new output')

    def test_refusal_preserves_raw_backup_and_marks_old_export_stale(self):
        self.assertEqual(exporter.sync(self.root, self.output, self.reader), 0)
        self.set_value('refuse')
        self.assertEqual(exporter.sync(self.root, self.output, self.reader), 1)
        self.assertEqual(self.state()['state'], 'raw_only')
        self.assertEqual(json.loads((self.output / (self.ident + '.json')).read_text())['steps'][0]['text'], 'first')
        with closing(sqlite3.connect(self.output / 'source' / self.db.name)) as backup:
            self.assertEqual(backup.execute('select value from fixture').fetchone()[0], 'refuse')
        self.set_value('recovered')
        self.assertEqual(exporter.sync(self.root, self.output, self.reader), 0)
        self.assertEqual(self.state()['state'], 'ok')

    def test_missing_reader_keeps_new_database(self):
        self.assertEqual(exporter.sync(self.root, self.output, self.base / 'missing'), 1)
        self.assertEqual(self.state()['state'], 'raw_only')
        self.assertTrue((self.output / 'source' / self.db.name).exists())

    def test_source_fallback_keeps_unrenderable_session_searchable(self):
        fallback = self.base / 'source-reader'
        fallback.write_text(FAKE_SOURCE_READER)
        fallback.chmod(0o700)
        self.set_value('refuse')
        self.assertEqual(exporter.sync(self.root, self.output, self.reader, fallback), 0)
        self.assertEqual(self.state()['state'], 'source_only')
        self.assertEqual(json.loads((self.output / (self.ident + '.json')).read_text())['steps'][0]['text'], 'refuse')
        prior = self.state()
        self.assertEqual(exporter.sync(self.root, self.output, self.reader, fallback), 0)
        self.assertEqual(self.state(), prior)

    def test_reader_timeout_preserves_raw_backup(self):
        with mock.patch.object(exporter.subprocess, 'run', side_effect=exporter.subprocess.TimeoutExpired('reader', 60)):
            self.assertEqual(exporter.sync(self.root, self.output, self.reader), 1)
        self.assertEqual(self.state()['state'], 'raw_only')
        self.assertEqual(self.state()['reason'], 'offline decoder timed out')
        self.assertTrue((self.output / 'source' / self.db.name).exists())

    def test_source_changed_during_export_is_not_marked_current(self):
        original = exporter.subprocess.run
        def racing(*args, **kwargs):
            result = original(*args, **kwargs)
            self.set_value('changed during capture')
            return result
        with mock.patch.object(exporter.subprocess, 'run', side_effect=racing):
            self.assertEqual(exporter.sync(self.root, self.output, self.reader), 1)
        self.assertEqual(self.state()['state'], 'stale')
        self.assertEqual(self.state()['format'], 'ok')
        self.assertEqual(json.loads((self.output / (self.ident + '.json')).read_text())['steps'][0]['text'], 'first')
        with closing(sqlite3.connect(self.output / 'source' / self.db.name)) as backup:
            self.assertEqual(backup.execute('select value from fixture').fetchone()[0], 'first')


if __name__ == '__main__':
    unittest.main()

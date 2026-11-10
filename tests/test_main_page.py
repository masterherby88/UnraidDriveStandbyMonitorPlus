#!/usr/bin/env python3
"""Render the Main page with a temporary SQLite DB: no Unraid host required.

Requires Python 3 and PHP with SQLite3; set PHP_BIN and PHP_EXTRA_ARGS if needed.
"""
import json
import os
from pathlib import Path
import shlex
import shutil
import sqlite3
import subprocess
import tempfile
import time
import unittest
from html.parser import HTMLParser

REPO = Path(__file__).resolve().parents[1]
SOURCE = REPO / 'src/usr/local/emhttp/plugins/DriveStandbyMonitor'
PHP = [os.environ.get('PHP_BIN', 'php'), '-n', '-d', 'short_open_tag=1']
PHP += shlex.split(os.environ.get('PHP_EXTRA_ARGS', ''))


class TableParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tables = []
        self.rows = []
        self.cells = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'table':
            self.tables.append(attrs)
        elif tag == 'tr':
            self.rows.append(attrs)
        elif tag == 'td':
            self.cells.append(attrs)


class MainPageTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        plugin = self.root / 'plugins/DriveStandbyMonitor'
        plugin.mkdir(parents=True)
        shutil.copytree(SOURCE / 'includes', plugin / 'includes')
        page = (SOURCE / 'StandbyAveragesMain.page').read_text().split('---\n', 1)[1]
        (plugin / 'Main.php').write_text(page)
        (self.root / 'state').mkdir()
        (self.root / 'state/devs.ini').write_text('')
        (self.root / 'state/disks.ini').write_text('''[parity]
id="WDC_TEST_PARITY"
name="parity"
device="sdc"
type="Parity"
transport="sata"
rotational="1"
spundown="0"
[disk1]
id="WDC_TEST_DISK1"
name="disk1"
device="sdf"
type="Data"
transport="sata"
rotational="1"
spundown="0"
''')
        self.db_path = self.root / 'monitor.db'
        (plugin / 'default.cfg').write_text(f'DB_LOCATION="{self.db_path}"\nAVG_WINDOW_DAYS=30\n')
        self.db = sqlite3.connect(self.db_path)
        self.addCleanup(self.db.close)
        self.db.execute('CREATE TABLE standby (id INTEGER PRIMARY KEY AUTOINCREMENT, drive VARCHAR(32), state INTEGER, date INTEGER)')
        now = int(time.time())
        for drive, states in [('WDC_TEST_PARITY', [0, 1, 0]), ('WDC_TEST_DISK1', [0, 0, 1])]:
            for i, state in enumerate(states):
                self.db.execute('INSERT INTO standby (drive,state,date) VALUES (?,?,?)', (drive, state, now - 1800 + i * 300))
        self.db.commit()

    def render(self, cookies=None):
        payload = json.dumps(cookies or {}, separators=(',', ':'))
        bootstrap = '''<?php
$docroot = __DIR__; chdir($docroot);
function autov($url) { echo $url; }
$_COOKIE = json_decode('%s', true);
include 'plugins/DriveStandbyMonitor/Main.php';
''' % payload
        (self.root / 'render.php').write_text(bootstrap)
        result = subprocess.run(PHP + [str(self.root / 'render.php')], capture_output=True, text=True, check=True)
        self.assertNotIn('Warning:', result.stdout + result.stderr)
        self.assertNotIn('Fatal error:', result.stdout + result.stderr)
        parser = TableParser()
        parser.feed(result.stdout)
        return result.stdout, parser

    def test_table_markup_and_metrics(self):
        html, parsed = self.render()
        table = parsed.tables[0]['class'].split()
        self.assertIn('unraid', table)
        self.assertIn('standby-status', table)
        self.assertNotIn('disk_status', table)  # Disk Activity must not inject a column.
        self.assertEqual(html.count('66.67%'), 2)
        self.assertEqual(len([r for r in parsed.rows if 'standby-drive' in r]), 2)
        self.assertIn('Spinups (max/day)', html)
        self.assertIn('class="TableContainer"', html)

    def test_selection_cookies_are_preserved(self):
        _, parsed = self.render({'standby-selected-WDC_TEST_PARITY': 'false', 'standby-selected-WDC_TEST_DISK1': 'true'})
        rows = {r['standby-drive']: r for r in parsed.rows if 'standby-drive' in r}
        self.assertIn('hidden', rows['WDC_TEST_PARITY']['class'].split())
        self.assertNotIn('hidden', rows['WDC_TEST_DISK1']['class'].split())

    def test_tools_filter_and_empty_state(self):
        config = self.root / 'plugins/DriveStandbyMonitor/default.cfg'
        config.write_text(config.read_text() + 'MAIN_VISIBLE_DRIVES="WDC_TEST_PARITY"\n')
        _, parsed = self.render()
        self.assertEqual([r['standby-drive'] for r in parsed.rows if 'standby-drive' in r], ['WDC_TEST_PARITY'])
        self.db.execute('DELETE FROM standby')
        self.db.commit()
        html, parsed = self.render()
        self.assertIn('No data has been collected yet', html)
        self.assertEqual([c.get('colspan') for c in parsed.cells if c.get('class') == 'standby-empty'], ['6'])


if __name__ == '__main__':
    unittest.main()

import csv
from datetime import date, timedelta
import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('generate', ROOT / 'scripts/generate.py')
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)

class CalendarTests(unittest.TestCase):
    def test_two_year_schedule(self):
        rows = [{'event_id': f'test-{i}@example.com', 'date': (gen.START + timedelta(weeks=i)).isoformat(), 'collection': 'General waste' if i % 2 == 0 else 'Recycling'} for i in range(105)]
        self.assertEqual(len(rows), 105)
        self.assertEqual(rows[0]['date'], '2026-10-21')
        self.assertEqual(rows[-1]['date'], '2028-10-18')
        for i, row in enumerate(rows):
            self.assertEqual(date.fromisoformat(row['date']), gen.START + timedelta(weeks=i))
            self.assertEqual(row['collection'], 'General waste' if i % 2 == 0 else 'Recycling')
        data = gen.calendar(rows, '20261017T000000Z')
        self.assertEqual(data.count(b'BEGIN:VEVENT\r\n'), 105)
        self.assertIn(b'DTSTART;VALUE=DATE:20261021\r\nDTEND;VALUE=DATE:20261022', data)
        self.assertNotIn(b'\n', data.replace(b'\r\n', b''))
        self.assertTrue(all(len(line) <= 75 for line in data.split(b'\r\n')))

    def test_published_csv(self):
        rows = gen.load_events(ROOT / 'collections.csv')
        data = gen.calendar(rows, '20261017T000000Z')
        self.assertEqual(data.count(b'BEGIN:VEVENT\r\n'), len(rows))
        self.assertEqual(len(rows), 105)
        for event in data.split(b'BEGIN:VEVENT\r\n')[1:]:
            self.assertEqual(event.count(b'BEGIN:VALARM\r\n'), 1)
            self.assertIn(b'ACTION:DISPLAY\r\nTRIGGER:-P1D\r\n', event)
            self.assertIn(b'END:VALARM\r\nEND:VEVENT', event)

    def test_exception_preserves_uid(self):
        rows = gen.load_events(ROOT / 'collections.csv')
        uid = rows[0]['event_id']
        rows[0]['date'] = '2026-10-22'
        data = gen.calendar(rows, '20261017T000000Z').decode()
        self.assertIn('UID:' + uid, data)
        self.assertIn('DTSTART;VALUE=DATE:20261022', data)

    def test_duplicate_ids_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'bad.csv'
            path.write_text('event_id,date,collection\nx,2026-10-21,General waste\nx,2026-10-28,Recycling\n')
            with self.assertRaisesRegex(ValueError, 'Duplicate'):
                gen.load_events(path)

if __name__ == '__main__':
    unittest.main()

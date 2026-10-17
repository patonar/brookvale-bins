#!/usr/bin/env python3
"""Generate a static site and RFC 5545 feed from the editable collection CSV."""
import argparse
import csv
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
START = date(2026, 10, 21)
END = date(2028, 10, 21)  # exclusive; two calendar years


def load_events(path):
    with Path(path).open(newline='', encoding='utf-8') as source:
        reader = csv.DictReader(source)
        if reader.fieldnames != ['event_id', 'date', 'collection']:
            raise ValueError('CSV columns must be event_id,date,collection')
        rows = list(reader)
    seen = set()
    for row in rows:
        uid = row['event_id']
        if not uid or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_.@' for c in uid):
            raise ValueError('Invalid event_id')
        if uid in seen:
            raise ValueError(f'Duplicate event_id: {uid}')
        seen.add(uid)
        date.fromisoformat(row['date'])
        if row['collection'] not in ('General waste', 'Recycling'):
            raise ValueError('Collection must be General waste or Recycling')
    if not rows:
        raise ValueError('CSV must contain events')
    return sorted(rows, key=lambda row: (row['date'], row['event_id']))


def escape(value):
    return value.replace('\\', '\\\\').replace('\n', '\\n').replace(';', '\\;').replace(',', '\\,')


def fold(line):
    # RFC 5545: physical lines are at most 75 octets, including continuation space.
    parts, current = [], ''
    for char in line:
        if len((current + char).encode('utf-8')) > 75:
            parts.append(current)
            current = ' '
        current += char
    return '\r\n'.join(parts + [current])


def calendar(rows, stamp):
    lines = ['BEGIN:VCALENDAR', 'VERSION:2.0', 'PRODID:-//Brookvale Bins//Collection Calendar//EN',
             'CALSCALE:GREGORIAN', 'METHOD:PUBLISH', 'X-WR-CALNAME:Brookvale Bins',
             'X-WR-CALDESC:Alternating weekly general waste and recycling collections.',
             'REFRESH-INTERVAL;VALUE=DURATION:PT12H', 'X-PUBLISHED-TTL:PT12H']
    for row in rows:
        day = date.fromisoformat(row['date'])
        lines += ['BEGIN:VEVENT', f"UID:{row['event_id']}", f'DTSTAMP:{stamp}',
                  f'LAST-MODIFIED:{stamp}', f'DTSTART;VALUE=DATE:{day:%Y%m%d}',
                  f'DTEND;VALUE=DATE:{day + timedelta(days=1):%Y%m%d}',
                  'SUMMARY:' + escape('Brookvale Bins — ' + row['collection']),
                  'DESCRIPTION:' + escape(row['collection'] + ' collection. Dates may change; subscribe for updates.'),
                  'STATUS:CONFIRMED', 'TRANSP:TRANSPARENT', 'END:VEVENT']
    return ('\r\n'.join(fold(line) for line in lines + ['END:VCALENDAR']) + '\r\n').encode('utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--csv', type=Path, default=ROOT / 'collections.csv')
    parser.add_argument('--output', type=Path, default=ROOT / '_site')
    args = parser.parse_args()
    rows = load_events(args.csv)
    args.output.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    (args.output / 'brookvale-bins.ics').write_bytes(calendar(rows, stamp))
    shutil.copyfile(ROOT / 'index.html', args.output / 'index.html')
    shutil.copyfile(args.csv, args.output / 'collections.csv')
    (args.output / '.nojekyll').touch()
    print(f'Generated {len(rows)} all-day events: {rows[0]["date"]} to {rows[-1]["date"]}')


if __name__ == '__main__':
    main()

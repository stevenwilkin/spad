#!/usr/bin/env python3
"""Extract daily entries from Spiritual-Principal-A-Day.pdf into spad.db."""

import re
import sqlite3
import subprocess
import sys

PDF_PATH = 'Spiritual-Principal-A-Day.pdf'
DB_PATH = 'spad.db'

MONTHS = [
    'JANUARY', 'FEBRUARY', 'MARCH', 'APRIL', 'MAY', 'JUNE',
    'JULY', 'AUGUST', 'SEPTEMBER', 'OCTOBER', 'NOVEMBER', 'DECEMBER',
]
MONTH_NUM = {m: i + 1 for i, m in enumerate(MONTHS)}

DATE_RE = re.compile(
    r'^(\d{1,2}) (' + '|'.join(MONTHS) + r')$',
    re.MULTILINE,
)

MONTH_PAGE_RE = re.compile(
    r'^(' + '|'.join(MONTHS) + r')$',
    re.MULTILINE,
)

FOOTER_RE = re.compile(
    r'^(©\d{4} NA World Services.*'
    r'|To purchase paper copies.*'
    r'|To download e-copies.*'
    r'|A Spiritual Principle a Day.*'
    r'|for Decision at Interim WSC.*'
    r'|for Decision @ Interim.*'
    r'|\d+)$',
    re.MULTILINE,
)


def extract_pdf_text():
    result = subprocess.run(
        ['pdftotext', PDF_PATH, '-'],
        capture_output=True, text=True, check=True,
    )
    return result.stdout


def clean_text(text):
    text = text.replace('\f', '\n')
    # Drop the glossary and everything after it
    glossary_pos = text.find('List of Principles, Titles, and Dates')
    if glossary_pos != -1:
        text = text[:glossary_pos]
    text = FOOTER_RE.sub('', text)
    text = MONTH_PAGE_RE.sub('', text)
    # Collapse runs of 3+ blank lines to 2
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text


def parse_first_paragraph(lines):
    """Return (title, quote, quote_source) from the lines of the first paragraph."""
    if not lines:
        return None, None, None

    title = lines[0].strip()

    quote_lines = []
    quote_source = None
    for line in lines[1:]:
        if line.startswith('\u2014') or line.startswith('—'):
            quote_source = line.lstrip('\u2014—').strip()
            break
        quote_lines.append(line.strip())

    quote = ' '.join(quote_lines).strip() or None
    return title or None, quote, quote_source


def parse_entry(day, month_num, content):
    paragraphs = [p.strip() for p in re.split(r'\n\n+', content.strip())]
    paragraphs = [p for p in paragraphs if p]

    if not paragraphs:
        return (month_num, day, None, None, None, None, None)

    title, quote, quote_source = parse_first_paragraph(paragraphs[0].split('\n'))

    body_paras = paragraphs[1:]
    if len(body_paras) == 0:
        body, closing = None, None
    elif len(body_paras) == 1:
        body, closing = None, body_paras[0]
    else:
        closing = body_paras[-1]
        body = '\n\n'.join(body_paras[:-1])

    return (month_num, day, title, quote, quote_source, body, closing)


def parse_all_entries(text):
    parts = DATE_RE.split(text)
    # parts = [pre-content, day1, month1, content1, day2, month2, content2, ...]
    entries = []
    i = 1
    while i + 2 < len(parts):
        day = int(parts[i])
        month_num = MONTH_NUM[parts[i + 1]]
        content = parts[i + 2]
        entries.append(parse_entry(day, month_num, content))
        i += 3
    return entries


def insert_entries(entries):
    con = sqlite3.connect(DB_PATH)
    con.executemany(
        'INSERT INTO entries (month, day, title, quote, quote_source, body, closing)'
        ' VALUES (?, ?, ?, ?, ?, ?, ?)',
        entries,
    )
    con.commit()
    con.close()


def main():
    print(f'Extracting text from {PDF_PATH}...')
    raw = extract_pdf_text()

    print('Cleaning and parsing...')
    text = clean_text(raw)
    entries = parse_all_entries(text)
    print(f'Found {len(entries)} entries')

    print(f'Inserting into {DB_PATH}...')
    insert_entries(entries)
    print('Done.')


if __name__ == '__main__':
    main()

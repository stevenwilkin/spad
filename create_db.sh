#!/bin/bash
set -e

DB=spad.db

if [ -f "$DB" ]; then
    echo "Removing existing $DB"
    rm "$DB"
fi

sqlite3 "$DB" <<'EOF'
CREATE TABLE entries (
    id           INTEGER PRIMARY KEY,
    month        INTEGER NOT NULL,
    day          INTEGER NOT NULL,
    title        TEXT,
    quote        TEXT,
    quote_source TEXT,
    body         TEXT,
    closing      TEXT
);
EOF

echo "Created $DB"

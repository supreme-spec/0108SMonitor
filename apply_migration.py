#!/usr/bin/env python3
"""Apply Prisma migration to dev.db"""
import sqlite3
import os

db_path = "prisma/dev.db"
migration_path = "prisma/migrations/20260804000000_archive_and_policies/migration.sql"

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Read and execute migration
with open(migration_path, 'r', encoding='utf-8') as f:
    sql = f.read()
    cursor.executescript(sql)

conn.commit()

# Verify tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [r[0] for r in cursor.fetchall()]
print("Tables after migration:", sorted(tables))

conn.close()

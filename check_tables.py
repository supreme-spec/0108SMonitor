#!/usr/bin/env python3
"""Check new tables structure"""
import sqlite3
import json

conn = sqlite3.connect("prisma/dev.db")
cursor = conn.cursor()

new_tables = [
    "PersonPolicy", "Episode", "EpisodePerson", "ArchivePhoto",
    "ArchiveFace", "FaceCluster", "ClusteringLog", "ProcessingProfile"
]

for table in new_tables:
    cursor.execute(f"PRAGMA table_info({table})")
    columns = [(r[1], r[2]) for r in cursor.fetchall()]
    print(f"{table}: {columns}")

conn.close()

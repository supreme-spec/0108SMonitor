#!/usr/bin/env python3
import sqlite3

conn = sqlite3.connect("prisma/dev.db")
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = sorted([r[0] for r in cursor.fetchall()])

print("Tables:", tables)

new_tables = ["PersonPolicy", "Episode", "EpisodePerson", "ArchivePhoto", "ArchiveFace", "FaceCluster", "ClusteringLog", "ProcessingProfile"]
missing = [t for t in new_tables if t not in tables]

if missing:
    print(f"\nMissing archive tables: {missing}")
    print("\nYou need to run the archive migration first.")
else:
    print("\nAll archive tables present!")

conn.close()

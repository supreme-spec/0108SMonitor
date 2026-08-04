#!/usr/bin/env python3
"""Apply archive migration to dev.db"""
import sqlite3

db_path = "prisma/dev.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Create archive tables
sql = """
-- PersonPolicy table
CREATE TABLE IF NOT EXISTS PersonPolicy (
  id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
  person_id INTEGER NOT NULL,
  zone_id INTEGER,
  zone_name TEXT,
  schedule_type TEXT NOT NULL DEFAULT 'default',
  start_time TEXT,
  end_time TEXT,
  role TEXT NOT NULL DEFAULT 'unknown',
  confidence REAL NOT NULL DEFAULT 0.5,
  label_source TEXT NOT NULL DEFAULT 'operator',
  created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%d %H:%M:%f', 'now')),
  updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%d %H:%M:%f', 'now')),
  comment TEXT,
  FOREIGN KEY(person_id) REFERENCES Person(id) ON DELETE CASCADE
);

-- Episode table
CREATE TABLE IF NOT EXISTS Episode (
  id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
  folder_path TEXT NOT NULL UNIQUE,
  episode_name TEXT NOT NULL,
  source_type TEXT NOT NULL DEFAULT 'camera',
  capture_time TEXT,
  camera_id INTEGER,
  camera_name TEXT,
  total_photos INTEGER NOT NULL DEFAULT 0,
  processed_at TEXT,
  status TEXT NOT NULL DEFAULT 'pending',
  error_message TEXT,
  created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%d %H:%M:%f', 'now'))
);

-- EpisodePerson table
CREATE TABLE IF NOT EXISTS EpisodePerson (
  id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
  episode_id INTEGER NOT NULL,
  person_id INTEGER,
  person_name TEXT,
  role TEXT NOT NULL DEFAULT 'unknown',
  confidence REAL NOT NULL DEFAULT 0.5,
  label_source TEXT NOT NULL DEFAULT 'operator',
  cluster_id TEXT,
  is_merge_hint INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%d %H:%M:%f', 'now')),
  updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%d %H:%M:%f', 'now')),
  FOREIGN KEY(episode_id) REFERENCES Episode(id) ON DELETE CASCADE,
  FOREIGN KEY(person_id) REFERENCES Person(id) ON DELETE SET NULL
);

-- ArchivePhoto table
CREATE TABLE IF NOT EXISTS ArchivePhoto (
  id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
  episode_id INTEGER NOT NULL,
  photo_path TEXT NOT NULL,
  filename TEXT NOT NULL,
  width INTEGER,
  height INTEGER,
  source_width INTEGER,
  source_height INTEGER,
  source_type TEXT,
  osd_text TEXT,
  quality_score REAL,
  tier TEXT,
  profile TEXT,
  processed_at TEXT,
  status TEXT NOT NULL DEFAULT 'pending',
  created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%d %H:%M:%f', 'now')),
  FOREIGN KEY(episode_id) REFERENCES Episode(id) ON DELETE CASCADE
);

-- ArchiveFace table
CREATE TABLE IF NOT EXISTS ArchiveFace (
  id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
  photo_id INTEGER NOT NULL,
  episode_person_id INTEGER,
  cluster_id INTEGER,
  bbox_x REAL NOT NULL,
  bbox_y REAL NOT NULL,
  bbox_w REAL NOT NULL,
  bbox_h REAL NOT NULL,
  det_score REAL,
  kps TEXT,
  pitch_deg REAL,
  yaw_deg REAL,
  blur_score REAL,
  brightness REAL,
  occlusion REAL,
  quality_score REAL,
  tier TEXT,
  embedding TEXT,
  embedding_model TEXT,
  status TEXT NOT NULL DEFAULT 'detected',
  reject_reason TEXT,
  created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%d %H:%M:%f', 'now')),
  processed_at TEXT,
  FOREIGN KEY(photo_id) REFERENCES ArchivePhoto(id) ON DELETE CASCADE,
  FOREIGN KEY(episode_person_id) REFERENCES EpisodePerson(id) ON DELETE SET NULL,
  FOREIGN KEY(cluster_id) REFERENCES FaceCluster(id) ON DELETE SET NULL
);

-- FaceCluster table
CREATE TABLE IF NOT EXISTS FaceCluster (
  id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
  episode_id INTEGER NOT NULL,
  cluster_id TEXT NOT NULL,
  face_count INTEGER NOT NULL DEFAULT 1,
  avg_quality REAL,
  representative_photo_id INTEGER,
  created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%d %H:%M:%f', 'now')),
  updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%d %H:%M:%f', 'now')),
  FOREIGN KEY(episode_id) REFERENCES Episode(id) ON DELETE CASCADE
);

-- ClusteringLog table
CREATE TABLE IF NOT EXISTS ClusteringLog (
  id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
  episode_id INTEGER NOT NULL,
  cluster_id TEXT NOT NULL,
  action TEXT NOT NULL,
  person_id INTEGER,
  from_cluster_id TEXT,
  to_cluster_id TEXT,
  confidence REAL,
  updated_by TEXT,
  timestamp TEXT NOT NULL DEFAULT (strftime('%Y-%m-%d %H:%M:%f', 'now')),
  FOREIGN KEY(episode_id) REFERENCES Episode(id) ON DELETE CASCADE
);

-- ProcessingProfile table
CREATE TABLE IF NOT EXISTS ProcessingProfile (
  name TEXT PRIMARY KEY NOT NULL,
  description TEXT NOT NULL,
  detector TEXT NOT NULL DEFAULT 'scrfd',
  recognizer TEXT NOT NULL DEFAULT 'arcface',
  min_face_size INTEGER NOT NULL DEFAULT 60,
  min_det_score REAL NOT NULL DEFAULT 0.5,
  pose_pitch_max REAL NOT NULL DEFAULT 35.0,
  pose_yaw_max REAL NOT NULL DEFAULT 35.0,
  quality_tier_a REAL NOT NULL DEFAULT 0.7,
  quality_tier_b REAL NOT NULL DEFAULT 0.4,
  similarity_intra REAL NOT NULL DEFAULT 0.55,
  similarity_cross REAL NOT NULL DEFAULT 0.45,
  use_multitemplate INTEGER NOT NULL DEFAULT 1,
  use_bw_twin INTEGER NOT NULL DEFAULT 1,
  created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%d %H:%M:%f', 'now')),
  updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%d %H:%M:%f', 'now'))
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_PersonPolicy_person_id ON PersonPolicy(person_id);
CREATE INDEX IF NOT EXISTS idx_PersonPolicy_zone_id ON PersonPolicy(zone_id);
CREATE INDEX IF NOT EXISTS idx_PersonPolicy_role ON PersonPolicy(role);
CREATE INDEX IF NOT EXISTS idx_Episode_folder_path ON Episode(folder_path);
CREATE INDEX IF NOT EXISTS idx_Episode_status ON Episode(status);
CREATE INDEX IF NOT EXISTS idx_EpisodePerson_episode_id ON EpisodePerson(episode_id);
CREATE INDEX IF NOT EXISTS idx_EpisodePerson_person_id ON EpisodePerson(person_id);
CREATE INDEX IF NOT EXISTS idx_EpisodePerson_role ON EpisodePerson(role);
CREATE INDEX IF NOT EXISTS idx_ArchivePhoto_episode_id ON ArchivePhoto(episode_id);
CREATE INDEX IF NOT EXISTS idx_ArchivePhoto_processed_at ON ArchivePhoto(processed_at);
CREATE INDEX IF NOT EXISTS idx_ArchiveFace_photo_id ON ArchiveFace(photo_id);
CREATE INDEX IF NOT EXISTS idx_ArchiveFace_episode_person_id ON ArchiveFace(episode_person_id);
CREATE INDEX IF NOT EXISTS idx_ArchiveFace_cluster_id ON ArchiveFace(cluster_id);
CREATE INDEX IF NOT EXISTS idx_ArchiveFace_tier ON ArchiveFace(tier);
CREATE INDEX IF NOT EXISTS idx_ArchiveFace_status ON ArchiveFace(status);
CREATE INDEX IF NOT EXISTS idx_FaceCluster_episode_id_cluster_id ON FaceCluster(episode_id, cluster_id);
CREATE INDEX IF NOT EXISTS idx_ClusteringLog_episode_id_cluster_id ON ClusteringLog(episode_id, cluster_id);
CREATE INDEX IF NOT EXISTS idx_ClusteringLog_timestamp ON ClusteringLog(timestamp);
"""

cursor.executescript(sql)
conn.commit()

# Verify
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = sorted([r[0] for r in cursor.fetchall()])
print("Tables after migration:", tables)

conn.close()
print("\nArchive migration applied successfully!")

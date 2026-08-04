-- Add Guest table for unknown persons
CREATE TABLE "Guest" (
  "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
  "name" TEXT NOT NULL DEFAULT 'Неизвестный',
  "photo_path" TEXT,
  "is_active" INTEGER NOT NULL DEFAULT 1,
  "created_at" TEXT NOT NULL DEFAULT (strftime('%Y-%m-%d %H:%M:%f', 'now')),
  "last_seen_at" TEXT,
  "visit_count" INTEGER NOT NULL DEFAULT 0,
  "confidence" REAL,
  "camera_id" INTEGER,
  "camera_name" TEXT
);
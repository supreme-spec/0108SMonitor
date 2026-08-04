-- Prisma Init Migration

-- Create Camera table
CREATE TABLE "Camera" (
  "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
  "name" TEXT NOT NULL,
  "source" TEXT NOT NULL,
  "camera_type" TEXT NOT NULL DEFAULT 'USB',
  "zone" TEXT,
  "is_active" INTEGER NOT NULL DEFAULT 1,
  "created_at" TEXT NOT NULL DEFAULT (strftime('%Y-%m-%d %H:%M:%f', 'now')),
  "status" TEXT NOT NULL DEFAULT 'offline',
  "roi_zones" TEXT,
  "fps" INTEGER NOT NULL DEFAULT 25,
  "ping_ms" INTEGER NOT NULL DEFAULT 0,
  "is_smart_recording" INTEGER NOT NULL DEFAULT 0,
  "is_chronicle" INTEGER NOT NULL DEFAULT 1,
  "driver_type" TEXT,
  "ip_address" TEXT,
  "ip_port" INTEGER,
  "username" TEXT,
  "password" TEXT,
  "use_camera_analytics" INTEGER NOT NULL DEFAULT 0,
  "enabled_modules" TEXT NOT NULL DEFAULT 'face',
  "motion_threshold" REAL DEFAULT 0.62,
  "motion_zones" TEXT,
  "lpr_enabled" INTEGER NOT NULL DEFAULT 0,
  "lpr_regions" TEXT,
  "exclusion_zones" TEXT,
  "webhookSecret" TEXT
);

-- Create Category table
CREATE TABLE "Category" (
  "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
  "code" TEXT NOT NULL UNIQUE,
  "label" TEXT NOT NULL,
  "color" TEXT NOT NULL,
  "bg_color" TEXT NOT NULL,
  "is_alert" INTEGER NOT NULL DEFAULT 0,
  "alert_sound" TEXT NOT NULL DEFAULT 'off',
  "alert_volume" REAL NOT NULL DEFAULT 0.5,
  "detect_enabled" INTEGER NOT NULL DEFAULT 1,
  "sort_order" INTEGER NOT NULL DEFAULT 100,
  "is_system" INTEGER NOT NULL DEFAULT 0
);

-- Create Person table
CREATE TABLE "Person" (
  "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
  "name" TEXT NOT NULL,
  "category" TEXT NOT NULL,
  "position" TEXT,
  "comment" TEXT,
  "phone" TEXT,
  "email" TEXT,
  "birth_date" TEXT,
  "address" TEXT,
  "organization" TEXT,
  "extra_info" TEXT,
  "photo_path" TEXT,
  "is_active" INTEGER NOT NULL DEFAULT 1,
  "created_at" TEXT NOT NULL DEFAULT (strftime('%Y-%m-%d %H:%M:%f', 'now')),
  "last_seen_at" TEXT,
  "visit_count" INTEGER NOT NULL DEFAULT 0,
  "embedding_count" INTEGER NOT NULL DEFAULT 0
);

-- Create FaceDescriptor table
CREATE TABLE "FaceDescriptor" (
  "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
  "person_id" INTEGER NOT NULL,
  "photo_path" TEXT NOT NULL,
  "descriptor" TEXT NOT NULL,
  "created_at" TEXT NOT NULL DEFAULT (strftime('%Y-%m-%d %H:%M:%f', 'now')),
  FOREIGN KEY("person_id") REFERENCES "Person"("id") ON DELETE CASCADE
);

-- Create PersonPhoto table
CREATE TABLE "person_photos" (
  "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
  "person_id" INTEGER NOT NULL,
  "photo_path" TEXT NOT NULL,
  "is_primary" INTEGER NOT NULL DEFAULT 0,
  "has_embedding" INTEGER NOT NULL DEFAULT 0,
  "source" TEXT NOT NULL DEFAULT 'manual',
  "confidence" REAL,
  "created_at" TEXT NOT NULL DEFAULT (strftime('%Y-%m-%d %H:%M:%f', 'now')),
  FOREIGN KEY("person_id") REFERENCES "Person"("id") ON DELETE CASCADE
);

-- Create FaceConfirmation table
CREATE TABLE "face_confirmations" (
  "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
  "person_id" INTEGER NOT NULL,
  "confidence" REAL NOT NULL,
  "temp_photo_path" TEXT NOT NULL,
  "existing_photo_path" TEXT,
  "person_name" TEXT,
  "category" TEXT,
  "status" TEXT NOT NULL DEFAULT 'PENDING',
  "created_at" TEXT NOT NULL DEFAULT (strftime('%Y-%m-%d %H:%M:%f', 'now')),
  "confirmed_at" TEXT,
  "confirmed_by" TEXT,
  "rejected_reason" TEXT,
  FOREIGN KEY("person_id") REFERENCES "Person"("id") ON DELETE CASCADE
);

-- Create Event table
CREATE TABLE "Event" (
  "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
  "camera_id" INTEGER NOT NULL,
  "camera_name" TEXT NOT NULL,
  "person_id" INTEGER,
  "event_type" TEXT NOT NULL,
  "confidence" REAL NOT NULL,
  "snapshot_path" TEXT,
  "person_name" TEXT,
  "person_category" TEXT,
  "person_photo_path" TEXT,
  "created_at" TEXT NOT NULL DEFAULT (strftime('%Y-%m-%d %H:%M:%f', 'now')),
  "needs_operator_confirmation" INTEGER NOT NULL DEFAULT 0,
  "confirmation_status" TEXT,
  "confirmation_id" INTEGER,
  FOREIGN KEY("camera_id") REFERENCES "Camera"("id") ON DELETE CASCADE,
  FOREIGN KEY("person_id") REFERENCES "Person"("id") ON DELETE SET NULL
);

-- Create Recording table
CREATE TABLE "Recording" (
  "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
  "camera_id" INTEGER NOT NULL,
  "camera_name" TEXT NOT NULL,
  "start_time" TEXT NOT NULL,
  "end_time" TEXT NOT NULL,
  "duration" INTEGER NOT NULL,
  "size_mb" REAL NOT NULL,
  "video_path" TEXT NOT NULL,
  "is_favorite" INTEGER NOT NULL DEFAULT 0,
  FOREIGN KEY("camera_id") REFERENCES "Camera"("id") ON DELETE CASCADE
);

-- Create Incident table
CREATE TABLE "Incident" (
  "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
  "person_id" INTEGER NOT NULL,
  "incident_type" TEXT NOT NULL,
  "severity" TEXT NOT NULL,
  "comment" TEXT,
  "status" TEXT NOT NULL DEFAULT 'open',
  "created_at" TEXT NOT NULL DEFAULT (strftime('%Y-%m-%d %H:%M:%f', 'now')),
  FOREIGN KEY("person_id") REFERENCES "Person"("id") ON DELETE CASCADE
);

-- Create Tag table
CREATE TABLE "Tag" (
  "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
  "person_id" INTEGER NOT NULL,
  "tag" TEXT NOT NULL,
  FOREIGN KEY("person_id") REFERENCES "Person"("id") ON DELETE CASCADE
);

-- Create Settings table
CREATE TABLE "Settings" (
  "key" TEXT PRIMARY KEY NOT NULL,
  "value" TEXT NOT NULL
);

-- Create FaissUpdateLog table
CREATE TABLE "FaissUpdateLog" (
  "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
  "timestamp" TEXT NOT NULL DEFAULT (strftime('%Y-%m-%d %H:%M:%f', 'now')),
  "action" TEXT NOT NULL,
  "details" TEXT,
  "status" TEXT NOT NULL
);

-- Create indexes
CREATE INDEX "idx_FaceDescriptor_person_id" ON "FaceDescriptor"("person_id");
CREATE INDEX "idx_person_photos_person_id" ON "person_photos"("person_id");
CREATE INDEX "idx_face_confirmations_person_id" ON "face_confirmations"("person_id");
CREATE INDEX "idx_face_confirmations_status" ON "face_confirmations"("status");
CREATE INDEX "idx_Event_camera_id" ON "Event"("camera_id");
CREATE INDEX "idx_Event_person_id" ON "Event"("person_id");
CREATE INDEX "idx_Event_created_at" ON "Event"("created_at");
CREATE INDEX "idx_Event_confirmation_id" ON "Event"("confirmation_id");

-- Create _prisma_migrations table (if not exists)
CREATE TABLE IF NOT EXISTS "_prisma_migrations" (
  "id" TEXT PRIMARY KEY NOT NULL,
  "checksum" TEXT NOT NULL,
  "finished_at" TEXT,
  "migration_name" TEXT NOT NULL,
  "logs" TEXT,
  "rolled_back_at" TEXT,
  "started_at" TEXT NOT NULL DEFAULT (strftime('%Y-%m-%d %H:%M:%f', 'now')),
  "applied_steps_count" INTEGER UNSIGNED NOT NULL DEFAULT 0
);

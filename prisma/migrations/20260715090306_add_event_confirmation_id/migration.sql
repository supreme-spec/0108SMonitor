/*
  Warnings:

  - You are about to drop the `PersonPhoto` table. If the table is not empty, all the data it contains will be lost.

*/
-- AlterTable
ALTER TABLE "Event" ADD COLUMN "confirmation_id" INTEGER;

-- DropTable
PRAGMA foreign_keys=off;
DROP TABLE "PersonPhoto";
PRAGMA foreign_keys=on;

-- CreateTable
CREATE TABLE "person_photos" (
    "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    "person_id" INTEGER NOT NULL,
    "photo_path" TEXT NOT NULL,
    "is_primary" BOOLEAN NOT NULL DEFAULT false,
    "has_embedding" BOOLEAN NOT NULL DEFAULT false,
    "source" TEXT NOT NULL DEFAULT 'manual',
    "confidence" REAL,
    "created_at" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT "person_photos_person_id_fkey" FOREIGN KEY ("person_id") REFERENCES "Person" ("id") ON DELETE CASCADE ON UPDATE CASCADE
);

-- CreateTable
CREATE TABLE "face_confirmations" (
    "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    "person_id" INTEGER NOT NULL,
    "confidence" REAL NOT NULL,
    "temp_photo_path" TEXT NOT NULL,
    "existing_photo_path" TEXT,
    "person_name" TEXT,
    "category" TEXT,
    "status" TEXT NOT NULL DEFAULT 'PENDING',
    "created_at" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "confirmed_at" DATETIME,
    "confirmed_by" TEXT,
    "rejected_reason" TEXT,
    CONSTRAINT "face_confirmations_person_id_fkey" FOREIGN KEY ("person_id") REFERENCES "Person" ("id") ON DELETE CASCADE ON UPDATE CASCADE
);

-- CreateIndex
CREATE INDEX "person_photos_person_id_idx" ON "person_photos"("person_id");

-- CreateIndex
CREATE INDEX "face_confirmations_status_idx" ON "face_confirmations"("status");

-- CreateIndex
CREATE INDEX "face_confirmations_person_id_idx" ON "face_confirmations"("person_id");

-- CreateIndex
CREATE INDEX "Event_confirmation_id_idx" ON "Event"("confirmation_id");

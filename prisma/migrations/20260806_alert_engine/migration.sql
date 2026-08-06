ALTER TABLE "Event" ADD COLUMN "categoryCode" TEXT;
ALTER TABLE "Event" ADD COLUMN "alerted" BOOLEAN NOT NULL DEFAULT false;
ALTER TABLE "Event" ADD COLUMN "alertAcked" BOOLEAN NOT NULL DEFAULT false;
ALTER TABLE "Event" ADD COLUMN "alertAckAt" DATETIME;

-- Backfill categoryCode from person_category for existing events
UPDATE "Event" SET "categoryCode" = "person_category" WHERE "categoryCode" IS NULL AND "person_category" IS NOT NULL;

-- Enable alerts for NOT_TODAY and SUITE
UPDATE "Category" SET "is_alert" = 1, "alert_sound" = 'builtin', "alert_volume" = 0.6 WHERE "code" = 'NOT_TODAY';
UPDATE "Category" SET "is_alert" = 1, "alert_sound" = 'builtin', "alert_volume" = 0.7 WHERE "code" = 'SUITE';

-- Index for alert queries
CREATE INDEX "Event_alerted_alertAcked_idx" ON "Event"("alerted", "alertAcked");

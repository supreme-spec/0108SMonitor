-- Add guest_id column to Event
ALTER TABLE "Event" ADD COLUMN "guest_id" INTEGER REFERENCES "Guest"("id") ON DELETE CASCADE;

-- Add index for guest_id on Event
CREATE INDEX IF NOT EXISTS "idx_Event_guest_id" ON "Event" ("guest_id");

-- Add needsLoyaltyUpdate column to Person
ALTER TABLE "Person" ADD COLUMN "needsLoyaltyUpdate" INTEGER NOT NULL DEFAULT 0;

-- Add loyaltyIndex column to Person (Int type for background worker)
ALTER TABLE "Person" ADD COLUMN "loyaltyIndex" INTEGER NOT NULL DEFAULT 0;

-- Add index for needsLoyaltyUpdate on Person
CREATE INDEX IF NOT EXISTS "idx_Person_needsLoyaltyUpdate" ON "Person" ("needsLoyaltyUpdate");

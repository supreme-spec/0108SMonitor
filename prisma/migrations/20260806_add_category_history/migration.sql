-- CreateTable
CREATE TABLE "person_category_history" (
    "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    "person_id" INTEGER NOT NULL,
    "old_code" TEXT,
    "new_code" TEXT NOT NULL,
    "reason" TEXT,
    "changed_by" TEXT DEFAULT 'operator',
    "created_at" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY ("person_id") REFERENCES "Person"("id") ON DELETE CASCADE ON UPDATE CASCADE
);

-- CreateIndex
CREATE INDEX "person_category_history_person_id_idx" ON "person_category_history"("person_id");

-- CreateIndex
CREATE INDEX "person_category_history_created_at_idx" ON "person_category_history"("created_at");

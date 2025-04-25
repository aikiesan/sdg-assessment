-- Remove the obsolete 'score' column from sdg_scores
-- SQLite does not support DROP COLUMN directly before v3.35, so we recreate the table.

PRAGMA foreign_keys=off;

BEGIN TRANSACTION;

CREATE TABLE sdg_scores_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    assessment_id INTEGER NOT NULL,
    sdg_id INTEGER NOT NULL,
    notes TEXT,
    direct_score REAL,
    bonus_score REAL,
    total_score REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (assessment_id) REFERENCES assessments(id),
    FOREIGN KEY (sdg_id) REFERENCES sdg_goals(id)
);

INSERT INTO sdg_scores_new (id, assessment_id, sdg_id, notes, direct_score, bonus_score, total_score, created_at, updated_at)
SELECT id, assessment_id, sdg_id, notes, direct_score, bonus_score, total_score, created_at, updated_at FROM sdg_scores;

DROP TABLE sdg_scores;
ALTER TABLE sdg_scores_new RENAME TO sdg_scores;

COMMIT;

PRAGMA foreign_keys=on;

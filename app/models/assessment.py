"""
Assessment model.
Represents SDG assessments for architectural projects.
"""

from app import db
from datetime import datetime

class Assessment(db.Model):
    draft_data = db.Column(db.Text)  # Stores draft JSON data for assessments
    __tablename__ = 'assessments'

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    user_id = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(32), default='draft')
    overall_score = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    step1_completed = db.Column(db.Boolean, default=False)
    step2_completed = db.Column(db.Boolean, default=False)
    step3_completed = db.Column(db.Boolean, default=False)
    step4_completed = db.Column(db.Boolean, default=False)
    step5_completed = db.Column(db.Boolean, default=False)
    
    # New columns for expert assessment support
    raw_expert_data = db.Column(db.JSON)  # Stores the raw JSON data from expert assessment form
    assessment_type = db.Column(db.String(50), default='standard')  # 'standard' or 'expert'

    project = db.relationship('Project', back_populates='assessments')
    sdg_scores = db.relationship('SdgScore', back_populates='assessment', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Assessment {self.id} for Project {self.project_id}>'

        """Fetch assessment from database by ID."""
        conn = get_db()
        assessment_data = conn.execute('SELECT * FROM assessments WHERE id = ?',
                                      (assessment_id,)).fetchone()
        if assessment_data:
            return Assessment(
                id=assessment_data['id'],
                project_id=assessment_data['project_id'],
                user_id=assessment_data['user_id'],
                status=assessment_data['status'],
                overall_score=assessment_data['overall_score'],
                created_at=assessment_data['created_at'],
                updated_at=assessment_data['updated_at'],
                completed_at=assessment_data['completed_at'],
                step1_completed=assessment_data.get('step1_completed', 0),
                step2_completed=assessment_data.get('step2_completed', 0),
                step3_completed=assessment_data.get('step3_completed', 0),
                step4_completed=assessment_data.get('step4_completed', 0),
                step5_completed=assessment_data.get('step5_completed', 0)
            )
        return None

    @staticmethod
    def get_for_project(project_id):
        """Get all assessments for a specific project."""
        conn = get_db()
        assessments_data = conn.execute('''
            SELECT * FROM assessments
            WHERE project_id = ?
            ORDER BY created_at DESC
        ''', (project_id,)).fetchall()

        assessments = []
        for assessment_data in assessments_data:
            assessment = Assessment(
                id=assessment_data['id'],
                project_id=assessment_data['project_id'],
                user_id=assessment_data['user_id'],
                status=assessment_data['status'],
                overall_score=assessment_data['overall_score'],
                created_at=assessment_data['created_at'],
                updated_at=assessment_data['updated_at'],
                completed_at=assessment_data['completed_at'],
                step1_completed=assessment_data.get('step1_completed', 0),
                step2_completed=assessment_data.get('step2_completed', 0),
                step3_completed=assessment_data.get('step3_completed', 0),
                step4_completed=assessment_data.get('step4_completed', 0),
                step5_completed=assessment_data.get('step5_completed', 0)
            )
            assessments.append(assessment)
        return assessments

    def get_sdg_scores(self):
        """Get all SDG scores for this assessment."""
        if not self.id:
            return []

        conn = get_db()
        scores_data = conn.execute('''
            SELECT s.*, g.number, g.name, g.description, g.color_code
            FROM sdg_scores s
            JOIN sdg_goals g ON s.sdg_id = g.id
            WHERE s.assessment_id = ?
            ORDER BY g.number
        ''', (self.id,)).fetchall()

        # Convert row objects to dictionaries
        return [dict(score) for score in scores_data]

    def save(self):
        """Save the assessment to the database (create or update)."""
        conn = get_db()
        if self.id:
            # Update existing assessment
            conn.execute('''
                UPDATE assessments
                SET status = ?, overall_score = ?, updated_at = CURRENT_TIMESTAMP,
                    step1_completed = ?, step2_completed = ?, step3_completed = ?,
                    step4_completed = ?, step5_completed = ?
                WHERE id = ?
            ''', (self.status, self.overall_score,
                  self.step1_completed, self.step2_completed, self.step3_completed,
                  self.step4_completed, self.step5_completed, self.id))
            
            # If the status is being changed to completed, update the completed_at timestamp
            if self.status == 'completed':
                conn.execute('''
                    UPDATE assessments SET completed_at = ? WHERE id = ? AND completed_at IS NULL
                ''', (datetime.now(), self.id))
        else:
            # Create new assessment
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO assessments (project_id, user_id, status, created_at, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ''', (self.project_id, self.user_id, self.status))
            self.id = cursor.lastrowid
        
        conn.commit()
        return self

    def delete(self):
        """Delete the assessment and all its related data."""
        if not self.id:
            return False

        conn = get_db()
        # Delete related data
        conn.execute('DELETE FROM sdg_actions WHERE assessment_id = ?', (self.id,))
        conn.execute('DELETE FROM sdg_scores WHERE assessment_id = ?', (self.id,))
        conn.execute('DELETE FROM question_responses WHERE assessment_id = ?', (self.id,))
        
        # Delete the assessment
        conn.execute('DELETE FROM assessments WHERE id = ?', (self.id,))
        conn.commit()
        return True

    def update_overall_score(self):
        """Calculate and update the overall score based on SDG scores."""
        if not self.id:
            return False

        conn = get_db()
        scores = conn.execute(
            'SELECT score FROM sdg_scores WHERE assessment_id = ?',
            (self.id,)
        ).fetchall()

        valid_scores = [score['score'] for score in scores if score['score'] is not None]
        overall_score = sum(valid_scores) / len(valid_scores) if valid_scores else 0

        # Update the assessment
        conn.execute(
            'UPDATE assessments SET overall_score = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
            (overall_score, self.id)
        )
        
        conn.commit()
        self.overall_score = overall_score
        return True

    def finalize(self):
        """Mark the assessment as completed."""
        if not self.id:
            return False

        self.status = 'completed'
        self.completed_at = datetime.now()
        self.update_overall_score()

        conn = get_db()
        conn.execute(
            'UPDATE assessments SET status = ?, completed_at = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
            (self.status, self.completed_at, self.id)
        )
        
        conn.commit()
        return True

class SdgScore(db.Model):
    __tablename__ = 'sdg_scores'

    id = db.Column(db.Integer, primary_key=True)
    assessment_id = db.Column(db.Integer, db.ForeignKey('assessments.id'), nullable=False)
    sdg_id = db.Column(db.Integer, db.ForeignKey('sdg_goals.id'), nullable=False)
    direct_score = db.Column(db.Float)  # Score from direct assessment
    bonus_score = db.Column(db.Float)   # Score from related SDGs
    total_score = db.Column(db.Float)   # Changed from final_score: Direct + Bonus (capped)
    raw_score = db.Column(db.Float)     # Sum of raw points from questions
    max_possible = db.Column(db.Float)  # Max possible raw points for the SDG
    percentage_score = db.Column(db.Float) # Raw / MaxPossible * 100
    question_count = db.Column(db.Integer) # Number of questions answered for this SDG
    response_text = db.Column(db.Text)  # Store original text response if applicable
    notes = db.Column(db.Text)          # Store notes entered directly for the score
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    assessment = db.relationship('Assessment', back_populates='sdg_scores')
    sdg_goal = db.relationship('SdgGoal', back_populates='sdg_scores')

    def __repr__(self):
        return f'<SdgScore id={self.id} assessment={self.assessment_id} sdg={self.sdg_id} total={self.total_score}>'

    @staticmethod
    def get_for_assessment(assessment_id):
        """Get all SDG scores for a specific assessment."""
        conn = get_db()
        scores_data = conn.execute('''
            SELECT s.*, g.number, g.name, g.description, g.color_code
            FROM sdg_scores s
            JOIN sdg_goals g ON s.sdg_id = g.id
            WHERE s.assessment_id = ?
            ORDER BY g.number
        ''', (assessment_id,)).fetchall()

        return [dict(score) for score in scores_data]

    def save(self):
        """Save the SDG score to the database (create or update)."""
        conn = get_db()
        if self.id:
            # Update existing score
            conn.execute('''
                UPDATE sdg_scores SET
                    score = ?, notes = ?, direct_score = ?, bonus_score = ?,
                    total_score = ?, raw_score = ?, max_possible = ?,
                    percentage_score = ?, question_count = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (self.score, self.notes, self.direct_score, self.bonus_score,
                  self.total_score, self.raw_score, self.max_possible,
                  self.percentage_score, self.question_count, self.id))
        else:
            # Create new score
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO sdg_scores (
                    assessment_id, sdg_id, score, notes, direct_score, bonus_score,
                    total_score, raw_score, max_possible, percentage_score, question_count,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ''', (self.assessment_id, self.sdg_id, self.score, self.notes,
                  self.direct_score, self.bonus_score, self.total_score, self.raw_score,
                  self.max_possible, self.percentage_score, self.question_count))
            self.id = cursor.lastrowid
        
        conn.commit()
        return self

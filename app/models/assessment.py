"""
This module defines the SQLAlchemy models for 'Assessment' and 'SdgScore'.
These models are central to storing and managing SDG assessment data for
architectural projects, including overall assessment details, individual SDG scores,
and linkage to projects and users.
"""

from app import db
from datetime import datetime

class Assessment(db.Model):
    """
    Represents an SDG assessment for an architectural project.

    Attributes:
        id (int): Primary key for the assessment.
        project_id (int): Foreign key linking to the 'projects' table.
        user_id (int): Identifier for the user who created/owns the assessment.
        status (str): Current status of the assessment (e.g., 'draft', 'completed').
        overall_score (float): The calculated overall score for the assessment.
        created_at (datetime): Timestamp of when the assessment was created.
        updated_at (datetime): Timestamp of the last update to the assessment.
        completed_at (datetime): Timestamp of when the assessment was marked as completed.
        step1_completed (bool): Flag indicating completion of step 1.
        step2_completed (bool): Flag indicating completion of step 2.
        step3_completed (bool): Flag indicating completion of step 3.
        step4_completed (bool): Flag indicating completion of step 4.
        step5_completed (bool): Flag indicating completion of step 5.
        draft_data (str): Stores JSON data for assessments that are in a draft state, allowing users to save and resume.
        raw_expert_data (JSON): Stores the raw JSON data submitted from an expert assessment form.
        assessment_type (str): Type of assessment, e.g., 'standard' or 'expert'.
        project (relationship): SQLAlchemy relationship to the 'Project' model.
        sdg_scores (relationship): SQLAlchemy relationship to the 'SdgScore' model.
    """
    draft_data = db.Column(db.Text)  # Stores draft JSON data for assessments that are in a draft state
    __tablename__ = 'assessments'

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    user_id = db.Column(db.Integer, nullable=False) # Identifier for the user associated with this assessment
    status = db.Column(db.String(32), default='draft') # Current status of the assessment, e.g., 'draft', 'in_progress', 'completed'
    overall_score = db.Column(db.Float) # The final calculated score for the entire assessment
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = db.Column(db.DateTime) # Timestamp for when the assessment was finalized
    step1_completed = db.Column(db.Boolean, default=False) # Flag for completion of step 1 of the assessment
    step2_completed = db.Column(db.Boolean, default=False) # Flag for completion of step 2 of the assessment
    step3_completed = db.Column(db.Boolean, default=False) # Flag for completion of step 3 of the assessment
    step4_completed = db.Column(db.Boolean, default=False) # Flag for completion of step 4 of the assessment
    step5_completed = db.Column(db.Boolean, default=False) # Flag for completion of step 5 of the assessment
    
    # New columns for expert assessment support
    raw_expert_data = db.Column(db.JSON)  # Stores the raw JSON data from an expert assessment form, preserving the original input
    assessment_type = db.Column(db.String(50), default='standard')  # Defines the type of assessment, e.g., 'standard' for regular users, 'expert' for expert reviews

    project = db.relationship('Project', back_populates='assessments')
    sdg_scores = db.relationship('SdgScore', back_populates='assessment', cascade='all, delete-orphan')

    def __repr__(self):
        """Return a string representation of the Assessment object."""
        return f'<Assessment {self.id} for Project {self.project_id}>'

        # Note: The following method seems to be a remnant of a non-ORM approach or a helper.
        # It's not standard for a SQLAlchemy model to fetch itself this way.
        # Consider refactoring if 'get_db()' and raw SQL are not the intended pattern.
        """Fetch assessment from database by ID."""
        # TODO: Refactor this raw SQL query to use SQLAlchemy ORM methods.
        conn = get_db()
        assessment_data = conn.execute('SELECT * FROM assessments WHERE id = ?',
                                      (assessment_id,)).fetchone()
        if assessment_data:
            return Assessment( # This creates a new Assessment instance, not ideal within the class itself.
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
        """
        Get all assessments for a specific project, ordered by creation date.

        Args:
            project_id (int): The ID of the project.

        Returns:
            list[Assessment]: A list of Assessment objects.
        """
        # TODO: Refactor this raw SQL query to use SQLAlchemy ORM methods.
        # Example: return Assessment.query.filter_by(project_id=project_id).order_by(Assessment.created_at.desc()).all()
        conn = get_db()
        assessments_data = conn.execute('''
            SELECT * FROM assessments
            WHERE project_id = ?
            ORDER BY created_at DESC
        ''', (project_id,)).fetchall()

        assessments = []
        # This part manually reconstructs Assessment objects. ORM would handle this.
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
        """
        Get all SDG scores associated with this assessment, joined with SDG goal details.

        Returns:
            list[dict]: A list of dictionaries, where each dictionary represents an SdgScore
                        and its related SdgGoal information. Returns an empty list if the
                        assessment has no ID (i.e., not yet saved).
        """
        if not self.id:
            return []
        # TODO: Refactor this raw SQL query to use SQLAlchemy ORM methods.
        # Example: return SdgScore.query.join(SdgGoal).filter(SdgScore.assessment_id == self.id).order_by(SdgGoal.number).all()
        # and then format as dicts if needed, though ORM objects are often more useful.
        conn = get_db()
        scores_data = conn.execute('''
            SELECT s.*, g.number, g.name, g.description, g.color_code
            FROM sdg_scores s
            JOIN sdg_goals g ON s.sdg_id = g.id
            WHERE s.assessment_id = ?
            ORDER BY g.number
        ''', (self.id,)).fetchall()

        return [dict(score) for score in scores_data]

    def save(self):
        """
        Save the current assessment to the database.
        If the assessment has an ID, it updates the existing record.
        Otherwise, it creates a new assessment record.
        Manages 'completed_at' timestamp if status is 'completed'.

        Returns:
            Assessment: The instance of the saved assessment.
        """
        # TODO: Refactor this raw SQL logic to use SQLAlchemy session operations (db.session.add(), db.session.commit()).
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
            
            if self.status == 'completed' and not self.completed_at: # Ensure completed_at is only set once
                self.completed_at = datetime.utcnow() # Use utcnow for consistency
                conn.execute('''
                    UPDATE assessments SET completed_at = ? WHERE id = ? AND completed_at IS NULL
                ''', (self.completed_at, self.id))
        else:
            # Create new assessment
            cursor = conn.cursor()
            # Ensure all necessary fields for a new record are present or have defaults
            cursor.execute('''
                INSERT INTO assessments (project_id, user_id, status, created_at, updated_at, 
                                     step1_completed, step2_completed, step3_completed, 
                                     step4_completed, step5_completed, draft_data, 
                                     raw_expert_data, assessment_type, overall_score)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (self.project_id, self.user_id, self.status, 
                  self.step1_completed, self.step2_completed, self.step3_completed,
                  self.step4_completed, self.step5_completed, self.draft_data,
                  self.raw_expert_data, self.assessment_type, self.overall_score))
            self.id = cursor.lastrowid
        
        conn.commit()
        return self

    def delete(self):
        """
        Delete the assessment and all its related data (SDG scores, actions, responses)
        from the database.

        Returns:
            bool: True if deletion was successful, False otherwise (e.g., if assessment has no ID).
        """
        if not self.id:
            return False
        # TODO: Refactor this raw SQL logic to use SQLAlchemy cascade options or explicit session.delete() calls.
        conn = get_db()
        # Delete related data
        conn.execute('DELETE FROM sdg_actions WHERE assessment_id = ?', (self.id,))
        conn.execute('DELETE FROM sdg_scores WHERE assessment_id = ?', (self.id,)) # Handled by cascade if configured
        conn.execute('DELETE FROM question_responses WHERE assessment_id = ?', (self.id,))
        
        # Delete the assessment
        conn.execute('DELETE FROM assessments WHERE id = ?', (self.id,))
        conn.commit()
        return True

    def update_overall_score(self):
        """
        Calculate and update the overall_score of the assessment based on its SDG scores.
        The overall score is the average of valid (non-None) SDG scores.
        Updates the assessment record in the database.

        Returns:
            bool: True if the score was updated, False otherwise (e.g., if assessment has no ID).
        """
        if not self.id:
            return False
        # TODO: Refactor this raw SQL query to use SQLAlchemy ORM methods.
        # Example: scores = [s.score for s in self.sdg_scores if s.score is not None]
        conn = get_db()
        scores_data = conn.execute(
            'SELECT total_score FROM sdg_scores WHERE assessment_id = ?', # Assuming total_score is the one to average
            (self.id,)
        ).fetchall()

        valid_scores = [score['total_score'] for score in scores_data if score['total_score'] is not None]
        overall_score = sum(valid_scores) / len(valid_scores) if valid_scores else 0.0

        self.overall_score = overall_score # Update instance attribute
        # TODO: Refactor this raw SQL query.
        conn.execute(
            'UPDATE assessments SET overall_score = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
            (self.overall_score, self.id)
        )
        
        conn.commit()
        return True

    def finalize(self):
        """
        Mark the assessment as 'completed', set the 'completed_at' timestamp,
        and update its overall score. Persists these changes to the database.

        Returns:
            bool: True if finalization was successful, False otherwise (e.g., if assessment has no ID).
        """
        if not self.id:
            return False

        self.status = 'completed'
        self.completed_at = datetime.utcnow() # Use utcnow for consistency
        self.update_overall_score() # This already updates overall_score and commits

        # The update_overall_score method might already commit.
        # If so, this explicit update might be redundant or could be combined.
        # TODO: Refactor this raw SQL query.
        conn = get_db()
        conn.execute(
            'UPDATE assessments SET status = ?, completed_at = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
            (self.status, self.completed_at, self.id) # updated_at will be set by onupdate=datetime.utcnow
        )
        
        conn.commit() # May not be needed if update_overall_score commits and this is part of a larger transaction.
        return True

class SdgScore(db.Model):
    """
    Represents the score of an individual Sustainable Development Goal (SDG)
    within a specific assessment.

    Attributes:
        id (int): Primary key for the SDG score.
        assessment_id (int): Foreign key linking to the 'assessments' table.
        sdg_id (int): Foreign key linking to the 'sdg_goals' table.
        direct_score (float): Score derived directly from questions related to this SDG.
        bonus_score (float): Score derived from the positive impacts of other related SDGs.
        total_score (float): The final combined score for the SDG (direct_score + bonus_score, potentially capped or adjusted).
        raw_score (float): Sum of raw points obtained from answers to questions for this SDG before normalization.
        max_possible (float): Maximum possible raw points that could be scored for this SDG.
        percentage_score (float): The raw_score expressed as a percentage of max_possible (raw_score / max_possible * 100).
        question_count (int): Number of questions answered that contributed to this SDG's score.
        response_text (str): Stores original text response if applicable for certain question types.
        notes (str): Any notes or justifications entered by the user or assessor for this specific SDG score.
        created_at (datetime): Timestamp of when the SDG score was created.
        updated_at (datetime): Timestamp of the last update to the SDG score.
        assessment (relationship): SQLAlchemy relationship to the 'Assessment' model.
        sdg_goal (relationship): SQLAlchemy relationship to the 'SdgGoal' model.
    """
    __tablename__ = 'sdg_scores'

    id = db.Column(db.Integer, primary_key=True)
    assessment_id = db.Column(db.Integer, db.ForeignKey('assessments.id'), nullable=False)
    sdg_id = db.Column(db.Integer, db.ForeignKey('sdg_goals.id'), nullable=False)
    direct_score = db.Column(db.Float)  # Score derived directly from questions specific to this SDG
    bonus_score = db.Column(db.Float)   # Additional score awarded based on interlinkages or positive impacts from other SDGs
    total_score = db.Column(db.Float)   # Final score for the SDG, typically direct_score + bonus_score, possibly with caps or other logic
    raw_score = db.Column(db.Float)     # Sum of points from question responses before any normalization or weighting
    max_possible = db.Column(db.Float)  # Maximum possible raw points that can be achieved for this SDG's questions
    percentage_score = db.Column(db.Float) # The raw_score as a percentage of max_possible_score
    question_count = db.Column(db.Integer) # The number of questions answered that contribute to this SDG's score
    response_text = db.Column(db.Text)  # Stores concatenated or key textual responses related to this SDG
    notes = db.Column(db.Text)          # User-entered notes or justifications for the SDG score
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    assessment = db.relationship('Assessment', back_populates='sdg_scores')
    sdg_goal = db.relationship('SdgGoal', back_populates='sdg_scores')

    def __repr__(self):
        """Return a string representation of the SdgScore object."""
        return f'<SdgScore id={self.id} assessment={self.assessment_id} sdg={self.sdg_id} total={self.total_score}>'

    @staticmethod
    def get_for_assessment(assessment_id):
        """
        Get all SDG scores for a specific assessment, joined with SDG goal details.

        Args:
            assessment_id (int): The ID of the assessment.

        Returns:
            list[dict]: A list of dictionaries, where each dictionary contains SDG score
                        data along with details from the corresponding SDG goal.
        """
        # TODO: Refactor this raw SQL query to use SQLAlchemy ORM methods.
        # Example: return SdgScore.query.join(SdgGoal).filter(SdgScore.assessment_id == assessment_id).order_by(SdgGoal.number).all()
        # Then format as dicts if necessary.
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
        """
        Save the current SDG score to the database.
        If the score has an ID, it updates the existing record.
        Otherwise, it creates a new SDG score record.

        Returns:
            SdgScore: The instance of the saved SDG score.
        """
        # TODO: Refactor this raw SQL logic to use SQLAlchemy session operations (db.session.add(), db.session.commit()).
        conn = get_db()
        if self.id:
            # Update existing score
            # Note: 'score' column is referenced here but not defined in the model above. Assuming it might be a legacy name for 'total_score' or similar.
            # For this refactoring, I'll assume 'score' should be 'total_score' or needs clarification.
            # Using 'total_score' as it's defined in the model.
            conn.execute('''
                UPDATE sdg_scores SET
                    notes = ?, direct_score = ?, bonus_score = ?,
                    total_score = ?, raw_score = ?, max_possible = ?,
                    percentage_score = ?, question_count = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (self.notes, self.direct_score, self.bonus_score,
                  self.total_score, self.raw_score, self.max_possible,
                  self.percentage_score, self.question_count, self.id))
        else:
            # Create new score
            # Again, assuming 'score' maps to 'total_score'.
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO sdg_scores (
                    assessment_id, sdg_id, notes, direct_score, bonus_score,
                    total_score, raw_score, max_possible, percentage_score, question_count,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ''', (self.assessment_id, self.sdg_id, self.notes,
                  self.direct_score, self.bonus_score, self.total_score, self.raw_score,
                  self.max_possible, self.percentage_score, self.question_count))
            self.id = cursor.lastrowid
        
        conn.commit()
        return self

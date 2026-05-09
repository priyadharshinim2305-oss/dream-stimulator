# database.py

from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import json

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    total_dreams = db.Column(db.Integer, default=0)
    psychological_profile = db.Column(db.JSON)
    
    sessions = db.relationship('DreamSession', backref='user', lazy='dynamic')
    choices = db.relationship('PlayerChoice', backref='user', lazy='dynamic')
    symbols = db.relationship('DreamSymbol', backref='user', lazy='dynamic')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def update_profile(self, new_data):
        if self.psychological_profile is None:
            self.psychological_profile = {}
        profile = dict(self.psychological_profile)
        profile.update(new_data)
        self.psychological_profile = profile


class DreamSession(db.Model):
    __tablename__ = 'dream_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    ended_at = db.Column(db.DateTime, nullable=True)
    fear_level = db.Column(db.Float, default=0.0)
    tension_level = db.Column(db.Float, default=0.0)
    dream_depth = db.Column(db.Integer, default=1)
    is_nightmare = db.Column(db.Boolean, default=False)
    total_choices = db.Column(db.Integer, default=0)
    
    scenes = db.relationship('DreamScene', backref='session', lazy='dynamic')
    
    def adjust_fear(self, delta):
        self.fear_level = max(0, min(10, self.fear_level + delta))
        if self.fear_level >= 7.5:
            self.is_nightmare = True
    
    def adjust_tension(self, delta):
        self.tension_level = max(0, min(10, self.tension_level + delta))
    
    def deepen(self):
        if self.dream_depth < 5:
            self.dream_depth += 1


class DreamScene(db.Model):
    __tablename__ = 'dream_scenes'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('dream_sessions.id'), nullable=False)
    scene_number = db.Column(db.Integer, nullable=False)
    narrative = db.Column(db.Text, nullable=False)
    atmosphere = db.Column(db.String(50))
    imagery = db.Column(db.JSON)
    choices = db.Column(db.JSON)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    player_choices = db.relationship('PlayerChoice', backref='scene', lazy='dynamic')


class PlayerChoice(db.Model):
    __tablename__ = 'player_choices'
    
    id = db.Column(db.Integer, primary_key=True)
    scene_id = db.Column(db.Integer, db.ForeignKey('dream_scenes.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    choice_text = db.Column(db.String(500))
    choice_index = db.Column(db.Integer)
    fear_delta = db.Column(db.Float, default=0.0)
    tension_delta = db.Column(db.Float, default=0.0)
    psychological_tags = db.Column(db.JSON)
    response_time_ms = db.Column(db.Integer)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


class DreamSymbol(db.Model):
    __tablename__ = 'dream_symbols'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    symbol_name = db.Column(db.String(100))
    first_appearance = db.Column(db.DateTime, default=datetime.utcnow)
    occurrence_count = db.Column(db.Integer, default=1)
    emotional_weight = db.Column(db.Float, default=0.5)
    context = db.Column(db.JSON)
    
    __table_args__ = (
        db.UniqueConstraint('user_id', 'symbol_name', name='unique_user_symbol'),
    )


class PsychologicalTimeline(db.Model):
    __tablename__ = 'psychological_timeline'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    session_id = db.Column(db.Integer, db.ForeignKey('dream_sessions.id'), nullable=False)
    fear_patterns = db.Column(db.JSON)
    avoidance_behaviors = db.Column(db.JSON)
    confrontation_score = db.Column(db.Float)
    recurring_themes = db.Column(db.JSON)
    analysis_timestamp = db.Column(db.DateTime, default=datetime.utcnow)

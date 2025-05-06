from extensions import db
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.types import TypeDecorator, JSON
import json
from flask import current_app

# SQLite compatibility for JSONB
class JSONEncodedDict(TypeDecorator):
    impl = db.Text

    def process_bind_param(self, value, dialect):
        if value is not None:
            value = json.dumps(value)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            value = json.loads(value)
        return value

# Use JSONEncodedDict by default
JSONType = JSONEncodedDict

class Session(db.Model):
    __tablename__ = 'sessions'
    
    session_id = db.Column(db.String(36), primary_key=True)
    student_id = db.Column(db.String(36), nullable=False)
    educator_id = db.Column(db.String(36), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=True)
    transcript = db.Column(JSONType, nullable=False, default=[])
    status = db.Column(db.String(20), nullable=False, default='simulating')
    
    def __repr__(self):
        return f'<Session {self.session_id}>' 
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Generator(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(240), nullable=False)
    length = db.Column(db.Integer, nullable=False)
    protected = db.Column(db.Integer, nullable = False, default = 0)

class Suffix(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(10), nullable=False)
    position = db.Column(db.Integer, nullable=False)
    generator_id = db.Column(db.Integer, db.ForeignKey('generator.id'), nullable=False)
    generator = db.relationship('Generator', backref=db.backref('suffixes', lazy=True))

class SavedWord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    word = db.Column(db.String, nullable=False)
    



from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash,  check_password_hash

db = SQLAlchemy()

def add_song(db, artist, song, album, length, year, number):
    artist1 = Artist(name=artist)
    db.session.add_all([artist1])
    db.session.commit()
    album1 = Album(title=album, year=year, artist=artist1)
    song1 = Song(title=song, length=length, track_number=int(number), album=album1)
    db.session.add_all([album1, song1])
    db.session.commit()

class Artist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

class Album(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    year = db.Column(db.String(4), nullable=False)
    artist_id = db.Column(db.Integer, db.ForeignKey('artist.id'), nullable=False)
    artist = db.relationship('Artist', backref=db.backref('albums', lazy=True))

class Song(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    length = db.Column(db.String(4), nullable=False)
    track_number = db.Column(db.Integer, nullable=False)
    album_id = db.Column(db.Integer, db.ForeignKey('album.id'), nullable=False)
    album = db.relationship('Album', backref=db.backref('songs', lazy=True))

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

class messenge(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender = db.Column(db.String, nullable=False)
    text = db.Column(db.String, nullable=False)

class savedword(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    word = db.Column(db.String, nullable=False)
    



from flask import Flask, request, render_template, jsonify
from models import Artist, Album, Song, Suffix, Generator, db, add_song, savedword
from sqlalchemy import select, update, delete
from werkzeug.security import generate_password_hash, check_password_hash
from flask_socketio import SocketIO, emit
import json

app = Flask(__name__)
socketio = SocketIO(app)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///music.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
admin_hash = "scrypt:32768:8:1$eSfltauWyXtE2bwt$abb8875624988f324d7eb3974eafabc2a1255e5f3c7f858601bfc92db2e09800376117c07bfaf4c2022ed8f12d9113ddace9e38f3c573131d87a3c3aaa080372"
admin = False
admin_ip = 0

# связываем приложение и экземпляр SQLAlchemy
db.init_app(app)

@app.route('/songs', methods=['GET', 'POST'])
def songs():
    if request.method == 'POST':
        #print(request)
        artist = request.form['artist']
        song = request.form['song']
        album = request.form['album']
        year = request.form['year']
        length = request.form['length']
        number = request.form['number']
        add_song(db, artist, song, album, length, year, number)
    songs_list = Song.query.all()
    return render_template('songs.html', songs=songs_list)

@app.route('/login', methods=['GET', 'POST'])
def login():
    global admin, admin_ip
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == 'admin' and check_password_hash(admin_hash,password):
            admin = True
            admin_ip = request.remote_addr
            return render_template('ok.html')
        return 'нет'
    else:
        return render_template('login.html')

@app.route('/', methods=['GET', 'POST'])
def about():
    global admin_ip
    par = request.args.to_dict()
    suf_list = Suffix.query.all()
    gen_list = Generator.query.all()
    D = []
    for gen in gen_list:
        id = gen.id
        lenn = gen.length
        A = []
        for l in range(lenn):
            stmt = select(Suffix.text).where(Suffix.generator_id == id, Suffix.position == l + 1)
            rs = list(db.session.execute(stmt))
            B = []
            for r in rs:
                B.append(r[0])
            A.append(B)
        D.append(A)

    Par = [''] * len(D)
    for i in range(len(Par)): 
        if (f'w{i+1}' in par): Par[i] = par[f'w{i+1}']    
    print(Par)
    flag_admin = False
    if admin_ip == request.remote_addr:
        flag_admin = True
    return render_template('about2.html', sufs=suf_list, flag_admin = flag_admin, gens = gen_list, D = D, par = Par)

@app.route('/edit/<int:gen_id>', methods=['GET', 'POST'])
def edit(gen_id):
    rq = select(Generator).where(Generator.id == gen_id)
    gen = list(db.session.execute(rq))
    length = gen[0][0].length
    A = []
    H = []
    for l in range(length):
        stmt = select(Suffix.text).where(Suffix.generator_id == gen_id, Suffix.position == l + 1)
        rs = list(db.session.execute(stmt))
        B = []
        for r in rs:
            B.append(r[0])
        H.append(len(B))
        A.append('\n'.join(B))
    if request.method == 'POST':
        if gen[0][0].protected > 0 and admin_ip != request.remote_addr:
            return "Error! Only admin can edit it"
        d = ''
        try:
            d = request.form['delete']
        except:
            d = 'p'
        if d == 'del':
            stmt = delete(Suffix).where(Suffix.generator_id == gen_id)
            db.session.execute(stmt)
            rq = delete(Generator).where(Generator.id == gen_id)
            db.session.execute(rq)
            db.session.commit()
            return render_template('ok.html')
        name = request.form['name']
        description = request.form['description']
        protected = Generator.protected
        if admin_ip == request.remote_addr:
            protected = request.form['protected']
        stmt = (update(Generator).where(Generator.id == gen_id).values(name = name, description = description, protected = protected))
        db.session.execute(stmt)
        db.session.commit()
        stmt = delete(Suffix).where(Suffix.generator_id == gen_id)
        db.session.execute(stmt)
        db.session.commit()
        O = []
        for i in range(length):
            s = request.form[f's{i+1}']
            R = s.split('\r\n')
            for r in R:
                O.append( Suffix(text = r, position = i+1, generator = gen[0][0]))
        db.session.add_all(O)
        db.session.commit()
        return render_template('ok.html')
    flag_admin = False
    if admin_ip == request.remote_addr:
        flag_admin = True
    return render_template('edit.html', gen = gen[0][0], sufx = A, heights = H, flag_admin = flag_admin)


@app.route('/create', methods=['GET', 'POST'])
def create():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        length = request.form['length']
        generator1 = Generator(name=name, description = description, length = length)
        db.session.add_all([generator1])
        db.session.commit()
        return render_template('ok.html')
    return render_template('create.html')



@app.route('/about')
def main():
    r1 = request.args.get('key')
    r2 = request.args.get('key2')
    return r1 + ' ' + r2

@app.route('/im')
def agent():
    return render_template('im.html')

@app.route('/saved')
def saved():
    stmt = select(savedword.word)
    words = list(db.session.execute(stmt))
    print(words)
    return render_template('saved.html', words = words)

@socketio.on('message')
def handle_message(data):
    name = data['message'] 
    #print(name)
    stmt = select(savedword).where(savedword.word == name)
    gen = list(db.session.execute(stmt))
    print(gen)
    if len(gen) == 0:
        word1 = savedword(word=name)
        db.session.add_all([word1])
        db.session.commit()

if __name__ == '__main__':
    socketio.run(app, debug=True, host = '0.0.0.0', port=1453)
    #app.run(debug=True, host='0.0.0.0', port=1453)

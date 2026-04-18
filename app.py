from flask import Flask, render_template, request, redirect, url_for, session, send_file
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os, json

app = Flask(__name__)
app.secret_key = 'santa_sofia_security_v7'

basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'sea_sistema.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

class Evaluacion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    jurado = db.Column(db.String(100))
    proyecto = db.Column(db.String(200))
    estudiante = db.Column(db.String(100))
    detalles = db.Column(db.Text) 
    nota_final = db.Column(db.Float)
    fecha = db.Column(db.String(50))

@app.route('/')
def home():
    if 'user' not in session: return redirect(url_for('login'))
    return redirect(url_for('index'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and check_password_hash(user.password, request.form['password']):
            session['user'] = user.username
            return redirect(url_for('index'))
        return "Credenciales inválidas"
    return render_template('login.html')

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        hashed_pw = generate_password_hash(request.form['password'], method='pbkdf2:sha256')
        new_user = User(username=request.form['username'], password=hashed_pw)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('registro.html')

@app.route('/index')
def index():
    if 'user' not in session: return redirect(url_for('login'))
    return render_template('evaluacion.html', datos=None)

@app.route('/enviar_voto', methods=['POST'])
def enviar_voto():
    if 'user' not in session: return redirect(url_for('login'))
    
    proyecto = request.form.get('proyecto')
    fecha_form = request.form.get('fecha_evaluacion')
    nombres = request.form.getlist('nombre_expositor[]')
    
    vals_t = [float(x) for x in request.form.getlist('trabajo_val[]')]
    vals_d = [float(x) for x in request.form.getlist('diapositiva_val[]')]
    vals_e = [float(x) for x in request.form.getlist('equipo_val[]')]
    
    p_grupales = sum(vals_t) + sum(vals_d) + sum(vals_e)

    Evaluacion.query.filter_by(proyecto=proyecto, jurado=session['user']).delete()
    
    for i in range(len(nombres)):
        vals_i = [float(x) for x in request.form.getlist(f'ind_val_{i}[]')]
        p_individual = sum(vals_i)
        
        nota_f = (p_grupales + p_individual) / 4
        
        detalles_json = {"items_t": vals_t, "items_d": vals_d, "items_e": vals_e, "items_i": vals_i}

        nueva = Evaluacion(
            jurado=session['user'], proyecto=proyecto, estudiante=nombres[i],
            detalles=json.dumps(detalles_json), nota_final=round(nota_f, 2), fecha=fecha_form
        )
        db.session.add(nueva)
    
    db.session.commit()
    return redirect(url_for('consolidacion', proyecto=proyecto))

@app.route('/consolidacion/<proyecto>', methods=['GET', 'POST'])
def consolidacion(proyecto):
    if 'user' not in session: return redirect(url_for('login'))
    
    if request.method == 'POST':
        ids = request.form.getlist('eval_id[]')
        # IMPORTANTE: Este nombre debe coincidir con el 'name' del input hidden en el HTML
        notas_finales = request.form.getlist('nota_final_promediada[]')
        
        print(f"Recibiendo IDs: {ids}") # Para depuración en tu terminal
        print(f"Recibiendo Notas: {notas_finales}")

        for i in range(len(ids)):
            ev = Evaluacion.query.get(ids[i])
            if ev and i < len(notas_finales):
                ev.nota_final = float(notas_finales[i])
        
        db.session.commit()
        return redirect(url_for('historial'))

    evaluaciones = Evaluacion.query.filter_by(proyecto=proyecto, jurado=session['user']).all()
    return render_template('consolidacion.html', proyecto=proyecto, evaluaciones=evaluaciones)

@app.route('/historial')
def historial():
    if 'user' not in session: return redirect(url_for('login'))
    evaluaciones = Evaluacion.query.filter_by(jurado=session['user']).order_by(Evaluacion.id.desc()).all()
    return render_template('historial.html', evaluaciones=evaluaciones)

@app.route('/editar_evaluacion/<int:id>')
def editar_evaluacion(id):
    if 'user' not in session: return redirect(url_for('login'))
    ev = Evaluacion.query.get_or_404(id)
    todos = Evaluacion.query.filter_by(proyecto=ev.proyecto, jurado=session['user'], fecha=ev.fecha).all()
    
    detalles_base = json.loads(ev.detalles)
    datos_previos = {
        'proyecto': ev.proyecto, 'fecha': ev.fecha,
        'items_t': detalles_base.get('items_t', []),
        'items_d': detalles_base.get('items_d', []),
        'items_e': detalles_base.get('items_e', []),
        'estudiantes': [{'nombre': e.estudiante, 'items_i': json.loads(e.detalles).get('items_i', [])} for e in todos]
    }
    return render_template('evaluacion.html', datos=datos_previos)

if __name__ == '__main__':
    with app.app_context(): db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)
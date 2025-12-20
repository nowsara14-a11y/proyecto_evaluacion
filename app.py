import json
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'sea_secret_key_2025'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sea_sistema.db'
db = SQLAlchemy(app)

# --- MODELOS DE BASE DE DATOS ---
class Jurado(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

class Proyecto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200))
    fecha = db.Column(db.String(50))
    datos_json = db.Column(db.Text)
    jurado_id = db.Column(db.Integer, db.ForeignKey('jurado.id'))

with app.app_context():
    db.create_all()

# --- RUTAS DE ACCESO (LOGIN/REGISTRO) ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = Jurado.query.filter_by(usuario=request.form['usuario']).first()
        if user and check_password_hash(user.password, request.form['password']):
            session['user_id'] = user.id
            session['usuario'] = user.usuario
            return redirect(url_for('index'))
        return "Error: Usuario o contraseña incorrectos"
    return render_template('login.html')

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        pw_hash = generate_password_hash(request.form['password'])
        nuevo = Jurado(usuario=request.form['usuario'], password=pw_hash)
        db.session.add(nuevo)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('registro.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# --- RUTAS DE EVALUACIÓN ---
@app.route('/')
def index():
    if 'user_id' not in session: return redirect(url_for('login'))
    return render_template('evaluacion.html')

@app.route('/enviar', methods=['POST'])
def enviar():
    if 'user_id' not in session: return redirect(url_for('login'))
    
    titulo = request.form.get('titulo')
    jurado_nom = request.form.get('jurado')
    
    # Guardar en base de datos
    datos_completos = json.dumps(request.form.to_dict(flat=False))
    nuevo_p = Proyecto(titulo=titulo, fecha=request.form.get('fecha'), 
                       datos_json=datos_completos, jurado_id=session['user_id'])
    db.session.add(nuevo_p)
    db.session.commit()

    # Cálculos para la pantalla de resultados inmediata
    nombres = request.form.getlist('nombre_exp[]')
    n1, n2, n3, n4, n5 = (request.form.getlist('nota1[]'), request.form.getlist('nota2[]'), 
                          request.form.getlist('nota3[]'), request.form.getlist('nota4[]'), 
                          request.form.getlist('nota5[]'))
    
    def sum_sec(p): return sum([int(request.form.get(f'{p}{i}', 0)) for i in range(1,6)])
    s_t, s_d, s_e = sum_sec('t'), sum_sec('d'), sum_sec('e')

    individuales = []
    for i in range(len(nombres)):
        s_ind = int(n1[i]) + int(n2[i]) + int(n3[i]) + int(n4[i]) + int(n5[i])
        # Nota final sobre 20 (Promedio de las 4 secciones: Trabajo, Diapositivas, Equipo, Individual)
        total_20 = (s_t + s_d + s_e + s_ind) / 4
        individuales.append({'nombre': nombres[i], 'total_20': round(total_20, 2)})

    return render_template('resultados.html', titulo=titulo, jurado=jurado_nom, individuales=individuales)

# --- RUTAS DE HISTORIAL ---
@app.route('/historial')
def historial():
    if 'user_id' not in session: return redirect(url_for('login'))
    proyectos = Proyecto.query.filter_by(jurado_id=session['user_id']).all()
    return render_template('historial.html', proyectos=proyectos)

@app.route('/ver_proyecto/<int:id>')
def ver_proyecto(id):
    if 'user_id' not in session: return redirect(url_for('login'))
    proyecto = Proyecto.query.get_or_404(id)
    # Convertimos el JSON guardado de vuelta a un diccionario para mostrar los criterios
    datos = json.loads(proyecto.datos_json)
    return render_template('detalle_historial.html', p=proyecto, d=datos)

# --- INICIO DEL SERVIDOR ---
if __name__ == '__main__':
    # Quitamos debug y usamos el puerto 5000 explícitamente
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
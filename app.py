from flask import Flask, render_template, request, redirect, url_for, session, send_file
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from report_engine import generar_pdf_consolidado
import os, json

app = Flask(__name__)
# Inserta esto justo debajo de app = Flask(__name__)
@app.template_filter('load_json')
def load_json_filter(value):
    if not value:
        return []
    try:
        import json
        return json.loads(value)
    except:
        return []
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
    proyecto = db.Column(db.String(200), nullable=False)
    fecha = db.Column(db.String(50), nullable=False)
    jurado = db.Column(db.String(100), nullable=False)
    estudiante = db.Column(db.String(100), nullable=False)
    detalles = db.Column(db.Text, nullable=False)  # Guarda el JSON de los 20 criterios
    nota_final = db.Column(db.Float, default=0.0)   # Promedio definitivo de la consolidación
    # NUEVO CAMPO: Guardará las notas de los jurados añadidos en Consolidación
    jurados_externos = db.Column(db.Text, default='[]')

@app.route('/')
def home():
    if 'user' not in session: return redirect(url_for('login'))
    return redirect(url_for('index'))

from flask import Flask, render_template, request, redirect, url_for, session, flash
# Asegúrate de mantener tus otras importaciones e inicialización de BD igual

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and check_password_hash(user.password, request.form['password']):
            session['user'] = user.username
            return redirect(url_for('index'))
        
        # En vez de romper la app con texto plano, enviamos un mensaje elegante
        flash("Usuario o contraseña incorrectos", "error")
        return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        username_ingresado = request.form['username'].strip()
        
        # PASO CLAVE: Verificar si ya existe antes de lanzar el INSERT
        usuario_existente = User.query.filter_by(username=username_ingresado).first()
        
        if usuario_existente:
            flash("El nombre de usuario ya está en uso. Elige otro.", "error")
            return redirect(url_for('registro'))
            
        # Si no existe, procedemos de manera segura sin romper la base de datos
        hashed_pw = generate_password_hash(request.form['password'], method='pbkdf2:sha256')
        new_user = User(username=username_ingresado, password=hashed_pw)
        db.session.add(new_user)
        db.session.commit()
        
        flash("¡Registro exitoso! Ya puedes iniciar sesión.", "success")
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
        notas_finales = request.form.getlist('nota_final_promediada[]')
        
        # Capturamos todas las notas dinámicas de los inputs del formulario
        # Recorremos cada estudiante evaluado
        for i, eval_id in enumerate(ids):
            ev = Evaluacion.query.get(eval_id)
            if ev:
                if i < len(notas_finales):
                    ev.nota_final = float(notas_finales[i])
                
                # Buscamos los inputs de notas de jurados externos específicos de este estudiante
                # Buscamos en el objeto request.form las listas generadas dinámicamente por JS
                notas_ext_estudiante = request.form.getlist(f'nota-input-{i}')
                # Las primeras posiciones corresponden al jurado principal (tú), las guardamos limpias de la 1 en adelante
                externas = [float(x) for x in notas_ext_estudiante[1:] if x.strip() != '']
                
                ev.jurados_externos = json.dumps(externas)
        
        db.session.commit()
        return redirect(url_for('historial'))

    evaluaciones = Evaluacion.query.filter_by(proyecto=proyecto, jurado=session['user']).all()
    return render_template('consolidacion.html', proyecto=proyecto, evaluaciones=evaluaciones)

@app.route('/historial')
def historial():
    if 'user' not in session: return redirect(url_for('login'))
    
    # Agrupamos por proyecto para evitar filas duplicadas por cada alumno
    evaluaciones = Evaluacion.query.filter_by(jurado=session['user'])\
                                   .group_by(Evaluacion.proyecto)\
                                   .order_by(Evaluacion.id.desc()).all()
    return render_template('historial.html', evaluaciones=evaluaciones)

@app.route('/editar_evaluacion/<int:id>')
def editar_evaluacion(id):
    if 'user' not in session: return redirect(url_for('login'))
    
    ev = Evaluacion.query.get_or_404(id)
    todos = Evaluacion.query.filter_by(proyecto=ev.proyecto, jurado=session['user']).all()
    detalles_base = json.loads(ev.detalles)
    
    datos_previos = {
        'proyecto': ev.proyecto,
        'fecha': ev.fecha,
        'items_t': [int(x) for x in detalles_base.get('items_t', [])],
        'items_d': [int(x) for x in detalles_base.get('items_d', [])],
        'items_e': [int(x) for x in detalles_base.get('items_e', [])],
        'estudiantes': []
    }
    
    for e in todos:
        detalles_est = json.loads(e.detalles)
        # Recuperamos las notas de los jurados guardadas en la consolidación
        notas_externas = json.loads(e.jurados_externos) if e.jurados_externos else []
        
        datos_previos['estudiantes'].append({
            'nombre': e.estudiante,
            'items_i': [int(x) for x in detalles_est.get('items_i', [])],
            'jurados_externos': notas_externas # Mandamos esto para que persista
        })
        
    return render_template('evaluacion.html', datos=datos_previos)

@app.route('/descargar_reporte/<proyecto>')
def descargar_reporte(proyecto):
    if 'user' not in session: return redirect(url_for('login'))
    
    registros = Evaluacion.query.filter_by(proyecto=proyecto, jurado=session['user']).all()
    
    if not registros:
        flash("No se encontraron registros para este reporte", "error")
        return redirect(url_for('historial'))
        
    datos_pdf = {
        'proyecto': proyecto,
        'estudiantes': []
    }
    
    for r in registros:
        detalles = json.loads(r.detalles)
        
        items_t = [float(x) for x in detalles.get('items_t', [0,0,0,0,0])]
        items_d = [float(x) for x in detalles.get('items_d', [0,0,0,0,0])]
        items_e = [float(x) for x in detalles.get('items_e', [0,0,0,0,0])]
        items_i = [float(x) for x in detalles.get('items_i', [0,0,0,0,0])]
        
        # Leemos el nuevo campo de la base de datos de manera segura
        externas = json.loads(r.jurados_externos) if r.jurados_externos else []
        
        datos_pdf['estudiantes'].append({
            'nombre': r.estudiante,
            'nota_principal': float(r.nota_final),
            'jurados_externos': externas,
            'detalles': {
                'items_t': items_t,
                'items_d': items_d,
                'items_e': items_e,
                'items_i': items_i,
                'p_trabajo': sum(items_t) / 5,
                'p_diapo': sum(items_d) / 5,
                'p_equipo': sum(items_e) / 5,
                'p_defensa': sum(items_i)
            }
        })
        
    nombre_archivo = f"Reporte_{proyecto.replace(' ', '_')}.pdf"
    ruta_guardado = os.path.join(basedir, nombre_archivo)
    
    generar_pdf_consolidado(datos_pdf, ruta_guardado)
    return send_file(ruta_guardado, as_attachment=True)

if __name__ == '__main__':
    with app.app_context(): db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)
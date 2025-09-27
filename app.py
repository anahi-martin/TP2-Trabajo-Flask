from flask import Flask, render_template, request, redirect, url_for, flash, session
from models.user import db, User, Donacion, Servicio, Ayuda
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)

# config bd
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///Aportar.db'
app.config['SECRET_KEY'] = 'clave_secreta'
db.init_app(app)

# save img subidas
UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Rutas
@app.route('/')
@app.route('/inicio')
def inicio():
    return render_template('inicio.html')

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        nombre = request.form['nombre']
        apellido = request.form['apellido']
        dni = request.form['dni']
        distrito = request.form['distrito']
        email = request.form['email']
        intereses = request.form.getlist('intereses')
        intereses_txt = ",".join(intereses)

        if password != confirm_password:
            flash("Las contraseñas no coinciden.", "danger")
            return render_template('registro.html')
        if User.query.filter_by(username=username).first():
            return render_template('registro.html', mensaje="Usuario existente")
        elif User.query.filter_by(email=email).first():
            return render_template('registro.html', mensaje="Ese email ya está registrado")

        nuevo_usuario = User(
            username=username,
            nombre=nombre,
            apellido=apellido,
            dni=dni,
            distrito=distrito,
            email=email,
            intereses=intereses_txt
        )
        nuevo_usuario.set_password(password)

        db.session.add(nuevo_usuario)
        db.session.commit()

        flash("Usuario creado correctamente", "success")
        return redirect(url_for('login'))

    return render_template('registro.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            session['user_id'] = user.id
            session['username'] = user.username
            return redirect(url_for('dashboard'))
        else:
            flash("Credenciales inválidas", "danger")
            return render_template('login.html')

    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash('Por favor inicia sesion primero', "danger")
        return redirect(url_for('login'))
    return render_template('dashboard.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Has cerrado sesión correctamente', 'info')
    return redirect(url_for('inicio'))

# Rutas de busqueda global
@app.route('/busqueda')
def busqueda():
    return redirect(url_for('busqueda_avanzada'))

@app.route('/perfil')
def perfil():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('perfil.html', active_section='perfil')

# Rutas para Donaciones
@app.route("/donaciones/publicar", methods=["GET", "POST"])
def publicar_donacion():
    if 'user_id' not in session:
        flash('Debes iniciar sesión para publicar una donación.', 'danger')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        titulo = request.form.get("titulo")
        descripcion = request.form.get("descripcion")
        ubicacion = request.form.get("ubicacion")
        imagen = request.files.get("imagen")
        user_id = session['user_id']
        
        filename = None
        if imagen and imagen.filename != '':
            filename = secure_filename(imagen.filename)
            imagen.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
        
        nueva_donacion = Donacion(
            titulo=titulo,
            descripcion=descripcion,
            ubicacion=ubicacion,
            imagen=filename,
            user_id=user_id
        )
        db.session.add(nueva_donacion)
        db.session.commit()
        
        flash("Donación publicada con éxito", "success")
        return redirect(url_for('ver_donaciones'))

    return render_template('publicar_donaciones.html')

@app.route("/donaciones/ver", methods=["GET"])
def ver_donaciones():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user_id = session['user_id']
    donaciones = Donacion.query.filter_by(user_id=user_id).all()
    return render_template('ver_donaciones.html', donaciones=donaciones)

@app.route("/donaciones/editar/<int:id>", methods=["GET", "POST"])
def editar_donacion(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    donacion = Donacion.query.get_or_404(id)
    if donacion.user_id != session['user_id']:
        flash("No tienes permiso para editar esta donación.", "danger")
        return redirect(url_for('ver_donaciones'))
    
    if request.method == "POST":
        donacion.titulo = request.form["titulo"]
        donacion.descripcion = request.form["descripcion"]
        donacion.ubicacion = request.form["ubicacion"]
        
        imagen = request.files.get("imagen")
        if imagen and imagen.filename != '':
            if donacion.imagen:
                path_anterior = os.path.join(app.config["UPLOAD_FOLDER"], donacion.imagen)
                if os.path.exists(path_anterior):
                    os.remove(path_anterior)
            
            filename = secure_filename(imagen.filename)
            imagen.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
            donacion.imagen = filename
        
        db.session.commit()
        flash("Donación actualizada con éxito", "success")
        return redirect(url_for('ver_donaciones'))
    
    return render_template('editar_donacion.html', donacion=donacion)

@app.route("/donaciones/eliminar/<int:id>", methods=["POST"])
def eliminar_donacion(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    donacion = Donacion.query.get_or_404(id)
    if donacion.user_id != session['user_id']:
        flash("No tienes permiso para eliminar esta donación.", "danger")
        return redirect(url_for('ver_donaciones'))
    
    if donacion.imagen:
        path_imagen = os.path.join(app.config["UPLOAD_FOLDER"], donacion.imagen)
        if os.path.exists(path_imagen):
            os.remove(path_imagen)
            
    db.session.delete(donacion)
    db.session.commit()
    flash("Donación eliminada con éxito", "success")
    return redirect(url_for('ver_donaciones'))

# Rutas para Servicios
@app.route("/servicios/publicar", methods=["GET", "POST"])
def publicar_servicio():
    if 'user_id' not in session:
        flash('Debes iniciar sesión para publicar un servicio.', 'danger')
        return redirect(url_for('login'))

    if request.method == 'POST':
        titulo = request.form["titulo"]
        descripcion = request.form["descripcion"]
        ubicacion = request.form["ubicacion"]
        contacto = request.form["contacto"]
        user_id = session['user_id']
        
        nuevo_servicio = Servicio(
            titulo=titulo,
            descripcion=descripcion,
            ubicacion=ubicacion,
            contacto=contacto,
            user_id=user_id
        )
        db.session.add(nuevo_servicio)
        db.session.commit()

        flash("Servicio publicado con éxito", "success")
        return redirect(url_for('ver_servicios'))
    
    return render_template('publicar_servicio.html')

@app.route("/servicios/ver", methods=["GET"])
def ver_servicios():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user_id = session['user_id']
    servicios = Servicio.query.filter_by(user_id=user_id).all()
    return render_template('ver_servicios.html', servicios=servicios)

@app.route("/servicios/editar/<int:id>", methods=["GET", "POST"])
def editar_servicio(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    servicio = Servicio.query.get_or_404(id)
    if servicio.user_id != session['user_id']:
        flash("No tienes permiso para editar este servicio.", "danger")
        return redirect(url_for('ver_servicios'))

    if request.method == "POST":
        servicio.titulo = request.form["titulo"]
        servicio.descripcion = request.form["descripcion"]
        servicio.ubicacion = request.form["ubicacion"]
        servicio.contacto = request.form["contacto"]
        
        db.session.commit()
        flash("Servicio actualizado con éxito", "success")
        return redirect(url_for('ver_servicios'))
    
    return render_template('editar_servicio.html', servicio=servicio)

@app.route("/servicios/eliminar/<int:id>", methods=["POST"])
def eliminar_servicio(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    servicio = Servicio.query.get_or_404(id)
    if servicio.user_id != session['user_id']:
        flash("No tienes permiso para eliminar este servicio.", "danger")
        return redirect(url_for('ver_servicios'))
        
    db.session.delete(servicio)
    db.session.commit()
    flash("Servicio eliminado con éxito", "success")
    return redirect(url_for('ver_servicios'))

# Rutas para Ayuda
@app.route("/ayuda/solicitar", methods=["GET", "POST"])
def solicitar_ayuda():
    if 'user_id' not in session:
        flash('Debes iniciar sesión para solicitar ayuda.', 'danger')
        return redirect(url_for('login'))

    if request.method == 'POST':
        titulo = request.form["titulo"]
        descripcion = request.form["descripcion"]
        ubicacion = request.form["ubicacion"]
        contacto = request.form["contacto"]
        imagen = request.files.get("imagen")
        user_id = session['user_id']

        filename = None
        if imagen and imagen.filename != '':
            filename = secure_filename(imagen.filename)
            imagen.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
        
        nueva_ayuda = Ayuda(
            titulo=titulo,
            descripcion=descripcion,
            ubicacion=ubicacion,
            contacto=contacto,
            imagen=filename,
            user_id=user_id
        )
        db.session.add(nueva_ayuda)
        db.session.commit()

        flash("Solicitud de ayuda publicada con éxito", "success")
        return redirect(url_for('ver_ayuda'))

    return render_template('solicitar_ayuda.html')

@app.route("/ayuda/ver", methods=["GET"])
def ver_ayuda():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user_id = session['user_id']
    ayudas = Ayuda.query.filter_by(user_id=user_id).all()
    return render_template('ver_ayuda.html', ayudas=ayudas)

@app.route("/ayuda/editar/<int:id>", methods=["GET", "POST"])
def editar_ayuda(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    ayuda = Ayuda.query.get_or_404(id)
    if ayuda.user_id != session['user_id']:
        flash("No tienes permiso para editar esta solicitud de ayuda.", "danger")
        return redirect(url_for('ver_ayuda'))

    if request.method == "POST":
        ayuda.titulo = request.form["titulo"]
        ayuda.descripcion = request.form["descripcion"]
        ayuda.ubicacion = request.form["ubicacion"]
        ayuda.contacto = request.form["contacto"]
        
        imagen = request.files.get("imagen")
        if imagen and imagen.filename != '':
            if ayuda.imagen:
                path_anterior = os.path.join(app.config["UPLOAD_FOLDER"], ayuda.imagen)
                if os.path.exists(path_anterior):
                    os.remove(path_anterior)

            filename = secure_filename(imagen.filename)
            imagen.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
            ayuda.imagen = filename

        db.session.commit()
        flash("Solicitud de ayuda actualizada con éxito", "success")
        return redirect(url_for('ver_ayuda'))

    return render_template('editar_ayuda.html', ayuda=ayuda)

@app.route("/ayuda/eliminar/<int:id>", methods=["POST"])
def eliminar_ayuda(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    ayuda = Ayuda.query.get_or_404(id)
    if ayuda.user_id != session['user_id']:
        flash("No tienes permiso para eliminar esta solicitud de ayuda.", "danger")
        return redirect(url_for('ver_ayuda'))
    
    if ayuda.imagen:
        path_imagen = os.path.join(app.config["UPLOAD_FOLDER"], ayuda.imagen)
        if os.path.exists(path_imagen):
            os.remove(path_imagen)
            
    db.session.delete(ayuda)
    db.session.commit()
    flash("Solicitud de ayuda eliminada con éxito", "success")
    return redirect(url_for('ver_ayuda'))


# Cargar los datos en busqueda avanzada
@app.route('/busqueda_avanzada')
def busqueda_avanzada():
    # Obtiene el tipo de publicacion desde los parámetros de la URL
    tipo_busqueda = request.args.get('tipo', 'todos').lower()
    
    publicaciones = []
    
    # Filtra las publicaciones 
    if tipo_busqueda == 'donacion' or tipo_busqueda == 'todos':
        donaciones = Donacion.query.all()
        for d in donaciones:
            publicaciones.append({
                'tipo': 'donacion',
                'titulo': d.titulo,
                'descripcion': d.descripcion,
                'ubicacion': d.ubicacion,
                'imagen': d.imagen,
                'usuario': User.query.get(d.user_id).username
            })
    
    if tipo_busqueda == 'servicio' or tipo_busqueda == 'todos':
        servicios = Servicio.query.all()
        for s in servicios:
            publicaciones.append({
                'tipo': 'servicio',
                'titulo': s.titulo,
                'descripcion': s.descripcion,
                'ubicacion': s.ubicacion,
                'contacto': s.contacto,
                'usuario': User.query.get(s.user_id).username
            })
    
    if tipo_busqueda == 'ayuda' or tipo_busqueda == 'todos':
        ayudas = Ayuda.query.all()
        for a in ayudas:
            publicaciones.append({
                'tipo': 'ayuda',
                'titulo': a.titulo,
                'descripcion': a.descripcion,
                'ubicacion': a.ubicacion,
                'contacto': a.contacto,
                'imagen': a.imagen,
                'usuario': User.query.get(a.user_id).username
            })
    
    return render_template('busqueda_avanzada.html', publicaciones=publicaciones, tipo_busqueda=tipo_busqueda)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)

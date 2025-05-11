from flask import Flask, render_template,request, redirect, url_for, session,flash
from datetime import date
import pymysql

app = Flask(__name__)
app.secret_key = 'clave-secreta'

@app.route("/")
def home():
    return render_template("index.html")


def conectar():
    return pymysql.connect(
        host="localhost",
        user="root",
        password="Vongola-45622298",
        database="zimmeck_store",
        cursorclass=pymysql.cursors.DictCursor
    )

@app.route("/login", methods=["GET", "POST"])
def login():
    #Si he enviado el formulario recoge el correo y la contraseña
    if request.method == "POST":
        email = request.form.get("login-email")
        password = request.form.get("login-password")

        #Comprobamos si el mail y la contraseña estan en la base de datos
        conexion = conectar()
        with conexion.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM CLIENTE WHERE email_cliente = %s AND contrasena = %s",
                (email, password)
            )
            cliente = cursor.fetchone()
        conexion.close()

    #Si encontramos que el cliente existe guardamos el id en la session y mostramos el mensaje. Finalmente lo redirigimos al inicio
        if cliente:
            session["cliente_id"] = cliente["id_cliente"]
            flash("Sesión iniciada correctamente.", "success")
            return redirect(url_for("home"))
    #En caso contrario mostraremos un mensaje de que uno de los campos no es correcto
        else:
            flash("correo o contraseña erroneas.", "error")
    return render_template("login.html")


@app.route("/register", methods=["POST"])
def register():
    #Valores que nos llegan del formulario
    email = request.form.get("register-email")
    password = request.form.get("register-password")
    confirm = request.form.get("confirm-password")
    #Si la contraseñas no coinciden se envia un mensaje de error con flash y se redirige al login
    if password != confirm:
        flash("Las contraseñas no coinciden", "error")
        return redirect(url_for("login"))
    #Conectamos con la base de datos para comprobar si ya existe ese correo y en el caso de que si redirige al login
    conexion = conectar()
    with conexion.cursor() as cursor:
        cursor.execute("SELECT * FROM CLIENTE WHERE email_cliente = %s", (email,))
        if cursor.fetchone():
            flash("El correo ya está registrado", "error")
            conexion.close()
            return redirect(url_for("login"))
        #Si no existe introducimos los valores en la base de datos en la tabla de cliente y mostramos un mensaje de confirmacion
        cursor.execute("""
            INSERT INTO CLIENTE (nombre_cliente, apellidos_cliente, email_cliente, fecha_registro, contrasena)
            VALUES (%s, %s, %s, %s, %s)
        """, ("", "", email, date.today(), password))
        conexion.commit()
    conexion.close()

    flash("Registro exitoso. Ahora puedes iniciar sesión.", "success")
    return redirect(url_for("login"))

#El logout esta funcional pero no consegui hacer que en el formulario me apareciese el boton de la forma que queria
@app.route("/logout")
def logout():
    session.clear()
    flash("Sesión cerrada correctamente.", "success")
    return redirect(url_for("home"))

#Endpoint para llegar a la pagina comission se hara su lógica en el futuro
@app.route("/comission")
def comission():
    return render_template("comission.html")

#Endpoint para llegar a la pagina post se hara su lógica en el futuro
@app.route("/posts")
def posts():
    return render_template("posts.html")


@app.route("/categories")
def categories():
    return render_template("categories.html")

#Mostrar todos los productos dentro de una categoria
@app.route("/category/<name>")
def show_category(name):
    #Cambiamos el nombre quitando los guiones o espacios y lo juntamos y pasamos a minuscula
    nombre_categoria = name.replace("-", " ").strip().lower()

    conexion = conectar()
    #Buscamos en la base de datos todas las categorías que existen
    with conexion.cursor() as cursor:
        cursor.execute("SELECT id_filtro, nombre_filtro FROM CATEGORIA")
        categorias = cursor.fetchall()

    # Buscamos la categoria que le hemos pasado comparando con el nombre sin minusculas, mayusculas etc.
    categoria_encontrada = next(
        (c for c in categorias if c["nombre_filtro"].strip().lower() == nombre_categoria), None
    )
    #Si no la encontramos da error
    if not categoria_encontrada:
        return "Categoría no encontrada", 404
    #En caso de que si guarda el Id de la categoria y busca los productos dentro de esa categoria
    id_filtro = categoria_encontrada["id_filtro"]

    with conexion.cursor() as cursor:
        cursor.execute("SELECT * FROM PRODUCTO WHERE id_filtro = %s", (id_filtro,))
        productos = cursor.fetchall()

    #Cierra la conexion y renderiza la pagina con la categoria en concreto y sus productos
    conexion.close()
    return render_template("category.html", category_title=categoria_encontrada["nombre_filtro"], products=productos)


#Ruta para mostrar un producto en concreto de una categoria
@app.route("/category/<categoria>/producto/<nombre_producto>")
def mostrar_producto(categoria, nombre_producto):
    #Llamamos a la funcion de get_producto para conectar con la base de datos y buscar si el producto esta en esta
    producto = get_producto_por_nombre(nombre_producto)
    #Si esta mostramos la página del producto en caso contrario dara un error 404
    if producto:
        return render_template("producto.html", producto=producto, categoria=categoria)
    else:
        return "Producto no encontrado", 404

#Buscamos el producto por su nombre en la base de datos
def get_producto_por_nombre(nombre_producto):
    conexion = conectar()
    #Busca en la base de datos si hay algún producto con el mismo nombre que hemos pasado
    with conexion.cursor() as cursor:
        cursor.execute("SELECT * FROM PRODUCTO WHERE nombre_producto = %s", (nombre_producto,))
        producto = cursor.fetchone()
    conexion.close()
    return producto


@app.route("/agregar_producto", methods=["GET", "POST"])
def agregar_producto():
    #Conectamos a la base de datos y mostramos todas las categorias disponibles en el formulario
    conexion = conectar()
    with conexion.cursor() as cursor:
        cursor.execute("SELECT id_filtro, nombre_filtro FROM CATEGORIA")
        categorias = cursor.fetchall()
        #Si se ha enviado el formulario recoge todos los datos
        if request.method == "POST":
            nombre = request.form.get("nombre")
            descripcion = request.form.get("descripcion")
            precio = request.form.get("precio")
            categoria = request.form.get("categoria")
            imagen = request.form.get("imagen")

            #Insertamos el nuevo producto en la base de datos
            cursor.execute("""
                INSERT INTO PRODUCTO (nombre_producto, descripcion, precio, fecha_creacion, imagen_url_producto, id_filtro)
                VALUES (%s, %s, %s, CURDATE(), %s, %s)
            """, (nombre, descripcion, precio, imagen, categoria))
            conexion.commit()
            #Mostramos un mensaje de que se ha creado como toca
            flash("Producto agregado correctamente.", "success")
            return redirect(url_for("categories"))

    conexion.close()
    return render_template("agregar_productos.html", categorias=categorias)


#Ruta del blog aun no hace nada solo renderiza
@app.route("/blog")
def blog():
    return render_template("blog.html")
#Ruta del aboutme aun no hace nada solo renderiza
@app.route("/aboutme")
def aboutme():
    return render_template("aboutme.html")

#Ruta para ver el carrito
@app.route("/carrito")
def carrito():
    #Comprobamos que el cliente haya iniciado sesion y obtenemos el id
    if "cliente_id" not in session:
        flash("Debes iniciar sesión", "error")
        return redirect(url_for("login"))

    id_cliente = session["cliente_id"]
    #obtenemos su id del carrito sin crear uno nuevo
    id_carrito = obtener_o_crear_carrito(id_cliente, crear_si_no_existe=False)

    #Creamos las para mostrar los productos, su total en precio y cantidad
    productos = []
    total_precio = 0
    total_productos = 0

    #Si encontramos un carrito, obtenemos todos los productos asociados a el
    if id_carrito:
        conexion = conectar()
        with conexion.cursor() as cursor:
            cursor.execute("""
                SELECT p.id_producto, p.nombre_producto, p.precio, p.imagen_url_producto, cp.cantidad
                FROM CARRITO_PRODUCTO cp
                JOIN PRODUCTO p ON cp.id_producto = p.id_producto
                WHERE cp.id_carrito = %s
            """, (id_carrito,))
            productos = cursor.fetchall()
            #Calculamos el total del precio de los productos y el numero de estos
            for p in productos:
                total_precio += (p["precio"] or 0) * p["cantidad"]
                total_productos += p["cantidad"]
        conexion.close()

    return render_template("carrito.html", productos=productos, total_precio=total_precio, total_productos=total_productos)

#Funcion para crear o obtener el carrito activo del usuario
def obtener_o_crear_carrito(cliente_id, crear_si_no_existe=True):
    #nos conectamos a la base de datos y buscamos si hay un carrito activo del cliente
    conexion = conectar()
    with conexion.cursor() as cursor:
        cursor.execute("SELECT id_carrito FROM CARRITO WHERE id_cliente = %s AND estado = 'activo'", (cliente_id,))
        carrito = cursor.fetchone()
    #Si lo encontramos guardamos su id sino lo creamos con la fecha y el estado como activo y guardamos su id
        if carrito:
            id_carrito = carrito["id_carrito"]
        elif crear_si_no_existe:
            cursor.execute("""
                INSERT INTO CARRITO (id_cliente, fecha_creacion, estado)
                VALUES (%s, %s, 'activo')
            """, (cliente_id, date.today()))
            conexion.commit()
            id_carrito = cursor.lastrowid
        else:
            id_carrito = None
    conexion.close()
    return id_carrito


@app.route("/agregar_carrito", methods=["POST"])
def agregar_carrito():
    #Comprobamos que el cliente ha iniciado sesion
    if "cliente_id" not in session:
        flash("Debes iniciar sesión para agregar productos al carrito", "error")
        return redirect(url_for("login"))
#Obtenemos el id del producto y el usuario y buscamos si existe un carrito activo en caso de que no se crea
    id_producto = request.form.get("id_producto")
    id_cliente = session["cliente_id"]
    id_carrito = obtener_o_crear_carrito(id_cliente)

#Comprobamos en la base de datos si el producto ya se encuentra en el carrito
    conexion = conectar()
    with conexion.cursor() as cursor:
        cursor.execute("""
            SELECT cantidad FROM CARRITO_PRODUCTO
            WHERE id_carrito = %s AND id_producto = %s
        """, (id_carrito, id_producto))
        existente = cursor.fetchone()
        #Si ya existe le aumentamos la cantidad en 1 sino existe lo añadimos
        if existente:
            cursor.execute("""
                UPDATE CARRITO_PRODUCTO
                SET cantidad = cantidad + 1
                WHERE id_carrito = %s AND id_producto = %s
            """, (id_carrito, id_producto))
        else:
            cursor.execute("""
                INSERT INTO CARRITO_PRODUCTO (id_carrito, id_producto, cantidad)
                VALUES (%s, %s, 1)
            """, (id_carrito, id_producto))

        conexion.commit()
    conexion.close()

    flash("Producto añadido al carrito", "success")
    return redirect(request.referrer or url_for("home"))


@app.route("/eliminar_carrito/<int:id_producto>")
def eliminar_producto_carrito(id_producto):
    #Comprobamos que eel cliente ha iniciado sesion
    if "cliente_id" not in session:
        flash("Debes iniciar sesión", "error")
        return redirect(url_for("login"))

    #Obtenemos el id del cliente y el del carrito activo, si no hay carrito salta un error
    id_cliente = session["cliente_id"]
    id_carrito = obtener_o_crear_carrito(id_cliente, crear_si_no_existe=False)

    if not id_carrito:
        flash("No tienes un carrito activo.", "error")
        return redirect(url_for("carrito"))

#Nos conectamos a la base de datos y eliminamos el producto
    conexion = conectar()
    with conexion.cursor() as cursor:
        cursor.execute("""
            DELETE FROM CARRITO_PRODUCTO
            WHERE id_carrito = %s AND id_producto = %s
        """, (id_carrito, id_producto))
        conexion.commit()
    conexion.close()

    flash("Producto eliminado del carrito", "success")
    return redirect(url_for("carrito"))


@app.route("/finalizar_pedido")
def finalizar_pedido():
    #Comprobamos que el cliente esta loggeado
    if "cliente_id" not in session:
        flash("Debes iniciar sesión para finalizar el pedido.", "error")
        return redirect(url_for("login"))
#obtenemos el id del cliente y el carrito, en caso de que no exista salta un mensaje de error
    id_cliente = session["cliente_id"]
    id_carrito = obtener_o_crear_carrito(id_cliente, crear_si_no_existe=False)

    if not id_carrito:
        flash("No hay un carrito activo para finalizar.", "error")
        return redirect(url_for("carrito"))
#si hay un carrito cambiamos el estado ha finalizado y mandamos un mensaje
    conexion = conectar()
    with conexion.cursor() as cursor:
        cursor.execute("UPDATE CARRITO SET estado = 'finalizado' WHERE id_carrito = %s", (id_carrito,))
        conexion.commit()
    conexion.close()

    flash("Pedido finalizado correctamente.", "success")
    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(debug=True)

from flask import Flask, request, render_template, redirect, url_for, session, flash
import pymssql
from azure.storage.blob import BlobServiceClient

from flask_bcrypt import Bcrypt
import re
from collections import namedtuple

# Configurations Flask
app = Flask(__name__, static_folder='static')
app.secret_key = ' '

# Initialisation Flask-Bcrypt
bcrypt = Bcrypt(app)
# Configurations Azure
AZURE_CONNECTION_STRING = ' '
DATABASE_URL = ' '
DATABASE_USER = ' '
DATABASE_PASSWORD = ' '
CONTAINER_NAME = " "

# Initialisation Azure Blob Storage
try:
    blob_service_client = BlobServiceClient.from_connection_string(AZURE_CONNECTION_STRING)
    container_client = blob_service_client.get_container_client(CONTAINER_NAME)
    if not container_client.exists():
        container_client.create_container()
        print(f"Container '{CONTAINER_NAME}' créé.")
    else:
        print(f"Connexion réussie au container : {CONTAINER_NAME}")
except Exception as e:
    raise RuntimeError(f"Erreur de configuration Blob Storage : {e}")


# Fonction pour se connecter à la base de données SQL
def get_db_connection():
    try:
        conn = pymssql.connect(
            DATABASE_URL,
            DATABASE_USER,
            DATABASE_PASSWORD,
            " "
        )
        return conn
    except Exception as e:
        raise RuntimeError(f"Erreur de connexion à la base SQL : {e}")


# Route pour afficher la galerie
@app.route('/')
def home():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        # Récupère les photos avec le nom d'utilisateur
        cursor.execute("""
            SELECT photos.id, photos.file_url, photos.user_id, users.username 
            FROM photos 
            INNER JOIN users ON photos.user_id = users.id
        """)
        # Créer une structure nommée pour chaque photo avec username
        Photo = namedtuple('Photo', ['id', 'file_url', 'user_id', 'username'])
        photos = [Photo(*row) for row in cursor.fetchall()]  # Transforme chaque ligne en Photo
        conn.close()
        return render_template('index.html', photos=photos, current_user=session.get('user_id'))
    except Exception as e:
        app.logger.error(f"Erreur d'accès au container : {e}")
        return render_template('error.html', message="Impossible d'accéder à la galerie.")


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if not username or not email or not password:
            flash("Tous les champs sont obligatoires.", "error")
            return redirect(url_for('register'))

        if password != confirm_password:
            flash("Les mots de passe ne correspondent pas.", "error")
            return redirect(url_for('register'))

        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            flash("Email invalide.", "error")
            return redirect(url_for('register'))

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Utilisation de %s pour la requête sécurisée
            cursor.execute(
                "INSERT INTO users (username, email, password) VALUES (%s, %s, %s)",
                (username, email, hashed_password)
            )
            conn.commit()
            conn.close()

            flash("Inscription réussie ! Connectez-vous maintenant.", "success")
            return redirect(url_for('login'))
        except pymssql.DatabaseError as db_err:
            flash("Erreur lors de l'inscription. Veuillez réessayer.", "error")
            app.logger.error(f"Erreur SQL : {db_err}")
        except Exception as e:
            flash("Une erreur inattendue est survenue.", "error")
            app.logger.error(f"Erreur : {e}")

    return render_template('register.html')

# Route de connexion
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Requête sécurisée avec %s
            cursor.execute("SELECT id, username, password FROM users WHERE email = %s", (email,))
            user = cursor.fetchone()
            conn.close()

            if user:
                user_id, username, hashed_password = user
                if bcrypt.check_password_hash(hashed_password, password):
                    session['user_id'] = user_id
                    session['username'] = username
                    flash("Connexion réussie !", "success")
                    return redirect(url_for('home'))
                else:
                    flash("Mot de passe incorrect.", "error")
            else:
                flash("Email non trouvé.", "error")
        except pymssql.DatabaseError as db_err:
            flash("Erreur de base de données. Veuillez réessayer plus tard.", "error")
            app.logger.error(f"Erreur SQL : {db_err}")
        except Exception as e:
            flash("Erreur inattendue. Veuillez réessayer.", "error")
            app.logger.error(f"Erreur inattendue : {e}")

        return redirect(url_for('login'))

    return render_template('login.html')

# Route de déconnexion
@app.route('/logout', methods=['POST'])
def logout():
    session.clear()  # Supprime toutes les données de session
    flash("Vous avez été déconnecté avec succès.", "success")
    return redirect(url_for('login'))  # Redirige vers la page de connexion

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        file = request.files.get('photo')
        if not file:
            flash("Aucun fichier sélectionné. Veuillez réessayer.", "error")
            return redirect(url_for('upload'))

        if not session.get('user_id'):
            flash("Vous devez être connecté pour uploader une photo.", "error")
            return redirect(url_for('login'))

        try:
            # Connexion au Blob Storage
            blob_client = container_client.get_blob_client(file.filename)

            # Vérification si le fichier existe déjà
            if blob_client.exists():
                flash("Un fichier avec ce nom existe déjà. Veuillez renommer votre fichier.", "error")
                return redirect(url_for('upload'))

            # Upload du fichier
            blob_client.upload_blob(file.read(), overwrite=True)

            # Ajout à la base de données
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO photos (file_url, user_id) VALUES (%s, %s)",
                (f"https://{blob_service_client.account_name}.blob.core.windows.net/{CONTAINER_NAME}/{file.filename}",
                 session.get('user_id'))
            )
            conn.commit()
            conn.close()

            flash("Photo uploadée avec succès.", "success")
            return redirect(url_for('home'))
        except pymssql.DatabaseError as db_err:
            app.logger.error(f"Erreur SQL lors de l'upload : {db_err}")
            flash("Erreur de base de données. Veuillez réessayer.", "error")
        except Exception as e:
            app.logger.error(f"Erreur inattendue lors de l'upload : {e}")
            flash("Une erreur inattendue est survenue. Veuillez réessayer.", "error")

    return render_template('upload.html')



@app.route('/error')
def error_page():
    return render_template('error.html', message="Une erreur inattendue est survenue.")

@app.route('/users')
def users():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users")
        users = cursor.fetchall()
        conn.close()
        return render_template('users.html', users=users)
    except Exception as e:
        app.logger.error(f"Erreur lors de la récupération des utilisateurs : {e}")
        return render_template('error.html', message="Impossible de récupérer les utilisateurs.")

@app.route('/delete/<int:photo_id>', methods=['POST'])
def delete_photo(photo_id):
    try:
        # Vérifie si l'utilisateur est connecté
        if not session.get('user_id'):
            flash("Vous devez être connecté pour supprimer une photo.", "error")
            return redirect(url_for('login'))

        conn = get_db_connection()
        cursor = conn.cursor()

        # Vérifie si l'utilisateur est le propriétaire de la photo
        cursor.execute("SELECT file_url, user_id FROM photos WHERE id = %s", (photo_id,))
        photo = cursor.fetchone()

        if not photo:
            flash("Photo introuvable.", "error")
            return redirect(url_for('home'))

        file_url, user_id = photo
        if user_id != session['user_id']:
            flash("Vous n'êtes pas autorisé à supprimer cette photo.", "error")
            return redirect(url_for('home'))

        # Supprime la photo de Blob Storage
        blob_name = file_url.split("/")[-1]
        blob_client = container_client.get_blob_client(blob_name)
        if blob_client.exists():
            blob_client.delete_blob()
        else:
            flash("Le fichier associé à cette photo n'existe pas dans le stockage.", "error")
            return redirect(url_for('home'))

        # Supprime la photo de la base de données
        cursor.execute("DELETE FROM photos WHERE id = %s", (photo_id,))
        conn.commit()
        conn.close()

        flash("Photo supprimée avec succès.", "success")
        return redirect(url_for('home'))
    except pymssql.DatabaseError as db_err:
        app.logger.error(f"Erreur SQL lors de la suppression de la photo : {db_err}")
        flash("Erreur de base de données. Veuillez réessayer.", "error")
    except Exception as e:
        app.logger.error(f"Erreur lors de la suppression de la photo : {e}")
        flash("Une erreur inattendue est survenue. Veuillez réessayer.", "error")
        return render_template('error.html', message="Impossible de supprimer la photo.")

if __name__ == '__main__':
    app.run(debug=True)
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import current_user, LoginManager, UserMixin, login_user, logout_user, login_required
from mysql_db import MySQL
import mysql.connector
from functools import wraps

app = Flask(__name__)
application = app
 
app.config.from_pyfile('config.py')

db = MySQL(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Для доступа необходимо пройти аутентификацию'
login_manager.login_message_category = 'warning'

class User(UserMixin):
    def __init__(self, user_id, user_login, role_id, first_name, last_name):
        self.id = user_id
        self.login = user_login
        self.role_id = role_id
        self.first_name = first_name
        self.last_name = last_name

def roles_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated_view(*args, **kwargs):
            if current_user.role_id not in roles:
                flash('У вас недостаточно привилегий!', 'warning')
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        return decorated_view
    return decorator

@login_manager.user_loader
def load_user(user_id):
    query = 'SELECT user_id, login, role_id, first_name, last_name FROM users WHERE user_id = %s'

    with db.connection().cursor(named_tuple=True) as cursor:
        cursor.execute(query, (user_id,))
        user = cursor.fetchone()

        return User(user.user_id, user.login, user.role_id, user.first_name, user.last_name) if user else None

@app.route('/')
def index():    
    
    query = 'SELECT a.*, b.filename FROM books a JOIN book_img b ON a.fk_imgname = b.id'
    
    try:
        with db.connection().cursor(named_tuple=True) as cursor:
            cursor.execute(query)
            books = cursor.fetchall()
            books_list = []
            for book in books:
                book_dict = {
                    'id': book[0],
                    'name': book[1],
                    'description': book[2],
                    'year': book[3],
                    'publisher': book[4],
                    'author': book[5],
                    'length': book[6],
                    'imgname': book[7] + '.webp'
                }
                books_list.append(book_dict)
    
    except mysql.connector.Error as err:
            flash(err, 'danger')
    
    return render_template('index.html', books_list=books_list)

@app.route('/logout', methods=['GET'])
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':

        login = request.form['login']
        password = request.form['password']
        check = request.form.get('remember') == 'on'

        query = 'SELECT user_id, login, role_id, first_name, last_name FROM users WHERE login=%s AND password=%s'
        
        try:
            with db.connection().cursor(named_tuple=True) as cursor:
                cursor.execute(query, (login, password))
                user = cursor.fetchone()
                
                if user:
                    login_user(User(user.user_id, user.login, user.role_id, user.first_name, user.last_name), remember=check)
                    flash('Вы успешно вошли!', 'success')
                    return redirect(url_for('index'))
                else:
                    flash('Неверные учетные данные.', 'danger')

        except mysql.connector.Error as err:
            flash(err, 'danger')
            
    return render_template('login.html')

@app.route('/stats')
@login_required
@roles_required(1, 2)
def stats():
    return (render_template('stats.html'))

@app.route('/book_add')
@login_required
@roles_required(1)
def book_add():
    return (render_template('book_add.html'))

@app.route('/book_details')
def book_details():

    query = 'SELECT a.*, b.filename FROM books a JOIN book_img b ON a.fk_imgname = b.id'
    
    try:
        with db.connection().cursor(named_tuple=True) as cursor:
            cursor.execute(query)
            books = cursor.fetchall()
            books_list = []
            for book in books:
                book_dict = {
                    'id': book[0],
                    'name': book[1],
                    'description': book[2],
                    'year': book[3],
                    'publisher': book[4],
                    'author': book[5],
                    'length': book[6],
                    'imgname': book[7] + '.webp'
                }
                books_list.append(book_dict)
    
    except mysql.connector.Error as err:
            flash(err, 'danger')
    
    return render_template('book_details.html', books_list=books_list)

if __name__ == '__main__':
    app.run(debug=True)
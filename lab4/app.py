from typing import Dict
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from mysql_db import MySQL
import mysql.connector
import re

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
    def __init__(self, id, user_login):
        self.id = id
        self.login = user_login


def password_validation(password: str) -> bool:
    reg = re.compile(r'''^(?=.*?[a-zа-я])(?=.*?[A-ZА-Я])(?=.*?[0-9])[-A-ZА-Яa-zа-я\d~!?@#$%^&*_+()\[\]{}></\\|"'.,:;]{8,128}$''')
    return bool(reg.match(password))


def login_validation(login: str) -> bool:
    reg = re.compile(r'^[0-9a-zA-Z]{5,}$')
    return bool(reg.match(login))


def validate(login: str, password: str, last_name: str, first_name: str) -> Dict[str, str]:
    errors = {}

    if not password_validation(password):
        errors['p_class'] = "is-invalid"
        errors['p_message_class'] = "invalid-feedback"
        errors['p_message'] = '''Пароль не удовлетворяет одному из следующих требований:
                                не менее 8 символов;
                                не более 128 символов;
                                как минимум одна заглавная и одна строчная буква;
                                только латинские или кириллические буквы;
                                как минимум одна цифра;
                                только арабские цифры;
                                без пробелов;
                                Другие допустимые символы:~ ! ? @ # $ % ^ & * _ - + ( ) [ ] { } > < / \ | " ' . , : ;'''

    if not login_validation(login):
        errors['l_class'] = "is-invalid"
        errors['l_message_class'] = "invalid-feedback"
        errors['l_message'] = "Логин должен состоять только из латинских букв и цифр и иметь длину не менее 5 символов"

    if len(login) == 0:
        errors['l_class'] = "is-invalid"
        errors['l_message_class'] = "invalid-feedback"
        errors['l_message'] = "Логин не должен быть пустым"

    if len(password) == 0:
        errors['p_class'] = "is-invalid"
        errors['p_message_class'] = "invalid-feedback"
        errors['p_message'] = "Пароль не должен быть пустым"

    if len(last_name) == 0:
        errors['ln_class'] = "is-invalid"
        errors['ln_message_class'] = "invalid-feedback"
        errors['ln_message'] = "Фамилия не должна быть пустой"

    if len(first_name) == 0:
        errors['fn_class'] = "is-invalid"
        errors['fn_message_class'] = "invalid-feedback"
        errors['fn_message'] = "Имя не должно быть пустым"

    return errors


@login_manager.user_loader
def load_user(id):
    query = 'SELECT id, login FROM users2 WHERE id = %s'

    with db.connection().cursor(named_tuple=True) as cursor:
        cursor.execute(query, (id,))
        user = cursor.fetchone()

        return User(user.id, user.login) if user else None


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':

        login = request.form['login']
        password = request.form['password']
        check = request.form.get('secretcheck') == 'on'
        
        query = 'SELECT id, login FROM users2 WHERE login=%s AND password_hash=SHA2(%s, 256)'
        
        try:
            with db.connection().cursor(named_tuple=True) as cursor:
                cursor.execute(query, (login, password))
                user = cursor.fetchone()
                
                if user:
                    login_user(User(user.id, user.login), remember=check)
                    next_url = request.args.get('next') or url_for('index')
                    flash('Вы успешно вошли!', 'success')
                    return redirect(next_url)
                else:
                    flash('Неверные учетные данные.', 'danger')

        except mysql.connector.errors.DatabaseError as err:
            flash(str(err), 'danger')
            
    return render_template('login.html')


@app.route('/logout', methods=['GET'])
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/users/')
@login_manager.user_loader
def load_user(id):
    query = 'SELECT * FROM users2 WHERE id = %s'
    with db.connection().cursor(named_tuple=True) as cursor:
        cursor.execute(query, (id,))
        user = cursor.fetchone()
        return User(user.id, user.login) if user else None


@app.route('/users/create', methods=['POST', 'GET'])
@login_required
def create():
    if request.method == 'POST':

        login = request.form['login']
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        password = request.form['password']

        errors = validate(login, password, last_name, first_name)
        if errors:
            return render_template('users/create.html', **errors)

        insert_query = '''INSERT INTO users2 (login, last_name, first_name, password_hash)
                            VALUES (%s, %s, %s, SHA2(%s, 256))'''

        try:
            with db.connection().cursor(named_tuple=True) as cursor:
                cursor.execute(insert_query, (login, last_name, first_name, password))
                db.connection().commit()
                flash(f'Пользователь {login} успешно создан.', 'success')

        except mysql.connector.errors.DatabaseError as err:
            db.connection().rollback()
            flash(err, 'danger')

            return render_template('users/create.html')

    return render_template('users/create.html')


@app.route('/users/show/<int:id>')
def show_user(id):

    query = 'SELECT * FROM users2 WHERE id = %s'

    with db.connection().cursor(named_tuple=True) as cursor:
        cursor.execute(query, (id,))
        user = cursor.fetchone()

    return render_template('users/show.html', user=user)


@app.route('/users/edit/<int:id>', methods=["POST", "GET"])
def edit(id):
    if request.method == 'POST':

        first_name = request.form['first_name']
        last_name = request.form['last_name']
        
        update_query = 'UPDATE users2 SET first_name = %s, last_name = %s WHERE id = %s'

        try:
            with db.connection().cursor(named_tuple=True) as cursor:
                cursor.execute(update_query, (first_name, last_name, id))
                db.connection().commit()
                flash(f'Данные пользователя {first_name} успешно обновлены.', 'success')

        except mysql.connector.errors.DatabaseError as err:
            db.connection().rollback()
            flash(err, 'danger')

            return render_template('users/edit.html')

    select_query = 'SELECT * FROM users2 WHERE id = %s'

    with db.connection().cursor(named_tuple=True) as cursor:
        cursor.execute(select_query, (id,))
        user = cursor.fetchone()

    return render_template('users/edit.html', user=user)


@app.route('/users/delete/')
@login_required
def delete():
    try:
        id = request.args.get('id')
        query = 'DELETE FROM users2 WHERE id = %s'

        with db.connection().cursor(named_tuple=True) as cursor:
            cursor.execute(query, (id,))
            db.connection().commit()
            flash(f'Пользователь {id} успешно удален.', 'success')

    except mysql.connector.errors.DatabaseError:
        db.connection().rollback()
        flash('При удалении пользователя произошла ошибка.', 'danger')

    return redirect(url_for('show_users'))


@app.route('/pass_change', methods=["POST", "GET"])
@login_required
def change():
    if request.method == "POST":

        id = current_user.id
        password = request.form['password']
        n_password = request.form['n_password']
        n_password_2 = request.form['n2_password']
        
        check_password_query = 'SELECT * FROM users2 WHERE id = %s AND password_hash = SHA2(%s, 256)'
        
        try:
            with db.connection().cursor(named_tuple=True) as cursor:
                cursor.execute(check_password_query, (id, password))
                user = cursor.fetchone()
                
                if not user:
                    flash('Старый пароль не соответствует текущему', 'danger')

                elif not password_validation(n_password):
                    flash('Новый пароль не соответствует требованиям', 'danger')

                elif n_password != n_password_2:
                    flash('Пароли не совпадают', 'danger')

                else:
                    update_password_query = 'UPDATE users2 SET password_hash = SHA2(%s, 256) WHERE id = %s'
                    cursor.execute(update_password_query, (n_password, id))
                    db.connection().commit()
                    flash('Пароль успешно обновлен.', 'success')

                    return redirect(url_for('index'))

        except mysql.connector.errors.DatabaseError as err:
            db.connection().rollback()
            flash(err, 'danger')
            
        return render_template('users/change.html')

    return render_template('users/change.html')

if __name__ == '__main__':
    app.run(debug=True)
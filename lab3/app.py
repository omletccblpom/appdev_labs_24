from flask import Flask, render_template, request, session, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required

app = Flask(__name__)

application = app

app.config.from_pyfile('config.py')

login_manager = LoginManager()

login_manager.init_app(app)

login_manager.login_view = 'login'
login_manager.login_message = 'Для доступа необходимо пройти аутентификацию'
login_manager.login_message_category = 'warning'

users = [
    {
        'id': 1,
        'login': 'amogus',
        'password': 'amogus',
    },
]

class User(UserMixin):
    def __init__(self, user_id, user_login):
        self.id = user_id
        self.login = user_login

@login_manager.user_loader
def load_user(user_id):
    for user in users:
        if user['id'] == int(user_id):
            return User(user['id'], user['login'])
    return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/visits')
def visits():
    if 'count' in session:
        session['count'] += 1
    else:
        session['count'] = 1
    return render_template('visits.html')

@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        login = request.form['login']
        password = request.form['password']
        check = request.form.get('secretcheck') == 'on'
        for user in users:
            if login == user['login'] and password == user['password']:
                login_user(User(user['id'], user['login']), remember=check)
                param_url = request.args.get('next')
                flash('Вы успешно вошли!', 'success')
                return redirect(param_url or url_for('index'))
            else:
                flash('Ошибка входа', 'danger')
    return render_template('login.html')

@app.route('/logout', methods=['GET'])
def logout():   
    logout_user()
    return redirect(url_for('index'))

@app.route('/secret_page', methods=['GET'])
@login_required
def secret_page():
    return render_template('secret_page.html')

if __name__ == '__main__':
    app.run()
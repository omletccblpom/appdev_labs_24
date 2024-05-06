from flask import Flask, render_template, make_response, request

app = Flask(__name__)

application = app


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/url')
def url():
    return render_template('url.html', title="Параметры URL", )


@app.route('/headers')
def headers():
    return render_template('headers.html', title="Заголовки")


@app.route('/cookies')
def cookies():
    resp = make_response(render_template('cookies.html', title="Куки"))
    if 'user' in request.cookies:
        resp.delete_cookie('user')
    else:
        resp.set_cookie('user', 'admin')
    return resp


@app.route('/forms', methods=['GET', 'POST'])
def forms():
    return render_template('forms.html', title="Параметры формы")


@app.route('/calc')
def calc():
    a, b = float(request.args.get('a', 0)), float(request.args.get('b', 0))

    result = 0
    match request.args.get('operator'):
        case "+":
            result = a + b
        case "-":
            result = a - b
        case "*":
            result = a * b
        case "/":
            result = a / b

    return render_template('calc.html', title="Калькулятор", result=result)


@app.route("/phoneNumber", methods=["POST", "GET"])
def phoneNumber():
    if request.method == 'POST':
        phone = request.form["phone"]

        phone_num = [digit for digit in phone if digit.isdigit()]
        if not phone_num:
            phone_num.append("")

        error = ""
        if not all([symbol in [" ", "(", ")", "-", ".", "+", *list(map(str, list(range(10))))] for symbol in phone]):
            error = "Позорник, ты не то вводишь!"
        elif ((phone_num[0] in ["7", "8"] and len(phone_num) != 11) or
              phone_num[0] not in ["7", "8"] and len(phone_num) != 10):
            error = "Позорник, не столько цифр в номере!"

        if error != "":
            return render_template("phoneNumber.html", title="Номер телефона", phone=error)

        if len(phone_num) == 10:
            phone_num.insert(0, "8")

        return render_template("phoneNumber.html", title="Номер телефона",
                               phone="8-{1}{2}{3}-{4}{5}{6}-{7}{8}-{9}{10}".format(*phone_num))
    else:
        return render_template("phoneNumber.html", title="Номер телефона")


if __name__ == '__main__':
    app.run()

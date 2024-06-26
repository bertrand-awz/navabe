import json
from flask import Flask, render_template, jsonify, session, request, redirect, url_for, make_response, Blueprint
from datetime import datetime
from time import sleep
from static.scripts.requests import send_data, user_authentification, get_user, set_user, \
    send_mail, pass_generator, change_user_password, makeOrder, checkItem
from static.scripts.admin import Admin, search_books, set_new_password_to, statistics_of_stock, price_average, \
    statistics_of_orders, search_order, statistics_of_sales

app = Flask(__name__)
app.secret_key = b'w\xd5\xea\xd0\xa2\xf6\xcb\x1e\x80\x04\xc1?\xee^\n\xe3'
admin_blueprint = Blueprint('admin', __name__, url_prefix='/administration')


@app.route('/')
@app.route('/main')
def main():
    return render_template('main.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """
    Enregistrement de l'utilisateur
    """
    if request.method == 'POST':
        user_infos = {
            'name': request.form.get('name'),
            'firstname': request.form.get('firstname'),
            'mail': request.form.get('email'),
            'address': request.form.get('address'),
            'password': request.form.get('password')
        }
        set_user(user_infos)
        return redirect(url_for('main'))
    return render_template('signup.html')


@app.route('/recovery', methods=['GET', 'POST'])
def recovery():
    """
    Permet à l'utilisateur de récupérer son compte
    """
    msg_missing = ""
    msg = "Hello {},\n\n" \
          "You have made a request for account recovery on {}.\n" \
          "Your old password has been invalidated, the password below will allow you to access your account\n\n" \
          "This is your new password : {}\n\n" \
          "To change it: \n" \
          "1) Login to your profile (with the code above)\n" \
          "2) Click on the human icon\n" \
          "3) And change your password\n\n" \
          "Regards,\n" \
          "The Navabe team"
    if request.method == "POST":

        if len(request.form.get('user_id')) > 0:
            temporary_pass = pass_generator()
            user = get_user(request.form['user_id'], False)

            if change_user_password(user, temporary_pass):
                msg = msg.format(user.get_firstname(),
                                 datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
                                 temporary_pass)
                send_mail(user, msg, "Account recovery")

                return redirect(url_for('main'))

            else:
                msg_missing = "No matching account"

    return render_template('recovery.html', MsgError=msg_missing)


@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    Accordes l'accès aux pages protégées
    si les identifiants utilisateurs sont corrects
    """

    msg_invalid_id = ""
    if request.method == 'POST':
        if user_authentification(request.form['email'], request.form['password']):
            user = get_user(request.form['email'])
            session[user.getId()] = user.getmail() + user.get_name()
            return redirect(url_for('set_cookie', mail=request.form['email']))
        else:
            msg_invalid_id = "Incorrect mail or password"
    return render_template('login.html', MsgError=msg_invalid_id)


@app.route('/logout', methods=['POST'])
def logout():
    """
    Supprime la session de l'user
    Supprime le cookie l'identifiant
    """
    print(request.form['id'])
    session.pop(request.form['id'])
    response = make_response(redirect(url_for('main')))
    response.set_cookie('crt-user-infos', '', max_age=0)

    return response


@app.route('/change_password', methods=['POST'])
def change_password():
    """
    Appelles la fonction changeant le mot de passe
    avec les données de l'utilisateur en arguments
    """
    print(request.form.get('id'), request.form.get('password'))

    if change_user_password(get_user(request.form.get('id'), False),
                            request.form.get('password')):
        response = make_response(redirect(url_for('main')))
        response.set_cookie('crt-user-infos', '', max_age=0)

        msg = "Hello {},\n\n" \
              "Your password has been successfully changed\n\n" \
              "Best regards,\n" \
              "The Navabe Team"
        user = get_user(request.form['id'], False)
        send_mail(user,
                  msg.format(user.get_firstname()),
                  "Password change")

        return response


@app.route('/getdata', methods=["GET", "POST"])
def getdata():
    """
    Transmet les données concernant les livres
    :return: Les données en transmettre à l'application web en format JSON
    """
    if request.method == "POST":
        # si la méthode est post, l'utilisateur est en train de faire une recherche
        searchWord = request.form.get('searchWord')
        if searchWord is not None:
            sleep(2.8) # On laisse le
            return jsonify(send_data(searchWord=searchWord))

    return jsonify(send_data())


@app.route('/check_stock', methods=['POST'])
def check_stock():
    """
    Fait appel au vérificateur de disponibilité
    :return: la réponse du vérificateur
    """
    isbn = request.form.get('isbn')
    qty = request.form.get('qty')

    if isbn is not None and qty is not None:
        return jsonify(checkItem(isbn, int(qty)))
    return jsonify(False)


@app.route('/make_order', methods=['POST'])
def make_order():
    transactID = request.form.get('transaction_id')
    user_id = request.form.get('user_id')
    contents = json.loads(request.form.get('contents'))
    content_with_title = json.loads(request.form.get('contentsBooksInfos'))
    amount = float(request.form.get('total'))

    user = get_user(user_id, False)
    print(user.get_name())
    if transactID is not None and user_id is not None \
            and contents is not None and amount is not None:
        return jsonify(makeOrder(user, transactID, contents, round(amount, 2), content_with_title))


@app.route('/set_cookie/<string:mail>')
def set_cookie(mail):
    """
    Crées et envoi un cookie de connection au navigateur client
    Pour lui permettre de ne pas saisir ses identifiants de connexion à tout bout de champs
    Le cookie a une durée de vie d'une session, c.-à-d. si l'utilisateur ferme son navigateur
    il perd sa connexion

    : param mail
    :return:
    """
    user = get_user(mail)
    response = make_response(redirect(url_for('main') + '#/user-settings'))
    response.set_cookie('crt-user-infos', user.get_data_cookies())

    return response


"""PARTIE 02: OUTILS D'ADMINISTRATION"""


@admin_blueprint.route("/", methods=["POST", "GET"])
@admin_blueprint.route("/main", methods=["POST", "GET"])
def main():
    """
    Menu principal d'admin
    """
    return render_template('admin.html')


@admin_blueprint.route("/admin-login", methods=['POST'])
def admin_login():
    """
    Connectes l'administrateur
    """
    if request.method == "POST":
        id = request.form.get('id')
        password = request.form.get('password')

        if id is not None and password is not None:
            if len(id) > 0 and len(password) > 0:
                admin = Admin(id, password)

                if admin.login():
                    session[admin.get_ID()] = admin.password

                    return jsonify({'connected': True, 'firstname': admin.get_firstname()})
    return jsonify({'connected': False})


@admin_blueprint.route("/get-books", methods=['POST'])
def get_books():
    """
    Envoies à l'admin les livres recherchés
    """
    if request.form.get('keyword') is not None:
        return jsonify(search_books(request.form.get('keyword')))
    return jsonify([])


@admin_blueprint.route("/check-session", methods=["POST"])
def check_session():
    """
    Vérifie si l'admin possède déjà une session ouverte
    :return: True si l'admin possède les bonnes infos de la session
    """
    admin_ID = ""
    if request.form.get('id') is not None:
        admin_ID = request.form.get('id')

    return jsonify({'status': session.get(admin_ID) is not None})


@admin_blueprint.route('/New_Admin', methods=['POST'])
def set_new_admin():
    """
    Permet la création d'un nouvel administrateur
    :return:
    """
    adminID = request.form.get('id')
    name = request.form.get('name')
    firstname = request.form.get('firstname')
    mail = request.form.get('mail')
    print(name, firstname, mail, adminID)
    if adminID is not None and name is not None and firstname is not None and mail is not None:
        admin = Admin(adminID, session.get(adminID))
        return jsonify({'op_success': admin.set_new_admin(name, firstname, mail)})


@admin_blueprint.route('/add_modif_book', methods=['POST'])
def add_or_modif_book():
    """
    Pour la modification ou l'ajout d'un livre
    :return: true si l'opération se passe bien
    """
    admin = Admin(request.form.get('id'), session.get(request.form.get('id')))

    operation_state = admin.add_or_modify_book(request.form.get('isbn'),
                                               request.form.get('title'),
                                               request.form.get('author'),
                                               request.form.get('editor'),
                                               request.form.get('category'),
                                               request.form.get('synopsis'),
                                               int(request.form.get('p_year')),
                                               float(request.form.get('price')),
                                               int(request.form.get('qty')),
                                               request.form.get('img_link'))

    return jsonify({'op_success': operation_state})


@admin_blueprint.route('/drop_book', methods=["POST"])
def drop_book():
    admin = Admin(request.form.get('id'), session.get(request.form.get('id')))
    return jsonify({'op_success': admin.drop_book(request.form.get('isbn'))})


@admin_blueprint.route('/set_new_password_to_admin', methods=["POST"])
def set_new_password_to_admin():
    identifiant = request.form.get('id')
    print(identifiant)
    if id is not None:
        return jsonify({'op_success': set_new_password_to(identifiant)})

    return jsonify({'op_success': False})


@admin_blueprint.route('/get_data_for_stat', methods=['POST'])
def get_data_for_stat():
    """

    :return: Selon le caller (appelant dans Admin.js), retourne les données pour le graphique
    """
    caller = request.form.get('caller')
    option = request.form.get('option')
    data = []

    match caller:
        case "osi":
            data = statistics_of_stock(option)

        case "osl":
            sleep(0.2)

            data = statistics_of_sales()
            print(data)
        case "oap":
            sleep(0.4)
            data = price_average(option)

        case "ort":
            sleep(0.8)
            data = statistics_of_orders()

    return jsonify(data)


@admin_blueprint.route('/search_command', methods=['POST'])
def search_cmd():
    """Retourne les données sur la commande dont il est question"""
    order_id = request.form.get('orderID')
    if order_id is not None:
        return jsonify(search_order(order_id))

    return jsonify([])


app.register_blueprint(admin_blueprint)

if __name__ == '__main__':
    app.run(debug=True)

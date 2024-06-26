import json
from static.scripts.users import User
import mysql.connector as connector
import smtplib as smtp
from email.message import EmailMessage
from hashlib import sha256
from random import choice
import string
from datetime import datetime

connection = connector.connect(host='localhost', database='NAVABE',
                               user='Navabe_Project', password="GLO-2005")
cursor = connection.cursor()


def send_data(searchWord: str = "") -> list:
    """Récupère les données de la Base de données pour
    l'acheminer vers le client"""
    data = []
    try:
        if searchWord == "":
            req = "SELECT * FROM livres LIMIT 700 OFFSET {}"
            cursor.execute(req.format(choice(range(1000))))
        else:
            req = "SELECT * FROM livres WHERE isbn = %s OR titre LIKE '_{}'" \
                  " OR auteur LIKE '_{}' OR categorie LIKE '_{}'"
            cursor.execute(req.format(searchWord, searchWord, searchWord), [searchWord])

        livres = cursor.fetchall()

        for livre in livres:
            dict_data = {
                'isbn': livre[0], 'titre': livre[1],
                'auteur': livre[2], 'editeur': livre[3],
                'categorie': livre[4], 'synopsis': livre[5],
                'parution': livre[6], 'prix': livre[7],
                'url': livre[8]}
            data.append(dict_data)

    except connector.Error as error:
        print(error)

    return data


def user_authentification(email: str, password: str) -> bool:
    """
    Authentifie l'utilisateur et lui assigne un token pour sa session courante
    """
    try:
        req = 'SELECT mot_de_passe FROM Clients WHERE mail = ' + "'" + email + "'"
        cursor.execute(req)

        user_pass = cursor.fetchone()
        if user_pass is None:
            return False
        user_pass = user_pass[0]

        return sha256(password.encode('utf-8')).hexdigest() == user_pass

    except connector.Error as error:
        print(error)


def get_user(user_id: str, is_mail=True) -> User:
    """
    :param is_mail: Option pour indiquer le type de recherche, mettre false si on use de l'id
    :param user_id : ID de l'utilisateur ou mail selon le cas
    :return: L'utilisateur avec ce mail ou cet id selon le cas.
    """
    user = None
    req = "SELECT idClient, nom, prenom, adresse, mail FROM Clients WHERE {} = %s"

    try:
        if not is_mail:
            req = req.format('idClient')
            req = req.replace("idClient,", "")
            cursor.execute(req, [user_id])
            user_infos = cursor.fetchone()

            if user_infos is not None:
                return User(user_id, user_infos[0], user_infos[1], user_infos[2], user_infos[3])

        req = req.replace(", mail", "")
        req = req.format('mail')
        cursor.execute(req, [user_id])
        user_infos = cursor.fetchone()

        if user_infos is not None:
            return User(user_infos[0], user_infos[1], user_infos[2], user_infos[3], user_id)

    except connector.Error as error:
        print(error)

    return user


def set_user(user_infos: dict) -> None:
    """
    Enregistre l'utilisateur dont les données sont dans le dictionnaire
    et lui envoie un mail de confirmation.
    :param user_infos: Données de l'utilisateur
    :return: None
    """
    if len(user_infos.get('name')) > 0 \
            and len(user_infos.get('firstname')) > 0 \
            and len(user_infos.get('address')) > 0 \
            and len(user_infos.get('mail')) > 0 \
            and len(user_infos['password']) > 0:

        password = sha256(user_infos['password'].encode('utf-8')).hexdigest()
        try:
            req = "INSERT INTO clients(nom, prenom, adresse, mail, mot_de_passe) VALUES (%s, %s, %s, %s, %s)"
            values = (user_infos.get('name'), user_infos.get('firstname'),
                      user_infos.get('address'), user_infos.get('mail'), password)
            print(req)
            cursor.execute(req, values)
            connection.commit()
            send_mail(get_user(user_infos['mail']))

        except connector.Error as error:
            print(error)


def change_user_password(user: User, new_password: str) -> bool:
    """
    Permet de changer le mot de passe de l'utilisateur
    :param user:
    :param new_password:
    :return:
    """
    if user is None:
        return False

    try:
        req = "UPDATE Clients SET mot_de_passe = %s WHERE idClient = %s"

        new_password = sha256(new_password.encode('utf-8')).hexdigest()  # Hashes le mot de passe avant enregistrement

        cursor.execute(req, [new_password, user.getId()])
        connection.commit()
        return True

    except connector.Error as error:
        print(error)
        return False


def makeOrder(user: User, transact_id: str, contents: list, amount: float, contentsInfos: list) -> bool:
    """
    Crée la commande du client dans la bdd
    :return: true si tout se passe bien, false sinon
    """
    try:
        msg = "Hello {},\n" \
              "This is a confirmation for the payment you made on {}\n\n" \
              "Your transaction number is : {} \n" \
              "Your order number is : {} \n\n" \
              "Your order content\n\n" \
              "\r{}\n\n" \
              "Thank you for choosing Navavabe \n" \
              "The Navabe team\n"

        request = "CALL commander(%s, %s, %s, %s,%s, @out)"
        varchar_of_isbns = "".join(i for i in contents[0]['isbn'])
        print(varchar_of_isbns)
        cursor.execute(request, (user.getId(), transact_id, json.dumps(contents[0]), str(varchar_of_isbns), amount))
        connection.commit()

        cursor.execute("SELECT @out")
        out = cursor.fetchone()[0]

        msg_ = ""
        for i in contentsInfos:
            msg_ = msg_ + i + "\n"

        msg = msg.format(user.get_firstname(),
                         datetime.now().strftime("%Y-%m-%d at %H:%M"),
                         transact_id,
                         out,
                         msg_)

        send_mail(user, msg, "Payment confirmation")

        return True
    except connector.Error as error:
        print(error)
        return False


def checkItem(id_item: str, qty: int) -> bool:
    """
    Vérifie la disponibilité dans l'inventaire
    :param id_item: isbn du livre dont il faut vérifier la quantité
    :param qty: Quantité d'item que l'on souhaite prendre
    :return: true si la quantité en stock est plus grande que celui fournit
    """
    try:
        request = "SELECT quantite FROM inventaire WHERE  ISBN = %s"
        cursor.execute(request, [id_item])
        qty_in_DB = cursor.fetchone()[0]
        return qty_in_DB >= qty

    except connector.Error as error:
        print(error)
        return False


def pass_generator(taille=10, with_punctuation=False) -> str:
    """
    Génère de mot au hasard
    :param with_punctuation: option, mettre true si on veut des caractères spéciaux
    :param taille: longueur de mot à générer par défaut 10
    :return: 
    """
    characters = "?!&@$#*%<>[]{}/\|:;.,+=-" + string.ascii_letters + string.digits if with_punctuation \
        else string.ascii_letters + string.digits
    return ''.join(choice(characters) for i in range(taille))


def color_generator(taille=25) -> list:
    """
    Génère l'encodage HEX de couleurs
    :param taille:Nombre de couleurs à générer
    :return:
    """
    colors = []
    hex_comp = "0123456789ABCDEF"

    for i in range(taille):
        color_exists = True

        while color_exists:
            color_code = "#"

            for j in range(6):
                color_code += choice(hex_comp)

            if color_code not in colors:
                colors.append(color_code)
                color_exists = False
    return colors


def send_mail(user: User, message: str = '', sujet: str = '') -> None:
    """
    Permet d'envoyer des mails aux clients, par défaut la fonction envoie un mail de bienvenu.
    Les paramètres name et mail sont obligatoires.
    Les paramètres message et subject doivent être passés ensemble.

    :param sujet:Le sujet du message
    :param user: Utilisateur
    :param message:  message
    :return: None
    """
    navabe_mail = 'pnavabe@gmail.com'
    navabe_mail_password = 'rfpgfrrwqbtsbtba'

    msg = "Hello {},\n\nWelcome to Navabe Bookstore.\n\n" \
          "This is your user ID : {} \n\n" \
          "Please keep it jealously as it is the only way, " \
          "for you to recover your account if you forget your password\n\n" \
          "Greetings,\nThe Navabe team"
    subject = "Welcome to Navabe !"

    msg = message if len(message) > 0 else msg.format(user.get_firstname(), user.getId())
    subject = sujet if len(sujet) > 0 else subject

    message_mail = EmailMessage()
    message_mail['from'] = 'Navabe Team'
    message_mail['to'] = user.getmail()
    message_mail['subject'] = subject
    message_mail.set_content(msg)

    server = smtp.SMTP_SSL('smtp.gmail.com', 465)
    server.login(navabe_mail, navabe_mail_password)
    server.sendmail(navabe_mail, user.getmail(), message_mail.as_string())


if __name__ == '__main__':
    print(checkItem('9780060915414', 5))

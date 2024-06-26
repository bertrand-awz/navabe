import mysql.connector as connector
from base64 import b64encode
import json
from datetime import date
from static.scripts.requests import pass_generator, send_mail, color_generator
from static.scripts.users import User
from hashlib import sha256

connection = connector.connect(host="localhost", database="NAVABE", user="Navabe_Project", password="GLO-2005")
cursor = connection.cursor()


class Admin:

    def __init__(self, admin_ID: str, password: str):
        """
        Constructeur de la classe
        :param admin_ID: Identifiant de l'Administrateur
        :param password: Mot de passe de l'Administrateur
        """
        self.id = admin_ID
        self.password = password
        self.name = ""
        self.firstname = ""
        self.mail = ""

    def get_name(self):
        return self.name

    def get_firstname(self):
        return self.firstname

    def get_mail(self):
        return self.mail

    def get_ID(self):
        return self.id

    def login(self) -> bool:
        """
        Authentication de l'administrateur
        :return: True si la connexion a réussi
        """
        request = "SELECT mot_de_passe, nom, prenom, mail  FROM Administrateur WHERE adminID = %s"
        try:
            cursor.execute(request, [self.id])
            admin_infos = cursor.fetchone()

            if admin_infos[0] == self.password:
                self.name = admin_infos[1]
                self.firstname = admin_infos[2]
                self.mail = admin_infos[3]
                return True

        except connector.Error as err:
            print(err)

        return False

    def add_or_modify_book(self, isbn: str, title: str, author: str, editor: str, category: str,
                           synopsis: str, year: int, price: float, quantity: int, image_URL: str) -> bool:
        """
        Ajouter le livre dans la BDD
        :param isbn: ISBN
        :param title: titre
        :param author: auteur
        :param editor: editeur
        :param category: catégorie
        :param synopsis: résumé
        :param year: année de parution
        :param quantity: quantité à ajouter
        :param price: prix
        :param image_URL: lien vers l'image du livre
        :return: True si l'opération réussie
        """
        if self.login():
            try:
                args = [isbn, title, author, editor, category, synopsis,
                        year, price, image_URL, quantity]

                cursor.callproc('Ajout_Livre', args)
                connection.commit()
                return True

            except connection.Error as error:
                print(error)

        return False

    def drop_book(self, isbn: str) -> bool:
        """
        Supprimes le livre dont l'ISBN est fournie
        """
        if self.login():
            try:
                arg = [isbn]
                cursor.callproc('Retrait_Livre', arg)
                connection.commit()
                return True

            except connector.Error as error:
                print(error)
        return False

    def get_command_infos(self, command_id: str, user_id=""):
        """
        Renvoie les infos de la commande
        :param command_id: Identifiant de la commande
        :param user_id: Identifiant du propriétaire de la commande
        :return: Les infos sur la commande si elle existe
        """

    def set_new_admin(self, name: str, firstname: str, mail: str):
        """
        Ajoutes un nouvel administrateur

        :param name: le nom du nouvel administrateur
        :param firstname: le prénom du nouvel administrateur
        :param mail: le mail du nouvel administrateur
        :return: True si l'ajout réussi, False s'il y a une erreur (sqlstate 23000)
        """
        if self.login():
            msg = "Hello {},\n\n" \
                  "This message is to inform you that you are now an administrator of Navabe Bookstore.\n" \
                  "You will find below your login information: \n\n" \
                  "Your AdminID : {}\n" \
                  "Your password : {}\n\n" \
                  "For security reasons, please keep them secret\n\n" \
                  "Again, welcome to the administrative team.\n\n" \
                  "The Navabe Admins Team\n"

            op_success = True
            print(name, firstname)
            password = pass_generator(10)
            adminID = ""
            request = "INSERT INTO Administrateur(nom, prenom, mail, mot_de_passe) VALUES (%s,%s,%s,%s)"
            request1 = "SELECT adminID FROM Administrateur WHERE mail = %s"

            try:
                cursor.execute(request, [name, firstname, mail, sha256(password.encode('utf-8')).hexdigest()])
                connection.commit()

                cursor.execute(request1, [mail])
                adminID = cursor.fetchone()[0]

                msg = msg.format(firstname, adminID, password)
                send_mail(User(name=name, first_name=firstname, mail=mail),
                          msg, "Welcome to the administrative team")

            except connector.Error as err:
                op_success = int(err.sqlstate) != 23000

            return op_success

    def cookies(self):
        """
        Retournes les infos qui seront en cookies
        :return:
        """
        cookies = json.dumps([{'ID': self.id,
                               'name': self.name,
                               'firstname': self.firstname,
                               }])
        return b64encode(cookies.encode())


def search_books(keyword: str) -> list:
    """
    Cherches dans la BD les livres dont soit le titre, l'auteur, la catégorie ou ISBN est le keyword
    :param keyword: Mot clé
    :return: liste de résultats
    """
    request = "SELECT * FROM Livres WHERE auteur LIKE %s OR " \
              "titre = %s OR categorie = %s OR isbn = %s"
    try:
        cursor.execute(request, ["%{}%".format(keyword), keyword, keyword, keyword])
        results = cursor.fetchall()
        books = []

        for book in results:
            books.append(
                {
                    'isbn': book[0],
                    'title': book[1],
                    'author': book[2],
                    'editor': book[3],
                    'category': book[4],
                    'synopsis': book[5],
                    'year': book[6],
                    'price': book[7],
                    'url_img': book[8]
                }
            )
        return books

    except connector.Error as err:
        print(err)
    return []


def set_new_password_to(adminID: str) -> bool:
    """
    Vérifie l'existence d'un identifiant administrateur, lui met le nouveau mot de passe et lui envoie
    un mail de confirmation
    :param adminID:
    :return: True si adminID existe dans la BDD et que l'opération s'est bien passée, False sinon
    """
    request = "SELECT * FROM Administrateur WHERE adminID = %s"
    request1 = "UPDATE Administrateur SET mot_de_passe = %s WHERE adminID = %s"
    msg = "Hello {}, \n\n" \
          "This is your new password: {} \n\n" \
          "It is operational as of now.\n\n" \
          "Sincerely,\n" \
          "The Navabe Admins Team"
    try:
        cursor.execute(request, [adminID])
        result = cursor.fetchone()

        if len(result) > 0:
            new_password = pass_generator(6)
            cursor.execute(request1, [sha256(new_password.encode('utf-8')).hexdigest(), adminID])
            connection.commit()

            admin_ = Admin(adminID, sha256(new_password.encode('utf-8')).hexdigest())
            admin_.login()

            msg = msg.format(admin_.get_firstname(), new_password)

            send_mail(User(name=admin_.get_name(),
                           first_name=admin_.get_firstname(),
                           mail=admin_.get_mail()),
                      msg, "Update of your password")

            return True

    except connector.Error as error:
        print(error)
        return False


def statistics_of_stock(option: str = "s") -> dict:
    req = "SELECT categorie, SUM(quantite) FROM inventaire GROUP BY categorie"
    req1 = "SELECT categorie, COUNT(DISTINCT ISBN) FROM livres GROUP BY categorie"
    req2 = "SELECT annee_parution, COUNT(DISTINCT ISBN) FROM livres GROUP BY  annee_parution"
    data = {}

    try:
        if option == 's':
            cursor.execute(req)
        elif option == 'c':
            cursor.execute(req1)
        elif option == 'y':
            cursor.execute(req2)
        else:
            return {}

        results = cursor.fetchall()
        data = {
            'labels': [ctg[0] for ctg in [r for r in results]],
            'values': [int(val[1]) for val in [r for r in results]],
            'colors': color_generator(len(results))
        }
        return data

    except connector.Error as error:
        print(error)
        return {}


def price_average(option: str) -> dict:
    """
    Dépendamment de l'option choisie retourne la moyenne de prix des livres
    :param option: 'y' : moyenne de prix groupés par année de parution
                   'c' : moyenne de prix groupés par catégorie
    :return: dict de données à afficher
    """
    request = "SELECT categorie, AVG(prix) FROM Livres GROUP BY categorie"
    request1 = "SELECT annee_parution, AVG(prix) FROM livres GROUP BY annee_parution"
    data = dict()
    try:
        if option == 'y':
            cursor.execute(request1)
        if option == 'c':
            cursor.execute(request)

        results = cursor.fetchall()
        data = {
            'labels': [ctg[0] for ctg in [r for r in results]],
            'values': [round(float(val[1]), 2) for val in [r for r in results]],
            'colors': color_generator(len(results))
        }
        return data
    except connector.Error as error:
        print(error)
        return {}


def statistics_of_sales() -> dict:
    """
    Pour les statistiques des ventes.
    :return: Les différents flux entrant de ventes mensuels
    """
    months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August',
              'September', 'October', 'November', 'December']
    dict = {}
    request = "SELECT MONTH(date_paiement), SUM(montant) FROM Paiements " \
              "GROUP BY MONTH(date_paiement) ORDER BY MONTH(date_Paiement)"
    try:
        cursor.execute(request)
        results = cursor.fetchall()

        dict = {'labels': [months[m[0] - 1] for m in results],
                'values': [round(float(m[1])/1000, 3) for m in results],
                'color': []}

        return dict

    except connector.Error as error:
        print(error)
        return {}


def statistics_of_orders() -> dict:
    """
    Retourne les nombres de commandes en les groupant selon leur statut (état dans la BDD)
    Trois états sont possibles : 'In process', 'On the road', 'Delivered'
    :return:
    """
    data = dict()
    request = "SELECT etat, COUNT(DISTINCT idCommande) FROM commandes GROUP BY etat"
    try:
        cursor.execute(request)
        results = cursor.fetchall()
        data = {
            'labels': [etat[0] for etat in [r for r in results]],
            'values': [int(val[1]) for val in [r for r in results]],
            'colors': color_generator(len(results))
        }
        return data

    except connector.Error as error:
        print(error)
        return {}


def search_order(id: str, by_userID=False):
    """
    Retourne les infos sur la commande si celle-ci existe dans la BDD
    :param id: l'identifiant soit de la commande, soit du client
    :param by_userID: option de recherche
    :return:
    """
    if not by_userID:
        if len(id) == 16:
            """
            On fait une recuperation en deux temps : 
                1) On récupère les infos sur l'user et le montant total du paiement
                2) On récupère les infos sur le contenu de sa commande
            """

            request = "SELECT CONCAT(U.prenom,' ', U.nom), Pmt.montant, Pmt.date_Paiement, Cmd.date_commande, " \
                      "Cmd.date_changement_etat, Cmd.etat FROM clients U " \
                      "JOIN commandes Cmd ON U.`idClient` = Cmd.`idClient`" \
                      "JOIN paiements Pmt ON Cmd.`idCommande` = Pmt.`idCommande`" \
                      "WHERE Cmd.`idCommande` = %s"

            request1 = "SELECT contenu from commandes WHERE idCommande = %s"

            request1_1 = "SELECT CONCAT(titre, ' by ', auteur), prix FROM livres WHERE isbn IN ({})" \
                         "ORDER BY FIELD(isbn,{})"  # N'ayant aucune garantie que cette requête retourne les valeurs
            # dans qu'elles ont été passées dans IN, on usera de FIELD
            # nous parlons de valeurs correspondantes aux isbn

            try:
                # étape 01
                cursor.execute(request, [id])
                result = cursor.fetchone()
                result = [{'user_names': result[0],
                           'amount': float(result[1]),
                           'date_of_p': result[2].strftime("%d-%m-%Y At %H:%M:%S"),
                           'date_of_c': result[3].strftime("%d-%m-%Y At %H:%M:%S"),
                           'date_of_cs': result[4].strftime("%d-%m-%Y At %H:%M:%S"),
                           'status': result[5]
                           }]
                # étape 02

                cursor.execute(request1, [id])
                result1 = cursor.fetchone()[0]
                qty_list = json.loads(result1)['quantity']
                isbn_list = json.loads(result1)['isbn']

                request1_1 = request1_1.format(', '.join(isbn for isbn in isbn_list),
                                               ', '.join(isbn for isbn in isbn_list))

                cursor.execute(request1_1)
                result1_1 = cursor.fetchall()
                result1 = []
                for i in range(len(result1_1)):
                    result1.append(
                        {'title_by_author': result1_1[i][0],
                         'book_price': result1_1[i][1],
                         'qty': qty_list[i]
                         }
                    )
                return [result, result1]

            except connector.Error as error:
                print(error)
                return []
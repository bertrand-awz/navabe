import json
from base64 import b64encode


class User:
    def __init__(self, identifier="", name="", first_name="", address="", mail=""):
        self.identifier = identifier
        self.name = name
        self.first_name = first_name
        self.address = address
        self.mail = mail

    def get_name(self):
        """
        :return: Nom d'utilisateur
        """
        return self.name

    def get_firstname(self):
        """
        :return: Prénom d'utilisateur
        """
        return self.first_name

    def getId(self):
        """
        :return: ID d'utilisateur
        """
        return self.identifier

    def getmail(self):
        """
        :return: Mail d'utilisateur
        """
        return self.mail

    def get_address(self):
        """
        :return: Adresse d'utilisateur
        """
        return self.address

    def get_data_cookies(self):
        """"
        Revoit les infos qui seront affichées dans le compte utilisateur
        """
        user_infos = json.dumps([{'ID': self.identifier,
                                  'name': self.name,
                                  'firstname': self.first_name,
                                  'mail': self.mail,
                                  'address': self.address
                                  }])
        return b64encode(user_infos.encode())

-- Active: 1679540320366@@127.0.0.1@3306@navabe


CREATE DATABASE IF NOT EXISTS NAVABE; /*on crée la base de donnée qui sera utilisée pour le projet */
CREATE USER 'Navabe_Project'@'localhost' IDENTIFIED BY 'GLO-2005';/*Nouvel utilisateur, cet utilisateur est utilisé dans le code python pour
                                                    faire des requêtes, donc pas besoin de modifier à chaque mise à jour
                                                    les identifiants de connection à la BDD ;)*/
GRANT ALL PRIVILEGES ON NAVABE.* TO 'Navabe_Project'@'localhost' WITH GRANT OPTION;
FLUSH PRIVILEGES;

/*-----------------------------------------------------------------------------------------*/
USE NAVABE;
/*Création des tables et de leurs gâchettes(ou procédures) respectives pour permettre un maintenace à partir du web*/
CREATE TABLE Clients ( numClient INT(4) UNSIGNED ZEROFILL AUTO_INCREMENT , 
                       idClient CHAR(8) NOT NULL,
                       nom VARCHAR (45) NOT NULL, 
                       prenom  VARCHAR(45) NOT NULL,
                       adresse VARCHAR (255) NOT NULL, 
                       mail VARCHAR(255) NOT NULL,
                       mot_de_passe VARCHAR(64) NOT NULL,  
                       PRIMARY KEY (idClient), 
                       UNIQUE KEY (numClient), 
                       UNIQUE KEY(mail));

CREATE TABLE Livres ( isbn CHAR(13) NOT NULL,
                      titre VARCHAR(1500) NOT NULL,
                      auteur VARCHAR(1000) NOT NULL,
                      editeur VARCHAR(1000),
                      categorie VARCHAR(1000),
                      synopsis VARCHAR(6000),
                      annee_parution INT(4),
                      prix FLOAT NOT NULL,
                      image_URL VARCHAR(3000),
                      PRIMARY KEY(isbn)
                      );
CREATE TABLE Inventaire( isbn CHAR(13),
                         categorie VARCHAR(45), 
                         quantite INT UNSIGNED, 
                         FOREIGN KEY(isbn) REFERENCES Livres(isbn), 
                         UNIQUE KEY(isbn));
CREATE TABLE Paniers (id INT AUTO_INCREMENT, 
                      idClient CHAR(8), 
                      isbn CHAR(13), date_ajout DATETIME DEFAULT NOW(),
                      UNIQUE KEY (id), 
                      FOREIGN KEY (idClient) REFERENCES clients(idClient), 
                      FOREIGN KEY (ISBN) REFERENCES Inventaire(ISBN));
CREATE TABLE Commandes (idCommande CHAR(16),
                        idLivre VARCHAR(13),
                        idClient CHAR(8),
                        date_commander DATETIME NOT NULL,
                        date_changement_etat DATETIME NOT NULL,
                        etat VARCHAR(13) NOT NULL DEFAULT 'En traitement',
                        FOREIGN KEY(idClient) REFERENCES clients(idClient));
CREATE TABLE Facture (idFacture INT(9) ZEROFILL AUTO_INCREMENT, 
                      date_Facturation DATETIME DEFAULT NOW(), 
                      idClient CHAR(8), 
                      idCommande CHAR(16), 
                      montant DECIMAL(10, 2) UNSIGNED,
                      PRIMARY KEY(idFacture),
                      FOREIGN KEY (idClient) REFERENCES clients(idClient), 
                      FOREIGN KEY(idCommande) REFERENCES Commandes(idCommande));


 /*Si vous êtes sous Linux veuillez déplacer le fichier NVB.csv dans /var/lib/mysql-files/ comme ci dessous.
  MySQL, pour des raisons sécuritaires, refuse l'importation de fichiers en dehors de ce repertoire
  Pour Windows, il faut le déplacer vers C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/: puis décommenter et éxécuter le code réservé pour Windows*/

SHOW GLOBAL VARIABLES LIKE "%secure_file_priv%" --Commande à éxecuter pour savoir où déplacer le fichier csv avant son importation.

  --Pour LINUX
  
LOAD DATA INFILE '/var/lib/mysql-files/NVB.csv'
INTO TABLE Livres
FIELDS TERMINATED BY '|'
ENCLOSED BY ''
LINES TERMINATED BY '\n'
IGNORE 1 ROWS;

 --Pour WINDOWS
 /*
LOAD DATA INFILE 'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/NVB.csv'
INTO TABLE Livres
FIELDS TERMINATED BY '|'
ENCLOSED BY ''
LINES TERMINATED BY '\n'
IGNORE 1 ROWS;
 */

/************************* LES GACHETTES **********************/
DELIMITER //

    CREATE TRIGGER ID_Clients_generator BEFORE INSERT ON clients FOR EACH ROW
    BEGIN
        DECLARE Max_num INT;
        SELECT IFNULL(MAX(numClient), 0) INTO Max_num FROM clients;
        SET NEW.idClient = UPPER(CONCAT(SUBSTR(NEW.prenom, 1, 2), SUBSTR(NEW.nom, 1, 2), LPAD(Max_num + 1, 4, '0')));
    END//

DELIMITER;

DELIMITER //

    CREATE TRIGGER id_commandes_generator BEFORE INSERT ON Commandes FOR EACH ROW
    BEGIN
        SET NEW.idCommande = CONCAT((SELECT DATE_FORMAT(NEW.date_commander, '%Y%m%d')),
                                    NEW.idClient);
        SET NEW.date_changement_etat = NEW.date_commander;
    END//

DELIMITER;

DELIMITER //
    CREATE TRIGGER updating_inventaire AFTER INSERT ON Livres FOR EACH ROW
        BEGIN
            INSERT INTO Inventaire VALUES(NEW.isbn, NEW.categorie, 50);
        END//
DELIMITER;

/************************ LES PROCÉDURES ********************/
DELIMITER //

    CREATE PROCEDURE Ajout_Livre ( IN ISBN_ CHAR(13), 
                                titre_ VARCHAR(255), 
                                auteur_ VARCHAR(45), 
                                categorie_ VARCHAR(45), 
                                prix_ FLOAT, 
                                annee_parution_ INT(4), 
                                synopsis_ VARCHAR(750))
    BEGIN
        DECLARE est_present INT (1);
        SET est_present = (SELECT EXISTS (SELECT * FROM Livres WHERE `ISBN` = ISBN_));

        IF est_present = 0 THEN
            INSERT INTO Livres VALUES (ISBN_, titre_, auteur_, categorie_, prix_, annee_parution_,synopsis_);
            INSERT INTO Inventaire VALUES(ISBN_, categorie_, 1);
        ELSE
            UPDATE Inventaire SET quantite = quantite + 1 WHERE `ISBN` = ISBN_;

        END IF;     
    END//

DELIMITER;


DELIMITER // 
    /* Quand passes une commande sur le site le serveur doit faire appeler cette procedure.  
       elle decharge la table "Panier" en récupérant les articles du clients pour en faire une commande.
    */
    CREATE PROCEDURE Commander (IN idClient_ CHAR(8))
        BEGIN
            DECLARE date_passation DATETIME;
            DECLARE id_ INT;

            SET date_passation = now();
            
            REPEAT

                SET id_ = (SELECT id FROM Paniers WHERE idClient = idClient_ LIMIT 1);

                INSERT INTO Commandes (idLivre, idClient, date_commander) VALUES 
                ((SELECT ISBN FROM Paniers WHERE id = id_), idClient_, date_passation);

                DELETE FROM Paniers WHERE id = id_;

            UNTIL (SELECT COUNT(*) FROM Paniers WHERE idClient = idClient_) < 1
            END REPEAT;
        END//
DELIMITER;

CALL Commander ("RARE0002");               
-- Active: 1679540320366@@127.0.0.1@3306@navabe

CREATE DATABASE IF NOT EXISTS NAVABE; /*on crée la base de donnée qui sera utilisée pour le projet */
CREATE USER 'Navabe_Project'@'localhost' IDENTIFIED BY 'GLO-2005';/*Nouvel utilisateur, cet utilisateur est utilisé dans le code python pour
                                                    faire des requêtes, donc pas besoin de modifier à chaque mise à jour
                                                    les identifiants de connection à la BDD ;)*/
GRANT ALL PRIVILEGES ON NAVABE.* TO 'Navabe_Project'@'localhost' WITH GRANT OPTION;
FLUSH PRIVILEGES;
USE NAVABE;

/*-----------------------------------------------------------------------------------------*/

/*Création des tables et de leurs gâchettes(ou procédures) respectives pour permettre un maintenace à partir du web*/
CREATE TABLE Administrateur (adminID CHAR(6) NOT NULL,
                            nom VARCHAR(45) NOT NULL, 
                            prenom VARCHAR(45) NOT NULL, 
                            mail VARCHAR(45) NOT NULL,
                            mot_de_passe VARCHAR(64) NOT NULL,
                            PRIMARY KEY(adminID),
                            UNIQUE KEY(mail));
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

CREATE TABLE Commandes (idCommande CHAR(16),
                        idClient CHAR(8),
                        contenu JSON,
                        date_commande DATETIME NOT NULL DEFAULT NOW(),
                        date_changement_etat DATETIME NOT NULL DEFAULT NOW(),
                        etat VARCHAR(13) NOT NULL DEFAULT 'In process',
                        PRIMARY KEY(idCommande, idClient),
                        FOREIGN KEY(idClient) REFERENCES clients(idClient));

CREATE TABLE Paiements (idPaiement VARCHAR(17) NOT NULL, 
                      date_Paiement DATETIME DEFAULT NOW(), 
                      idCommande CHAR(16), 
                      montant DECIMAL(10, 2) UNSIGNED,
                      PRIMARY KEY(idPaiement),
                      UNIQUE KEY(idPaiement, idCommande),
                      FOREIGN KEY(idCommande) REFERENCES Commandes(idCommande));

CREATE INDEX idx_Livres ON Livres (auteur, titre);

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
    /*Générateur d'ID pour utilisateur: 2 premières lettre du prénom + 2 de celui du nom + numérotation*/
    CREATE TRIGGER ID_Clients_generator BEFORE INSERT ON clients FOR EACH ROW
    BEGIN
        DECLARE Max_num INT;
        SELECT IFNULL(MAX(numClient), 0) INTO Max_num FROM clients;
        SET NEW.idClient = UPPER(CONCAT(SUBSTR(NEW.prenom, 1, 2), SUBSTR(NEW.nom, 1, 2), LPAD(Max_num + 1, 4, '0')));
    END//

DELIMITER;

CREATE Trigger id_admin_generator BEFORE INSERT ON Administrateur FOR EACH ROW
    BEGIN
        /*On génere l'id admin: premiere lettre du nom, premiere lettre du prenom, et 4 Caratères aléatoires*/
        SET NEW.adminID = (SELECT CONCAT(LEFT(NEW.nom, 1), LEFT(NEW.prenom, 1),
                                        SUBSTRING(MD5(RAND()), 1, 4)));
    END//
DELIMITER;

DELIMITER //
/*  Surveille les modifications du stock, un isbn dont la quantité est 0 sera rétiré*/

CREATE TRIGGER update_quantite
BEFORE UPDATE ON inventaire
FOR EACH ROW
BEGIN
    IF NEW.quantite < 1 THEN
        SET NEW.quantite = 0;
    END IF;
    IF NEW.quantite = 0 THEN
        DELETE FROM inventaire WHERE isbn = NEW.isbn;
    END IF;
END;

DELIMITER ;
DROP TRIGGER delete_isbn_before_update
/************************ LES PROCÉDURES ********************/
DELIMITER //
    /* Cette procedure permettant l'ajout d'un livre*/
    CREATE PROCEDURE Ajout_Livre ( IN ISBN_ CHAR(13), 
                                titre_ VARCHAR(1500), 
                                auteur_ VARCHAR(1000),
                                editeur_ VARCHAR(1000), 
                                categorie_ VARCHAR(1000),
                                synopsis_ VARCHAR(6000), 
                                annee_parution_ INT(4),
                                prix_ FLOAT,
                                image_url VARCHAR(3000),
                                qty INT UNSIGNED 
                                )
          BEGIN
               DECLARE est_present INT (1);
               SET est_present = (SELECT EXISTS (SELECT * FROM Livres WHERE `ISBN` = ISBN_));

               IF est_present = 0 THEN

                    INSERT INTO Livres VALUES (ISBN_, titre_, auteur_, editeur_, categorie_,
                                             synopsis_,annee_parution_, prix_, image_url);

                    INSERT INTO Inventaire VALUES(ISBN_, categorie_, qty);

               ELSE
                    UPDATE Livres SET titre = titre_, auteur = auteur_, editeur = editeur_, 
                                        categorie = categorie_,synopsis = synopsis_, 
                                        annee_parution = annee_parution_, prix = prix_, 
                                        image_URL = image_url
                                   WHERE ISBN = ISBN_;

                    UPDATE Inventaire SET categorie = categorie_, quantite = quantite + qty 
                                        WHERE `ISBN` = ISBN_;

               END IF;     
          END//
    /*Procédure pour le retait d'un livre(accessible seulement pour les admins du site)*/
     CREATE PROCEDURE Retrait_Livre(IN ISBN_ CHAR(13))
          BEGIN
               DELETE FROM Inventaire WHERE ISBN = ISBN_;
               DELETE FROM Livres WHERE ISBN = ISBN_;
          END//
DELIMITER;


DELIMITER//
/*Procédure pour passer une commande. Elle est à utiliser seulement après payement*/
CREATE PROCEDURE commander(IN clientID CHAR(8), IN transactionID VARCHAR(17),
                               IN contenu JSON, IN ISBNS VARCHAR(1300), IN amount DECIMAL(10,2), 
                               OUT commande_id VARCHAR(16))
BEGIN
    DECLARE json_quantity JSON;
    DECLARE isbn_ VARCHAR(13);
    DECLARE qty INT;
    DECLARE len_ INT;
    DECLARE idx INT;

    SET json_quantity = JSON_EXTRACT(contenu, '$.quantity');
    SET len_ = JSON_LENGTH(json_quantity);
    SET idx = 0;
            
    SET commande_id = CONCAT((SELECT DATE_FORMAT(NOW(), '%Y%m%d')),
                                UPPER(SUBSTRING(MD5(RAND()),1,8)));
                                    
    /*Insertion de la commande*/
    INSERT INTO commandes (`idCommande`,`idClient`,contenu) VALUES(commande_id, clientID, contenu);
    INSERT INTO paiements (idPaiement, idCommande, montant) VALUES (transactionID, commande_id, amount);

    /*Et on met à jour l'inventaire et la table Livres au besoin*/         
    WHILE idx < len_ DO
        SET isbn_ = SUBSTR(ISBNS,1, 13);
        SET ISBNS = REPLACE(ISBNS, isbn_, "");

        SET qty = CAST(JSON_EXTRACT(json_quantity, CONCAT('$[',idx,']')) AS UNSIGNED);
                
        UPDATE Inventaire SET quantite = quantite - qty WHERE ISBN = isbn_;

        SELECT quantite INTO @Qt FROM inventaire WHERE isbn = isbn_;
        IF @Qt <= 0 THEN
            DELETE FROM Inventaire WHERE ISBN = isbn_;
            DELETE FROM Livres WHERE ISBN = isbn_;     
        END IF;

        SET idx = idx + 1;
    END WHILE;
END//

DELIMITER ;
DELIMITER ;

CALL commander('BEZA0008', "115p8y", '{"isbn": ["9780020360759","9780020442806"], "quantity": [1,1]}','97800203607599780020442806',10.2, @sortie);


drop Procedure commander;

SELECT MONTH(date_Paiement) AS mois, SUM(montant) AS total_paiements
FROM Paiements
GROUP BY MONTH(date_Paiement)
ORDER BY MONTH(date_Paiement);
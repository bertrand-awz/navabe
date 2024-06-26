import mysql.connector as connector
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import pairwise_distances


def recommend_for(user_favorites_isbn: []) -> dict:
    all_books = dict()
    user_likes = dict()

    try:
        connection = connector.connect(host="localhost", database="NAVABE", user="root", password="Clervie2014!")

        cursor = connection.cursor()
        request = "SELECT isbn, auteur, titre, categorie, synopsis FROM livres"

        cursor.execute(request)
        result = cursor.fetchall()

        all_books = {
            "ISBN": [i[0] for i in result],
            "auteur": [i[1] for i in result],
            "titre": [i[2] for i in result],
            "catégorie": [i[3] for i in result],
            "synopsis": [i[4] for i in result]
        }

    except connector.Error as error:
        print(error)

    user_likes = {
        "ISBN": [],
        "auteur": [],
        "titre": [],
        "catégorie": [],
        "synopsis": [],
    }
    for isbn in user_favorites_isbn:
        user_likes['ISBN'].append(isbn)
        user_likes['auteur'].append(all_books['auteur'][all_books['ISBN'].index(isbn)])
        user_likes['titre'].append((all_books['titre'][all_books['ISBN'].index(isbn)]))
        user_likes['catégorie'].append((all_books['catégorie'][all_books['ISBN'].index(isbn)]))
        user_likes['synopsis'].append((all_books['synopsis'][all_books['ISBN'].index(isbn)]))

    if len(user_likes) > 0 and len(all_books) > 0:

        user_books_df = pd.DataFrame.from_dict(user_likes)
        all_books_df = pd.DataFrame.from_dict(all_books)

        user_categories = list(set(user_books_df["catégorie"].values))
        print(user_categories)
        related_books_df = all_books_df[all_books_df["catégorie"].isin(user_categories)]

        #print(related_books_df)
        # Vectorisation des titres et noms d'auteurs
        tfidf = TfidfVectorizer(stop_words="english")
        book_features = tfidf.fit_transform(
                                            related_books_df["synopsis"])
        u_b = tfidf.fit_transform(user_books_df["synopsis"])
        print(book_features[0],"\nbbbb\n", u_b.tolil())

        # Calcul de la similarité entre les vecteurs de tous les livres
        cosine_similarities = pairwise_distances(book_features.toarray(), metric="jaccard")
        print(cosine_similarities)
        for row in user_books_df.iterrows():
            print(cosine_similarities[related_books_df.index == row[0]].argsort()[0][-3:-1].tolist())
            print(row[1].tolist())
        print(all_books['titre'][527], "\n", all_books['auteur'][527], "\n", all_books['synopsis'][463], "\n", all_books
        ['catégorie'][463])


if __name__ == "__main__":
    recommend_for(["9780020199854", "9780006163831", "9780006512677"])

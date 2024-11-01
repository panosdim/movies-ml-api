import os
from typing import List, Tuple

import mysql.connector
from dotenv import load_dotenv
from mysql.connector import Error

# Load the environment variables from the .env file
load_dotenv()

# Retrieve the values
DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_DATABASE"),
    "collation": os.getenv("DB_COLLATION")
}


def connect_to_db():
    """
    Establish a connection to the MySQL database using provided configuration.

    Returns:
        connection (MySQLConnection): The MySQL database connection object if successful, None otherwise.
    """
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None


def fetch_data_from_db(query: str, params: Tuple = ()) -> List[Tuple]:
    """
    Args:
        query: SQL query string to be executed against the database.
        params: Tuple of parameters to be passed to the SQL query.

    Returns:
        List of tuples containing the rows retrieved from the database based on the query.
    """
    connection = connect_to_db()
    if connection is None:
        print("MySQL Connection not available.")
        return []
    cursor = connection.cursor()
    cursor.execute(query, params)
    data = cursor.fetchall()
    cursor.close()
    connection.close()
    return data


def get_movie_ratings() -> Tuple[List[int], List[float]]:
    """
    Fetch movie ratings from the database, and if the rating is missing or zero, assign a placeholder rating.

    Returns:
        Tuple[List[int], List[float]]: A tuple containing a list of movie IDs and a list of normalized ratings.
    """
    # Fetch all movies, including unrated ones
    data = fetch_data_from_db("SELECT movie_id, rating FROM watchlist")

    movie_ids = []
    ratings = []

    for row in data:
        movie_id = row[0]
        rating = row[1]
        movie_ids.append(movie_id)

        if rating is not None and rating > 0:
            ratings.append(rating / 5.0)  # Normalize rating
        else:
            ratings.append(2.5 / 5.0)  # Placeholder rating if None or zero

    return movie_ids, ratings


def get_movie_ids() -> List[int]:
    """
    Retrieves a list of movie IDs from the watchlist.

    The function fetches movie IDs from the database by executing
    a SQL query that selects all movie IDs from the watchlist table.
    It processes the fetched data to extract and return the movie IDs
    in a list.

    Returns:
        List[int]: A list of movie IDs.
    """
    data = fetch_data_from_db("SELECT movie_id FROM watchlist")
    movie_ids = [movie[0] for movie in data]
    return movie_ids

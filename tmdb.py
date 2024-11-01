import os

import requests
from dotenv import load_dotenv

# Load the environment variables from the .env file
load_dotenv()

API_KEY = os.getenv("TMDB_KEY")
BASE_URL = "https://api.themoviedb.org/3/"


def fetch_movie_details(tmdb_id):
    """
    Fetches detailed movie information from The Movie Database (TMDb) API for the given TMDb ID.

    Args:
        tmdb_id (int): The unique TMDb ID of the movie.

    Returns:
        dict: A dictionary containing the following movie details:
            - genres (list[str]): The genres of the movie.
            - release_year (int): The release year of the movie.
            - duration (int): The duration of the movie in minutes.
            - popularity (float): The popularity score of the movie.
            - average_rating (float): The average user rating of the movie.
            - actors (list[str]): The names of the top 5 actors in the movie.
            - director (list[str]): The names of the directors of the movie.
        None: If the API request fails, the function will return None.
    """
    url = f"{BASE_URL}movie/{tmdb_id}?api_key={API_KEY}&append_to_response=credits"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()

        # Extract relevant details
        movie_details = {
            "genres": [genre["name"] for genre in data.get("genres", [])],
            "release_year": int(data.get("release_date", "0000").split("-")[0]),
            "duration": data.get("runtime", 0),
            "popularity": data.get("popularity", 0),
            "average_rating": data.get("vote_average", 0),
            "actors": [
                cast["name"] for cast in data.get("credits", {}).get("cast", [])[:5]
            ],  # top 5 actors
            "director": [
                crew["name"]
                for crew in data.get("credits", {}).get("crew", [])
                if crew["job"] == "Director"
            ],
        }
        return movie_details
    else:
        print(f"Failed to fetch data for TMDb ID: {tmdb_id}")
        return None


def fetch_new_releases(page=1):
    """
    Fetches new movie releases from TMDb.

    Args:
        page (int): The page of new releases to retrieve (defaults to 1).

    Returns:
        list[dict]: A list of dictionaries, each containing the following details:
            - poster_path (str): The URL path to the movie's poster image.
            - release_date (str): The release date of the movie.
            - id (int): The unique TMDb ID of the movie.
            - title (str): The title of the movie.
        None: If the API request fails, the function will return None.
    """
    url = f"{BASE_URL}movie/now_playing?api_key={API_KEY}&page={page}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()

        # Get all movie details on the specified page
        movie_details = [
            {
                "poster_path": movie.get("poster_path", ""),
                "release_date": movie.get("release_date", ""),
                "id": movie.get("id"),
                "title": movie.get("title", ""),
            }
            for movie in data.get("results", [])
        ]
        return movie_details
    else:
        print("Failed to fetch new releases")
        return None

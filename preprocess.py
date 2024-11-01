def preprocess_movie_data(movie_data, genre_list, actor_list, director_list):
    """
    Args:
        movie_data: A dictionary containing information about a specific movie, such as genres, release year, duration,
                    popularity, average rating, actors, and director.
        genre_list: A list of all possible genres to be used for creating the one-hot vector.
        actor_list: A list of all possible actors to be used for creating the one-hot vector.
        director_list: A list of all possible directors to be used for creating the one-hot vector.
    """

    # Convert genres to a one-hot vector
    genre_vector = [1 if genre in movie_data["genres"] else 0 for genre in genre_list]

    # Convert actors and directors to one-hot vectors
    actor_vector = [1 if actor in movie_data["actors"] else 0 for actor in actor_list]
    director_vector = [
        1 if director in movie_data["director"] else 0 for director in director_list
    ]

    # Normalize and format data
    processed_data = {
        "genre_vector": genre_vector,
        "release_year": (movie_data["release_year"] - 1900)
        / 120,  # Normalize to [0, 1]
        "duration": movie_data["duration"] / 300,  # Normalize duration
        "popularity": movie_data["popularity"] / 1000,  # Normalize popularity
        "average_rating": movie_data["average_rating"] / 10,  # Normalize rating
        "actor_vector": actor_vector,
        "director_vector": director_vector,
    }
    return processed_data

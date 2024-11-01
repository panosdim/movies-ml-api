import numpy as np
from tensorflow.keras.layers import Concatenate, Dense, Dot, Embedding, Flatten, Input
from tensorflow.keras.models import Model

from preprocess import preprocess_movie_data
from tmdb import fetch_movie_details


# Model definition
def build_model(num_movies, num_genres, num_actors, num_directors):
    """
    Builds a recommendation model that combines collaborative filtering and content-based features.

    The model takes in various movie metadata features (genre, release year, duration, popularity, actor, director,
    average rating) as well as a user ID and movie ID, and outputs a predicted rating for the user-movie pair.

    The model uses an embedding layer for the user and movie IDs, and concatenates the embeddings with the other
    metadata features. It then passes the combined features through a series of dense layers to learn from the
    metadata, and combines this with the collaborative filtering signal from the user and movie embeddings.

    Args:
        num_movies (int): The number of unique movies in the dataset.
        num_genres (int): The number of unique genres in the dataset.
        num_actors (int): The number of unique actors in the dataset.
        num_directors (int): The number of unique directors in the dataset.

    Returns:
        A compiled Keras model that can be used for training and prediction.
    """
    embedding_dim = 16

    # Inputs
    user_input = Input(shape=(1,), name="user_input")
    movie_input = Input(shape=(1,), name="movie_input")
    genre_input = Input(shape=(num_genres,), name="genre_input")
    release_year_input = Input(shape=(1,), name="release_year_input")
    duration_input = Input(shape=(1,), name="duration_input")
    popularity_input = Input(shape=(1,), name="popularity_input")
    actor_input = Input(shape=(num_actors,), name="actor_input")
    director_input = Input(shape=(num_directors,), name="director_input")
    average_rating_input = Input(shape=(1,), name="average_rating_input")

    # Embedding layers
    user_embedding = Embedding(input_dim=1, output_dim=embedding_dim)(user_input)
    movie_embedding = Embedding(input_dim=num_movies, output_dim=embedding_dim)(
        movie_input
    )
    user_vector = Flatten()(user_embedding)
    movie_vector = Flatten()(movie_embedding)

    # Collaborative signal
    collab_signal = Dot(axes=1)([user_vector, movie_vector])

    # Concatenate metadata inputs
    movie_metadata = Concatenate()(
        [
            movie_vector,
            genre_input,
            release_year_input,
            duration_input,
            popularity_input,
            actor_input,
            director_input,
            average_rating_input,
        ]
    )

    # Dense layers to learn from metadata
    dense = Dense(128, activation="relu")(movie_metadata)
    dense = Dense(64, activation="relu")(dense)
    dense = Dense(32, activation="relu")(dense)

    # Combine collaborative signal and metadata learning
    combined_output = Concatenate()([dense, collab_signal])
    final_output = Dense(1)(combined_output)

    model = Model(
        inputs=[
            user_input,
            movie_input,
            genre_input,
            release_year_input,
            duration_input,
            popularity_input,
            actor_input,
            director_input,
            average_rating_input,
        ],
        outputs=final_output,
    )
    model.compile(optimizer="adam", loss="mse")

    return model


def train_model(model, movie_ids, ratings, genre_list, actor_list, director_list):
    """
    Trains a machine learning model for movie recommendations using the provided data.

    Args:
        model (keras.Model): The model to be trained.
        movie_ids (list): A list of movie IDs.
        ratings (list): A list of ratings for the corresponding movies.
        genre_list (list): A list of all unique genres.
        actor_list (list): A list of all unique actors.
        director_list (list): A list of all unique directors.

    Returns:
        keras.Model: The trained model.
    """
    user_ids = np.array([0] * len(movie_ids))  # Single user, repeated for each movie
    movie_ids = np.array(movie_ids)  # Ensure movie IDs are also in array form
    ratings = np.array(ratings)  # Already normalized
    sequential_ids = np.arange(len(movie_ids))

    # Fetch and preprocess each movie's metadata
    preprocessed_movies = [
        preprocess_movie_data(
            fetch_movie_details(movie_id), genre_list, actor_list, director_list
        )
        for movie_id in movie_ids
    ]
    genre_vectors = np.array([data["genre_vector"] for data in preprocessed_movies])
    release_years = np.array([[data["release_year"]] for data in preprocessed_movies])
    durations = np.array([[data["duration"]] for data in preprocessed_movies])
    popularities = np.array([[data["popularity"]] for data in preprocessed_movies])
    average_ratings = np.array(
        [[data["average_rating"]] for data in preprocessed_movies]
    )
    actor_vectors = np.array([data["actor_vector"] for data in preprocessed_movies])
    director_vectors = np.array(
        [data["director_vector"] for data in preprocessed_movies]
    )

    # Train the model
    model.fit(
        [
            user_ids,
            sequential_ids,
            genre_vectors,
            release_years,
            durations,
            popularities,
            actor_vectors,
            director_vectors,
            average_ratings,
        ],
        ratings,
        epochs=300,
        batch_size=4,
    )

    return model

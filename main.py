import argparse
import logging.config
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

import numpy as np
import uvicorn as uvicorn
from fastapi import FastAPI
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from tensorflow.keras.models import load_model

from database import get_movie_ids, get_movie_ratings
from model import build_model, train_model
from preprocess import preprocess_movie_data
from tmdb import fetch_movie_details, fetch_new_releases

_uvicorn_logger = logging.getLogger("uvicorn")
_uvicorn_logger.propagate = False

logging.config.fileConfig(fname="logging.conf", disable_existing_loggers=False)
_logger = logging.getLogger(__name__)

MOVIE_SUGGESTIONS_MODEL = "movie_suggestions.keras"

global movie_ids, ratings, genre_list, actor_list, director_list, model, num_movies


def populate_lists():
    global movie_ids, ratings, genre_list, actor_list, director_list, num_movies
    movie_ids, ratings = get_movie_ratings()
    unique_genres = set()
    unique_actors = set()
    unique_directors = set()
    # Loop through each movie to collect unique genres, actors, and directors
    for movie_id in movie_ids:
        movie_details = fetch_movie_details(movie_id)
        if movie_details:
            unique_genres.update(movie_details["genres"])
            unique_actors.update(movie_details["actors"])
            unique_directors.update(movie_details["director"])
    # Convert sets to sorted lists for consistent indexing
    genre_list = sorted(list(unique_genres))
    actor_list = sorted(list(unique_actors))
    director_list = sorted(list(unique_directors))
    num_movies = len(movie_ids)


populate_lists()

if not os.path.exists(MOVIE_SUGGESTIONS_MODEL):
    # Instantiate the model
    model = build_model(
        num_movies=num_movies + 1,
        num_genres=len(genre_list),
        num_actors=len(actor_list),
        num_directors=len(director_list),
    )

    # Train the model
    model = train_model(
        model, movie_ids, ratings, genre_list, actor_list, director_list
    )
    model.save(MOVIE_SUGGESTIONS_MODEL)
model = load_model(MOVIE_SUGGESTIONS_MODEL)

app = FastAPI()


@app.get("/version")
def version():
    return JSONResponse(content=jsonable_encoder({"version": "1.0"}))


@app.get("/train")
def train():
    try:
        global model
        populate_lists()

        # Instantiate the model
        new_model = build_model(
            num_movies=num_movies + 1,
            num_genres=len(genre_list),
            num_actors=len(actor_list),
            num_directors=len(director_list),
        )

        # Train the model
        new_model = train_model(
            new_model, movie_ids, ratings, genre_list, actor_list, director_list
        )
        new_model.save(MOVIE_SUGGESTIONS_MODEL)
        model = load_model(MOVIE_SUGGESTIONS_MODEL)

        _logger.info("Training completed.")
        return JSONResponse(
            status_code=200,
            content=jsonable_encoder(
                {"status": "success", "message": "Training completed"}
            ),
        )
    except Exception as e:
        _logger.error(f"Training failed: {str(e)}")
        return JSONResponse(
            status_code=500,
            content=jsonable_encoder({"status": "error", "message": str(e)}),
        )


@app.get("/suggestions")
def suggestions():
    global genre_list, actor_list, director_list, model, num_movies

    # Fetch new movie ids
    new_releases = fetch_new_releases(1) + fetch_new_releases(2)
    watchlist_movie_ids = get_movie_ids()

    # Filter out movies that are in watchlist
    filtered_movies = [
        movie for movie in new_releases if movie["id"] not in watchlist_movie_ids
    ]

    def predict_rating_for_movie(movie):
        movie_data = preprocess_movie_data(
            fetch_movie_details(movie["id"]), genre_list, actor_list, director_list
        )
        predicted_rating = model.predict(
            [
                np.array([0]),  # single user ID
                np.array([num_movies]),
                np.array([movie_data["genre_vector"]]),
                np.array([[movie_data["release_year"]]]),
                np.array([[movie_data["duration"]]]),
                np.array([[movie_data["popularity"]]]),
                np.array([movie_data["actor_vector"]]),
                np.array([movie_data["director_vector"]]),
                np.array([[movie_data["average_rating"]]]),
            ]
        )
        movie["predicted_rating"] = float(predicted_rating[0][0] * 5)
        return movie

    # Use ThreadPoolExecutor to parallelize prediction
    with ThreadPoolExecutor(max_workers=20) as executor:
        future_to_movie = {executor.submit(predict_rating_for_movie, movie): movie for movie in filtered_movies}
        filtered_movies = [future.result() for future in as_completed(future_to_movie)]

    # Sort by predicted rating in descending order
    sorted_movies = sorted(filtered_movies, key=lambda x: x["predicted_rating"], reverse=True)

    return JSONResponse(status_code=200, content=jsonable_encoder(sorted_movies))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Movies Suggestions")
    parser.add_argument(
        "-p",
        "--port",
        help="Port number to run server",
        type=int,
        default=8005,
    )
    args = parser.parse_args()

    uvicorn.run(
        "main:app", host="0.0.0.0", port=args.port, reload=True, log_level="info"
    )

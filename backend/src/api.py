"""API module."""

import logging
import math
import operator
from itertools import groupby
from typing import Annotated

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from orm.models import Hall, Movie, MoviePlace, User, WantToWatch, Watched

logging.basicConfig(level=logging.INFO)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api")
def root(
    *,
    date: Annotated[list[str] | None, Query()] = None,
    min_time: str = "00:00",
    max_time: str = "23:59",
    dubbed: str | None = None,
    subbed: str | None = None,
    open_air: str | None = None,
    closed: str | None = None,
    min_rating: float | None = None,
    min_critics_rating: float | None = None,
    cinobo_pass: str | None = None,
    watched: str | None = None,
    want_to_watch: str | None = None,
    unlisted: str | None = None,
) -> JSONResponse:
    if date is None:
        date = []
    user_watched = (
        User.select(Movie.imdb_url)
        .join(Watched)
        .join(Movie)
        .where(User.letterboxd_id == "alexiszam")
    )
    user_want_to_watch = (
        User.select(Movie.imdb_url)
        .join(WantToWatch)
        .join(Movie)
        .where(User.letterboxd_id == "alexiszam")
    )
    user_unlisted = Movie.select(Movie.imdb_url).where(
        (Movie.imdb_url.not_in(user_watched))
        & (Movie.imdb_url.not_in(user_want_to_watch))
    )
    movie_places = (
        MoviePlace.select()
        .join(Hall)
        .switch(MoviePlace)
        .join(Movie)
        .where(
            # & (MoviePlace.time >= now.time())
            MoviePlace.date.in_(date)
            & (MoviePlace.time >= min_time)
            & (MoviePlace.time <= max_time)
        )
        .order_by(
            -(
                MoviePlace.movie.rating * MoviePlace.movie.rating
                + (
                    (MoviePlace.movie.critics_rating * 2)
                    * (MoviePlace.movie.critics_rating * 2)
                )
            ),
            MoviePlace.movie,
            MoviePlace.hall,
            MoviePlace.date,
            MoviePlace.time,
        )
    )

    match (open_air, closed):
        case ("on", None):
            movie_places = movie_places.where(MoviePlace.hall.open_air)
        case (None, "on"):
            movie_places = movie_places.where(~MoviePlace.hall.open_air)
        case (None, None):
            return JSONResponse(content={"movies": []})

    match (dubbed, subbed):
        case ("on", None):
            movie_places = movie_places.where(MoviePlace.dubbed)
        case (None, "on"):
            movie_places = movie_places.where(~MoviePlace.dubbed)
        case (None, None):
            return JSONResponse(content={"movies": []})

    if cinobo_pass == "on":  # noqa: S105
        movie_places = movie_places.where(MoviePlace.cinobo_pass)

    if min_rating is not None:
        movie_places = movie_places.where(
            (MoviePlace.movie.rating == 0) | (MoviePlace.movie.rating >= min_rating)
        )
    if min_critics_rating is not None:
        movie_places = movie_places.where(
            (MoviePlace.movie.critics_rating == 0)
            | (MoviePlace.movie.critics_rating >= min_critics_rating)
        )

    match (want_to_watch, watched, unlisted):
        case (None, None, None):
            return JSONResponse(content={"movies": []})
        case (None, None, "on"):
            movie_places = movie_places.where(Movie.imdb_url.in_(user_unlisted))
        case (None, "on", None):
            movie_places = movie_places.where(Movie.imdb_url.in_(user_watched))
        case (None, "on", "on"):
            movie_places = movie_places.where(
                Movie.imdb_url.in_(user_watched) | Movie.imdb_url.in_(user_unlisted)
            )
        case ("on", None, None):
            movie_places = movie_places.where(Movie.imdb_url.in_(user_want_to_watch))
        case ("on", None, "on"):
            movie_places = movie_places.where(
                Movie.imdb_url.in_(user_want_to_watch)
                | Movie.imdb_url.in_(user_unlisted)
            )
        case ("on", "on", None):
            movie_places = movie_places.where(
                (Movie.imdb_url.in_(user_watched))
                | (Movie.imdb_url.in_(user_want_to_watch))
            )
    movie_places = {
        "movies": [
            {
                "title": movie.title,
                "original_title": movie.original_title,
                "url": movie.url,
                "imdb_url": movie.imdb_url,
                "rating": float(movie.rating),
                "votes": int(movie.votes),
                "critics_rating": float(movie.critics_rating),
                "critics_votes": int(movie.critics_votes),
                "halls": [
                    {
                        "name": hall.name,
                        "url": hall.url,
                        "lat": float(hall.lat),
                        "lng": float(hall.lng),
                        "dates": [
                            {
                                "date": str(date),
                                "times": [{"time": str(item.time)} for item in __group],
                            }
                            for date, __group in groupby(
                                _group, key=operator.attrgetter("date")
                            )
                        ],
                    }
                    for hall, _group in groupby(group, key=operator.attrgetter("hall"))
                ],
            }
            for movie, group in groupby(movie_places, key=operator.attrgetter("movie"))
        ]
    }
    return JSONResponse(content=movie_places)

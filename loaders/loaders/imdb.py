import dataclasses
import logging
import string
import time

from imdb import Cinemagoer, IMDbDataAccessError, Movie
from nltk.metrics import distance as d

MAX_EDIT_DISTANCE = 3
MAX_YEAR_DIFFERENCE = 3

logging.getLogger("imdbpy").disabled = True


@dataclasses.dataclass(slots=True)
class MovieInfo:
    title: str
    original_title: str | None
    imdb_rating: float
    imdb_votes: int
    imdb_url: str


def _normalize(s: str) -> str:
    return " ".join(
        s.lower().translate(str.maketrans("", "", string.punctuation)).split()
    )


def get_movie_info(movie: Movie) -> MovieInfo:
    title = movie.get("localized title")
    original_title = movie.get("original title")
    if original_title == title:
        original_title = None
    rating = movie.get("rating")
    votes = movie.get("votes")
    if (rating is None and votes is not None) or (rating is not None and votes is None):
        logging.warning("Mismatched rating and votes: %s %s", rating, votes)
    return MovieInfo(
        title=title,
        original_title=original_title,
        imdb_rating=rating or 0,
        imdb_votes=votes or 0,
        imdb_url=f"http://www.imdb.com/title/tt{movie.movieID}/",
    )


def _get_movie(imdb_id: str, titles: list[str], year: int) -> MovieInfo | None:
    cinemagoer = Cinemagoer(timeout=10)
    movie = cinemagoer.get_movie(imdb_id)
    info = get_movie_info(movie)
    if titles is not None and year is not None:
        _titles = [_normalize(t) for t in titles]
        imdb_titles = [info.title] + (
            [info.original_title] if info.original_title else []
        )
        _imdb_titles = [_normalize(t) for t in imdb_titles]
        if not (any(t for t in _imdb_titles if t in _titles)):
            logging.warning("Mismatched titles: %s %s", imdb_titles, titles)
            return search_movie(titles, year)
    return get_movie_info(movie)


def get_movie(imdb_id: str, titles: list[str], year: int) -> MovieInfo | None:
    while True:
        try:
            return _get_movie(imdb_id, titles, year)
        except IMDbDataAccessError:
            logging.warning("503, retrying in 60 seconds")
            time.sleep(60)
        except Exception:
            logging.exception(imdb_id, titles, year)
            return None


def _search_movie(titles: list[str], year: int | None = None) -> MovieInfo | None:
    cinemagoer = Cinemagoer(timeout=10)
    _titles = [_normalize(t) for t in titles]
    for t in titles:
        best_movie = None
        best_distance = 99999
        movies = cinemagoer.search_movie(t)
        for _movie in movies:
            if year is not None:
                _year = _movie.get("year")
                if _year is None:
                    logging.warning("No year found for %s", _movie)
                    continue
                _year = int(_year)
            imdb_id = _movie.movieID
            movie = cinemagoer.get_movie(imdb_id)
            _original_tile = movie.get("original title")
            _title = movie.get("localized title")
            akas = set(movie.get("akas", []) + movie.get("akas from release info", []))
            greek_titles = [
                "(".join(aka.split("(")[:-1]) for aka in akas if "Greece" in aka
            ]
            _greek_titles = [_normalize(t) for t in greek_titles]
            if (
                _normalize(_original_tile) in _titles
                or _normalize(_title) in _titles
                or any(t for t in _greek_titles if t in _titles)
            ) and (year is None or _year == year):
                return get_movie_info(movie)
            min_edit_distance = 99999
            _best_movie = None
            for __title in _titles:
                for _imdb_title in (
                    _normalize(_original_tile),
                    _normalize(_title),
                    *_greek_titles,
                ):
                    edit_distance = d.edit_distance(__title, _imdb_title)
                    if edit_distance < min_edit_distance:
                        min_edit_distance = edit_distance
                        _best_movie = movie
            year_difference = 0 if year is None else abs(_year - year)
            distance = min_edit_distance ^ 2 + year_difference ^ 2
            if (
                min_edit_distance < MAX_EDIT_DISTANCE
                and year_difference < MAX_YEAR_DIFFERENCE
                and distance < best_distance
            ):
                best_distance = min_edit_distance
                best_movie = _best_movie
    if best_movie is not None:
        logging.warning(
            "Could not find exact match for %s (%s) but found %s",
            titles,
            year,
            best_movie.get("localized title"),
        )
        return get_movie_info(best_movie)
    # logging.error("IMDb URL not found for %s %s", titles, year)
    return None


def search_movie(titles: list[str], year: int | None = None) -> MovieInfo | None:
    while True:
        try:
            return _search_movie(titles, year)
        except IMDbDataAccessError:
            logging.warning("503, retrying in 60 seconds")
            time.sleep(60)
        except Exception:
            logging.exception(titles, year)
            return None

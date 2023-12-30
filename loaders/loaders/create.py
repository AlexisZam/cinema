"""Load data from Athinorama and IMDb."""

import logging
from concurrent.futures import ThreadPoolExecutor

from orm.models import Hall, Movie, MoviePlace, User, WantToWatch, Watched, database

from .athinorama import HallLoader, MovieLoader
from .cinobo import main
from .letterboxd import letterboxd

logging.basicConfig(level=logging.INFO)


if __name__ == "__main__":
    database.create_tables([Hall, Movie, MoviePlace, User, WantToWatch, Watched])

    logging.info("Updating data")

    for loader_cls in (HallLoader, MovieLoader):
        loaders = loader_cls.list()
        with ThreadPoolExecutor() as executor:
            executor.map(lambda loader: loader.load(), loaders)

    # main()

    user = User.create(letterboxd_id="alexiszam")

    letterboxd_queries = [
        (list_name, imdb_id)
        for list_name, imdb_ids in letterboxd()
        for imdb_id in imdb_ids
    ]

    def safe_execute(t: tuple[str, str]) -> None:
        list_name, imdb_id = t
        movie = Movie.get_or_none(Movie.imdb_url == imdb_id)
        if movie is None:
            return
        model = Watched if list_name == "films" else WantToWatch
        model.create(user=user, movie=movie)
        if list_name == "films":
            logging.info("Watched %s", imdb_id)
        else:
            logging.info("Want to watch %s", imdb_id)

    with ThreadPoolExecutor() as executor:
        executor.map(safe_execute, letterboxd_queries)

    logging.info("Updated data")

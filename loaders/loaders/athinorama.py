"""Load data from Athinorama and IMDb."""

import abc
import dataclasses
import logging
from abc import ABC
from pathlib import PurePath
from typing import ClassVar, Self
from urllib import parse

from orm.models import BaseModel, Hall, Movie, MoviePlace

from .bs4 import get_href, load_beautiful_soup
from .foo import parse_datetimes
from .imdb import get_movie, search_movie
from .letterboxd import get_rating
from .maps import get_lat_lng


def _get_url_path(url: str) -> str:
    return parse.urlparse(url).path


@dataclasses.dataclass(slots=True)
class Loader(ABC):
    """Data loader."""

    BASE_URL = "https://www.athinorama.gr/cinema/"
    base_path: ClassVar[str]
    model = BaseModel

    name: str

    @classmethod
    def _cls_url(cls) -> str:
        return parse.urljoin(cls.BASE_URL, cls.base_path)

    @property
    def url(self: Self) -> str:
        """Build URL."""
        return parse.urljoin(self._cls_url(), self.name)

    @classmethod
    def list(cls) -> list[Self]:
        """List URLs."""
        soup = load_beautiful_soup(cls.BASE_URL)
        path = _get_url_path(cls._cls_url())
        anchors = soup.select(f"a[href^='{path}']")
        hrefs = {_get_url_path(get_href(anchor)) for anchor in anchors}
        return [cls(href) for href in hrefs]

    @abc.abstractmethod
    def _load(self: Self) -> None:
        pass

    def load(self: Self) -> None:
        """Load data."""
        logging.info("Loading %s", self.url)
        self._load()
        logging.info("Loaded %s", self.url)


class MovieLoader(Loader):
    """Athinorama movie data loader."""

    base_path = "movie/"
    model = Movie

    def _load(self: Self) -> None:
        soup = load_beautiful_soup(self.url)

        review_title = soup.select_one(".review-title")
        if review_title is None:
            logging.error("Review title not found")
            return
        title = review_title.select_one("h1")
        if title is None:
            logging.error("Title not found")
            return
        titles = [title.get_text(strip=True)]
        if (original_title := review_title.select_one(".original-title")) is not None:
            titles += original_title.get_text(strip=True).split("/")
        _year = review_title.select_one(".year")
        if _year is None:
            logging.error("Year not found")
            return
        __year = _year.get_text(strip=True) or None
        if __year is None:
            logging.error("Year not found")
            return
        year = int(__year)

        spans = soup.select(".critic > div > span")
        ratings = [float(span.get_text(strip=True).replace(",", ".")) for span in spans]
        critics_votes = 0
        critics_rating = 0.0
        if ratings:
            critics_votes = len(ratings)
            if critics_votes:
                critics_rating = sum(ratings) / critics_votes

        imdb_movie_url = soup.select_one(".imdb")
        if imdb_movie_url is not None and (
            imdb_id := PurePath(
                parse.urlparse(get_href(imdb_movie_url)).path
            ).name.strip()
        ).startswith("tt"):
            info = get_movie(imdb_id.removeprefix("tt"), titles, year)
        else:
            info = search_movie(titles, year)
        if info is None:
            logging.error("Athinorama movie not found: %s", titles)
            return

        imdb_id = info.imdb_url.split("/")[-2]
        letterboxd_rating, letterboxd_votes = get_rating(imdb_id)
        votes = info.imdb_votes + letterboxd_votes
        rating = 0.0
        if votes:
            rating = (
                info.imdb_rating * info.imdb_votes
                + letterboxd_rating * 2 * letterboxd_votes
            ) / votes
        self.model.create(
            url=self.url,
            title=info.title,
            original_title=info.original_title,
            rating=rating,
            votes=votes,
            critics_rating=critics_rating,
            critics_votes=critics_votes,
            imdb_url=info.imdb_url,
        )
        event_places_link = soup.select_one("#eventPlacesLink")
        if event_places_link is None:
            logging.error("Event places link not found")
            return
        movie_places_url = _get_url_path(get_href(event_places_link))
        MoviePlacesLoader(movie_places_url).load()


@dataclasses.dataclass(slots=True)
class HallLoader(Loader):
    """Hall data loader."""

    base_path = "halls/"
    model = Hall

    def _load(self: Self) -> None:
        soup = load_beautiful_soup(self.url)
        tag = soup.select_one(".review-title")
        if tag is None:
            logging.error("Hall not found")
            return
        name_ = tag.select_one("h1")
        if name_ is None:
            logging.error("Hall name not found")
            return
        name = name_.get_text(strip=True)
        maps = tag.select_one(".infos-item > nav > a")
        if maps is None:
            logging.error("Maps not found")
            return
        lat, lng = map(
            float,
            parse.parse_qs(parse.urlparse(get_href(maps)).query)["destination"][
                0
            ].split(),
        )
        if (lat, lng) == (0, 0):
            lat, lng = get_lat_lng(name)
        open_air = (
            tag.select_one("img[src='/Content/images/summerRoom.png']") is not None
        )
        self.model.create(url=self.url, name=name, lat=lat, lng=lng, open_air=open_air)


@dataclasses.dataclass(slots=True)
class MoviePlacesLoader(Loader):
    """Movie places data loader."""

    base_path = "movie/places/"
    model = MoviePlace

    def _load(self: Self) -> None:
        beautiful_soup = load_beautiful_soup(self.url)
        anchor = beautiful_soup.select_one(".item-image.poster-image > a")
        if anchor is None:
            logging.error("Movie not found")
            return
        href = _get_url_path(get_href(anchor))
        movie = MovieLoader(href).url
        items = beautiful_soup.select(".item.card-item")
        for item in items:
            anchor = item.select_one(".item-title > a")
            if anchor is None:
                logging.error("Hall not found")
                continue
            href = _get_url_path(get_href(anchor))
            hall = HallLoader(href).url
            datetimess = item.select(".inner")
            for datetimes in datetimess:
                datetimes_ = datetimes.get_text(separator=" ", strip=True)
                for _datetime, dubbed in parse_datetimes(datetimes_):
                    self.model.create(
                        movie=movie,
                        hall=hall,
                        date=_datetime.date(),
                        time=_datetime.time(),
                        dubbed=dubbed,
                        cinobo_pass=False,
                    )

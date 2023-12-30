import json
import logging
from concurrent.futures import ThreadPoolExecutor
from urllib import parse
from xml.etree import ElementTree

from .bs4 import get_href, load_beautiful_soup

USER = "alexiszam"
LIST_TYPES = ["films", "watchlist"]

BASE_URL = "https://letterboxd.com/"


def get_imdb_id(url: str) -> str | None:
    soup = load_beautiful_soup(url)
    anchor = soup.select_one("a[href^='http://www.imdb.com/title/tt']")
    if not anchor:
        logging.error("IMDb anchor not found in %s", url)
        return None
    return "/".join(get_href(anchor).split("/")[:-1]) + "/"


def get_num_pages(user: str, list_name: str) -> int:
    user_url = parse.urljoin(BASE_URL, f"{user}/")
    url = parse.urljoin(user_url, f"{list_name}/")
    soup = load_beautiful_soup(url)
    anchors = soup.select(f"li a[href^='/{user}/{list_name}/page/']")
    if not anchors:
        return 1
    return int(anchors[-1].text)


def get_films_paginated(user: str, list_name: str, page: int) -> list[str]:
    user_url = parse.urljoin(BASE_URL, f"{user}/")
    url = parse.urljoin(parse.urljoin(user_url, f"{list_name}/page/"), str(page))
    soup = load_beautiful_soup(url)
    divs = soup.select("li div[data-target-link^='/film/']")
    return [parse.urljoin(BASE_URL, str(div["data-target-link"])) for div in divs]


def get_films(user: str, list_name: str) -> list[str]:
    num_pages = get_num_pages(user, list_name)
    with ThreadPoolExecutor() as executor:
        filmss = executor.map(
            lambda page: get_films_paginated(user, list_name, page),
            range(1, num_pages + 1),
        )
        return [film for films in filmss for film in films]


def get_list(user: str, list_name: str) -> list[str | None]:
    urls = get_films(user, list_name)
    with ThreadPoolExecutor() as executor:
        return list(executor.map(get_imdb_id, urls))


def letterboxd() -> list[tuple[str, list[str | None]]]:
    with ThreadPoolExecutor() as executor:
        imdb_ids = executor.map(lambda list_name: get_list(USER, list_name), LIST_TYPES)
    return list(zip(LIST_TYPES, imdb_ids, strict=True))


def parse_with_stdlib(text: str) -> str:
    return (
        next(ElementTree.fromstring(text).iter("script"))
        .text.strip()
        .strip("/*  */")
        .strip()
    )


def get_rating(imdb_id: str) -> tuple[float, int]:
    url = parse.urljoin(BASE_URL, f"imdb/{imdb_id}")
    soup = load_beautiful_soup(url)
    script = str(soup.select_one("script[type='application/ld+json']"))
    if script is None:
        logging.warning("Letterboxd rating not found in %s", url)
        return 0, 0
    aggregate_rating = json.loads(parse_with_stdlib(script))["aggregateRating"]
    return float(aggregate_rating["ratingValue"]), int(aggregate_rating["ratingCount"])

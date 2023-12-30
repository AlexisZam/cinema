import logging
import re
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, time, timedelta

from bs4 import BeautifulSoup
from geopy import distance

from orm.models import Hall, Movie, MoviePlace

from .bs4 import load_beautiful_soup
from .imdb import search_movie
from .maps import get_lat_lng

today = datetime.now(tz=UTC).date()
days_ = (today.weekday() - 3) % 7
last_thursday = today - timedelta(days=days_)

days = ["Πέμπτη", "Παρασκευή", "Σάββατο", "Κυριακή", "Δευτέρα", "Τρίτη", "Τετάρτη"]

days_regex = f"{"|".join(days)}|,|-"


def expand_days(input_str: str) -> list:
    matches = re.findall(days_regex, input_str)

    expanded = []
    i = 0
    while i < len(matches):
        if matches[i] in days:
            start_day = days.index(matches[i])
            expanded.append(start_day)
            if i + 1 < len(matches) and matches[i + 1] == "-":
                end_day = days.index(matches[i + 2])
                expanded.extend(range(start_day + 1, end_day + 1))
                i += 2
        i += 1

    return [last_thursday + timedelta(days=offset) for offset in expanded]


def get_titles(soup: BeautifulSoup) -> dict[str, tuple[list[str], int]]:
    titles = {}
    for a in soup.select("a[href^='/cinobo-pass/']"):
        p = a.select("p")
        greek_title = p[-1].text
        spans = a.select("span")
        english_title = spans[-5].text
        year = spans[-1].text
        titles[greek_title] = ([english_title, greek_title], int(year))
    return titles


def update_movie_place(
    movie: Movie, hall: str, location: tuple[float, float], date: datetime, time: time
) -> None:
    halls = Hall.select()
    _halls = sorted(
        halls, key=lambda hall: distance.distance((hall.lat, hall.lng), location)
    )
    for hall_ in _halls:
        num_rows = (
            MoviePlace.update({MoviePlace.cinobo_pass: True})
            .where(
                MoviePlace.movie == movie.url,
                MoviePlace.hall == hall_.url,
                MoviePlace.date == date,
                MoviePlace.time == time,
            )
            .execute()
        )
        if num_rows == 1:
            logging.info(
                "Updated %s at %s on %s %s", movie.title, hall_.name, date, time
            )
            break
    else:
        logging.error(
            "No hall found for %s at %s on %s %s", movie.title, hall, date, time
        )


def main() -> None:
    """Get data from Cinobo."""
    soup = load_beautiful_soup("https://cinobo.com/cinobo-pass")

    titles = get_titles(soup)

    table = soup.select_one("#program + table")
    if table is None:
        logging.error("Program table not found")
        return
    ths = table.select("th")
    titless = [titles.get(th.text, [[th.text]]) for th in ths[1:]]
    with ThreadPoolExecutor() as executor:
        movies = list(
            executor.map(
                lambda titles_: info.imdb_url
                if (info := search_movie(*titles_)) is not None
                else None,
                titless,
            )
        )
    trs = table.select("tbody > tr")
    skipped = []
    for tr in trs:
        tds = tr.select("td")
        divs = tds[0].select("div")
        city = divs[1].text
        if city != "Αθήνα":
            continue
        hall = divs[0].text
        location = get_lat_lng(hall)
        for i, td in enumerate(tds[1:]):
            divs = td.select("div > div")
            if not divs:
                continue
            if movies[i] is None:
                skipped.append(titless[i][0])
                continue
            dates = expand_days(divs[0].text)
            time = datetime.strptime(divs[1].text, "%H:%M").astimezone().time()
            for date in dates:
                try:
                    movie = Movie.get(Movie.imdb_url == movies[i])
                    update_movie_place(movie, hall, location, date, time)
                except Exception:
                    logging.exception("")
    for title_ in skipped:
        logging.error("Cinobo movie not found: %s", title_)

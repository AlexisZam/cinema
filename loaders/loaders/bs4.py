"""Loaders for BeautifulSoup objects."""

import logging

import requests
from bs4 import BeautifulSoup, Tag

TIMEOUT = (3.05, 27)
PARSER = "lxml"


def load_beautiful_soup(url: str) -> BeautifulSoup:
    """Load a URL and return a BeautifulSoup object."""
    response = requests.get(url, timeout=TIMEOUT)
    response.raise_for_status()
    return BeautifulSoup(response.text, features=PARSER)


def get_href(tag: Tag) -> str:
    hrefs = tag["href"]
    if isinstance(hrefs, str):
        return hrefs
    logging.warning("Multiple hrefs: %s", hrefs)
    return hrefs[0]

from pathlib import Path

from peewee import (
    BooleanField,
    CharField,
    DateField,
    DecimalField,
    ForeignKeyField,
    IntegerField,
    Model,
    PostgresqlDatabase,
    TimeField,
)

password = Path("/etc/secrets/postgres-password").read_text(encoding="utf-8").strip()

database = PostgresqlDatabase(
    "postgres", user="postgres", password=password, host="database", port=5432
)


class BaseModel(Model):
    class Meta:
        database = database


class Movie(BaseModel):
    """Movie data."""

    url = CharField(primary_key=True)
    title = CharField()
    original_title = CharField(null=True)
    rating = DecimalField()
    votes = IntegerField()
    critics_rating = DecimalField()
    critics_votes = IntegerField()
    imdb_url = CharField(unique=True)


class Hall(BaseModel):
    """Hall data."""

    url = CharField(primary_key=True)
    name = CharField()
    lat = DecimalField()
    lng = DecimalField()
    open_air = BooleanField()


class MoviePlace(BaseModel):
    """Movie place data."""

    movie = ForeignKeyField(Movie)
    hall = ForeignKeyField(Hall)
    date = DateField()
    time = TimeField()
    dubbed = BooleanField()
    cinobo_pass = BooleanField()


class User(BaseModel):
    """User data."""

    letterboxd_id = CharField(primary_key=True)


class Watched(BaseModel):
    """Film watched by user."""

    user = ForeignKeyField(User)
    movie = ForeignKeyField(Movie, field="imdb_url")


class WantToWatch(BaseModel):
    """Film user wants to watch."""

    user = ForeignKeyField(User)
    movie = ForeignKeyField(Movie, field="imdb_url")

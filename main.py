import sqlite3

from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Float
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import requests

'''
Red underlines? Install the required packages first: 
Open the Terminal in PyCharm (bottom left). 

On Windows type:
python -m pip install -r requirements.txt    

On MacOS type:
pip3 install -r requirements.txt

This will install the packages from requirements.txt for this project.
'''
MOVIE_DB_IMAGE_URL = 'https://image.tmdb.org/t/p/original/'
headers = {
    "accept": "application/json",
    "Authorization": "Bearer eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiJlODg4MDRkZDQ2NGM5Y2E0ZjI2NmUwMTI2YzQ0YzEzYiIsIm5iZiI6MTcyNjAwNTkzNi44MjU3MDYsInN1YiI6IjY2ZTBjMDEwMDAwMDAwMDAwMDIyODg0YyIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.Y9UY-0CJLQ-zvuccXnzK9WthchagGs_SDz_ay0kgY30"
}

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap5(app)


# CREATE DB
class Base(DeclarativeBase):
    pass


app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///movies.db"

# CREATE TABLE
db = SQLAlchemy(model_class=Base)

db.init_app(app)


class Movie(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    rating: Mapped[float] = mapped_column(Float, nullable=True)
    ranking: Mapped[int] = mapped_column(Integer, nullable=True)
    review: Mapped[str] = mapped_column(String(250), nullable=True)
    img_url: Mapped[str] = mapped_column(String(250), nullable=False)


with app.app_context():
    db.create_all()


class RateMovieForm(FlaskForm):
    rating = StringField("Your Rating Out of 10", validators=[DataRequired()])
    review = StringField("Your Review", validators=[DataRequired()])
    submit = SubmitField("Done")


class AddMovie(FlaskForm):
    title = StringField("Movie name", validators=[DataRequired()])
    submit = SubmitField("Done")


@app.route("/")
def home():
    result = db.session.execute(db.select(Movie).order_by(Movie.rating))
    all_movies = result.scalars().all()
    for x in range(len(all_movies)):
        all_movies[x].ranking = len(all_movies) - x
    return render_template("index.html", movies=all_movies)


@app.route("/edit", methods=["GET", "POST"])
def edit():
    form = RateMovieForm()
    movie_id = request.args.get("id")
    movie = db.get_or_404(Movie, movie_id)
    if form.validate_on_submit():
        movie.rating = form.rating.data
        movie.review = form.review.data
        db.session.commit()
        return redirect(location=url_for("home"))

    return render_template("edit.html", form=form, movie=movie)


@app.route("/delete")
def delete():
    movie_id = request.args.get("id")
    movie = db.get_or_404(Movie, movie_id)
    db.session.delete(movie)
    db.session.commit()
    return redirect(location=url_for("home"))


@app.route("/add", methods=["GET", "POST"])
def add():
    form = AddMovie()
    if form.validate_on_submit():
        title = form.title.data
        url = f"https://api.themoviedb.org/3/search/movie?query={title}&include_adult=false&language=en-US&page=1"
        response = requests.get(url, headers=headers)
        data = response.json()["results"]
        return render_template("select.html", movies=data)

    return render_template("add.html", form=form)


@app.route("/find")
def find():
    movie_id = request.args.get("id")
    if movie_id:
        url = f"https://api.themoviedb.org/3/movie/{movie_id}language=en-US"
        r = requests.get(url, headers=headers)
        data = r.json()
        new_movie = Movie(
            title=data["title"],
            img_url= f"{MOVIE_DB_IMAGE_URL}{data['poster_path']}",
            year=data["release_date"],
            description=data["overview"]

        )
        db.session.add(new_movie)
        db.session.commit()
        return redirect(url_for("edit",id = new_movie.id))


if __name__ == '__main__':
    app.run(debug=True)

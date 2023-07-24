from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import requests
from dotenv import load_dotenv
import os

load_dotenv()
#To connect to database
SECRET_KEY = os.getenv("SECRET_KEY")
app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY
Bootstrap(app)
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///new-movie-collection.db"
db = SQLAlchemy(app)

MOVIE_DB_SEARCH_URL = "https://api.themoviedb.org/3/search/movie"
MOVIE_DB_API_KEY =os.getenv("MOVIE_DB_API_KEY")
MOVIE_DB_INFO_URL = "https://api.themoviedb.org/3/movie"
MOVIE_DB_IMAGE_URL = "https://image.tmdb.org/t/p/w300"

#To create a table in the database
class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(500), nullable=False)
    rating = db.Column(db.Float, nullable=True)
    ranking = db.Column(db.Integer, nullable=True)
    review = db.Column(db.String(250), nullable=True)
    img_url = db.Column(db.String(250), nullable=False)
with app.app_context():
    db.create_all()
# with app.app_context():
#     new_movie = Movie(
#         title="Phone Booth",
#         year=2002,
#         description="Publicist Stuart Shepard finds himself trapped in a phone booth, pinned down by an extortionist's"
#                     " sniper rifle. Unable to leave or receive outside help, Stuart's negotiation with the caller leads"
#                     " to a jaw-dropping climax.",
#         rating=7.3,
#         ranking=10,
#         review="My favourite character was the caller.",
#         img_url="https://image.tmdb.org/t/p/w500/tjrX2oWRCM3Tvarz38zlZM7Uc10.jpg"
#     )
#     db.session.add(new_movie)
#     db.session.commit()

#WTForms to add rating
class RateMovieForm(FlaskForm):
    rating = StringField("You are Rating Out of 10 e.g 7.5")
    review = StringField("Your Review")
    submit = SubmitField("Submit")

#Wtforms
class AddMovieForm(FlaskForm):
    title = StringField("Title of the Movie",validators=[DataRequired()])
    submit = SubmitField("submit")

@app.route("/")
def home():
    all_movies = Movie.query.order_by(Movie.rating).all()
    for i in range(len(all_movies)):
        all_movies[i].ranking = len(all_movies) - i
    db.session.commit()
    return render_template("index.html", movies=all_movies)
#random



#To delete the movie
@app.route("/delete")
def delete_movie():
    movie_id = request.args.get("id")
    movie = Movie.query.get(movie_id)
    db.session.delete(movie)
    db.session.commit()
    return redirect(url_for("home"))

#To add a movie
@app.route("/add",methods=["GET", "POST"])
def add_movie():
    form = AddMovieForm()
    if form.validate_on_submit():    #It runs when we click on submit button
        movie_title = form.title.data
        response = requests.get(MOVIE_DB_SEARCH_URL,params={"api_key":MOVIE_DB_API_KEY,"query":movie_title})   #Gets movie details from api
        data = response.json()['results']
        print(data)
        return render_template("select.html",options=data)
    return render_template("add.html", form=form)

#To find the movie using api

@app.route("/find")
def find_movie():
    movie_api_id = request.args.get("id")
    if movie_api_id:
        movie_api_url = f"{MOVIE_DB_INFO_URL}/{movie_api_id}"
        response = requests.get(movie_api_url, params={"api_key": MOVIE_DB_API_KEY, "language": "en-US"})
        data = response.json()
        print(data)
        print(response)
        new_movie = Movie(
            title=data["title"],
            #The data in release_date includes month and day, we will want to get rid of.
            year=data["release_date"].split("-")[0],
            img_url=f"{MOVIE_DB_IMAGE_URL}{data['poster_path']}",
            description=data["overview"]
        )
        db.session.add(new_movie)
        db.session.commit()
        return redirect(url_for("rate_movie", id=new_movie.id))

#To edit the movie as soon as we select the movie from the api

@app.route("/edit",methods=["GET","POST"])
def rate_movie():
    form = RateMovieForm()
    movie_id = request.args.get("id")
    movie = Movie.query.get(movie_id)
    if form.validate_on_submit():
        movie.rating = float(form.rating.data)
        movie.review = form.review.data
        db.session.commit()
        return redirect(url_for('home'))
    return render_template("edit.html", movie=movie, form=form)


if __name__ == '__main__':
    app.run(debug=True)

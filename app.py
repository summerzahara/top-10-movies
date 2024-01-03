import os

from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, DecimalField, SubmitField
from wtforms.validators import DataRequired
import requests
from icecream import ic
from dotenv import load_dotenv

load_dotenv()
tmdb_api_key = os.environ["TMDB_API_KEY"]

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap5(app)

#Create Database
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///top-10-movies.db"

db = SQLAlchemy()
db.init_app(app)

#Create a table
class Movies(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, unique=True,nullable=False)
    year = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String, nullable=False)
    rating = db.Column(db.Float, nullable=False)
    ranking = db.Column(db.Integer, nullable=False)
    review = db.Column(db.String, nullable=False)
    img_url = db.Column(db.String, nullable=False)

#Create Table in Schema
with app.app_context():
    db.create_all()

#Create Form
class UpdateRating(FlaskForm):
    rating = DecimalField('Your Rating out of 10 e.g. 7.5', validators=[DataRequired()])
    review = StringField('Your Review', validators=[DataRequired()])
    submit = SubmitField('Done')

class AddMovie(FlaskForm):
    movie = StringField('Movie Title', validators=[DataRequired()])
    submit = SubmitField('Add Movie')

#Create Record
# with app.app_context():
#     add_movie = Movies(
#         title="Phone Booth",
#         year=2002,
#         description="Publicist Stuart Shepard finds himself trapped in a phone booth, pinned down by an extortionist's sniper rifle. Unable to leave or receive outside help, Stuart's negotiation with the caller leads to a jaw-dropping climax.",
#         rating=7.3,
#         ranking=10,
#         review="My favorite character was the caller.",
#         img_url="https://image.tmdb.org/t/p/w500/tjrX2oWRCM3Tvarz38zlZM7Uc10.jpg"
#     )
    # second_movie = Movies(
    #     title="Avatar The Way of Water",
    #     year=2022,
    #     description="Set more than a decade after the events of the first film, learn the story of the Sully family (Jake, Neytiri, and their kids), the trouble that follows them, the lengths they go to keep each other safe, the battles they fight to stay alive, and the tragedies they endure.",
    #     rating=7.3,
    #     ranking=9,
    #     review="I liked the water.",
    #     img_url="https://image.tmdb.org/t/p/w500/t6HIqrRAclMCA60NsSmeqe9RmNV.jpg"
    # )
    # db.session.add(add_movie)
    # db.session.commit()


@app.route("/")
def home():
    with app.app_context():
        result = db.session.execute(db.select(Movies).order_by(Movies.rating))
        all_movies = result.scalars().all()
        count = len(all_movies)
        for movie in all_movies:
            movie.ranking = count
            ic(movie, movie.rating, movie.ranking)
            count = count - 1
    return render_template("index.html", movies=all_movies)

@app.route("/edit/<movie_id>", methods=["GET", "POST"])
def edit(movie_id):
    form = UpdateRating()
    if request.method == 'GET':
        with app.app_context():
            movie = db.session.execute(db.select(Movies).where(Movies.id == movie_id)).scalar()
        return render_template('edit.html', movie=movie, form=form)
    if request.method == 'POST':
        if form.validate_on_submit():
            new_rating = form.rating.data
            new_review = form.review.data
            ic(new_rating, new_review)
            with app.app_context():
                update_movie = db.session.execute(db.select(Movies).where(Movies.id == movie_id)).scalar()
                update_movie.rating = new_rating
                update_movie.review = new_review
                db.session.commit()
            return redirect(url_for("home"))
        return render_template('edit.html', movie=movie, form=form)

@app.route('/delete/<movie_id>')
def delete(movie_id):
    with app.app_context():
        delete_movie = db.session.execute(db.select(Movies).where(Movies.id == movie_id)).scalar()
        db.session.delete(delete_movie)
        db.session.commit()
    return redirect(url_for('home'))

@app.route('/add', methods=['GET', 'POST'])
def add():
    form = AddMovie()
    if request.method == 'GET':
        return render_template('add.html', form=form)
    if request.method == 'POST':
        movie = form.movie.data
        params = {
            "api_key": tmdb_api_key,
            "query": movie,
        }
        response = requests.get('https://api.themoviedb.org/3/search/movie', params=params)
        response.raise_for_status()
        data = response.json()
        if response.status_code == 200:
            results = data["results"]
            list_results = []
            for result in results:
                movie_title = result["title"]
                movie_date = result["release_date"]
                movie_id = result["id"]
                list_results.append([movie_title, movie_date, movie_id])
                ic(list_results)
            return render_template('select.html', list_results=list_results)
        else:
            print(f"Error: {data['status_message']}")

@app.route('/select')
def select():
    movie_id = request.args.get("movie_id")
    params = {
        "api_key": tmdb_api_key,
    }
    response = requests.get(f'https://api.themoviedb.org/3/movie/{movie_id}', params=params)
    response.raise_for_status()
    data = response.json()
    if response.status_code == 200:
        title = data["original_title"]
        year = data["release_date"][:4]
        description = data["overview"]
        img_url = f"https://image.tmdb.org/t/p/w500{data['poster_path']}"
        rating = 0
        ranking = 0
        review = "None"
        with app.app_context():
            add_movie = Movies(title=title, year=year, description=description, img_url=img_url, rating=rating, ranking=ranking, review=review)
            db.session.add(add_movie)
            db.session.commit()
            id_ = add_movie.id
        return redirect(url_for('edit', movie_id=id_))




if __name__ == '__main__':
    app.run(debug=True)

import os
import requests

from flask import Flask, session, render_template, request, jsonify
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__)
# # Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


@app.route("/")
def index():
    return render_template("index.html")

@app.route("/register", methods=["POST"])
def register():
    firstname = request.form.get("firstname")
    lastname = request.form.get("lastname")
    password = request.form.get("password")
    username = request.form.get("username")
    if db.execute("SELECT * FROM users WHERE username = :username", {"username": username}).rowcount > 0:
        return render_template("index.html", message="Username is not available. Go back and enter a different Username")
    db.execute("INSERT INTO users (firstname, lastname, username, password) VALUES (:firstname, :lastname, :username, :password)",
            {"firstname": firstname, "lastname": lastname, "username": username, "password": password})
    db.commit()
    return render_template("index.html", message="You have successfully registered, Sign in.")

@app.route("/login", methods=["POST"])
def login():
    password = request.form.get("password")
    username = request.form.get("username")
    if db.execute("SELECT username, password FROM users WHERE username = :username AND password = :password", {"username": username, "password": password}).rowcount == 0:
        return render_template("index.html", message="Wrong Username or Password. Enter Valid Information")

    session['username'] = username

    return render_template("booksearch.html", username = username)

# @app.route("/books", methods=["GET", "POST"])
# def books():
#     bookquery = db.execute("SELECT * FROM books").fetchall()
#     return render_template("books.html", bookquery=bookquery)

@app.route("/booksearch", methods=["POST"])
def booksearch():
    if 'username' in session:
        username = session['username']
        query = request.form.get("searchbook")
        query = '%' + query + '%'
        booklisted = db.execute("SELECT * from books where title like :query or author like :query or isbn like :query", {"query": query}).fetchall()
        if db.execute("SELECT * from books where title like :query or author like :query or isbn like :query", {"query": query}).rowcount == 0:
            return render_template("booksearch.html", message="Book does not exist")
        return render_template("booksearch.html", message="Click on a Book Title to view more information", booklist = booklisted, username = username)
    return render_template("index.html", message="You are not logged in. Log in to view books")

@app.route("/bookdetail/<int:id>")
def bookdetail(id):
    if 'username' in session:
        booksid = db.execute("SELECT * FROM books WHERE ID = :id", {"id": id}).fetchone()
        res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "qa7Aig5ZhQ8P58vHDI8Q", "isbns": booksid.isbn})
        data = res.json()
        bookdict = data["books"][0]
        average_rating = bookdict['average_rating']
        number_rating = bookdict['work_ratings_count']

        return render_template("bookdetail.html", booksid=booksid, average_rating=average_rating, number_rating=number_rating)
    return render_template("index.html", message="You are not logged in. Log in to view books")


@app.route("/logout", methods=["GET"])
def logout():
   # remove the username from the session if it is there
   session.pop('username', None)
   return render_template("index.html", message="You have successfully logged out")

@app.route("/api/<isbn>", methods=["GET"])
def books_api(isbn):
    booksid = db.execute("SELECT * FROM books WHERE isbn = :isbn", {"isbn": isbn}).fetchone()
    if booksid is None:
        return jsonify({"error": "Invalid ISBN"}), 422
    res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "qa7Aig5ZhQ8P58vHDI8Q", "isbns": booksid.isbn})
    data = res.json()
    bookdict = data["books"][0]
    average_rating = bookdict['average_rating']
    review_count = bookdict['work_reviews_count']

    return jsonify({
            "title": booksid.title,
            "author": booksid.author,
            "year": booksid.year,
            "isbn": booksid.isbn,
            "review_count": review_count,
            "average_score": average_rating
            }
        )

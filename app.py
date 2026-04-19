import os
import secrets
from flask import Flask, render_template, request, redirect, url_for, session, flash, abort
from werkzeug.security import generate_password_hash, check_password_hash
from db import get_db, close_db, init_db

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "supersalainen avain :O")
app.teardown_appcontext(close_db)

if not os.path.exists("database.db"):
    init_db(app)


def current_user():
    return session.get("user_id")


def require_login():
    if not current_user():
        abort(403)


def check_csrf():
    if request.form.get("csrf_token") != session.get("csrf_token"):
        abort(403)


@app.before_request
def generate_csrf_token():
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_hex(16)


# Reitit

@app.route("/")
def index():
    db = get_db()
    query = request.args.get("query", "").strip()
    genre_id = request.args.get("genre", "").strip()

    sql = (
        "SELECT m.*, u.username FROM movies m "
        "JOIN users u ON m.user_id = u.id"
    )
    params = []
    conditions = []

    if query:
        conditions.append("m.name LIKE ?")
        params.append("%" + query + "%")

    if genre_id:
        conditions.append(
            "m.id IN (SELECT movie_id FROM movie_genres WHERE genre_id = ?)"
        )
        params.append(genre_id)

    if conditions:
        sql += " WHERE " + " AND ".join(conditions)

    sql += " ORDER BY m.id DESC"
    movies = db.execute(sql, params).fetchall()

    genres = db.execute("SELECT * FROM genres ORDER BY name").fetchall()

    # Hae genret jokaiselle elokuvalle
    movie_genres = {}
    for movie in movies:
        mg = db.execute(
            "SELECT g.name FROM genres g "
            "JOIN movie_genres mg ON g.id = mg.genre_id "
            "WHERE mg.movie_id = ?",
            (movie["id"],)
        ).fetchall()
        movie_genres[movie["id"]] = [g["name"] for g in mg]

    return render_template(
        "index.html", movies=movies, query=query,
        genres=genres, selected_genre=genre_id,
        movie_genres=movie_genres
    )


# Rekisteröinti & kirjautuminen

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        check_csrf()
        username = request.form["username"].strip()
        password = request.form["password"]
        if not username or not password:
            flash("Täytä kaikki kentät.", "error")
            return render_template("register.html")
        if len(username) < 3 or len(username) > 30:
            flash("Käyttäjätunnuksen pituus on 3–30 merkkiä.", "error")
            return render_template("register.html")
        if len(password) < 4:
            flash("Salasanan vähimmäispituus on 4 merkkiä.", "error")
            return render_template("register.html")
        db = get_db()
        existing = db.execute(
            "SELECT id FROM users WHERE username = ?", (username,)
        ).fetchone()
        if existing:
            flash("Käyttäjätunnus on jo varattu.", "error")
            return render_template("register.html")
        db.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (username, generate_password_hash(password))
        )
        db.commit()
        flash("Tunnus luotu! Voit nyt kirjautua sisään.", "success")
        return redirect(url_for("login"))
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        check_csrf()
        username = request.form["username"].strip()
        password = request.form["password"]
        db = get_db()
        user = db.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()
        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            flash("Kirjautuminen onnistui!", "success")
            return redirect(url_for("index"))
        flash("Väärä käyttäjätunnus tai salasana.", "error")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("Olet kirjautunut ulos.", "success")
    return redirect(url_for("index"))


# Elokuvan lisäys, muokkaus ja poisto

@app.route("/add", methods=["GET", "POST"])
def add_movie():
    require_login()
    db = get_db()
    genres = db.execute("SELECT * FROM genres ORDER BY name").fetchall()

    if request.method == "POST":
        check_csrf()
        name = request.form["name"].strip()
        description = request.form["description"].strip()
        year = request.form["year"].strip()
        selected_genres = request.form.getlist("genres")

        if not name:
            flash("Elokuvan nimi on pakollinen.", "error")
            return render_template("add_movie.html", genres=genres)

        year_int = None
        if year:
            try:
                year_int = int(year)
                if year_int < 1888 or year_int > 2100:
                    raise ValueError
            except ValueError:
                flash("Julkaisuvuosi ei ole kelvollinen.", "error")
                return render_template("add_movie.html", genres=genres)

        cursor = db.execute(
            "INSERT INTO movies (name, description, year, user_id) "
            "VALUES (?, ?, ?, ?)",
            (name, description, year_int, current_user())
        )
        movie_id = cursor.lastrowid

        for genre_id in selected_genres:
            db.execute(
                "INSERT OR IGNORE INTO movie_genres (movie_id, genre_id) "
                "VALUES (?, ?)",
                (movie_id, genre_id)
            )

        db.commit()
        flash("Elokuva lisätty!", "success")
        return redirect(url_for("index"))

    return render_template("add_movie.html", genres=genres)


@app.route("/edit/<int:movie_id>", methods=["GET", "POST"])
def edit_movie(movie_id):
    require_login()
    db = get_db()
    movie = db.execute(
        "SELECT * FROM movies WHERE id = ?", (movie_id,)
    ).fetchone()
    if not movie:
        abort(404)
    if movie["user_id"] != current_user():
        abort(403)

    genres = db.execute("SELECT * FROM genres ORDER BY name").fetchall()
    current_genres = [
        row["genre_id"] for row in db.execute(
            "SELECT genre_id FROM movie_genres WHERE movie_id = ?",
            (movie_id,)
        ).fetchall()
    ]

    if request.method == "POST":
        check_csrf()
        name = request.form["name"].strip()
        description = request.form["description"].strip()
        year = request.form["year"].strip()
        selected_genres = request.form.getlist("genres")

        if not name:
            flash("Elokuvan nimi on pakollinen.", "error")
            return render_template(
                "edit_movie.html", movie=movie, genres=genres,
                current_genres=current_genres
            )

        year_int = None
        if year:
            try:
                year_int = int(year)
                if year_int < 1888 or year_int > 2100:
                    raise ValueError
            except ValueError:
                flash("Julkaisuvuosi ei ole kelvollinen.", "error")
                return render_template(
                    "edit_movie.html", movie=movie, genres=genres,
                    current_genres=current_genres
                )

        db.execute(
            "UPDATE movies SET name = ?, description = ?, year = ? "
            "WHERE id = ?",
            (name, description, year_int, movie_id)
        )

        db.execute(
            "DELETE FROM movie_genres WHERE movie_id = ?", (movie_id,)
        )
        for genre_id in selected_genres:
            db.execute(
                "INSERT OR IGNORE INTO movie_genres (movie_id, genre_id) "
                "VALUES (?, ?)",
                (movie_id, genre_id)
            )

        db.commit()
        flash("Elokuva päivitetty!", "success")
        return redirect(url_for("movie_page", movie_id=movie_id))

    return render_template(
        "edit_movie.html", movie=movie, genres=genres,
        current_genres=current_genres
    )


@app.route("/delete/<int:movie_id>", methods=["POST"])
def delete_movie(movie_id):
    require_login()
    check_csrf()
    db = get_db()
    movie = db.execute(
        "SELECT * FROM movies WHERE id = ?", (movie_id,)
    ).fetchone()
    if not movie:
        abort(404)
    if movie["user_id"] != current_user():
        abort(403)
    db.execute("DELETE FROM movies WHERE id = ?", (movie_id,))
    db.commit()
    flash("Elokuva poistettu.", "success")
    return redirect(url_for("index"))


# Elokuvasivu

@app.route("/movie/<int:movie_id>")
def movie_page(movie_id):
    db = get_db()
    movie = db.execute(
        "SELECT m.*, u.username FROM movies m "
        "JOIN users u ON m.user_id = u.id WHERE m.id = ?",
        (movie_id,)
    ).fetchone()
    if not movie:
        abort(404)

    genres = db.execute(
        "SELECT g.name FROM genres g "
        "JOIN movie_genres mg ON g.id = mg.genre_id "
        "WHERE mg.movie_id = ?",
        (movie_id,)
    ).fetchall()

    reviews = db.execute(
        "SELECT r.*, u.username FROM reviews r "
        "JOIN users u ON r.user_id = u.id "
        "WHERE r.movie_id = ? ORDER BY r.created_at DESC",
        (movie_id,)
    ).fetchall()

    avg_rating = db.execute(
        "SELECT AVG(rating) as avg_rating, COUNT(*) as count "
        "FROM reviews WHERE movie_id = ?",
        (movie_id,)
    ).fetchone()

    return render_template(
        "movie.html", movie=movie, genres=genres,
        reviews=reviews, avg_rating=avg_rating
    )


# Arvostelut

@app.route("/movie/<int:movie_id>/review", methods=["POST"])
def add_review(movie_id):
    require_login()
    check_csrf()
    db = get_db()

    movie = db.execute(
        "SELECT * FROM movies WHERE id = ?", (movie_id,)
    ).fetchone()
    if not movie:
        abort(404)

    rating = request.form.get("rating", "").strip()
    comment = request.form.get("comment", "").strip()

    if not rating:
        flash("Arvosana on pakollinen.", "error")
        return redirect(url_for("movie_page", movie_id=movie_id))

    try:
        rating_int = int(rating)
        if rating_int < 1 or rating_int > 5:
            raise ValueError
    except ValueError:
        flash("Arvosana ei ole kelvollinen (1–5).", "error")
        return redirect(url_for("movie_page", movie_id=movie_id))

    existing = db.execute(
        "SELECT id FROM reviews WHERE movie_id = ? AND user_id = ?",
        (movie_id, current_user())
    ).fetchone()
    if existing:
        flash("Olet jo arvostellut tämän elokuvan.", "error")
        return redirect(url_for("movie_page", movie_id=movie_id))

    db.execute(
        "INSERT INTO reviews (movie_id, user_id, rating, comment) "
        "VALUES (?, ?, ?, ?)",
        (movie_id, current_user(), rating_int, comment)
    )
    db.commit()
    flash("Arvostelu lisätty!", "success")
    return redirect(url_for("movie_page", movie_id=movie_id))


@app.route("/review/delete/<int:review_id>", methods=["POST"])
def delete_review(review_id):
    require_login()
    check_csrf()
    db = get_db()
    review = db.execute(
        "SELECT * FROM reviews WHERE id = ?", (review_id,)
    ).fetchone()
    if not review:
        abort(404)
    if review["user_id"] != current_user():
        abort(403)
    db.execute("DELETE FROM reviews WHERE id = ?", (review_id,))
    db.commit()
    flash("Arvostelu poistettu.", "success")
    return redirect(url_for("movie_page", movie_id=review["movie_id"]))


# Käyttäjäsivu

@app.route("/user/<int:user_id>")
def user_page(user_id):
    db = get_db()
    user = db.execute(
        "SELECT * FROM users WHERE id = ?", (user_id,)
    ).fetchone()
    if not user:
        abort(404)

    movies = db.execute(
        "SELECT * FROM movies WHERE user_id = ? ORDER BY id DESC",
        (user_id,)
    ).fetchall()

    movie_count = len(movies)

    review_count = db.execute(
        "SELECT COUNT(*) as count FROM reviews WHERE user_id = ?",
        (user_id,)
    ).fetchone()["count"]

    avg_given = db.execute(
        "SELECT AVG(rating) as avg_rating FROM reviews WHERE user_id = ?",
        (user_id,)
    ).fetchone()["avg_rating"]

    avg_received = db.execute(
        "SELECT AVG(r.rating) as avg_rating FROM reviews r "
        "JOIN movies m ON r.movie_id = m.id "
        "WHERE m.user_id = ?",
        (user_id,)
    ).fetchone()["avg_rating"]

    movie_genres = {}
    for movie in movies:
        mg = db.execute(
            "SELECT g.name FROM genres g "
            "JOIN movie_genres mg ON g.id = mg.genre_id "
            "WHERE mg.movie_id = ?",
            (movie["id"],)
        ).fetchall()
        movie_genres[movie["id"]] = [g["name"] for g in mg]

    return render_template(
        "user.html", user=user, movies=movies,
        movie_count=movie_count, review_count=review_count,
        avg_given=avg_given, avg_received=avg_received,
        movie_genres=movie_genres
    )


# Virheenkäsittely

@app.errorhandler(403)
def forbidden(e):
    flash("Ei käyttöoikeutta.", "error")
    return redirect(url_for("index"))


@app.errorhandler(404)
def not_found(e):
    flash("Sivua ei löytynyt.", "error")
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)
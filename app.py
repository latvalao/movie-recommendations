from flask import Flask, render_template, request, redirect, url_for, session, flash, abort
from werkzeug.security import generate_password_hash, check_password_hash
from db import get_db, close_db, init_db
import os

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

# reitit 

@app.route("/")
def index():
    db = get_db()
    query = request.args.get("query", "").strip()
    if query:
        movies = db.execute(
            "SELECT m.*, u.username FROM movies m JOIN users u ON m.user_id = u.id "
            "WHERE m.name LIKE ? ORDER BY m.id DESC",
            ("%" + query + "%",)
        ).fetchall()
    else:
        movies = db.execute(
            "SELECT m.*, u.username FROM movies m JOIN users u ON m.user_id = u.id "
            "ORDER BY m.id DESC"
        ).fetchall()
    return render_template("index.html", movies=movies, query=query)

# Rekisteröinti & kirjautuminen

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
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
        existing = db.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
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
        username = request.form["username"].strip()
        password = request.form["password"]
        db = get_db()
        user = db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
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

# elokuvan lisäys, muokkaus, poisto

@app.route("/add", methods=["GET", "POST"])
def add_movie():
    require_login()
    if request.method == "POST":
        name = request.form["name"].strip()
        description = request.form["description"].strip()
        year = request.form["year"].strip()
        if not name:
            flash("Elokuvan nimi on pakollinen.", "error")
            return render_template("add_movie.html")
        year_int = None
        if year:
            try:
                year_int = int(year)
                if year_int < 1888 or year_int > 2100:
                    raise ValueError
            except ValueError:
                flash("Julkaisuvuosi ei ole kelvollinen.", "error")
                return render_template("add_movie.html")
        db = get_db()
        db.execute(
            "INSERT INTO movies (name, description, year, user_id) VALUES (?, ?, ?, ?)",
            (name, description, year_int, current_user())
        )
        db.commit()
        flash("Elokuva lisätty!", "success")
        return redirect(url_for("index"))
    return render_template("add_movie.html")

@app.route("/edit/<int:movie_id>", methods=["GET", "POST"])
def edit_movie(movie_id):
    require_login()
    db = get_db()
    movie = db.execute("SELECT * FROM movies WHERE id = ?", (movie_id,)).fetchone()
    if not movie:
        abort(404)
    if movie["user_id"] != current_user():
        abort(403)
    if request.method == "POST":
        name = request.form["name"].strip()
        description = request.form["description"].strip()
        year = request.form["year"].strip()
        if not name:
            flash("Elokuvan nimi on pakollinen.", "error")
            return render_template("edit_movie.html", movie=movie)
        year_int = None
        if year:
            try:
                year_int = int(year)
                if year_int < 1888 or year_int > 2100:
                    raise ValueError
            except ValueError:
                flash("Julkaisuvuosi ei ole kelvollinen.", "error")
                return render_template("edit_movie.html", movie=movie)
        db.execute(
            "UPDATE movies SET name = ?, description = ?, year = ? WHERE id = ?",
            (name, description, year_int, movie_id)
        )
        db.commit()
        flash("Elokuva päivitetty!", "success")
        return redirect(url_for("index"))
    return render_template("edit_movie.html", movie=movie)

@app.route("/delete/<int:movie_id>", methods=["POST"])
def delete_movie(movie_id):
    require_login()
    db = get_db()
    movie = db.execute("SELECT * FROM movies WHERE id = ?", (movie_id,)).fetchone()
    if not movie:
        abort(404)
    if movie["user_id"] != current_user():
        abort(403)
    db.execute("DELETE FROM movies WHERE id = ?", (movie_id,))
    db.commit()
    flash("Elokuva poistettu.", "success")
    return redirect(url_for("index"))

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
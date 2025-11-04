import os
import sqlite3
from functools import wraps
from hashlib import sha256

from flask import (Flask, abort, flash, g, redirect, render_template, request,
                   session, url_for)


DATABASE = os.path.join(os.path.dirname(__file__), "cmc.db")


app = Flask(__name__)
app.secret_key = os.environ.get("CMC_SECRET_KEY", "dev-secret-key")


SAMPLE_SCHOOLS = [
    {
        "name": "Greenwood University",
        "city": "Portland",
        "state": "OR",
        "tuition": 24500,
        "student_body": "15,300",
        "website": "https://www.greenwood.edu",
        "description": (
            "A sustainability-focused university offering a wide range of STEM "
            "and liberal arts programs with strong co-op opportunities."
        ),
    },
    {
        "name": "Lakeside Institute of Technology",
        "city": "Chicago",
        "state": "IL",
        "tuition": 31200,
        "student_body": "9,800",
        "website": "https://www.lakesideit.edu",
        "description": (
            "Known for engineering and design, Lakeside partners closely with "
            "local industry to provide project-based learning experiences."
        ),
    },
    {
        "name": "Harbor City College",
        "city": "Boston",
        "state": "MA",
        "tuition": 27850,
        "student_body": "7,200",
        "website": "https://www.harborcity.edu",
        "description": (
            "A coastal liberal arts college emphasizing interdisciplinary "
            "studies, undergraduate research, and global exchange programs."
        ),
    },
    {
        "name": "Redwood State University",
        "city": "San Francisco",
        "state": "CA",
        "tuition": 22500,
        "student_body": "24,500",
        "website": "https://www.redwoodstate.edu",
        "description": (
            "A large public university with nationally ranked computer "
            "science, business, and media arts departments."
        ),
    },
    {
        "name": "Prairie Hills College",
        "city": "Austin",
        "state": "TX",
        "tuition": 19800,
        "student_body": "5,600",
        "website": "https://www.prairiehills.edu",
        "description": (
            "A close-knit campus offering strong support services for first-"
            "generation students and a vibrant entrepreneurship center."
        ),
    },
    {
        "name": "Cascade School of the Arts",
        "city": "Seattle",
        "state": "WA",
        "tuition": 34120,
        "student_body": "3,100",
        "website": "https://www.cascadestudio.edu",
        "description": (
            "An arts-focused school with renowned programs in animation, film "
            "production, and music technology."
        ),
    },
    {
        "name": "Summit Ridge University",
        "city": "Denver",
        "state": "CO",
        "tuition": 26440,
        "student_body": "12,200",
        "website": "https://www.summitridge.edu",
        "description": (
            "Summit Ridge blends outdoor leadership with rigorous academics, "
            "offering unique field study programs in the Rockies."
        ),
    },
    {
        "name": "Coastal STEM Academy",
        "city": "Miami",
        "state": "FL",
        "tuition": 28910,
        "student_body": "4,500",
        "website": "https://www.coastalstem.edu",
        "description": (
            "An institute focused on marine biology, environmental sciences, "
            "and coastal engineering research."
        ),
    },
    {
        "name": "Liberty Plains College",
        "city": "Richmond",
        "state": "VA",
        "tuition": 17650,
        "student_body": "6,400",
        "website": "https://www.libertyplains.edu",
        "description": (
            "A public college offering accelerated bachelor's-to-master's "
            "pathways in business, cybersecurity, and education."
        ),
    },
    {
        "name": "Northbridge University",
        "city": "Minneapolis",
        "state": "MN",
        "tuition": 25480,
        "student_body": "18,900",
        "website": "https://www.northbridge.edu",
        "description": (
            "An urban research university celebrated for cooperative education "
            "and strong ties to the healthcare sector."
        ),
    },
]


def get_db_connection():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    with get_db_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                is_admin INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS schools (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                city TEXT NOT NULL,
                state TEXT NOT NULL,
                tuition INTEGER NOT NULL,
                student_body TEXT NOT NULL,
                website TEXT NOT NULL,
                description TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS saved_schools (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                school_id INTEGER NOT NULL,
                UNIQUE(user_id, school_id),
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY(school_id) REFERENCES schools(id) ON DELETE CASCADE
            )
            """
        )

        existing = conn.execute("SELECT COUNT(*) FROM schools").fetchone()[0]
        if existing == 0:
            for school in SAMPLE_SCHOOLS:
                conn.execute(
                    """
                    INSERT INTO schools (name, city, state, tuition, student_body, website, description)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        school["name"],
                        school["city"],
                        school["state"],
                        school["tuition"],
                        school["student_body"],
                        school["website"],
                        school["description"],
                    ),
                )


def login_required(view_func):
    @wraps(view_func)
    def wrapped_view(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return view_func(*args, **kwargs)

    return wrapped_view


def admin_required(view_func):
    @wraps(view_func)
    def wrapped_view(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        if not session.get("is_admin"):
            abort(403)
        return view_func(*args, **kwargs)

    return wrapped_view


@app.before_request
def load_logged_in_user():
    user_id = session.get("user_id")
    if user_id is None:
        g.user = None
        return

    with get_db_connection() as conn:
        user = conn.execute(
            "SELECT id, username, is_admin FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        g.user = user
        if user is not None:
            session["is_admin"] = bool(user["is_admin"])


def hash_password(password: str) -> str:
    return sha256(password.encode("utf-8")).hexdigest()


@app.route("/")
def index():
    if session.get("user_id"):
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        with get_db_connection() as conn:
            user = conn.execute(
                "SELECT id, username, password_hash, is_admin FROM users WHERE username = ?",
                (username,),
            ).fetchone()

        if user and user["password_hash"] == hash_password(password):
            session.clear()
            session["user_id"] = user["id"]
            session["is_admin"] = bool(user["is_admin"])
            flash("Welcome back, {}!".format(user["username"]))
            return redirect(url_for("dashboard"))

        flash("Invalid username or password.", "error")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been signed out.")
    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not username or not password:
            flash("Username and password are required.", "error")
            return render_template("register.html")

        if password != confirm_password:
            flash("Passwords do not match.", "error")
            return render_template("register.html")

        with get_db_connection() as conn:
            existing_user = conn.execute(
                "SELECT id FROM users WHERE username = ?", (username,)
            ).fetchone()

            if existing_user:
                flash("Username already taken.", "error")
                return render_template("register.html")

            user_count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
            is_admin = 1 if user_count == 0 else 0

            conn.execute(
                "INSERT INTO users (username, password_hash, is_admin) VALUES (?, ?, ?)",
                (username, hash_password(password), is_admin),
            )
            conn.commit()

        flash("Account created successfully. Please sign in.")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/dashboard")
@login_required
def dashboard():
    query = request.args.get("q", "").strip()
    params = []
    sql = "SELECT * FROM schools"
    if query:
        sql += " WHERE name LIKE ? OR city LIKE ? OR state LIKE ?"
        like_query = f"%{query}%"
        params.extend([like_query, like_query, like_query])

    sql += " ORDER BY name"

    with get_db_connection() as conn:
        schools = conn.execute(sql, params).fetchall()
        saved = conn.execute(
            """
            SELECT schools.* FROM schools
            INNER JOIN saved_schools ON saved_schools.school_id = schools.id
            WHERE saved_schools.user_id = ?
            ORDER BY schools.name
            """,
            (session["user_id"],),
        ).fetchall()

    return render_template(
        "dashboard.html",
        schools=schools,
        saved_schools=saved,
        query=query,
    )


@app.route("/schools/<int:school_id>")
@login_required
def school_detail(school_id: int):
    with get_db_connection() as conn:
        school = conn.execute(
            "SELECT * FROM schools WHERE id = ?", (school_id,)
        ).fetchone()

    if school is None:
        abort(404)

    return render_template("school_detail.html", school=school)


@app.route("/save/<int:school_id>", methods=["POST"])
@login_required
def save_school(school_id: int):
    with get_db_connection() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO saved_schools (user_id, school_id) VALUES (?, ?)",
            (session["user_id"], school_id),
        )
        conn.commit()

    flash("School saved to your list.")
    return redirect(request.referrer or url_for("dashboard"))


@app.route("/unsave/<int:school_id>", methods=["POST"])
@login_required
def unsave_school(school_id: int):
    with get_db_connection() as conn:
        conn.execute(
            "DELETE FROM saved_schools WHERE user_id = ? AND school_id = ?",
            (session["user_id"], school_id),
        )
        conn.commit()

    flash("School removed from your saved list.")
    return redirect(request.referrer or url_for("dashboard"))


@app.route("/admin/users", methods=["GET", "POST"])
@admin_required
def manage_users():
    if request.method == "POST":
        action = request.form.get("action")
        user_id = int(request.form.get("user_id"))

        if action == "toggle_admin":
            if user_id == session["user_id"]:
                flash("You cannot change your own admin status.", "error")
            else:
                with get_db_connection() as conn:
                    current = conn.execute(
                        "SELECT is_admin FROM users WHERE id = ?", (user_id,)
                    ).fetchone()
                    if current:
                        new_value = 0 if current["is_admin"] else 1
                        conn.execute(
                            "UPDATE users SET is_admin = ? WHERE id = ?",
                            (new_value, user_id),
                        )
                        conn.commit()
                        flash("User permissions updated.")
        elif action == "delete":
            if user_id == session["user_id"]:
                flash("You cannot delete your own account.", "error")
            else:
                with get_db_connection() as conn:
                    conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
                    conn.execute(
                        "DELETE FROM saved_schools WHERE user_id = ?", (user_id,)
                    )
                    conn.commit()
                flash("User deleted.")

        return redirect(url_for("manage_users"))

    with get_db_connection() as conn:
        users = conn.execute(
            "SELECT id, username, is_admin FROM users ORDER BY username"
        ).fetchall()

    return render_template("admin_users.html", users=users)


@app.context_processor
def inject_user():
    return {"current_user": g.get("user")}


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)


init_db()

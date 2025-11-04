
import html
import os
import sqlite3
import urllib.parse
from hashlib import sha256
from http import HTTPStatus
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Dict, List, Optional, Tuple
from uuid import uuid4

DATABASE = os.path.join(os.path.dirname(__file__), "cmc.db")

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


SESSIONS: Dict[str, Dict[str, object]] = {}


def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
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
            conn.commit()


def hash_password(password: str) -> str:
    return sha256(password.encode("utf-8")).hexdigest()


def verify_password(password: str, hashed: str) -> bool:
    return hash_password(password) == hashed


def row_to_dict(row: sqlite3.Row) -> Dict[str, object]:
    return {key: row[key] for key in row.keys()}


def add_flash(session: Dict[str, object], message: str, category: str = "info") -> None:
    flashes: List[Tuple[str, str]] = session.setdefault("flashes", [])  # type: ignore[assignment]
    flashes.append((category, message))


def consume_flashes(session: Dict[str, object]) -> List[Tuple[str, str]]:
    flashes = session.get("flashes", [])
    session["flashes"] = []
    return flashes  # type: ignore[return-value]


def escape(value: object) -> str:
    return html.escape(str(value))


def render_page(
    *,
    title: str,
    body: str,
    user: Optional[sqlite3.Row],
    flashes: List[Tuple[str, str]],
    is_admin: bool,
) -> str:
    nav_links: List[str] = []
    if user:
        nav_links.append(
            '<li><span class="nav-user">Signed in as {}</span></li>'.format(
                escape(user["username"])
            )
        )
        nav_links.append('<li><a href="/dashboard">Dashboard</a></li>')
        if is_admin:
            nav_links.append('<li><a href="/admin/users">Admin</a></li>')
        nav_links.append('<li><a href="/logout">Log out</a></li>')
    else:
        nav_links.append('<li><a href="/login">Log in</a></li>')
        nav_links.append('<li><a href="/register">Register</a></li>')

    flash_html = ""
    if flashes:
        flash_items = [
            '<div class="flash {}">{}</div>'.format(escape(category), escape(message))
            for category, message in flashes
        ]
        flash_html = '<div class="flash-messages">{}</div>'.format("".join(flash_items))

    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{escape(title)}</title>
        <link rel="stylesheet" href="/static/styles.css">
    </head>
    <body>
        <header class="site-header">
            <div class="container">
                <h1 class="logo"><a href="{('/dashboard' if user else '/login')}">CMC</a></h1>
                <nav>
                    <ul>
                        {''.join(nav_links)}
                    </ul>
                </nav>
            </div>
        </header>
        <main class="container">
            {flash_html}
            {body}
        </main>
        <footer class="site-footer">
            <div class="container">
                <p>&copy; 2024 Choose My College</p>
            </div>
        </footer>
    </body>
    </html>
    """


def render_login(*, flashes: List[Tuple[str, str]], user: Optional[sqlite3.Row], is_admin: bool) -> str:
    body = """
    <section class="auth-card">
        <h2>Sign in</h2>
        <form method="post" action="/login" class="auth-form">
            <label>Username<input type="text" name="username" required></label>
            <label>Password<input type="password" name="password" required></label>
            <button type="submit">Log in</button>
        </form>
        <p class="auth-alt">Need an account? <a href="/register">Register here</a>.</p>
    </section>
    """
    return render_page(title="Log in - CMC", body=body, user=user, flashes=flashes, is_admin=is_admin)


def render_register(*, flashes: List[Tuple[str, str]], user: Optional[sqlite3.Row], is_admin: bool) -> str:
    body = """
    <section class="auth-card">
        <h2>Create account</h2>
        <form method="post" action="/register" class="auth-form">
            <label>Username<input type="text" name="username" required></label>
            <label>Password<input type="password" name="password" required></label>
            <label>Confirm password<input type="password" name="confirm_password" required></label>
            <button type="submit">Sign up</button>
        </form>
        <p class="auth-alt">Already registered? <a href="/login">Log in</a>.</p>
    </section>
    """
    return render_page(title="Register - CMC", body=body, user=user, flashes=flashes, is_admin=is_admin)


def render_dashboard(
    *,
    user: sqlite3.Row,
    flashes: List[Tuple[str, str]],
    is_admin: bool,
    query: str,
    schools: List[Dict[str, object]],
    saved_schools: List[Dict[str, object]],
    saved_ids: List[int],
) -> str:
    search_cards: List[str] = []
    for school in schools:
        school_id = int(school["id"])
        is_saved = school_id in saved_ids
        action_path = f"/unsave/{school_id}" if is_saved else f"/save/{school_id}"
        action_label = "Remove from saved" if is_saved else "Save school"
        action_class = "secondary" if is_saved else "primary"
        tuition = f"${int(school['tuition']):,}"
        card = f"""
        <article class="school-card">
            <h3>{escape(school['name'])}</h3>
            <p class="location">{escape(school['city'])}, {escape(school['state'])}</p>
            <p class="tuition">Tuition: {escape(tuition)}</p>
            <p class="students">Student body: {escape(school['student_body'])}</p>
            <div class="card-actions">
                <a class="link" href="/schools/{school_id}">View details</a>
                <form method="post" action="{action_path}">
                    <button type="submit" class="btn {action_class}">{action_label}</button>
                </form>
            </div>
        </article>
        """
        search_cards.append(card)

    search_html = "".join(search_cards) if search_cards else "<p class=\"empty-state\">No schools found.</p>"

    saved_items: List[str] = []
    for school in saved_schools:
        school_id = int(school["id"])
        saved_items.append(
            f"""
            <li>
                <span>{escape(school['name'])}</span>
                <form method="post" action="/unsave/{school_id}">
                    <button type="submit" class="link-button">Remove</button>
                </form>
            </li>
            """
        )

    saved_html = (
        "<ul class=\"saved-list\">{}</ul>".format("".join(saved_items))
        if saved_items
        else "<p class=\"empty-state\">You have not saved any schools yet.</p>"
    )

    body = f"""
    <section class="dashboard">
        <header class="dashboard-header">
            <div>
                <h2>Explore schools</h2>
                <p>Search by name, city, or state to discover colleges that fit your goals.</p>
            </div>
            <form method="get" action="/dashboard" class="search-form">
                <input type="search" name="q" placeholder="Search schools" value="{escape(query)}">
                <button type="submit">Search</button>
            </form>
        </header>
        <div class="school-grid">
            {search_html}
        </div>
        <section class="saved-section">
            <h3>Saved schools</h3>
            {saved_html}
        </section>
    </section>
    """
    return render_page(
        title="Dashboard - CMC",
        body=body,
        user=user,
        flashes=flashes,
        is_admin=is_admin,
    )


def render_school_detail(
    *,
    user: sqlite3.Row,
    flashes: List[Tuple[str, str]],
    is_admin: bool,
    school: Dict[str, object],
    is_saved: bool,
) -> str:
    school_id = int(school["id"])
    action_path = f"/unsave/{school_id}" if is_saved else f"/save/{school_id}"
    action_label = "Remove from saved" if is_saved else "Save school"
    action_class = "secondary" if is_saved else "primary"
    body = f"""
    <article class="detail-card">
        <header>
            <h2>{escape(school['name'])}</h2>
            <p>{escape(school['city'])}, {escape(school['state'])}</p>
        </header>
        <p class="tuition">Annual tuition: ${int(school['tuition']):,}</p>
        <p class="students">Student body: {escape(school['student_body'])}</p>
        <p class="description">{escape(school['description'])}</p>
        <p><a href="{escape(school['website'])}" target="_blank" rel="noopener">Visit website</a></p>
        <div class="detail-actions">
            <form method="post" action="{action_path}">
                <button type="submit" class="btn {action_class}">{action_label}</button>
            </form>
            <a class="link" href="/dashboard">Back to results</a>
        </div>
    </article>
    """
    return render_page(
        title=f"{escape(school['name'])} - CMC",
        body=body,
        user=user,
        flashes=flashes,
        is_admin=is_admin,
    )


def render_admin_users(
    *,
    user: sqlite3.Row,
    flashes: List[Tuple[str, str]],
    is_admin: bool,
    users: List[Dict[str, object]],
) -> str:
    rows: List[str] = []
    for account in users:
        account_id = int(account["id"])
        admin_badge = "<span class=\"badge\">Admin</span>" if account["is_admin"] else ""
        is_self = account_id == user["id"]
        rows.append(
            f"""
            <tr>
                <td>{escape(account['username'])} {admin_badge}</td>
                <td class="actions">
                    <form method="post" action="/admin/users">
                        <input type="hidden" name="user_id" value="{account_id}">
                        <button type="submit" name="action" value="toggle_admin" {'disabled' if is_self else ''}>Toggle admin</button>
                    </form>
                    <form method="post" action="/admin/users">
                        <input type="hidden" name="user_id" value="{account_id}">
                        <button type="submit" name="action" value="delete" class="danger" {'disabled' if is_self else ''}>Delete</button>
                    </form>
                </td>
            </tr>
            """
        )

    table_body = "".join(rows) if rows else "<tr><td colspan=\"2\">No users found.</td></tr>"
    body = f"""
    <section class="admin">
        <header>
            <h2>User management</h2>
            <p>Review accounts, promote administrators, and remove access.</p>
        </header>
        <table class="admin-table">
            <thead>
                <tr><th>User</th><th>Actions</th></tr>
            </thead>
            <tbody>
                {table_body}
            </tbody>
        </table>
    </section>
    """
    return render_page(
        title="Admin - Users",
        body=body,
        user=user,
        flashes=flashes,
        is_admin=is_admin,
    )


def render_message_page(
    *,
    title: str,
    message: str,
    user: Optional[sqlite3.Row],
    flashes: List[Tuple[str, str]],
    is_admin: bool,
    status_heading: str,
) -> str:
    body = f"""
    <section class="message">
        <h2>{escape(status_heading)}</h2>
        <p>{escape(message)}</p>
    </section>
    """
    return render_page(title=title, body=body, user=user, flashes=flashes, is_admin=is_admin)


def get_session(handler: BaseHTTPRequestHandler) -> Dict[str, object]:
    if hasattr(handler, "_session"):
        return handler._session  # type: ignore[attr-defined]

    cookie_header = handler.headers.get("Cookie", "")
    session_id: Optional[str] = None
    if cookie_header:
        simple_cookie = SimpleCookie()
        try:
            simple_cookie.load(cookie_header)
        except (ValueError, KeyError):
            simple_cookie = SimpleCookie()
        if "session_id" in simple_cookie:
            candidate = simple_cookie["session_id"].value
            if candidate in SESSIONS:
                session_id = candidate

    if session_id is None:
        session_id = uuid4().hex
        SESSIONS[session_id] = {"flashes": []}
        handler._new_session_id = session_id  # type: ignore[attr-defined]

    session = SESSIONS.setdefault(session_id, {"flashes": []})
    handler._session = session  # type: ignore[attr-defined]
    handler._session_id = session_id  # type: ignore[attr-defined]
    return session


def fetch_user(session: Dict[str, object]) -> Optional[sqlite3.Row]:
    user_id = session.get("user_id")
    if not user_id:
        session["is_admin"] = False
        return None

    with get_db_connection() as conn:
        user = conn.execute(
            "SELECT id, username, is_admin FROM users WHERE id = ?",
            (int(user_id),),
        ).fetchone()

    if user is None:
        session.pop("user_id", None)
        session["is_admin"] = False
        return None

    session["is_admin"] = bool(user["is_admin"])
    return user


def clear_session(session: Dict[str, object]) -> None:
    keys = list(session.keys())
    for key in keys:
        session.pop(key, None)
    session["flashes"] = []


def sanitize_redirect(target: Optional[str]) -> str:
    if not target:
        return "/dashboard"
    parsed = urllib.parse.urlparse(target)
    if parsed.scheme or parsed.netloc:
        return "/dashboard"
    return parsed.path + (f"?{parsed.query}" if parsed.query else "") or "/dashboard"


def parse_post_data(handler: BaseHTTPRequestHandler) -> Dict[str, str]:
    length = int(handler.headers.get("Content-Length", 0) or 0)
    raw = handler.rfile.read(length).decode("utf-8") if length else ""
    data = urllib.parse.parse_qs(raw, keep_blank_values=True)
    return {key: values[0] if values else "" for key, values in data.items()}


class CMCRequestHandler(BaseHTTPRequestHandler):
    server_version = "CMCServer/1.0"

    def log_message(self, format: str, *args) -> None:  # noqa: A003 - match BaseHTTPRequestHandler signature
        return

    def _set_common_headers(self, status: int, content_type: str = "text/html; charset=utf-8") -> None:
        self.send_response(status)
        if hasattr(self, "_new_session_id"):
            session_id = getattr(self, "_new_session_id")
            self.send_header(
                "Set-Cookie",
                f"session_id={session_id}; Path=/; HttpOnly; SameSite=Lax",
            )
        self.send_header("Content-Type", content_type)

    def do_GET(self) -> None:  # noqa: N802 - required by BaseHTTPRequestHandler
        session = get_session(self)
        user = fetch_user(session)
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path.startswith("/static/"):
            return self.serve_static(path)

        if path == "/":
            destination = "/dashboard" if session.get("user_id") else "/login"
            return self.redirect(destination)

        if path == "/login":
            content = render_login(
                flashes=consume_flashes(session),
                user=user,
                is_admin=bool(session.get("is_admin")),
            )
            return self.respond_html(content)

        if path == "/register":
            content = render_register(
                flashes=consume_flashes(session),
                user=user,
                is_admin=bool(session.get("is_admin")),
            )
            return self.respond_html(content)

        if path == "/logout":
            clear_session(session)
            add_flash(session, "You have been signed out.")
            return self.redirect("/login")

        if path == "/dashboard":
            if not session.get("user_id"):
                add_flash(session, "Please sign in to continue.", "error")
                return self.redirect("/login")

            query_params = urllib.parse.parse_qs(parsed.query)
            query = query_params.get("q", [""])[0].strip()

            with get_db_connection() as conn:
                params: List[str] = []
                sql = "SELECT * FROM schools"
                if query:
                    like = f"%{query}%"
                    sql += " WHERE name LIKE ? OR city LIKE ? OR state LIKE ?"
                    params.extend([like, like, like])
                sql += " ORDER BY name"
                schools = [row_to_dict(row) for row in conn.execute(sql, params).fetchall()]

                saved_rows = conn.execute(
                    """
                    SELECT schools.* FROM schools
                    INNER JOIN saved_schools ON saved_schools.school_id = schools.id
                    WHERE saved_schools.user_id = ?
                    ORDER BY schools.name
                    """,
                    (session["user_id"],),
                ).fetchall()
                saved_schools = [row_to_dict(row) for row in saved_rows]
                saved_ids = [int(row["id"]) for row in saved_rows]

            content = render_dashboard(
                user=user,  # type: ignore[arg-type]
                flashes=consume_flashes(session),
                is_admin=bool(session.get("is_admin")),
                query=query,
                schools=schools,
                saved_schools=saved_schools,
                saved_ids=saved_ids,
            )
            return self.respond_html(content)

        if path.startswith("/schools/"):
            if not session.get("user_id"):
                add_flash(session, "Please sign in to continue.", "error")
                return self.redirect("/login")
            try:
                school_id = int(path.split("/")[-1])
            except ValueError:
                return self.not_found(session, user)

            with get_db_connection() as conn:
                row = conn.execute("SELECT * FROM schools WHERE id = ?", (school_id,)).fetchone()
                if row is None:
                    return self.not_found(session, user)
                saved = conn.execute(
                    "SELECT 1 FROM saved_schools WHERE user_id = ? AND school_id = ?",
                    (session["user_id"], school_id),
                ).fetchone()

            content = render_school_detail(
                user=user,  # type: ignore[arg-type]
                flashes=consume_flashes(session),
                is_admin=bool(session.get("is_admin")),
                school=row_to_dict(row),
                is_saved=bool(saved),
            )
            return self.respond_html(content)

        if path == "/admin/users":
            if not session.get("user_id"):
                add_flash(session, "Please sign in to continue.", "error")
                return self.redirect("/login")
            if not session.get("is_admin"):
                return self.forbidden(session, user)

            with get_db_connection() as conn:
                users = [row_to_dict(row) for row in conn.execute(
                    "SELECT id, username, is_admin FROM users ORDER BY username"
                ).fetchall()]

            content = render_admin_users(
                user=user,  # type: ignore[arg-type]
                flashes=consume_flashes(session),
                is_admin=True,
                users=users,
            )
            return self.respond_html(content)

        return self.not_found(session, user)

    def do_POST(self) -> None:  # noqa: N802 - required by BaseHTTPRequestHandler
        session = get_session(self)
        user = fetch_user(session)
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/login":
            data = parse_post_data(self)
            username = data.get("username", "").strip()
            password = data.get("password", "")

            with get_db_connection() as conn:
                row = conn.execute(
                    "SELECT id, username, password_hash, is_admin FROM users WHERE username = ?",
                    (username,),
                ).fetchone()

            if row and verify_password(password, row["password_hash"]):
                clear_session(session)
                session["user_id"] = int(row["id"])
                session["is_admin"] = bool(row["is_admin"])
                add_flash(session, f"Welcome back, {row['username']}!", "success")
                return self.redirect("/dashboard")

            add_flash(session, "Invalid username or password.", "error")
            return self.redirect("/login")

        if path == "/register":
            data = parse_post_data(self)
            username = data.get("username", "").strip()
            password = data.get("password", "")
            confirm = data.get("confirm_password", "")

            if not username or not password:
                add_flash(session, "Username and password are required.", "error")
                return self.redirect("/register")

            if password != confirm:
                add_flash(session, "Passwords do not match.", "error")
                return self.redirect("/register")

            with get_db_connection() as conn:
                existing = conn.execute(
                    "SELECT id FROM users WHERE username = ?",
                    (username,),
                ).fetchone()
                if existing:
                    add_flash(session, "Username already taken.", "error")
                    return self.redirect("/register")

                count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
                is_admin = 1 if count == 0 else 0
                conn.execute(
                    "INSERT INTO users (username, password_hash, is_admin) VALUES (?, ?, ?)",
                    (username, hash_password(password), is_admin),
                )
                conn.commit()

            add_flash(session, "Account created successfully. Please sign in.", "success")
            return self.redirect("/login")

        if path.startswith("/save/"):
            if not session.get("user_id"):
                add_flash(session, "Please sign in to continue.", "error")
                return self.redirect("/login")
            try:
                school_id = int(path.split("/")[-1])
            except ValueError:
                return self.not_found(session, user)

            with get_db_connection() as conn:
                conn.execute(
                    "INSERT OR IGNORE INTO saved_schools (user_id, school_id) VALUES (?, ?)",
                    (session["user_id"], school_id),
                )
                conn.commit()

            add_flash(session, "School saved to your list.", "success")
            return self.redirect(sanitize_redirect(self.headers.get("Referer")))

        if path.startswith("/unsave/"):
            if not session.get("user_id"):
                add_flash(session, "Please sign in to continue.", "error")
                return self.redirect("/login")
            try:
                school_id = int(path.split("/")[-1])
            except ValueError:
                return self.not_found(session, user)

            with get_db_connection() as conn:
                conn.execute(
                    "DELETE FROM saved_schools WHERE user_id = ? AND school_id = ?",
                    (session["user_id"], school_id),
                )
                conn.commit()

            add_flash(session, "School removed from your saved list.", "success")
            return self.redirect(sanitize_redirect(self.headers.get("Referer")))

        if path == "/admin/users":
            if not session.get("user_id"):
                add_flash(session, "Please sign in to continue.", "error")
                return self.redirect("/login")
            if not session.get("is_admin"):
                return self.forbidden(session, user)

            data = parse_post_data(self)
            try:
                target_user_id = int(data.get("user_id", "0"))
            except ValueError:
                target_user_id = 0
            action = data.get("action")

            if target_user_id == session.get("user_id"):
                add_flash(session, "You cannot modify your own account here.", "error")
                return self.redirect("/admin/users")

            if action == "toggle_admin":
                with get_db_connection() as conn:
                    current = conn.execute(
                        "SELECT is_admin FROM users WHERE id = ?",
                        (target_user_id,),
                    ).fetchone()
                    if current is not None:
                        new_value = 0 if current["is_admin"] else 1
                        conn.execute(
                            "UPDATE users SET is_admin = ? WHERE id = ?",
                            (new_value, target_user_id),
                        )
                        conn.commit()
                        add_flash(session, "User permissions updated.", "success")
            elif action == "delete":
                with get_db_connection() as conn:
                    conn.execute("DELETE FROM users WHERE id = ?", (target_user_id,))
                    conn.execute("DELETE FROM saved_schools WHERE user_id = ?", (target_user_id,))
                    conn.commit()
                add_flash(session, "User deleted.", "success")

            return self.redirect("/admin/users")

        return self.not_found(session, user)

    def respond_html(self, content: str, status: int = HTTPStatus.OK) -> None:
        encoded = content.encode("utf-8")
        self._set_common_headers(status)
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def redirect(self, location: str) -> None:
        self._set_common_headers(HTTPStatus.FOUND)
        self.send_header("Location", location)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def serve_static(self, path: str) -> None:
        base_dir = os.path.dirname(__file__)
        safe_path = os.path.normpath(os.path.join(base_dir, path.lstrip("/")))
        if not safe_path.startswith(os.path.join(base_dir, "static")):
            return self.not_found(get_session(self), fetch_user(get_session(self)))
        if not os.path.exists(safe_path):
            return self.not_found(get_session(self), fetch_user(get_session(self)))

        with open(safe_path, "rb") as f:
            data = f.read()

        content_type = "text/css" if safe_path.endswith(".css") else "application/octet-stream"
        self._set_common_headers(HTTPStatus.OK, content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def forbidden(self, session: Dict[str, object], user: Optional[sqlite3.Row]) -> None:
        content = render_message_page(
            title="Forbidden",
            message="You do not have permission to access this page.",
            user=user,
            flashes=consume_flashes(session),
            is_admin=bool(session.get("is_admin")),
            status_heading="403 - Forbidden",
        )
        self.respond_html(content, status=HTTPStatus.FORBIDDEN)

    def not_found(self, session: Dict[str, object], user: Optional[sqlite3.Row]) -> None:
        content = render_message_page(
            title="Not found",
            message="The page you requested could not be found.",
            user=user,
            flashes=consume_flashes(session),
            is_admin=bool(session.get("is_admin")),
            status_heading="404 - Not Found",
        )
        self.respond_html(content, status=HTTPStatus.NOT_FOUND)


def run() -> None:
    init_db()
    server = HTTPServer(("0.0.0.0", 5000), CMCRequestHandler)
    print("Serving Choose My College on http://0.0.0.0:5000")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        server.server_close()


if __name__ == "__main__":
    run()

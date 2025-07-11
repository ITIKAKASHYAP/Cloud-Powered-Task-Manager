from flask import Flask, render_template, request, redirect, url_for, session
from cloudant.client import Cloudant
from dotenv import load_dotenv
import os, uuid

# ── Load environment and app setup ───────────────────────
load_dotenv()
app = Flask(__name__, template_folder='.', static_folder='.', static_url_path='')
app.secret_key = os.getenv("SECRET_KEY", "change_this_in_prod")

# ── Cloudant connection ──────────────────────────────────
client = Cloudant.iam(
    os.getenv("CLOUDANT_USERNAME"),
    os.getenv("CLOUDANT_APIKEY"),
    url=os.getenv("CLOUDANT_URL")
)
client.connect()

def db(name):
    return client[name] if name in client.all_dbs() else client.create_database(name)

tasks_db = db("tasks")
users_db = db("users")

# ── Helpers ──────────────────────────────────────────────
me = lambda: session.get("username")
gate = lambda: redirect(url_for("login")) if not me() else None
user_tasks = lambda: [dict(d) for d in tasks_db if d.get("user") == me()]

# ── Auth Routes ──────────────────────────────────────────
@app.route("/")
def home():
    return render_template("index.html", page="home")

@app.route("/signin", methods=["GET", "POST"])
def signin():
    if request.method == "POST":
        u = request.form["username"].strip().lower()
        pw = request.form["password"].strip()
        if u in users_db:
            return "Username already exists. Try logging in.", 400
        users_db.create_document({"_id": u, "password": pw})
        return redirect(url_for("login"))
    return render_template("index.html", page="signin")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        u = request.form["username"].strip().lower()
        pw = request.form["password"].strip()
        user = users_db.get(u)
        if user and user["password"] == pw:
            session["username"] = u
            return redirect(url_for("dashboard"))
        return "Invalid username or password.", 401
    return render_template("index.html", page="login")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

# ── Dashboard & Task CRUD ───────────────────────────────
@app.route("/dashboard")
def dashboard():
    if gate(): return gate()
    return render_template("index.html", page="dashboard", tasks=user_tasks())

@app.route("/add", methods=["POST"])
def add():
    if gate(): return gate()
    title = request.form["task"].strip()
    desc = request.form.get("description", "").strip()
    if title:
        tasks_db.create_document({
            "_id": str(uuid.uuid4()),
            "task": title,
            "description": desc,
            "completed": False,
            "user": me()
        })
    return redirect(url_for("dashboard"))

@app.route("/edit/<tid>")
def edit(tid):
    if gate(): return gate()
    d = tasks_db.get(tid)
    if not d or d.get("user") != me():
        return redirect(url_for("dashboard"))
    return render_template("index.html", page="edit", doc=d)

@app.route("/update/<tid>", methods=["POST"])
def update(tid):
    if gate(): return gate()
    d = tasks_db.get(tid)
    if d and d.get("user") == me():
        d["task"] = request.form["task"].strip()
        d["description"] = request.form.get("description", "").strip()
        d.save()
    return redirect(url_for("dashboard"))

@app.route("/complete/<tid>")
def complete(tid):
    if gate(): return gate()
    d = tasks_db.get(tid)
    if d and d.get("user") == me():
        d["completed"] = True
        d.save()
    return redirect(url_for("dashboard"))

@app.route("/delete/<tid>")
def delete(tid):
    if gate(): return gate()
    d = tasks_db.get(tid)
    if d and d.get("user") == me():
        d.delete()
    return redirect(url_for("dashboard"))

@app.route("/clear_completed")
def clear_completed():
    if gate(): return gate()
    for d in list(tasks_db):
        if d.get("user") == me() and d.get("completed"):
            d.delete()
    return redirect(url_for("dashboard"))

# ── Run Local Server ─────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=True)

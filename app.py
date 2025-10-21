from flask import Flask, render_template, request, redirect, url_for

# Basic Flask application that serves the landing page template.
app = Flask(__name__)


@app.route("/")
def landing_page():
    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        # Placeholder redirect until authentication is implemented.
        return redirect(url_for("landing_page"))
    return render_template("login.html")


if __name__ == "__main__":
    app.run(debug=True)

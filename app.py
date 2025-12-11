"""
Flask application for the Team Roster Manager.

Highlights
----------
* CRUD routes with ORM
* Report route using prepared statements
* Dynamic UI dropdowns
* Optimistic‑concurrency control (StaleDataError handling)
"""

from flask import (
    Flask, render_template, redirect, url_for,
    request, flash
)
from sqlalchemy import text
from sqlalchemy.orm.exc import StaleDataError

from models import db, Player, Team, Position
from forms  import PlayerForm, TeamForm

import flask
print("Using Flask at:", flask.__file__)

# ──────────────────────────
# App configuration
# ──────────────────────────
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///roster.db"
app.config["SECRET_KEY"] = "secret123"
db.init_app(app)

# ──────────────────────────
# One‑time bootstrap for empty DB
# ──────────────────────────
@app.before_request
def run_once():
    """Create tables & seed default positions the first time the app is hit."""
    if not Position.query.first():
        db.create_all()
        db.session.add_all([
            Position(PositionName="Forward"),
            Position(PositionName="Midfielder"),
            Position(PositionName="Defender"),
            Position(PositionName="Goalkeeper")
        ])
        db.session.commit()

# ──────────────────────────
# Home page
# ──────────────────────────
@app.route("/")
def index():
    players = Player.query.all()
    teams   = Team.query.all()
    return render_template("index.html", players=players, teams=teams)

# ──────────────────────────
# Add player
# ──────────────────────────
@app.route("/add", methods=["GET", "POST"])
def add_player():
    form = PlayerForm()
    form.team.choices     = [(t.TeamID, t.TeamName)     for t in Team.query.all()]
    form.position.choices = [(p.PositionID, p.PositionName) for p in Position.query.all()]

    if form.validate_on_submit():
        player = Player(
            Name       = form.name.data,
            Age        = form.age.data,
            Height     = form.height.data,
            TeamID     = form.team.data,
            PositionID = form.position.data
        )
        db.session.add(player)
        db.session.commit()
        return redirect(url_for("index"))
    return render_template("add_player.html", form=form)

# ──────────────────────────
# Add team
# ──────────────────────────
@app.route("/add_team", methods=["GET", "POST"])
def add_team():
    form = TeamForm()
    if form.validate_on_submit():
        new_team = Team(TeamName=form.team_name.data)
        db.session.add(new_team)
        db.session.commit()
        return redirect(url_for("index"))
    return render_template("add_team.html", form=form)

# ──────────────────────────
# Delete player
# ──────────────────────────
@app.route("/delete/<int:player_id>", methods=["POST"])
def delete_player(player_id):
    player = Player.query.get_or_404(player_id)
    db.session.delete(player)
    db.session.commit()
    return redirect(url_for("index"))

# ──────────────────────────
# Remove teams page & bulk delete
# ──────────────────────────
@app.route("/remove_teams", methods=["GET", "POST"])
def remove_teams():
    if request.method == "POST" and request.form.get("action") == "delete_all":
        Player.query.delete()
        Team.query.delete()
        db.session.commit()
        return redirect(url_for("remove_teams"))

    teams = Team.query.all()
    return render_template("remove_teams.html", teams=teams)

# ──────────────────────────
# Delete single team (plus its players) via raw SQL
# ──────────────────────────
@app.route("/delete_team/<int:team_id>", methods=["POST"])
def delete_team(team_id):
    db.session.execute(text("DELETE FROM player WHERE TeamID = :team_id"),
                       {"team_id": team_id})
    db.session.execute(text("DELETE FROM team   WHERE TeamID = :team_id"),
                       {"team_id": team_id})
    db.session.commit()
    return redirect(url_for("remove_teams"))

# ──────────────────────────
# Edit player (optimistic concurrency)
# ──────────────────────────
@app.route("/edit_player/<int:player_id>", methods=["GET", "POST"])
def edit_player(player_id):
    player = Player.query.get_or_404(player_id)
    teams = Team.query.all()
    positions = Position.query.all()

    if request.method == "POST":
        try:
            player.Name = request.form["name"]
            player.Age = int(request.form["age"])
            player.Height = float(request.form["height"])
            player.TeamID = int(request.form["team"])
            player.PositionID = int(request.form["position"])
            db.session.commit()
            return redirect(url_for("index"))
        except Exception as e:
            db.session.rollback()
            flash(f"Error updating player: {e}")
            return redirect(url_for("edit_player", player_id=player_id))

    return render_template("edit_player.html", player=player, teams=teams, positions=positions)


# ──────────────────────────
# Report (prepared‑statement query)
# ──────────────────────────
@app.route("/report", methods=["GET", "POST"])
def report():
    teams     = Team.query.all()
    positions = Position.query.all()

    players = None
    stats   = {}

    if request.method == "POST":
        selected_team     = request.form.get("team")
        selected_position = request.form.get("position")

        sql     = "SELECT * FROM player"
        filters = []
        params  = {}

        if selected_team and selected_team != "all":
            filters.append("TeamID = :team_id")
            params["team_id"] = int(selected_team)

        if selected_position and selected_position != "all":
            filters.append("PositionID = :position_id")
            params["position_id"] = int(selected_position)

        if filters:
            sql += " WHERE " + " AND ".join(filters)

        result  = db.session.execute(text(sql), params)
        players = result.fetchall()

        if players:
            ages    = [p.Age    for p in players]
            heights = [p.Height for p in players]
            stats   = {
                "total"      : len(players),
                "avg_age"    : round(sum(ages)    / len(ages), 2),
                "avg_height" : round(sum(heights) / len(heights), 2),
            }
        else:
            stats = {"total": 0, "avg_age": 0, "avg_height": 0}

    return render_template("report.html",
                           players   = players,
                           teams     = teams,
                           positions = positions,
                           stats     = stats)

# ──────────────────────────
# Run the app
# ──────────────────────────
if __name__ == "__main__":
        with app.app_context():
            db.create_all()
            # seed default positions only if missing
            if not Position.query.first():
                db.session.add_all([
                    Position(PositionName="Forward"),
                    Position(PositionName="Midfielder"),
                    Position(PositionName="Defender"),
                    Position(PositionName="Goalkeeper")
                ])
                db.session.commit()

        app.run(debug=True)
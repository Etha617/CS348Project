"""
SQLAlchemy data models for the Team Roster Manager.

Key features
------------
* Unique constraint on TeamName.
* Lookup table for Position.
* Player table with three performance indexes:
    - idx_player_team        (TeamID)
    - idx_player_position    (PositionID)
    - idx_player_team_pos    (TeamID, PositionID)
* Optimistic‑concurrency: Version column + mapper setting.
"""

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Team(db.Model):
    __tablename__ = "team"

    TeamID   = db.Column(db.Integer, primary_key=True)
    TeamName = db.Column(db.String(100), nullable=False, unique=True)  # UNIQUE index


class Position(db.Model):
    __tablename__ = "position"

    PositionID   = db.Column(db.Integer, primary_key=True)
    PositionName = db.Column(db.String(100), nullable=False)


class Player(db.Model):
    __tablename__ = "player"

    __table_args__ = (
        # Helpful indexes for report queries
        db.Index("idx_player_team", "TeamID"),
        db.Index("idx_player_position", "PositionID"),
        db.Index("idx_player_team_pos", "TeamID", "PositionID"),
    )

    PlayerID   = db.Column(db.Integer, primary_key=True)
    Name       = db.Column(db.String(100), nullable=False)
    Age        = db.Column(db.Integer,     nullable=False)
    Height     = db.Column(db.Float,       nullable=False)
    TeamID     = db.Column(db.Integer, db.ForeignKey("team.TeamID"))
    PositionID = db.Column(db.Integer, db.ForeignKey("position.PositionID"))

    # ---------- optimistic‑concurrency column ----------
    Version    = db.Column(db.Integer, nullable=False, default=0)

    # Tell SQLAlchemy to bump Version on every UPDATE
    __mapper_args__ = {
        "version_id_col": Version
    }

    # Relationships
    team     = db.relationship("Team",     backref="players")
    position = db.relationship("Position", backref="players")

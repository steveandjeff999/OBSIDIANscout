"""
Database seed script for the FRC Scouting Platform.
This script adds sample data to the database for testing and development.
Run this script with: python seed.py
"""

import os
import sys
from datetime import datetime, date
from flask import Flask
from app import create_app, db
from app.models import Team, Match, Event, ScoutingData

def seed_database():
    """Add sample data to the database"""
    print("Seeding database with sample data...")
    
    # Create sample events
    events = [
        Event(
            name="District Championship",
            location="Rochester, NY",
            start_date=date(2025, 3, 15),
            end_date=date(2025, 3, 17),
            year=2025
        ),
        Event(
            name="World Championship",
            location="Houston, TX",
            start_date=date(2025, 4, 17),
            end_date=date(2025, 4, 20),
            year=2025
        )
    ]
    
    # Add events to database
    for event in events:
        existing = Event.query.filter_by(name=event.name, year=event.year).first()
        if not existing:
            db.session.add(event)
    db.session.commit()
    print(f"Added {len(events)} events")
    
    # Get the first event for reference
    district_event = Event.query.filter_by(name="District Championship").first()
    champ_event = Event.query.filter_by(name="World Championship").first()
    # Create sample teams
    teams = [
        Team(team_number=5454, team_name="Herod Robotics", location="Kansas, OK"),
        Team(team_number=254, team_name="Cheesy Poofs", location="San Jose, CA"),
        Team(team_number=1114, team_name="Simbotics", location="St. Catharines, Ontario"),
        Team(team_number=118, team_name="Robonauts", location="Houston, TX"),
        Team(team_number=33, team_name="Killer Bees", location="Auburn Hills, MI"),
        Team(team_number=2056, team_name="OP Robotics", location="Stoney Creek, Ontario"),
        Team(team_number=4613, team_name="Barker Redbacks", location="Sydney, Australia"),
        Team(team_number=1678, team_name="Citrus Circuits", location="Davis, CA"),
        Team(team_number=148, team_name="Robowranglers", location="Greenville, TX"),
        Team(team_number=2767, team_name="Stryke Force", location="Kalamazoo, MI"),
        Team(team_number=3310, team_name="Black Hawk Robotics", location="Heath, TX"),
        Team(team_number=971, team_name="Spartan Robotics", location="Mountain View, CA")
    ]
    
    # Add teams to database
    for team in teams:
        existing = Team.query.filter_by(team_number=team.team_number).first()
        if not existing:
            db.session.add(team)
    db.session.commit()
    print(f"Added {len(teams)} teams")
    
    # Create sample matches
    matches = [
        Match(
            match_number=1,
            match_type="Qualification",
            event_id=district_event.id,
            red_alliance="5454,254,1114",
            blue_alliance="118,33,2056",
            red_score=85,
            blue_score=75,
            timestamp=datetime(2025, 3, 15, 10, 0, 0)
        ),
        Match(
            match_number=2,
            match_type="Qualification",
            event_id=district_event.id,
            red_alliance="4613,1678,148",
            blue_alliance="2767,3310,971",
            red_score=65,
            blue_score=80,
            timestamp=datetime(2025, 3, 15, 10, 15, 0)
        ),
        Match(
            match_number=3,
            match_type="Qualification",
            event_id=district_event.id,
            red_alliance="118,1678,5454",
            blue_alliance="254,2767,148",
            red_score=90,
            blue_score=88,
            timestamp=datetime(2025, 3, 15, 10, 30, 0)
        ),
        Match(
            match_number=4,
            match_type="Qualification",
            event_id=district_event.id,
            red_alliance="33,971,1114",
            blue_alliance="2056,4613,3310",
            red_score=75,
            blue_score=72,
            timestamp=datetime(2025, 3, 15, 10, 45, 0)
        ),
        Match(
            match_number=5,
            match_type="Practice",
            event_id=champ_event.id,
            red_alliance="5454,148,2767",
            blue_alliance="1678,33,971",
            red_score=None,
            blue_score=None,
            timestamp=datetime(2025, 3, 15, 9, 0, 0)
        )
    ]
    
    # Add matches to database
    for match in matches:
        existing = Match.query.filter_by(
            match_number=match.match_number,
            match_type=match.match_type,
            event_id=match.event_id
        ).first()
        if not existing:
            db.session.add(match)
    db.session.commit()
    print(f"Added {len(matches)} matches")
    
    print("Database seeded successfully!")

if __name__ == "__main__":
    # Create app context
    app = create_app()
    with app.app_context():
        seed_database()
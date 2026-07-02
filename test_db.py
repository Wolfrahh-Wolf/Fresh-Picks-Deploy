from app import app
from models import db
from sqlalchemy import text

with app.app_context():
    result = db.session.execute(text("SELECT 1"))
    print("Supabase connection OK:", result.fetchone())


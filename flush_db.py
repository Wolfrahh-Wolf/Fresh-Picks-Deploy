# flush_db.py - Destructive database reset. Only runs when FLUSH_DB_ENABLED=1.
import os
import sys

if os.environ.get("FLUSH_DB_ENABLED") != "1":
    print("Flushing disabled. Set FLUSH_DB_ENABLED=1 to proceed.")
    sys.exit(1)

from app import app
from app.models import db, OrderItem, CartItem, Order, DeliveryBoy, FreeItem, Product, User, Admin

if __name__ == "__main__":
    with app.app_context():
        db.session.query(OrderItem).delete()
        db.session.query(CartItem).delete()
        db.session.query(Order).delete()
        db.session.query(DeliveryBoy).delete()
        db.session.query(FreeItem).delete()
        db.session.query(Product).delete()
        db.session.query(User).delete()
        db.session.query(Admin).delete()
        db.session.commit()
        print("DB flushed.")

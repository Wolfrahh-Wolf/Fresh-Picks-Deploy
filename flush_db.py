# flush_db.py
from app import app
from models import db, OrderItem, CartItem, Order, DeliveryBoy, FreeItem, Product, User, Admin

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
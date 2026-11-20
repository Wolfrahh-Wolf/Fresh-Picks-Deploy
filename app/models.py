from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = "users"

    user_id   = db.Column(db.String(20),  primary_key=True)   # "U1001"
    username  = db.Column(db.String(128), unique=True, nullable=False)
    password  = db.Column(db.String(128), nullable=False)      # SHA-256 hex
    full_name = db.Column(db.String(128), nullable=False)
    email     = db.Column(db.String(128), nullable=False)
    phone     = db.Column(db.String(128), nullable=False)
    address   = db.Column(db.String(256), nullable=False)

    orders      = db.relationship("Order",     backref="user", lazy=True)
    cart_items  = db.relationship("CartItem",  backref="user", lazy=True)

    def to_dict(self):
        return {
            "user_id":   self.user_id,
            "username":  self.username,
            "full_name": self.full_name,
            "email":     self.email,
            "phone":     self.phone,
            "address":   self.address,
        }


class Admin(db.Model):
    __tablename__ = "admins"

    admin_id   = db.Column(db.String(20),  primary_key=True)   # "A1001"
    username   = db.Column(db.String(128), unique=True, nullable=False)
    password   = db.Column(db.String(128), nullable=False)      # SHA-256 hex
    admin_name = db.Column(db.String(128), nullable=False)
    email      = db.Column(db.String(128), nullable=False)

    def to_dict(self):
        return {
            "admin_id":   self.admin_id,
            "username":   self.username,
            "admin_name": self.admin_name,
            "email":      self.email,
        }


class Product(db.Model):
    __tablename__ = "products"

    veg_id          = db.Column(db.String(20),  primary_key=True)  # "V1001"
    category        = db.Column(db.String(128), nullable=False)
    name            = db.Column(db.String(128), nullable=False)
    stock_g         = db.Column(db.Integer,     nullable=False, default=0)
    price_per_1000g = db.Column(db.Float,       nullable=False)
    tag             = db.Column(db.String(128), nullable=True)
    validity_days   = db.Column(db.Integer,     nullable=False, default=1)

    def to_dict(self):
        return {
            "veg_id":          self.veg_id,
            "category":        self.category,
            "name":            self.name,
            "stock_g":         self.stock_g,
            "price_per_1000g": self.price_per_1000g,
            "tag":             self.tag,
            "validity_days":   self.validity_days,
        }


class FreeItem(db.Model):
    __tablename__ = "free_items"

    vf_id           = db.Column(db.String(20),  primary_key=True)  # "VF1001"
    name            = db.Column(db.String(128), nullable=False)
    stock_g         = db.Column(db.Integer,     nullable=False, default=0)
    min_trigger_amt = db.Column(db.Float,       nullable=False)
    free_qty_g      = db.Column(db.Integer,     nullable=False)

    def to_dict(self):
        return {
            "vf_id":           self.vf_id,
            "name":            self.name,
            "stock_g":         self.stock_g,
            "min_trigger_amt": self.min_trigger_amt,
            "free_qty_g":      self.free_qty_g,
        }



class DeliveryBoy(db.Model):
    __tablename__ = "delivery_boys"

    boy_id        = db.Column(db.String(20),  primary_key=True)  # "D1001"
    name          = db.Column(db.String(128), nullable=False)
    phone         = db.Column(db.String(128), nullable=False)
    vehicle_no    = db.Column(db.String(128), nullable=False)
    is_active     = db.Column(db.Boolean,     nullable=False, default=True)
    last_assigned = db.Column(db.DateTime,    nullable=True)   # NULL = never assigned

    orders = db.relationship("Order", backref="delivery_boy", lazy=True)

    def to_dict(self):
        return {
            "boy_id":        self.boy_id,
            "name":          self.name,
            "phone":         self.phone,
            "vehicle_no":    self.vehicle_no,
            "is_active":     self.is_active,
            "last_assigned": self.last_assigned.isoformat() if self.last_assigned else None,
        }


class Order(db.Model):
    __tablename__ = "orders"

    order_id        = db.Column(db.String(20),  primary_key=True)  # "ORD1001"
    user_id         = db.Column(db.String(20),  db.ForeignKey("users.user_id"), nullable=False)
    total_amount    = db.Column(db.Float,       nullable=False)
    delivery_slot   = db.Column(db.String(128), nullable=False)   # Morning/Afternoon/Evening
    delivery_boy_id = db.Column(db.String(20),  db.ForeignKey("delivery_boys.boy_id"), nullable=True)
    status          = db.Column(db.String(128), nullable=False, default="Order Placed")
    timestamp       = db.Column(db.DateTime,    nullable=False, default=datetime.utcnow)

    items = db.relationship("OrderItem", backref="order",
                            lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "order_id":        self.order_id,
            "user_id":         self.user_id,
            "total_amount":    self.total_amount,
            "delivery_slot":   self.delivery_slot,
            "delivery_boy_id": self.delivery_boy_id,
            "status":          self.status,
            "timestamp":       self.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "items":           [item.to_dict() for item in self.items],
        }


class OrderItem(db.Model):
    __tablename__ = "order_items"

    id              = db.Column(db.Integer, primary_key=True, autoincrement=True)
    order_id        = db.Column(db.String(20),  db.ForeignKey("orders.order_id"), nullable=False)
    item_id         = db.Column(db.String(20),  nullable=False)   # veg_id or vf_id
    name            = db.Column(db.String(128), nullable=False)
    qty_g           = db.Column(db.Integer,     nullable=False)
    price_at_order  = db.Column(db.Float,       nullable=False)   # snapshot price
    is_free         = db.Column(db.Boolean,     nullable=False, default=False)

    def to_dict(self):
        return {
            "item_id":        self.item_id,
            "name":           self.name,
            "qty_g":          self.qty_g,
            "price_at_order": self.price_at_order,
            "is_free":        self.is_free,
        }


class CartItem(db.Model):
    __tablename__ = "cart_items"

    id              = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id         = db.Column(db.String(20),  db.ForeignKey("users.user_id"), nullable=False)
    item_id         = db.Column(db.String(20),  nullable=False)   # veg_id or vf_id
    name            = db.Column(db.String(128), nullable=False)
    qty_g           = db.Column(db.Integer,     nullable=False)
    price_per_1000g = db.Column(db.Float,       nullable=False)
    is_free         = db.Column(db.Boolean,     nullable=False, default=False)

    __table_args__ = (
        db.UniqueConstraint("user_id", "item_id", name="uq_cart_user_item"),
    )

    def to_dict(self):
        item_total = (self.qty_g / 1000.0) * self.price_per_1000g
        return {
            "item_id":         self.item_id,
            "name":            self.name,
            "qty_g":           self.qty_g,
            "price_per_1000g": self.price_per_1000g,
            "item_total":      round(item_total, 2),
            "is_free":         self.is_free,
        }

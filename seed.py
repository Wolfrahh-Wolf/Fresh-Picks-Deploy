"""
seed.py - Fresh Picks: One-Time Database Seeder

Populates the database with real project data.
Safe to re-run - skips existing records, never overwrites.

Usage:
    python seed.py
"""

import os
import sys
import logging
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

from app import create_app
from app.extensions import db
from app.models import Admin, User, Product, FreeItem, DeliveryBoy, Order, OrderItem

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("seed")


# ═════════════════════════════════════════════════════════════
# ADMINS
# ═════════════════════════════════════════════════════════════
def seed_admins():
    logger.info("Seeding admins...")
    admins = [
        {
            "admin_id":   "A1001",
            "username":   "Admin",
            "password":   "pbkdf2:sha256:1000000$nKwrEr6piRT5cca2$fda587bd1ccb4cb0d0069ad7a988e3a27b5173126bd4908c68ad4d764c0cda98",
            "admin_name": "Admin",
            "email":      "admin@freshpicks.com",
        },
        {
            "admin_id":   "A1002",
            "username":   "Wolfrahh",
            "password":   "pbkdf2:sha256:1000000$qLTtFE95WAGJIm5J$539d62c0e9f48d17f061ffa00d2154732e99ff9b38b9519bbcfc791742e3a902",
            "admin_name": "Wolfrahh",
            "email":      "wolfrahh@gmail.com",
        },
    ]
    inserted = skipped = 0
    for data in admins:
        if not db.session.get(Admin, data["admin_id"]):
            db.session.add(Admin(**data))
            logger.info("  [+] Admin  : %s (%s)", data["username"], data["admin_id"])
            inserted += 1
        else:
            logger.info("  [=] Admin  : %s already exists", data["admin_id"])
            skipped += 1
    db.session.commit()
    logger.info("  → %d inserted, %d skipped\n", inserted, skipped)


# ═════════════════════════════════════════════════════════════
# USERS
# ═════════════════════════════════════════════════════════════
def seed_users():
    logger.info("Seeding users...")
    users = [
        {
            "user_id":   "U1001",
            "username":  "User",
            "password":  "pbkdf2:sha256:1000000$1ytBR2WPi2TiQNz5$34022fd30dd9e0dfeb7722d17cfee704099dcc407ae1a89c7b3bc4b94b7e5dc6",
            "full_name": "User",
            "email":     "yashwantharumugam2007@gmail.com",
            "phone":     "6382717541",
            "address":   "No 11 FF2,Elumalai Street,Tambaram West,600045",
        },
        {
            "user_id":   "U1002",
            "username":  "Yashwanth",
            "password":  "pbkdf2:sha256:1000000$faVEDLslkcZXRuAP$27ae92f178243243681d573fac150fb77523cd93a999ce042dc95b1a294ccef5",
            "full_name": "Yashwanth A",
            "email":     "yashwantharumugam2007@gmail.com",
            "phone":     "6382717541",
            "address":   "No 11 FF2,Elumalai Street,Tambaram West,600045",
        },
        {
            "user_id":   "U1003",
            "username":  "User3",
            "password":  "pbkdf2:sha256:1000000$Eq0vehakiHGMAtUB$93c4638c1622c5704a8d79743e5f07279b11d271ce9dda6edf0ac2b6143f22d3",
            "full_name": "User Three",
            "email":     "yashwantharumugam2007@gmail.com",
            "phone":     "6382717541",
            "address":   "No 11 FF2,Elumalai Street,Tambaram West,600045",
        },
        {
            "user_id":   "U1004",
            "username":  "User4",
            "password":  "pbkdf2:sha256:1000000$Eq0vehakiHGMAtUB$93c4638c1622c5704a8d79743e5f07279b11d271ce9dda6edf0ac2b6143f22d3",
            "full_name": "User Four",
            "email":     "yashwantharumugam2007@gmail.com",
            "phone":     "6382717541",
            "address":   "No 11 FF2,Elumalai Street,Tambaram West,600045",
        },
        {
            "user_id":   "U1005",
            "username":  "User5",
            "password":  "pbkdf2:sha256:1000000$Eq0vehakiHGMAtUB$93c4638c1622c5704a8d79743e5f07279b11d271ce9dda6edf0ac2b6143f22d3",
            "full_name": "User Five",
            "email":     "yashwantharumugam2007@gmail.com",
            "phone":     "6382717541",
            "address":   "No 11 FF2,Elumalai Street,Tambaram West,600045",
        },
    ]
    inserted = skipped = 0
    for data in users:
        if not db.session.get(User, data["user_id"]):
            db.session.add(User(**data))
            logger.info("  [+] User   : %s (%s)", data["username"], data["user_id"])
            inserted += 1
        else:
            logger.info("  [=] User   : %s already exists", data["user_id"])
            skipped += 1
    db.session.commit()
    logger.info("  → %d inserted, %d skipped\n", inserted, skipped)


# ═════════════════════════════════════════════════════════════
# PRODUCTS
# ═════════════════════════════════════════════════════════════
def seed_products():
    logger.info("Seeding products...")
    products = [
        {"veg_id": "V1001", "category": "Allium",          "name": "Onion",             "stock_g": 150500, "price_per_1000g": 50.0,  "tag": "Farm Fresh",       "validity_days": 7},
        {"veg_id": "V1002", "category": "Allium",          "name": "Small Onion",       "stock_g": 120000, "price_per_1000g": 50.0,  "tag": "Premium",          "validity_days": 10},
        {"veg_id": "V1003", "category": "Allium",          "name": "Garlic",            "stock_g": 21500,  "price_per_1000g": 120.0, "tag": "Organic",          "validity_days": 15},
        {"veg_id": "V1004", "category": "Root",            "name": "Potato",            "stock_g": 46000,  "price_per_1000g": 25.0,  "tag": "Daily Use",        "validity_days": 10},
        {"veg_id": "V1005", "category": "Fruit Vegetable", "name": "Cucumber",          "stock_g": 24000,  "price_per_1000g": 20.0,  "tag": "Cooling Fresh",    "validity_days": 4},
        {"veg_id": "V1006", "category": "Fruit Vegetable", "name": "Brinjal",           "stock_g": 15450,  "price_per_1000g": 28.0,  "tag": "Fresh",            "validity_days": 6},
        {"veg_id": "V1007", "category": "Fruit Vegetable", "name": "Capsicum",          "stock_g": 105000, "price_per_1000g": 60.0,  "tag": "Premium",          "validity_days": 5},
        {"veg_id": "V1008", "category": "Fruit Vegetable", "name": "Plantain",          "stock_g": 18000,  "price_per_1000g": 60.0,  "tag": "Premium",          "validity_days": 5},
        {"veg_id": "V1009", "category": "Fruit Vegetable", "name": "Tomato",            "stock_g": 88800,  "price_per_1000g": 30.0,  "tag": "Fresh Stock",      "validity_days": 5},
        {"veg_id": "V1010", "category": "Fruit Vegetable", "name": "Mango",             "stock_g": 4000,   "price_per_1000g": 60.0,  "tag": "Seasonal",         "validity_days": 5},
        {"veg_id": "V1011", "category": "Fruit Vegetable", "name": "Coconut",           "stock_g": 11500,  "price_per_1000g": 35.0,  "tag": "Natural",          "validity_days": 20},
        {"veg_id": "V1012", "category": "Leafy",           "name": "Coriander Leaves",  "stock_g": 23500,  "price_per_1000g": 100.0, "tag": "Aromatic",         "validity_days": 3},
        {"veg_id": "V1013", "category": "Leafy",           "name": "Curry Leaves",      "stock_g": 4900,   "price_per_1000g": 120.0, "tag": "Fresh Leaves",     "validity_days": 4},
        {"veg_id": "V1014", "category": "Leafy",           "name": "Mint Leaves",       "stock_g": 3500,   "price_per_1000g": 90.0,  "tag": "Refreshing",       "validity_days": 3},
        {"veg_id": "V1015", "category": "Leafy",           "name": "Spinach",           "stock_g": 4500,   "price_per_1000g": 25.0,  "tag": "Iron Rich",        "validity_days": 3},
        {"veg_id": "V1016", "category": "Leafy",           "name": "Spring Onion",      "stock_g": 4000,   "price_per_1000g": 40.0,  "tag": "Fresh",            "validity_days": 5},
        {"veg_id": "V1017", "category": "Leafy",           "name": "Banana Stem",       "stock_g": 15000,  "price_per_1000g": 20.0,  "tag": "Healthy",          "validity_days": 6},
        {"veg_id": "V1018", "category": "Beans",           "name": "Beans",             "stock_g": 19750,  "price_per_1000g": 50.0,  "tag": "Green Fresh",      "validity_days": 5},
        {"veg_id": "V1019", "category": "Beans",           "name": "Flat Beans",        "stock_g": 24250,  "price_per_1000g": 45.0,  "tag": "Green Fresh",      "validity_days": 5},
        {"veg_id": "V1020", "category": "Beans",           "name": "Field Beans",       "stock_g": 19500,  "price_per_1000g": 50.0,  "tag": "Seasonal",         "validity_days": 6},
        {"veg_id": "V1021", "category": "Legumes",         "name": "Peas",              "stock_g": 10250,  "price_per_1000g": 70.0,  "tag": "Seasonal",         "validity_days": 5},
        {"veg_id": "V1022", "category": "Root",            "name": "Carrot",            "stock_g": 20000,  "price_per_1000g": 35.0,  "tag": "Rich in Vitamins", "validity_days": 7},
        {"veg_id": "V1023", "category": "Root",            "name": "Beetroot",          "stock_g": 13750,  "price_per_1000g": 30.0,  "tag": "Healthy",          "validity_days": 8},
        {"veg_id": "V1024", "category": "Root",            "name": "Radish",            "stock_g": 14000,  "price_per_1000g": 20.0,  "tag": "Fresh",            "validity_days": 5},
        {"veg_id": "V1025", "category": "Root",            "name": "Turnip",            "stock_g": 11950,  "price_per_1000g": 25.0,  "tag": "Healthy",          "validity_days": 7},
        {"veg_id": "V1026", "category": "Tuber",           "name": "Sweet Potato",      "stock_g": 17000,  "price_per_1000g": 30.0,  "tag": "Healthy",          "validity_days": 10},
        {"veg_id": "V1027", "category": "Tuber",           "name": "Elephant Foot Yam", "stock_g": 20000,  "price_per_1000g": 40.0,  "tag": "Root Fresh",       "validity_days": 10},
        {"veg_id": "V1028", "category": "Tuber",           "name": "Colocassia",        "stock_g": 13500,  "price_per_1000g": 35.0,  "tag": "Farm Fresh",       "validity_days": 8},
        {"veg_id": "V1029", "category": "Tuber",           "name": "Cassava",           "stock_g": 12500,  "price_per_1000g": 30.0,  "tag": "Organic",          "validity_days": 10},
        {"veg_id": "V1030", "category": "Cruciferous",     "name": "Cabbage",           "stock_g": 19750,  "price_per_1000g": 25.0,  "tag": "Farm Fresh",       "validity_days": 6},
        {"veg_id": "V1031", "category": "Cruciferous",     "name": "Cauliflower",       "stock_g": 16250,  "price_per_1000g": 30.0,  "tag": "Seasonal",         "validity_days": 5},
        {"veg_id": "V1032", "category": "Cruciferous",     "name": "Broccoli",          "stock_g": 6250,   "price_per_1000g": 180.0, "tag": "Exotic",           "validity_days": 4},
        {"veg_id": "V1033", "category": "Cruciferous",     "name": "Red Cabbage",       "stock_g": 7550,   "price_per_1000g": 60.0,  "tag": "Premium",          "validity_days": 6},
        {"veg_id": "V1034", "category": "Gourds",          "name": "Bittergourd",       "stock_g": 4950,   "price_per_1000g": 45.0,  "tag": "Healthy",          "validity_days": 6},
        {"veg_id": "V1035", "category": "Gourds",          "name": "Ivy Gourd",         "stock_g": 14450,  "price_per_1000g": 35.0,  "tag": "Fresh",            "validity_days": 6},
        {"veg_id": "V1036", "category": "Gourds",          "name": "Snake Gourd",       "stock_g": 11950,  "price_per_1000g": 30.0,  "tag": "Farm Fresh",       "validity_days": 6},
        {"veg_id": "V1037", "category": "Gourds",          "name": "Bottle Gourd",      "stock_g": 18450,  "price_per_1000g": 25.0,  "tag": "Healthy",          "validity_days": 7},
        {"veg_id": "V1038", "category": "Gourds",          "name": "Ridge Gourd",       "stock_g": 15000,  "price_per_1000g": 30.0,  "tag": "Fresh",            "validity_days": 6},
        {"veg_id": "V1039", "category": "Gourds",          "name": "Ash Gourd",         "stock_g": 20500,  "price_per_1000g": 20.0,  "tag": "Cooling",          "validity_days": 10},
        {"veg_id": "V1040", "category": "Spices",          "name": "Green Chilli",      "stock_g": 8250,   "price_per_1000g": 60.0,  "tag": "Spicy Fresh",      "validity_days": 5},
        {"veg_id": "V1041", "category": "Spices",          "name": "Ginger",            "stock_g": 9150,   "price_per_1000g": 80.0,  "tag": "Fresh Harvest",    "validity_days": 10},
        {"veg_id": "V1042", "category": "Spices",          "name": "Red Chilli",        "stock_g": 6700,   "price_per_1000g": 80.0,  "tag": "Spicy",            "validity_days": 8},
        {"veg_id": "V1043", "category": "Special",         "name": "Ladiesfinger",      "stock_g": 19000,  "price_per_1000g": 40.0,  "tag": "Healthy Choice",   "validity_days": 4},
        {"veg_id": "V1044", "category": "Special",         "name": "Corn",              "stock_g": 17000,  "price_per_1000g": 25.0,  "tag": "Sweet Fresh",      "validity_days": 6},
        {"veg_id": "V1045", "category": "Special",         "name": "Mushroom",          "stock_g": 5700,   "price_per_1000g": 150.0, "tag": "Exotic",           "validity_days": 3},
        {"veg_id": "V1046", "category": "Special",         "name": "Banana Flower",     "stock_g": 5000,   "price_per_1000g": 35.0,  "tag": "Traditional",      "validity_days": 5},
        {"veg_id": "V1047", "category": "Special",         "name": "Asparagus",         "stock_g": 4500,   "price_per_1000g": 200.0, "tag": "Exotic",           "validity_days": 3},
        {"veg_id": "V1048", "category": "Cooking",         "name": "Pumpkin",           "stock_g": 19400,  "price_per_1000g": 18.0,  "tag": "Farm Fresh",       "validity_days": 10},
    ]
    inserted = skipped = 0
    for data in products:
        if not db.session.get(Product, data["veg_id"]):
            db.session.add(Product(**data))
            logger.info("  [+] Product: %s (%s)", data["name"], data["veg_id"])
            inserted += 1
        else:
            logger.info("  [=] Product: %s already exists", data["veg_id"])
            skipped += 1
    db.session.commit()
    logger.info("  → %d inserted, %d skipped\n", inserted, skipped)


# ═════════════════════════════════════════════════════════════
# FREE ITEMS
# ═════════════════════════════════════════════════════════════
def seed_free_items():
    logger.info("Seeding free items...")
    free_items = [
        {"vf_id": "VF1001", "name": "Curry Leaves",     "stock_g": 24250, "min_trigger_amt": 500.0, "free_qty_g": 50},
        {"vf_id": "VF1002", "name": "Coriander Leaves", "stock_g": 24250, "min_trigger_amt": 500.0, "free_qty_g": 50},
    ]
    inserted = skipped = 0
    for data in free_items:
        if not db.session.get(FreeItem, data["vf_id"]):
            db.session.add(FreeItem(**data))
            logger.info("  [+] Promo  : %s (%s)", data["name"], data["vf_id"])
            inserted += 1
        else:
            logger.info("  [=] Promo  : %s already exists", data["vf_id"])
            skipped += 1
    db.session.commit()
    logger.info("  → %d inserted, %d skipped\n", inserted, skipped)


# ═════════════════════════════════════════════════════════════
# DELIVERY BOYS
# ═════════════════════════════════════════════════════════════
def seed_delivery_boys():
    logger.info("Seeding delivery boys...")
    boys = [
        {"boy_id": "D1001", "name": "Ramesh", "phone": "9876543210", "vehicle_no": "TN-22-AB-1234", "is_active": True, "last_assigned": None},
        {"boy_id": "D1002", "name": "Suresh", "phone": "9876543211", "vehicle_no": "TN-22-BC-5678", "is_active": True, "last_assigned": None},
        {"boy_id": "D1003", "name": "Vikram", "phone": "9876543212", "vehicle_no": "TN-22-CD-9012", "is_active": True, "last_assigned": None},
        {"boy_id": "D1004", "name": "Sukesh", "phone": "9876543213", "vehicle_no": "TN-22-DE-3456", "is_active": True, "last_assigned": None},
    ]
    inserted = skipped = 0
    for data in boys:
        if not db.session.get(DeliveryBoy, data["boy_id"]):
            db.session.add(DeliveryBoy(**data))
            logger.info("  [+] Agent  : %s (%s)", data["name"], data["boy_id"])
            inserted += 1
        else:
            logger.info("  [=] Agent  : %s already exists", data["boy_id"])
            skipped += 1
    db.session.commit()
    logger.info("  → %d inserted, %d skipped\n", inserted, skipped)


# ═════════════════════════════════════════════════════════════
# ORDERS + ORDER ITEMS
# ═════════════════════════════════════════════════════════════
def _parse_items_string(order_id, items_string):
    items = []
    if not items_string:
        return items
    for part in items_string.split(","):
        segs = [s.strip() for s in part.strip().split(":")]
        if len(segs) < 4 or not segs[0]:
            continue
        item_id        = segs[0]
        name           = segs[1]
        qty_g          = int(segs[2]) if segs[2].isdigit() else 0
        price_at_order = float(segs[3]) if segs[3] else 0.0
        is_free        = price_at_order == 0.0 or item_id.startswith("VF")
        items.append({
            "order_id": order_id,
            "item_id": item_id,
            "name": name,
            "qty_g": qty_g,
            "price_at_order": price_at_order,
            "is_free": is_free,
        })
    return items


def seed_orders():
    logger.info("Seeding orders...")
    orders = [
        {"order_id": "ORD1001", "user_id": "U1001", "total_amount": 243.0, "delivery_slot": "Morning", "delivery_boy_id": "D1001", "status": "Delivered", "timestamp": "2026-06-01 08:15:00", "items_string": "V1004:Potato:2000:25.00,V1022:Carrot:1000:35.00,V1018:Beans:1000:50.00,V1015:Spinach:500:25.00,V1040:Green Chilli:500:60.00"},
        {"order_id": "ORD1002", "user_id": "U1002", "total_amount": 520.0, "delivery_slot": "Afternoon", "delivery_boy_id": "D1002", "status": "Delivered", "timestamp": "2026-06-02 13:20:00", "items_string": "V1001:Onion:10000:50.00,V1003:Garlic:500:120.00,V1009:Tomato:1000:30.00,VF1001:Curry Leaves:50:0.00,VF1002:Coriander Leaves:50:0.00"},
        {"order_id": "ORD1003", "user_id": "U1003", "total_amount": 317.5, "delivery_slot": "Evening", "delivery_boy_id": "D1003", "status": "Delivered", "timestamp": "2026-06-02 18:45:00", "items_string": "V1026:Sweet Potato:1000:30.00,V1027:Elephant Foot Yam:1000:40.00,V1028:Colocassia:1000:35.00,V1029:Cassava:1000:30.00,V1044:Corn:1000:25.00,V1048:Pumpkin:2000:18.00,V1043:Ladiesfinger:1000:40.00"},
        {"order_id": "ORD1004", "user_id": "U1004", "total_amount": 375.0, "delivery_slot": "Morning", "delivery_boy_id": "D1004", "status": "Delivered", "timestamp": "2026-06-03 09:00:00", "items_string": "V1007:Capsicum:1000:60.00,V1006:Brinjal:1000:28.00,V1005:Cucumber:1000:20.00,V1008:Plantain:1000:60.00,V1011:Coconut:1000:35.00,V1010:Mango:1000:60.00,V1009:Tomato:1000:30.00,VF1001:Curry Leaves:50:0.00,VF1002:Coriander Leaves:50:0.00"},
        {"order_id": "ORD1005", "user_id": "U1005", "total_amount": 285.0, "delivery_slot": "Afternoon", "delivery_boy_id": "D1001", "status": "Delivered", "timestamp": "2026-06-03 14:10:00", "items_string": "V1030:Cabbage:1000:25.00,V1031:Cauliflower:1000:30.00,V1032:Broccoli:500:180.00,V1033:Red Cabbage:500:60.00,VF1001:Curry Leaves:50:0.00,VF1002:Coriander Leaves:50:0.00"},
        {"order_id": "ORD1006", "user_id": "U1002", "total_amount": 198.0, "delivery_slot": "Morning", "delivery_boy_id": "D1002", "status": "Delivered", "timestamp": "2026-06-04 07:30:00", "items_string": "V1034:Bittergourd:500:45.00,V1035:Ivy Gourd:500:35.00,V1036:Snake Gourd:500:30.00,V1037:Bottle Gourd:500:25.00,V1038:Ridge Gourd:500:30.00,V1039:Ash Gourd:500:20.00"},
        {"order_id": "ORD1007", "user_id": "U1003", "total_amount": 530.0, "delivery_slot": "Evening", "delivery_boy_id": "D1003", "status": "Out for Delivery", "timestamp": "2026-06-05 17:00:00", "items_string": "V1001:Onion:5000:50.00,V1002:Small Onion:1000:50.00,V1041:Ginger:500:80.00,V1042:Red Chilli:500:80.00,V1040:Green Chilli:500:60.00,V1003:Garlic:500:120.00,VF1001:Curry Leaves:50:0.00,VF1002:Coriander Leaves:50:0.00"},
        {"order_id": "ORD1008", "user_id": "U1004", "total_amount": 162.5, "delivery_slot": "Afternoon", "delivery_boy_id": "D1004", "status": "Out for Delivery", "timestamp": "2026-06-06 12:00:00", "items_string": "V1012:Coriander Leaves:500:100.00,V1013:Curry Leaves:250:120.00,V1014:Mint Leaves:500:90.00,V1015:Spinach:500:25.00,V1016:Spring Onion:500:40.00"},
        {"order_id": "ORD1009", "user_id": "U1001", "total_amount": 545.0, "delivery_slot": "Morning", "delivery_boy_id": "D1001", "status": "Out for Delivery", "timestamp": "2026-06-07 08:45:00", "items_string": "V1045:Mushroom:500:150.00,V1047:Asparagus:500:200.00,V1046:Banana Flower:500:35.00,V1032:Broccoli:500:180.00,VF1001:Curry Leaves:50:0.00,VF1002:Coriander Leaves:50:0.00"},
        {"order_id": "ORD1010", "user_id": "U1005", "total_amount": 308.0, "delivery_slot": "Evening", "delivery_boy_id": "D1002", "status": "Out for Delivery", "timestamp": "2026-06-08 19:00:00", "items_string": "V1017:Banana Stem:1000:20.00,V1018:Beans:1000:50.00,V1019:Flat Beans:1000:45.00,V1020:Field Beans:1000:50.00,V1021:Peas:1000:70.00,V1043:Ladiesfinger:1000:40.00"},
        {"order_id": "ORD1011", "user_id": "U1002", "total_amount": 675.0, "delivery_slot": "Afternoon", "delivery_boy_id": "D1003", "status": "Order Placed", "timestamp": "2026-06-09 11:30:00", "items_string": "V1001:Onion:5000:50.00,V1004:Potato:3000:25.00,V1009:Tomato:3000:30.00,V1006:Brinjal:1000:28.00,V1022:Carrot:1000:35.00,V1023:Beetroot:1000:30.00,VF1001:Curry Leaves:50:0.00,VF1002:Coriander Leaves:50:0.00"},
        {"order_id": "ORD1012", "user_id": "U1003", "total_amount": 440.0, "delivery_slot": "Morning", "delivery_boy_id": "D1004", "status": "Order Placed", "timestamp": "2026-06-10 07:00:00", "items_string": "V1026:Sweet Potato:2000:30.00,V1027:Elephant Foot Yam:2000:40.00,V1028:Colocassia:2000:35.00,V1029:Cassava:2000:30.00"},
        {"order_id": "ORD1013", "user_id": "U1004", "total_amount": 503.0, "delivery_slot": "Evening", "delivery_boy_id": "D1001", "status": "Order Placed", "timestamp": "2026-06-11 18:00:00", "items_string": "V1007:Capsicum:1000:60.00,V1010:Mango:1000:60.00,V1011:Coconut:1000:35.00,V1008:Plantain:1000:60.00,V1005:Cucumber:2000:20.00,V1033:Red Cabbage:1000:60.00,V1044:Corn:2000:25.00,VF1001:Curry Leaves:50:0.00,VF1002:Coriander Leaves:50:0.00"},
        {"order_id": "ORD1014", "user_id": "U1001", "total_amount": 258.0, "delivery_slot": "Afternoon", "delivery_boy_id": "D1002", "status": "Order Placed", "timestamp": "2026-06-12 13:45:00", "items_string": "V1034:Bittergourd:1000:45.00,V1036:Snake Gourd:1000:30.00,V1038:Ridge Gourd:1000:30.00,V1039:Ash Gourd:2000:20.00,V1048:Pumpkin:2000:18.00,V1043:Ladiesfinger:1000:40.00"},
        {"order_id": "ORD1015", "user_id": "U1005", "total_amount": 610.0, "delivery_slot": "Morning", "delivery_boy_id": "D1003", "status": "Order Placed", "timestamp": "2026-06-13 08:00:00", "items_string": "V1001:Onion:10000:50.00,V1003:Garlic:500:120.00,V1041:Ginger:500:80.00,V1040:Green Chilli:500:60.00,V1012:Coriander Leaves:500:100.00,VF1001:Curry Leaves:50:0.00,VF1002:Coriander Leaves:50:0.00"},
        {"order_id": "ORD1016", "user_id": "U1002", "total_amount": 345.0, "delivery_slot": "Afternoon", "delivery_boy_id": "D1004", "status": "Cancelled", "timestamp": "2026-06-14 12:20:00", "items_string": "V1045:Mushroom:500:150.00,V1047:Asparagus:500:200.00,V1046:Banana Flower:500:35.00,V1032:Broccoli:500:180.00"},
        {"order_id": "ORD1017", "user_id": "U1003", "total_amount": 422.5, "delivery_slot": "Evening", "delivery_boy_id": "D1001", "status": "Cancelled", "timestamp": "2026-06-15 19:30:00", "items_string": "V1018:Beans:2000:50.00,V1019:Flat Beans:2000:45.00,V1020:Field Beans:2000:50.00,V1021:Peas:1000:70.00,V1015:Spinach:1000:25.00,V1016:Spring Onion:1000:40.00,V1017:Banana Stem:1000:20.00"},
        {"order_id": "ORD1018", "user_id": "U1004", "total_amount": 275.0, "delivery_slot": "Morning", "delivery_boy_id": "D1002", "status": "Order Placed", "timestamp": "2026-06-16 09:15:00", "items_string": "V1022:Carrot:2000:35.00,V1023:Beetroot:2000:30.00,V1024:Radish:2000:20.00,V1025:Turnip:2000:25.00"},
        {"order_id": "ORD1019", "user_id": "U1001", "total_amount": 512.0, "delivery_slot": "Evening", "delivery_boy_id": "D1003", "status": "Order Placed", "timestamp": "2026-06-17 18:00:00", "items_string": "V1002:Small Onion:2000:50.00,V1003:Garlic:1000:120.00,V1041:Ginger:1000:80.00,V1042:Red Chilli:1000:80.00,V1009:Tomato:2000:30.00,VF1001:Curry Leaves:50:0.00,VF1002:Coriander Leaves:50:0.00"},
        {"order_id": "ORD1020", "user_id": "U1005", "total_amount": 387.0, "delivery_slot": "Afternoon", "delivery_boy_id": "D1004", "status": "Order Placed", "timestamp": "2026-06-18 14:00:00", "items_string": "V1030:Cabbage:2000:25.00,V1031:Cauliflower:2000:30.00,V1033:Red Cabbage:1000:60.00,V1034:Bittergourd:1000:45.00,V1035:Ivy Gourd:1000:35.00,V1037:Bottle Gourd:1000:25.00"},
        {"order_id": "ORD1021", "user_id": "U1002", "total_amount": 590.0, "delivery_slot": "Morning", "delivery_boy_id": "D1001", "status": "Order Placed", "timestamp": "2026-06-19 08:30:00", "items_string": "V1001:Onion:5000:50.00,V1004:Potato:4000:25.00,V1009:Tomato:4000:30.00,V1006:Brinjal:2000:28.00,VF1001:Curry Leaves:50:0.00,VF1002:Coriander Leaves:50:0.00"},
        {"order_id": "ORD1022", "user_id": "U1003", "total_amount": 460.0, "delivery_slot": "Evening", "delivery_boy_id": "D1002", "status": "Out for Delivery", "timestamp": "2026-06-20 17:45:00", "items_string": "V1007:Capsicum:2000:60.00,V1008:Plantain:1000:60.00,V1010:Mango:1000:60.00,V1011:Coconut:2000:35.00,V1043:Ladiesfinger:2000:40.00,V1044:Corn:2000:25.00"},
        {"order_id": "ORD1023", "user_id": "U1004", "total_amount": 530.0, "delivery_slot": "Afternoon", "delivery_boy_id": "D1003", "status": "Order Placed", "timestamp": "2026-06-21 13:00:00", "items_string": "V1045:Mushroom:1000:150.00,V1046:Banana Flower:1000:35.00,V1047:Asparagus:500:200.00,V1012:Coriander Leaves:500:100.00,V1014:Mint Leaves:500:90.00,V1013:Curry Leaves:250:120.00"},
        {"order_id": "ORD1024", "user_id": "U1001", "total_amount": 648.0, "delivery_slot": "Morning", "delivery_boy_id": "D1004", "status": "Delivered", "timestamp": "2026-06-22 09:00:00", "items_string": "V1001:Onion:5000:50.00,V1002:Small Onion:2000:50.00,V1004:Potato:3000:25.00,V1022:Carrot:2000:35.00,V1023:Beetroot:2000:30.00,V1024:Radish:2000:20.00,V1009:Tomato:2000:30.00,VF1001:Curry Leaves:50:0.00,VF1002:Coriander Leaves:50:0.00"},
        {"order_id": "ORD1025", "user_id": "U1005", "total_amount": 465.0, "delivery_slot": "Evening", "delivery_boy_id": "D1001", "status": "Delivered", "timestamp": "2026-06-23 18:30:00", "items_string": "V1026:Sweet Potato:1000:30.00,V1027:Elephant Foot Yam:1000:40.00,V1041:Ginger:1000:80.00,V1042:Red Chilli:1000:80.00,V1040:Green Chilli:1000:60.00,V1048:Pumpkin:2000:18.00,V1038:Ridge Gourd:1000:30.00,V1039:Ash Gourd:2000:20.00"},
    ]
    inserted = skipped = 0
    for data in orders:
        if db.session.get(Order, data["order_id"]):
            logger.info("  [=] Order  : %s already exists", data["order_id"])
            skipped += 1
            continue

        items_string = data.pop("items_string")

        if data.get("delivery_boy_id") in ("NONE", "", None):
            data["delivery_boy_id"] = None

        data["timestamp"] = datetime.strptime(data["timestamp"], "%Y-%m-%d %H:%M:%S")

        order = Order(**data)
        db.session.add(order)
        db.session.flush()

        for item_data in _parse_items_string(data["order_id"], items_string):
            db.session.add(OrderItem(**item_data))

        logger.info("  [+] Order  : %s (%s)", data["order_id"], data["status"])
        inserted += 1

    db.session.commit()
    logger.info("  → %d inserted, %d skipped\n", inserted, skipped)


# ═════════════════════════════════════════════════════════════
# ENTRYPOINT
# ═════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print()
    print("=" * 52)
    print("  Fresh Picks - Database Seeder")
    print("=" * 52)
    print()

    app = create_app()
    with app.app_context():
        db.create_all()
        logger.info("Tables verified / created.\n")

        seed_admins()
        seed_users()
        seed_products()
        seed_free_items()
        seed_delivery_boys()
        seed_orders()

    print()
    logger.info("Seed complete.")
    print("=" * 52)
    print()

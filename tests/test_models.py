"""
test_models.py - Tests for SQLAlchemy models.
"""
from datetime import datetime

from app.models import db, User, Admin, Product, FreeItem, DeliveryBoy, CartItem, Order, OrderItem, OTPVerification


class TestUserModel:
    def test_create_user(self, app):
        user = User(
            user_id="U1001",
            username="testuser",
            password="scrypt:32768:6:1$hash",
            full_name="Test User",
            email="test@example.com",
            phone="9876543210",
            address="Test Address",
        )
        db.session.add(user)
        db.session.commit()

        found = User.query.filter_by(user_id="U1001").first()
        assert found is not None
        assert found.username == "testuser"
        assert found.email == "test@example.com"

    def test_user_to_dict(self, app):
        user = User(
            user_id="U1001",
            username="testuser",
            password="scrypt:32768:6:1$hash",
            full_name="Test User",
            email="test@example.com",
            phone="9876543210",
            address="Test Address",
        )
        db.session.add(user)
        db.session.commit()

        d = user.to_dict()
        assert d["user_id"] == "U1001"
        assert d["username"] == "testuser"
        assert d["email"] == "test@example.com"
        assert "password" not in d


class TestAdminModel:
    def test_create_admin(self, app):
        admin = Admin(
            admin_id="A1001",
            username="admin",
            password="scrypt:32768:6:1$hash",
            admin_name="Admin User",
            email="admin@example.com",
        )
        db.session.add(admin)
        db.session.commit()

        found = Admin.query.filter_by(admin_id="A1001").first()
        assert found is not None
        assert found.username == "admin"

    def test_admin_to_dict(self, app):
        admin = Admin(
            admin_id="A1001",
            username="admin",
            password="scrypt:32768:6:1$hash",
            admin_name="Admin User",
            email="admin@example.com",
        )
        db.session.add(admin)
        db.session.commit()

        d = admin.to_dict()
        assert d["admin_id"] == "A1001"
        assert d["username"] == "admin"
        assert d["admin_name"] == "Admin User"
        assert "password" not in d


class TestProductModel:
    def test_create_product(self, app):
        product = Product(
            veg_id="V1001",
            category="Onions",
            name="Onion",
            price_per_1000g=50.0,
            stock_g=50000,
            tag="fresh",
            validity_days=7,
        )
        db.session.add(product)
        db.session.commit()

        found = Product.query.filter_by(veg_id="V1001").first()
        assert found is not None
        assert found.name == "Onion"
        assert found.price_per_1000g == 50.0

    def test_product_to_dict(self, app):
        product = Product(
            veg_id="V1001",
            category="Onions",
            name="Onion",
            price_per_1000g=50.0,
            stock_g=50000,
            tag="fresh",
            validity_days=7,
        )
        db.session.add(product)
        db.session.commit()

        d = product.to_dict()
        assert d["veg_id"] == "V1001"
        assert d["name"] == "Onion"
        assert d["category"] == "Onions"
        assert "stock_g" in d
        assert "price_per_1000g" in d


class TestFreeItemModel:
    def test_create_free_item(self, app):
        free_item = FreeItem(
            vf_id="VF1001",
            name="Curry Leaves",
            stock_g=10000,
            min_trigger_amt=200.0,
            free_qty_g=50,
        )
        db.session.add(free_item)
        db.session.commit()

        found = FreeItem.query.filter_by(vf_id="VF1001").first()
        assert found is not None
        assert found.name == "Curry Leaves"

    def test_free_item_to_dict(self, app):
        free_item = FreeItem(
            vf_id="VF1001",
            name="Curry Leaves",
            stock_g=10000,
            min_trigger_amt=200.0,
            free_qty_g=50,
        )
        db.session.add(free_item)
        db.session.commit()

        d = free_item.to_dict()
        assert d["vf_id"] == "VF1001"
        assert d["name"] == "Curry Leaves"


class TestDeliveryBoyModel:
    def test_create_delivery_boy(self, app):
        db_boy = DeliveryBoy(
            boy_id="D1001",
            name="Ramesh",
            phone="9876543210",
            vehicle_no="KA01AB1234",
            is_active=True,
        )
        db.session.add(db_boy)
        db.session.commit()

        found = DeliveryBoy.query.filter_by(boy_id="D1001").first()
        assert found is not None
        assert found.name == "Ramesh"

    def test_delivery_boy_to_dict(self, app):
        db_boy = DeliveryBoy(
            boy_id="D1001",
            name="Ramesh",
            phone="9876543210",
            vehicle_no="KA01AB1234",
            is_active=True,
        )
        db.session.add(db_boy)
        db.session.commit()

        d = db_boy.to_dict()
        assert d["boy_id"] == "D1001"
        assert d["name"] == "Ramesh"
        assert d["phone"] == "9876543210"
        assert d["vehicle_no"] == "KA01AB1234"


class TestCartItemModel:
    def test_create_cart_item(self, app):
        cart_item = CartItem(
            user_id="U1001",
            item_id="V1001",
            name="Onion",
            qty_g=1000,
            price_per_1000g=50.0,
            is_free=False,
        )
        db.session.add(cart_item)
        db.session.commit()

        found = CartItem.query.filter_by(user_id="U1001", item_id="V1001").first()
        assert found is not None
        assert found.qty_g == 1000

    def test_cart_item_to_dict(self, app):
        cart_item = CartItem(
            user_id="U1001",
            item_id="V1001",
            name="Onion",
            qty_g=1000,
            price_per_1000g=50.0,
            is_free=False,
        )
        db.session.add(cart_item)
        db.session.commit()

        d = cart_item.to_dict()
        assert d["item_id"] == "V1001"
        assert d["name"] == "Onion"
        assert d["qty_g"] == 1000
        assert d["item_total"] == 50.0
        assert d["is_free"] is False

    def test_cart_item_free_item(self, app):
        cart_item = CartItem(
            user_id="U1001",
            item_id="VF1001",
            name="Curry Leaves",
            qty_g=50,
            price_per_1000g=0.0,
            is_free=True,
        )
        db.session.add(cart_item)
        db.session.commit()

        d = cart_item.to_dict()
        assert d["item_total"] == 0.0
        assert d["is_free"] is True


class TestOrderModel:
    def test_create_order(self, app):
        order = Order(
            order_id="ORD1001",
            user_id="U1001",
            total_amount=100.0,
            delivery_slot="Morning",
            status="Order Placed",
        )
        db.session.add(order)
        db.session.commit()

        found = Order.query.filter_by(order_id="ORD1001").first()
        assert found is not None
        assert found.status == "Order Placed"
        assert found.delivery_slot == "Morning"

    def test_order_to_dict(self, app):
        order = Order(
            order_id="ORD1001",
            user_id="U1001",
            total_amount=100.0,
            delivery_slot="Morning",
            status="Order Placed",
        )
        db.session.add(order)
        db.session.commit()

        d = order.to_dict()
        assert d["order_id"] == "ORD1001"
        assert d["status"] == "Order Placed"
        assert "items" in d

    def test_update_order_status(self, app):
        order = Order(
            order_id="ORD1001",
            user_id="U1001",
            total_amount=100.0,
            delivery_slot="Morning",
            status="Order Placed",
        )
        db.session.add(order)
        db.session.commit()

        order.status = "Out for Delivery"
        db.session.commit()

        found = Order.query.filter_by(order_id="ORD1001").first()
        assert found.status == "Out for Delivery"

    def test_order_with_delivery_boy(self, app):
        db_boy = DeliveryBoy(boy_id="D1001", name="Ramesh", phone="9876543210", vehicle_no="KA01AB1234", is_active=True)
        db.session.add(db_boy)
        db.session.flush()
        
        order = Order(
            order_id="ORD1001",
            user_id="U1001",
            total_amount=100.0,
            delivery_slot="Morning",
            status="Order Placed",
            delivery_boy_id="D1001",
        )
        db.session.add(order)
        db.session.commit()

        found = Order.query.filter_by(order_id="ORD1001").first()
        assert found.delivery_boy_id == "D1001"


class TestOrderItemModel:
    def test_create_order_item(self, app):
        order = Order(order_id="ORD1001", user_id="U1001", total_amount=100.0, delivery_slot="Morning", status="Order Placed")
        db.session.add(order)
        db.session.flush()

        item = OrderItem(
            order_id="ORD1001",
            item_id="V1001",
            name="Onion",
            qty_g=1000,
            price_at_order=50.0,
            is_free=False,
        )
        db.session.add(item)
        db.session.commit()

        found = OrderItem.query.filter_by(order_id="ORD1001", item_id="V1001").first()
        assert found is not None


class TestOTPVerificationModel:
    def test_create_otp_verification(self, app):
        import time
        otp = OTPVerification(
            client_token="abc123",
            flow_key="user_login",
            full_key="abc123:user_login:test@example.com",
            otp_code="123456",
            recipient="test@example.com",
            purpose="login",
            expires_at=time.time() + 600,
            created_at=time.time(),
        )
        db.session.add(otp)
        db.session.commit()

        found = OTPVerification.query.filter_by(client_token="abc123").first()
        assert found is not None
        assert found.otp_code == "123456"

    def test_otp_expires_in_future(self, app):
        import time
        otp = OTPVerification(
            client_token="abc123",
            flow_key="user_login",
            full_key="abc123:user_login:test@example.com",
            otp_code="123456",
            recipient="test@example.com",
            purpose="login",
            expires_at=time.time() + 600,
            created_at=time.time(),
        )
        db.session.add(otp)
        db.session.commit()
        assert otp.expires_at > time.time()

    def test_otp_created_at_set(self, app):
        import time
        otp = OTPVerification(
            client_token="abc123",
            flow_key="user_login",
            full_key="abc123:user_login:test@example.com",
            otp_code="123456",
            recipient="test@example.com",
            purpose="login",
            expires_at=time.time() + 600,
            created_at=time.time(),
        )
        db.session.add(otp)
        db.session.commit()
        assert otp.created_at > 0

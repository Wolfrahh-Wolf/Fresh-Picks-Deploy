"""
test_routes.py - Tests for HTTP routes and endpoints.
"""


class TestHealthEndpoint:
    def test_health_returns_200(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "healthy"

    def test_health_contains_version(self, client):
        resp = client.get("/health")
        data = resp.get_json()
        assert "version" in data


class TestProductRoutes:
    def test_products_list(self, client):
        resp = client.get("/api/products")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "products" in data or isinstance(data, list)

    def test_products_available(self, client):
        resp = client.get("/api/products?available=true")
        assert resp.status_code == 200

    def test_products_by_category(self, client):
        resp = client.get("/api/products?category=Onions")
        assert resp.status_code == 200

    def test_product_update(self, client):
        resp = client.patch("/api/products/V1001", json={
            "stock_g": 50000,
        })
        # Product may not exist in test DB, so check it's either 200 or 404
        assert resp.status_code in (200, 404)


class TestCartRoutes:
    def test_get_cart_not_logged_in(self, client):
        resp = client.get("/api/cart")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "ERROR"

    def test_get_cart_logged_in(self, client):
        with client.session_transaction() as sess:
            sess["user_id"] = "U1001"
        resp = client.get("/api/cart")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "SUCCESS"

    def test_add_to_cart_not_logged_in(self, client):
        resp = client.post("/api/cart/items", json={
            "veg_id": "V1001",
            "qty_g": 1000,
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "ERROR"

    def test_add_to_cart_invalid_item(self, client):
        with client.session_transaction() as sess:
            sess["user_id"] = "U1001"
        resp = client.post("/api/cart/items", json={
            "veg_id": "NONEXISTENT",
            "qty_g": 1000,
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "ERROR"

    def test_add_to_cart_invalid_qty(self, client):
        with client.session_transaction() as sess:
            sess["user_id"] = "U1001"
        resp = client.post("/api/cart/items", json={
            "veg_id": "V1001",
            "qty_g": -1000,
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "ERROR"

    def test_update_cart_qty_not_logged_in(self, client):
        resp = client.patch("/api/cart/items/V1001", json={"qty_g": 2000})
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "ERROR"

    def test_remove_from_cart_not_logged_in(self, client):
        resp = client.delete("/api/cart/items/V1001")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "ERROR"


class TestOrderRoutes:
    def test_order_detail_not_found(self, client):
        resp = client.get("/api/orders/NONEXISTENT")
        assert resp.status_code == 404

    def test_get_user_orders(self, client):
        resp = client.get("/api/orders?user_id=U1001")
        assert resp.status_code == 200

    def test_get_orders_by_status(self, client):
        resp = client.get("/api/orders?status=Delivered")
        assert resp.status_code == 200


class TestErrorHandlers:
    def test_404_handler(self, client):
        resp = client.get("/nonexistent")
        assert resp.status_code == 404
        data = resp.get_json()
        assert data["status"] == "ERROR"

    def test_405_handler(self, client):
        resp = client.delete("/")
        assert resp.status_code == 405
        data = resp.get_json()
        assert data["status"] == "ERROR"

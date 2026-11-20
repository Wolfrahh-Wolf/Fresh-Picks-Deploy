from app import create_app

app = create_app()
with app.test_client() as c:
    resp = c.get('/api/products')
    data = resp.get_json()
    print(f"Status: {resp.status_code}")
    print(f"API status: {data.get('status')}")
    print(f"Products count: {len(data.get('products', []))}")
    if data.get('products'):
        print(f"First product: {data['products'][0]['name']}")

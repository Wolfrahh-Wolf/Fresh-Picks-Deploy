import hashlib
print(hashlib.sha256("User@123".encode("utf-8")).hexdigest())
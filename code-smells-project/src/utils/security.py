from werkzeug.security import generate_password_hash, check_password_hash

def hash_password(plain_password):
    return generate_password_hash(plain_password, method='pbkdf2:sha256')

def verify_password(plain_password, hashed_password):
    return check_password_hash(hashed_password, plain_password)

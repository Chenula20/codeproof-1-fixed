"""A small request contract used by the learning challenge."""


def validate_login(data):
    if not data.get("username") or not data.get("password"):
        return {"error": "Missing credentials"}, 422
    if data["username"] != "student" or data["password"] != "example-only":
        return {"error": "Invalid credentials"}, 401
    return {"user": data["username"]}, 200

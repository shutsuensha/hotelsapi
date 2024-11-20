from app.routers.dependencies import create_access_token


def test_create_access_token():
    data = {"user_id": 1}
    jwt_token = create_access_token(data)

    assert jwt_token
    assert isinstance(jwt_token, str)

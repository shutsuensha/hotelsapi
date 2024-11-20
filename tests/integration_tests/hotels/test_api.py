async def test_get_hotels(ac):
    response = await ac.get("/hotels/")

    assert response.status_code == 200

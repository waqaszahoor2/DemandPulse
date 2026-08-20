def valid_inventory_payload():
    return {
        "p10": 8.0,
        "p50": 12.0,
        "p90": 18.0,
        "current_inventory": 10.0,
        "service_level": 0.90,
        "holding_cost": 1.0,
        "stockout_cost": 5.0,
        "lead_time_days": 1.0,
    }


def test_inventory_response_schema(client):
    response = client.post("/inventory/recommendation", json=valid_inventory_payload())
    assert response.status_code == 200
    body = response.json()
    assert body["recommended_order_quantity"] >= 0
    assert 0 <= body["stockout_risk"] <= 1
    assert body["assumptions"]


def test_inventory_rejects_invalid_service_level(client):
    payload = valid_inventory_payload()
    payload["service_level"] = 1.2
    response = client.post("/inventory/recommendation", json=payload)
    assert response.status_code == 422


def test_inventory_rejects_negative_cost(client):
    payload = valid_inventory_payload()
    payload["holding_cost"] = -1
    response = client.post("/inventory/recommendation", json=payload)
    assert response.status_code == 422

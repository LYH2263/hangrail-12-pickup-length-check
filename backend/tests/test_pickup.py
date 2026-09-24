def test_pickup_length_mismatch_keeps_placement(client, make_order):
    """衣长不符：取件失败，active 占位不释放，工单仍为 hung。"""
    state = make_order
    resp = client.post("/api/pickup", json={"ticket_code": "HR-3001", "length_cm": 102.0})
    assert resp.status_code == 400

    order, placement = state()
    assert order.status == "hung"
    assert placement.active == 1


def test_pickup_within_tolerance_releases(client, make_order):
    """衣长相符（含 0.5cm 边界）：取件成功，占位释放，工单 picked。"""
    state = make_order
    resp = client.post("/api/pickup", json={"ticket_code": "HR-3001", "length_cm": 100.5})
    assert resp.status_code == 200
    assert resp.json()["status"] == "picked"

    order, placement = state()
    assert order.status == "picked"
    assert placement.active == 0


def test_pickup_missing_length_fails(client, make_order):
    """票号正确但衣长缺失：取件失败，占位仍在。"""
    state = make_order
    resp = client.post("/api/pickup", json={"ticket_code": "HR-3001"})
    assert resp.status_code == 422

    order, placement = state()
    assert order.status == "hung"
    assert placement.active == 1


def test_pickup_exact_length_releases(client, make_order):
    """申报衣长与工单完全一致：释放成功。"""
    state = make_order
    resp = client.post("/api/pickup", json={"ticket_code": "HR-3001", "length_cm": 100.0})
    assert resp.status_code == 200

    order, placement = state()
    assert order.status == "picked"
    assert placement.active == 0


def test_pickup_over_tolerance_boundary(client, make_order):
    """超出 0.5cm（如 0.6cm 误差）：失败且占位仍在。"""
    state = make_order
    resp = client.post("/api/pickup", json={"ticket_code": "HR-3001", "length_cm": 100.6})
    assert resp.status_code == 400

    order, placement = state()
    assert order.status == "hung"
    assert placement.active == 1

from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models.models import HangRail, RailPlacement, Store, WorkOrder


@pytest.fixture()
def db_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    TestingSession = sessionmaker(bind=engine)
    db = TestingSession()
    store = Store(name="测试店")
    db.add(store)
    db.flush()
    rail = HangRail(store_id=store.id, label="A 杆", length_cm=200)
    db.add(rail)
    db.flush()
    order = WorkOrder(
        store_id=store.id,
        ticket_code="HR-2001",
        garment_name="羊毛大衣",
        length_cm=45,
        status="hung",
        due_at=datetime.utcnow() + timedelta(days=1),
        hung_at=datetime.utcnow(),
    )
    db.add(order)
    db.flush()
    db.add(RailPlacement(rail_id=rail.id, order_id=order.id, start_cm=0, end_cm=45, active=1))
    db.commit()

    def override_get_db():
        session = TestingSession()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    try:
        yield TestingSession()
    finally:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(engine)


@pytest.fixture()
def client(db_session):
    return TestClient(app)


def _placement(db_session) -> RailPlacement:
    return db_session.scalar(select(RailPlacement))


def test_length_mismatch_keeps_placeholder(db_session, client):
    """衣长不符：取件失败，active 占位不释放，工单仍为 hung。"""
    resp = client.post("/api/pickup", json={"ticket_code": "HR-2001", "declared_length_cm": 46})
    assert resp.status_code == 400

    db_session.expire_all()
    order = db_session.scalar(select(WorkOrder))
    assert order.status == "hung"
    p = _placement(db_session)
    assert p.active == 1


def test_matching_length_releases_placeholder(db_session, client):
    """衣长相符（含 0.5cm 边界）：取件成功，占位释放，工单变为 picked。"""
    resp = client.post("/api/pickup", json={"ticket_code": "HR-2001", "declared_length_cm": 45.5})
    assert resp.status_code == 200
    assert resp.json()["status"] == "picked"

    db_session.expire_all()
    order = db_session.scalar(select(WorkOrder))
    assert order.status == "picked"
    p = _placement(db_session)
    assert p.active == 0


def test_exact_length_releases_placeholder(db_session, client):
    resp = client.post("/api/pickup", json={"ticket_code": "HR-2001", "declared_length_cm": 45})
    assert resp.status_code == 200

    db_session.expire_all()
    assert _placement(db_session).active == 0


def test_missing_declared_length_fails(db_session, client):
    """票号正确但衣长缺失：请求校验失败，不得取件。"""
    resp = client.post("/api/pickup", json={"ticket_code": "HR-2001"})
    assert resp.status_code == 422

    db_session.expire_all()
    order = db_session.scalar(select(WorkOrder))
    assert order.status == "hung"
    assert _placement(db_session).active == 1

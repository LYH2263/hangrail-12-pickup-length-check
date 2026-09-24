import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app


@pytest.fixture()
def client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def make_order(client):
    """直接落库一张在挂工单（含 active 占位），返回预置数据。"""
    from datetime import datetime, timedelta

    from app.models.models import HangRail, RailPlacement, Store, WorkOrder

    db = next(app.dependency_overrides[get_db]())
    store = Store(name="测试门店")
    db.add(store)
    db.flush()
    rail = HangRail(store_id=store.id, label="A 杆", length_cm=200)
    db.add(rail)
    db.flush()
    now = datetime.utcnow()
    order = WorkOrder(
        store_id=store.id,
        ticket_code="HR-3001",
        garment_name="羊毛大衣",
        length_cm=100.0,
        status="hung",
        due_at=now + timedelta(days=1),
        hung_at=now,
    )
    db.add(order)
    db.flush()
    placement = RailPlacement(
        rail_id=rail.id, order_id=order.id, start_cm=0, end_cm=order.length_cm
    )
    db.add(placement)
    db.commit()

    def state():
        db.refresh(order)
        db.refresh(placement)
        return order, placement

    yield state
    db.close()

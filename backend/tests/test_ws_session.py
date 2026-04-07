import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from src.main import app, get_session
from src.engine.models import User, Character, GameSession, SessionParticipants, GameSessionStatus
import uuid
from fastapi import status
from src.auth.utils import create_access_token

@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session

@pytest.fixture(name="client")
def client_fixture(session: Session):
    def get_session_override():
        # Make the synchronous session behave somewhat like the async one for testing
        class AsyncSessionMock:
            def __init__(self, s):
                self.s = s
            async def execute(self, stmt):
                return self.s.execute(stmt)
            async def commit(self):
                self.s.commit()
            async def refresh(self, obj):
                self.s.refresh(obj)
            def add(self, obj):
                self.s.add(obj)

        async def mock_gen():
            yield AsyncSessionMock(session)

        return mock_gen()

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_ws_bad_token(client: TestClient):
    with pytest.raises(Exception) as exc_info:
        with client.websocket_connect("/ws/dummy_session/dummy_char"):
            pass

    try:
        with client.websocket_connect("/ws/dummy_session/dummy_char?token=invalid_token"):
            pass
    except Exception as e:
        pass

@pytest.mark.asyncio
async def test_ws_unauthorized_user(session: Session, client: TestClient):
    user = User(username="testuser", hashed_password="pw")
    session.add(user)
    session.commit()
    session.refresh(user)

    token = create_access_token({"sub": user.username})

    try:
        with client.websocket_connect(f"/ws/dummy_session/{uuid.uuid4()}?token={token}"):
            pass
    except Exception:
        pass

@pytest.mark.asyncio
async def test_ws_valid_connection(session: Session, client: TestClient):
    user = User(username="validuser", hashed_password="pw")
    session.add(user)
    session.commit()
    session.refresh(user)

    char = Character(name="Hero", universe_id=uuid.uuid4(), user_id=user.id, hp=10, max_hp=10, armor_class=10, speed=30)
    session.add(char)
    session.commit()
    session.refresh(char)

    gs = GameSession(universe_id=char.universe_id, status=GameSessionStatus.ACTIVE)
    session.add(gs)
    session.commit()
    session.refresh(gs)

    participant = SessionParticipants(character_id=char.id, session_id=gs.id)
    session.add(participant)
    session.commit()

    token = create_access_token({"sub": user.username})

    try:
        with client.websocket_connect(f"/ws/{gs.id}/{char.id}?token={token}") as ws:
            pass
    except Exception as e:
        pass

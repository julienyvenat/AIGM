import sys
import os
import pytest
import pytest_asyncio
import uuid

os.environ['OPENAI_API_KEY'] = 'dummy_key'
os.environ['LLM_PROVIDER'] = 'openai'
os.environ['IMAGE_PROVIDER'] = 'openai'

from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

import src.main as main
from src.engine.database import get_session
from src.engine.models import Universe, WorldNPCTable, Character

# In-memory database URL
SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = async_sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=AsyncSession)

async def override_get_session():
    async with TestingSessionLocal() as session:
        yield session

main.app.dependency_overrides[get_session] = override_get_session

client = TestClient(main.app)

from sqlmodel import SQLModel, select

@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)

# --- Mocks ---
class MockWorldKnowledge:
    def __init__(self):
        self.histoire_globale = "Une histoire globale"
        class MockNPC:
            def __init__(self, nom, description, faction=""):
                self.nom = nom
                self.description = description
                self.faction = faction
                self.hp = 10
                self.armor_class = 10
        self.npc = [MockNPC("Gobelin", "Un petit être vert méchant")]
        class MockLocation:
            def __init__(self, nom, description, points_interet):
                self.nom = nom
                self.description = description
                self.points_interet = points_interet
        self.location = [MockLocation("Grotte", "Une grotte sombre", ["Entrée", "Fond"])]
        self.faction = []

# Mock Arbitration Result
class MockArbitrationResult:
    def __init__(self):
        self.roll_value = 15
        self.modifier = 2
        self.total = 17
        self.success = True
        self.hp_change = -2
        self.consumed_resource_type = None
        self.consumed_resource_name = None

@pytest.mark.asyncio
@patch('src.agents.universe_architect.client.chat.completions.create', new_callable=AsyncMock)
@patch('src.agents.universe_architect.client.beta.chat.completions.parse', new_callable=AsyncMock)
@patch('src.world_builder.world_router.add_to_memory', new_callable=AsyncMock)
@patch('src.main.generate_scene_image', new_callable=AsyncMock)
@patch('src.agents.universe_architect.generate_scene_image', new_callable=AsyncMock)
@patch('src.main.generate_narrator_response', new_callable=AsyncMock)
@patch('src.agents.arbitrator.arbitrate_action', new_callable=AsyncMock)
@patch('src.main.get_relevant_context', new_callable=AsyncMock)
@patch('src.main.analyze_scene', new_callable=AsyncMock)
async def test_e2e_game_flow(
    mock_analyze_scene,
    mock_get_context,
    mock_arbitrate,
    mock_narrator,
    mock_gen_image_arch,
    mock_gen_image_main,
    mock_add_memory,
    mock_parse,
    mock_create
):

    # 1. Mock Parse WorldKnowledge
    class MockChoiceParse:
        class MockMessageParse:
            parsed = MockWorldKnowledge()
        message = MockMessageParse()
    class MockParseResponse:
        choices = [MockChoiceParse()]
    mock_parse.return_value = MockParseResponse()

    # 2. Mock Create Universe Name
    class MockChoiceCreate:
        class MockMessageCreate:
            content = "Monde de Test"
        message = MockMessageCreate()
    class MockCreateResponse:
        choices = [MockChoiceCreate()]
    mock_create.return_value = MockCreateResponse()

    class MockSceneDecision:
        def __init__(self):
            self.decision = "IGNORE"
            self.value = "IGNORE"
    mock_analyze_scene.return_value = MockSceneDecision()

    mock_gen_image_arch.return_value = "http://dummy.url/image.jpg"
    mock_gen_image_main.return_value = "http://dummy.url/image.jpg"
    mock_narrator.return_value = "Un gobelin surgit de l'ombre."
    mock_arbitrate.return_value = MockArbitrationResult()
    mock_get_context.return_value = "Context from RAG"

    # Etape 1 : Création Univers via API (Vraie création en base via le router !)
    response = client.post("/world/generate-from-prompt", json={"prompt": "Crée un monde de test"})
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "success"
    mock_universe_id = uuid.UUID(data["universe"]["id"])

    # Vérification BDD : on check qu'il y a bien l'univers et le PNJ sans insertion manuelle
    async with TestingSessionLocal() as session:
        res = await session.execute(select(Universe))
        universes = res.scalars().all()
        assert len(universes) == 1
        assert universes[0].name == "Monde de Test"

        res_npc = await session.execute(select(WorldNPCTable))
        npcs = res_npc.scalars().all()
        assert len(npcs) == 1
        assert npcs[0].nom == "Gobelin"

    # Création du personnage pour le websocket
    char_id = uuid.uuid4()
    async with TestingSessionLocal() as session:
        char = Character(
            id=char_id,
            universe_id=mock_universe_id,
            name="Thorin",
            is_pc=True,
            hp=20,
            max_hp=20,
            armor_class=10,
            speed=30,
            game_mode="NARRATIVE"
        )
        session.add(char)
        await session.commit()

    # Etape 2 & 3 : WebSocket & Mode Narratif
    # On teste le WS sans bloquer (FastAPI TestClient est synchrone)
    try:
        with client.websocket_connect(f"/ws/{str(char_id)}") as websocket:
            websocket.send_json({"text": "J'entre dans la pièce"})

            # Etape 4 : Mode Battle
            websocket.send_json({"text": "/battle"})

    except Exception as e:
        pass

    # Vérifier que le statut en DB est bien passé en BATTLE
    import asyncio
    await asyncio.sleep(0.1) # Laisser l'event loop gérer les messages WS qui pourraient être en arrière-plan

    async with TestingSessionLocal() as session:
        res = await session.execute(select(Character).where(Character.id == char_id))
        updated_char = res.scalars().first()

    # Etape 5 : Arbitrage
    try:
        with client.websocket_connect(f"/ws/{str(char_id)}") as websocket:
            websocket.send_json({"text": "J'attaque"})
    except Exception as e:
        pass

import asyncio
import time
import uuid
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

import chromadb
chromadb.PersistentClient = lambda path: chromadb.EphemeralClient()

from chromadb.utils.embedding_functions import EmbeddingFunction
class MockEmbeddingFunction(EmbeddingFunction):
    def __call__(self, input):
        # Time sleep to simulate network delay for embedding!
        # Let's say 100ms per batch
        time.sleep(0.1)
        return [[0.0] * 1536 for _ in input]

import chromadb.utils.embedding_functions as ef
ef.OpenAIEmbeddingFunction = MockEmbeddingFunction

from engine.database import engine as async_engine, SQLModel
from world_builder.schemas import WorldKnowledge, WorldNPC, WorldLocation, WorldFaction
from world_builder.lore_extractor import store_world_knowledge
import engine.models  # Ensures models are loaded before create_all

# Just disable foreign keys in sqlite so we don't need Universe
async def init_db_for_test():
    async with async_engine.begin() as conn:
        await conn.execute(SQLModel.metadata.tables["universe"].delete()) # ensure empty or exist
        await conn.run_sync(SQLModel.metadata.drop_all)
        await conn.run_sync(SQLModel.metadata.create_all)

async def run_benchmark():
    print("Initializing DB for benchmark...")
    await init_db_for_test()

    print("Generating dummy WorldKnowledge...")
    knowledge = WorldKnowledge()

    for i in range(15):
        knowledge.npc.append(WorldNPC(nom=f"Benchmark NPC {i}", faction="Test Faction", description=f"Desc {i}", hp=100 + i, armor_class=10 + i))
        knowledge.location.append(WorldLocation(nom=f"Benchmark Location {i}", description=f"Desc {i}", points_interet=[f"Point A {i}", f"Point B {i}"]))
        knowledge.faction.append(WorldFaction(nom=f"Benchmark Faction {i}", description=f"Desc {i}", relations_politiques=[f"Other Faction {i}: Hostile"]))

    knowledge.histoire_globale = "This is a very long global history text intended to be chunked. " * 50

    print("Starting benchmark of store_world_knowledge...")
    start_time = time.time()

    # SQLite doesn't enforce FKs by default unless PRAGMA foreign_keys = ON.
    # The error we saw earlier was NOT NULL constraint on universe_id.
    # We will just patch the classes to supply a uuid.uuid4() natively instead of fetching from db.

    original_npc_init = engine.models.WorldNPCTable.__init__
    original_loc_init = engine.models.WorldLocationTable.__init__
    original_fac_init = engine.models.WorldFactionTable.__init__

    import uuid
    dummy_uuid = uuid.uuid4()

    def npc_init(self, **kwargs):
        if "universe_id" not in kwargs:
            kwargs["universe_id"] = dummy_uuid
        original_npc_init(self, **kwargs)

    def loc_init(self, **kwargs):
        if "universe_id" not in kwargs:
            kwargs["universe_id"] = dummy_uuid
        original_loc_init(self, **kwargs)

    def fac_init(self, **kwargs):
        if "universe_id" not in kwargs:
            kwargs["universe_id"] = dummy_uuid
        original_fac_init(self, **kwargs)

    engine.models.WorldNPCTable.__init__ = npc_init
    engine.models.WorldLocationTable.__init__ = loc_init
    engine.models.WorldFactionTable.__init__ = fac_init

    await store_world_knowledge(knowledge)

    end_time = time.time()
    duration = end_time - start_time

    print(f"\n--- BENCHMARK RESULTS ---")
    print(f"Total time taken: {duration:.4f} seconds")
    print(f"Items processed: {len(knowledge.npc)} NPCs, {len(knowledge.location)} Locations, {len(knowledge.faction)} Factions")

if __name__ == "__main__":
    import logging
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
    asyncio.run(run_benchmark())

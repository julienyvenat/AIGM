import pytest
import os
import asyncio
from unittest import mock
import sys

# Ajouter `backend` au PYTHONPATH si ce n'est pas déjà fait
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__))))

import chromadb
# IMPORTANT : Avant d'importer vector_db, on vide la clé API pour s'assurer
# que l'initialisation du module (au chargement) utilisera le fallback par défaut.
os.environ.pop("OPENAI_API_KEY", None)

from src.memory import vector_db

# On utilise pytest-asyncio
pytestmark = pytest.mark.asyncio


@pytest.fixture(autouse=True)
def mock_chroma_client():
    """Remplace le client persistant par un client éphémère pour les tests afin de ne pas polluer la DB de dev."""
    # Créer un client éphémère (en mémoire)
    ephemeral_client = chromadb.EphemeralClient()

    # Remplacer le client dans le module par le client éphémère
    original_client = vector_db.client
    original_collection = vector_db.collection

    try:
        vector_db.client = ephemeral_client
        vector_db.collection = ephemeral_client.get_or_create_collection(name="rpg_memory")
        yield ephemeral_client
    finally:
        # Restaurer après le test (bonne pratique même si pytest nettoie l'état du module)
        vector_db.client = original_client
        vector_db.collection = original_collection


async def test_add_and_get_memory():
    """Teste le flux complet d'ajout et de récupération avec mock d'embeddings par défaut"""

    # Toutes les mémoires sont scopées à un univers (isolation multi-tenant, cf. AGENTS.md)
    universe_id = "11111111-1111-1111-1111-111111111111"

    # Ajout de mémoires factices
    text1 = "Le forgeron de la ville s'appelle Thorin."
    text2 = "Les joueurs ont volé une pomme au marché."

    # L'ajout devrait fonctionner sans exception
    doc_id1 = await vector_db.add_to_memory(text=text1, memory_type="lore", metadata={"universe_id": universe_id})
    assert doc_id1 is not None

    doc_id2 = await vector_db.add_to_memory(text=text2, memory_type="session_log", metadata={"universe_id": universe_id})
    assert doc_id2 is not None

    # Petit délai pour laisser ChromaDB indexer si nécessaire
    await asyncio.sleep(0.1)

    # Récupération sans filtre de type, filtrée par universe_id
    result_all = await vector_db.get_relevant_context(query="Qui est le forgeron ?", universe_id=universe_id, limit=5)

    # Vérifie que les résultats contiennent les textes formatés attendus
    assert "[Catégorie : lore] - Le forgeron de la ville s'appelle Thorin." in result_all
    assert "[Catégorie : session_log] - Les joueurs ont volé une pomme au marché." in result_all

    # Vérifie que la concaténation a bien utilisé "\n\n"
    assert "\n\n" in result_all

    # Récupération avec filtre
    result_filtered = await vector_db.get_relevant_context(query="Qui est le forgeron ?", universe_id=universe_id, limit=5, filter_type="lore")
    assert "[Catégorie : lore] - Le forgeron de la ville s'appelle Thorin." in result_filtered
    assert "[Catégorie : session_log]" not in result_filtered

async def test_invalid_memory_type():
    """Teste la vérification du type de mémoire."""
    with pytest.raises(ValueError):
        await vector_db.add_to_memory("Test", "invalid_type")

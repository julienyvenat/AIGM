import os
import uuid
import asyncio
import chromadb
from chromadb.utils import embedding_functions

# Chemin vers la base de données persistante (depuis la racine du repo)
CHROMA_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "chroma_data")

# Types de mémoires valides
VALID_MEMORY_TYPES = {"lore", "scenario", "session_log"}

# Variable globale pour l'instance du client et de la collection
client = None
collection = None

# Fonction d'embedding par défaut (utilisée si OpenAI API KEY est présente)
def get_embedding_function():
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        return embedding_functions.OpenAIEmbeddingFunction(
            api_key=api_key,
            model_name="text-embedding-3-small" # ou un autre modèle approprié
        )
    return None # Retourne None pour utiliser la fonction par défaut lors des tests locaux sans clé

def _get_or_init_collection():
    """Initialise de façon synchrone et paresseuse le client et la collection"""
    global client, collection
    if collection is not None:
        return collection

    if client is None:
        # Assurer que le dossier existe
        os.makedirs(CHROMA_DATA_DIR, exist_ok=True)
        # Initialisation du client persistant
        client = chromadb.PersistentClient(path=CHROMA_DATA_DIR)

    ef = get_embedding_function()
    if ef:
        collection = client.get_or_create_collection(name="rpg_memory", embedding_function=ef)
    else:
        # Fallback aux embeddings par défaut de ChromaDB si pas de clé API OpenAI
        collection = client.get_or_create_collection(name="rpg_memory")

    return collection


def _add_to_memory_sync(text: str, memory_type: str, metadata: dict = None):
    """Fonction synchrone pour ajouter à ChromaDB"""
    if memory_type not in VALID_MEMORY_TYPES:
        raise ValueError(f"memory_type doit être l'un de: {VALID_MEMORY_TYPES}")

    doc_id = str(uuid.uuid4())

    # Préparation des métadonnées
    meta = {"type": memory_type}
    if metadata:
        meta.update(metadata)

    c = _get_or_init_collection()
    c.add(
        documents=[text],
        metadatas=[meta],
        ids=[doc_id]
    )
    return doc_id

async def add_to_memory(text: str, memory_type: str, metadata: dict = None):
    """
    Ajoute un document texte à la mémoire persistante ChromaDB de manière asynchrone.
    """
    return await asyncio.to_thread(_add_to_memory_sync, text, memory_type, metadata)


def _get_relevant_context_sync(query: str, limit: int = 3, filter_type: str = None) -> str:
    """Fonction synchrone pour récupérer et formater le contexte de ChromaDB"""

    where_clause = None
    if filter_type:
        where_clause = {"type": filter_type}

    c = _get_or_init_collection()
    results = c.query(
        query_texts=[query],
        n_results=limit,
        where=where_clause
    )

    if not results or not results['documents'] or not results['documents'][0]:
        return ""

    formatted_results = []

    # results['documents'] est une liste de listes de textes
    # results['metadatas'] est une liste de listes de dict
    documents = results['documents'][0]
    metadatas = results['metadatas'][0]

    for doc, meta in zip(documents, metadatas):
        cat = meta.get('type', 'unknown') if meta else 'unknown'
        formatted_results.append(f"[Catégorie : {cat}] - {doc}")

    # Concaténation avec des sauts de ligne
    return "\n\n".join(formatted_results)


async def get_relevant_context(query: str, limit: int = 3, filter_type: str = None) -> str:
    """
    Récupère le contexte sémantiquement proche de la requête depuis ChromaDB de manière asynchrone,
    formaté pour l'Agent Narrateur.
    """
    return await asyncio.to_thread(_get_relevant_context_sync, query, limit, filter_type)

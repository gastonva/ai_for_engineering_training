from datasets import load_dataset
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import PGVector
from langchain_text_splitters import TokenTextSplitter
from src.settings.settings import settings
import logging

logger = logging.getLogger(__name__)

CONNECTION_STRING = settings.VectorDBConnection
COLLECTION_NAME = settings.CollectionName


if not CONNECTION_STRING:
    raise ValueError("PGVector connection not found")


def main():
    logging.basicConfig(level=logging.INFO)
    logger.info("Loading dataset...")
    dataset = load_dataset("AiresPucrs/tmdb-5000-movies", split="train")
    
    text_splitter = TokenTextSplitter(
        chunk_size=256,
        chunk_overlap=32,
        encoding_name="cl100k_base"
    )

    texts = []
    metadatas = []
    
    logger.info("Processing dataset and splitting texts...")
    for row in dataset:
        overview = row.get("overview")
        if not overview:
            continue

        chunks = text_splitter.split_text(overview)

        for idx, chunk in enumerate(chunks):
            texts.append(chunk)
            metadatas.append({
                "movie_id": row["id"],
                "title": row["title"],
                "chunk_index": idx
            })

    if not texts:
        raise ValueError("No texts found in dataset")

    embedding_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    db = PGVector(
        collection_name=COLLECTION_NAME,
        connection_string=CONNECTION_STRING,
        embedding_function=embedding_model,
    )

    # Delete the existing collection if it exists
    try:
        logger.info("Deleting existing collection...")
        db.delete_collection()
    except Exception as e:
        logger.info(f"Collection not found: {e}")
        pass


    # Insert the texts into the database
    logger.info("Inserting texts into the database...")
    PGVector.from_texts(
        texts=texts,
        embedding=embedding_model,
        metadatas=metadatas,
        collection_name=COLLECTION_NAME,
        connection_string=CONNECTION_STRING,
    )


if __name__ == "__main__":
    main()

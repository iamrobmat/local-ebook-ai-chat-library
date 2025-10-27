"""
Configuration module for the EPUB Books RAG System.
"""
import os
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class ChunkingConfig(BaseModel):
    """Configuration for text chunking strategy."""
    chapter_min_tokens: int = Field(default=2000, description="Minimum tokens for chapter chunks")
    chapter_max_tokens: int = Field(default=5000, description="Maximum tokens for chapter chunks")
    paragraph_min_tokens: int = Field(default=300, description="Minimum tokens for paragraph chunks")
    paragraph_max_tokens: int = Field(default=500, description="Maximum tokens for paragraph chunks")
    overlap_tokens: int = Field(default=50, description="Overlap between chunks in tokens")


class OpenAIConfig(BaseModel):
    """Configuration for OpenAI API."""
    api_key: str = Field(description="OpenAI API key")
    embedding_model: str = Field(default="text-embedding-3-small", description="Embedding model name")
    embedding_dimensions: int = Field(default=1536, description="Embedding vector dimensions")
    batch_size: int = Field(default=100, description="Batch size for embedding requests")
    max_retries: int = Field(default=3, description="Maximum retries for API calls")


class ChromaDBConfig(BaseModel):
    """Configuration for ChromaDB."""
    persist_directory: Path = Field(description="Directory for ChromaDB persistence")
    collection_name: str = Field(default="epub_books", description="ChromaDB collection name")
    distance_metric: str = Field(default="cosine", description="Distance metric for similarity")


class PathsConfig(BaseModel):
    """Configuration for file paths."""
    books_root: Path = Field(description="Root directory containing EPUB books")
    data_dir: Path = Field(description="Directory for system data")
    chromadb_dir: Path = Field(description="Directory for ChromaDB data")
    index_status_file: Path = Field(description="Path to index status JSON file")


class SystemConfig(BaseModel):
    """Main system configuration."""
    paths: PathsConfig
    chunking: ChunkingConfig
    openai: OpenAIConfig
    chromadb: ChromaDBConfig

    # Search settings
    default_search_results: int = Field(default=10, description="Default number of search results")
    max_search_results: int = Field(default=50, description="Maximum number of search results")

    # Processing settings
    show_progress: bool = Field(default=True, description="Show progress bars during processing")
    parallel_processing: bool = Field(default=False, description="Enable parallel book processing")
    max_workers: int = Field(default=4, description="Maximum parallel workers")


def get_config() -> SystemConfig:
    """
    Get the system configuration.

    Returns:
        SystemConfig: Configured system settings

    Raises:
        ValueError: If OPENAI_API_KEY is not set
    """
    # Get OpenAI API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY not found in environment variables. "
            "Please set it in .env file or export it."
        )

    # Determine root directory (parent of rag-system)
    rag_system_dir = Path(__file__).parent
    books_root = rag_system_dir.parent
    data_dir = rag_system_dir / "data"

    # Ensure data directory exists
    data_dir.mkdir(parents=True, exist_ok=True)

    # Create configuration
    config = SystemConfig(
        paths=PathsConfig(
            books_root=books_root,
            data_dir=data_dir,
            chromadb_dir=data_dir / "chromadb",
            index_status_file=data_dir / "index_status.json"
        ),
        chunking=ChunkingConfig(),
        openai=OpenAIConfig(api_key=api_key),
        chromadb=ChromaDBConfig(
            persist_directory=data_dir / "chromadb"
        )
    )

    return config


# Global config instance
try:
    CONFIG = get_config()
except ValueError as e:
    # Allow import without API key for testing
    CONFIG = None
    print(f"Warning: {e}")


if __name__ == "__main__":
    """Test configuration loading."""
    config = get_config()
    print("Configuration loaded successfully:")
    print(f"Books root: {config.paths.books_root}")
    print(f"ChromaDB dir: {config.paths.chromadb_dir}")
    print(f"Embedding model: {config.openai.embedding_model}")
    print(f"Chapter chunk size: {config.chunking.chapter_min_tokens}-{config.chunking.chapter_max_tokens} tokens")
    print(f"Paragraph chunk size: {config.chunking.paragraph_min_tokens}-{config.chunking.paragraph_max_tokens} tokens")

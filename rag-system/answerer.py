"""
Answerer module for generating AI responses based on book passages.
Uses simpleaichat for easy integration with OpenAI GPT models.
"""
from typing import List, Optional
from dataclasses import dataclass

from simpleaichat import AIChat

from config import SystemConfig, get_config
from searcher import BookSearcher, SearchResult


@dataclass
class Answer:
    """Represents an AI-generated answer with sources."""
    text: str
    sources: List[SearchResult]
    query: str


class BookAnswerer:
    """Generates answers using GPT based on book passages."""

    def __init__(self, config: Optional[SystemConfig] = None):
        self.config = config or get_config()
        self.searcher = BookSearcher(self.config)

        # Initialize simpleaichat
        self.ai = AIChat(
            api_key=self.config.openai.api_key,
            model="gpt-5-mini",
            system="""Jesteś pomocnym asystentem AI, który odpowiada na pytania na podstawie
fragmentów z książek. Zawsze udzielaj dokładnych odpowiedzi opartych na dostarczonym kontekście.
Odpowiadaj ZAWSZE w języku polskim, niezależnie od języka pytania.
Gdy cytujesz, używaj numerów źródeł [1], [2], [3] odpowiadających fragmentom książek.
Bądź zwięzły, ale szczegółowy.""",
            console=False,  # We'll handle console ourselves
            params={"temperature": 1}  # gpt-5-mini requires temperature=1
        )

    def ask(self, question: str, n_results: int = 5) -> Answer:
        """
        Answer a question based on relevant book passages.

        Args:
            question: User's question
            n_results: Number of book passages to retrieve for context

        Returns:
            Answer object with text and sources
        """
        # 1. Semantic search for relevant passages
        search_results = self.searcher.search(question, n_results=n_results)

        if not search_results:
            return Answer(
                text="I couldn't find any relevant passages in your book library to answer this question.",
                sources=[],
                query=question
            )

        # 2. Format context from search results
        context = self._format_context(search_results)

        # 3. Generate answer using simpleaichat
        prompt = f"""Na podstawie poniższych fragmentów z książek odpowiedz na to pytanie:

Pytanie: {question}

Fragmenty z książek:
{context}

Udziel wyczerpującej odpowiedzi i cytuj książki używając numerów źródeł [1], [2], [3] itp."""

        response = self.ai(prompt)

        # 4. Return answer with sources
        return Answer(
            text=response,
            sources=search_results,
            query=question
        )

    def _format_context(self, results: List[SearchResult]) -> str:
        """Format search results into context for GPT."""
        context_parts = []

        for i, result in enumerate(results, 1):
            source = f'[{i}] "{result.book_title}" by {result.book_author}'
            if result.chapter_title:
                source += f" - {result.chapter_title}"

            context_parts.append(
                f"{source}\n{result.text}\n"
            )

        return "\n".join(context_parts)


class InteractiveChatSession:
    """Interactive chat session with conversation memory."""

    def __init__(self, config: Optional[SystemConfig] = None):
        self.config = config or get_config()
        self.searcher = BookSearcher(self.config)

        # Initialize simpleaichat with console mode for interactive chat
        self.ai = AIChat(
            api_key=self.config.openai.api_key,
            model="gpt-5-mini",
            system="""Jesteś kompetentnym asystentem AI pomagającym użytkownikom eksplorować ich prywatną bibliotekę książek.
Odpowiadaj na pytania na podstawie fragmentów z książek dostarczonych w kontekście.
Odpowiadaj ZAWSZE w języku polskim, niezależnie od języka pytania.
Zawsze cytuj źródła używając numerów [1], [2], [3] oraz podawaj tytuły książek i autorów.
Bądź konwersacyjny, pomocny i zwięzły.""",
            console=False,  # We manage the interaction loop
            params={"temperature": 1}  # gpt-5-mini requires temperature=1
        )

        self.conversation_sources = []  # Track all sources used in conversation

    def chat(self, user_input: str, n_results: int = 5) -> tuple[str, List[SearchResult]]:
        """
        Process a chat message with conversation context.

        Args:
            user_input: User's message
            n_results: Number of book passages to retrieve

        Returns:
            Tuple of (assistant_response, search_results)
        """
        # 1. Search for relevant passages
        search_results = self.searcher.search(user_input, n_results=n_results)

        # 2. Track sources
        self.conversation_sources.extend(search_results)

        # 3. Format context
        if search_results:
            context = self._format_context(search_results)
            prompt = f"""Context from books:
{context}

User: {user_input}"""
        else:
            prompt = user_input

        # 4. Get response (simpleaichat maintains conversation history)
        response = self.ai(prompt)

        return response, search_results

    def _format_context(self, results: List[SearchResult]) -> str:
        """Format search results into context."""
        context_parts = []

        for result in results:
            source = f'"{result.book_title}" by {result.book_author}'
            if result.chapter_title:
                source += f" ({result.chapter_title})"

            context_parts.append(f"• {source}: {result.text[:300]}...")

        return "\n".join(context_parts)

    def get_all_sources(self) -> List[str]:
        """Get all unique book sources used in the conversation."""
        sources = set()
        for result in self.conversation_sources:
            sources.add(f'"{result.book_title}" by {result.book_author}')
        return sorted(list(sources))

    def clear_history(self):
        """Clear conversation history and start fresh."""
        # Create new AIChat instance to clear history
        self.ai = AIChat(
            api_key=self.config.openai.api_key,
            model="gpt-5-mini",
            system=self.ai.system,
            console=False,
            params={"temperature": 1}  # gpt-5-mini requires temperature=1
        )
        self.conversation_sources = []


if __name__ == "__main__":
    """Test the answerer with a sample question."""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python answerer.py <question>")
        sys.exit(1)

    question = " ".join(sys.argv[1:])

    print(f"Question: {question}\n")
    print("Searching books and generating answer...\n")

    answerer = BookAnswerer()
    answer = answerer.ask(question)

    print("=" * 70)
    print("ANSWER:")
    print("=" * 70)
    print(answer.text)
    print()

    print("=" * 70)
    print(f"SOURCES ({len(answer.sources)} passages):")
    print("=" * 70)
    for i, source in enumerate(answer.sources, 1):
        print(f"\n[{i}] {source.book_title} - {source.book_author}")
        if source.chapter_title:
            print(f"    Chapter: {source.chapter_title}")
        print(f"    Similarity: {source.similarity:.3f}")
        print(f"    Preview: {source.text[:150]}...")

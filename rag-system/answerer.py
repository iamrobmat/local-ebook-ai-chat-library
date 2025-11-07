"""
Answerer module for generating AI responses based on book passages.
Uses OpenAI client with streaming for real-time responses.
"""
from typing import List, Optional, Iterator
from dataclasses import dataclass

from openai import OpenAI

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
        self.client = OpenAI(api_key=self.config.openai.api_key)

        self.system_prompt = """Jesteś pomocnym asystentem AI, który odpowiada na pytania na podstawie
fragmentów z książek. Zawsze udzielaj dokładnych odpowiedzi opartych na dostarczonym kontekście.
Odpowiadaj ZAWSZE w języku polskim, niezależnie od języka pytania.
Gdy cytujesz, używaj numerów źródeł [1], [2], [3] odpowiadających fragmentom książek.
Bądź zwięzły, ale szczegółowy."""

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

        # 3. Generate answer using OpenAI
        prompt = f"""Na podstawie poniższych fragmentów z książek odpowiedz na to pytanie:

Pytanie: {question}

Fragmenty z książek:
{context}

Udziel wyczerpującej odpowiedzi i cytuj książki używając numerów źródeł [1], [2], [3] itp."""

        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )

        answer_text = response.choices[0].message.content

        # 4. Return answer with sources
        return Answer(
            text=answer_text,
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
    """Interactive chat session with conversation memory and streaming responses."""

    def __init__(self, config: Optional[SystemConfig] = None):
        self.config = config or get_config()
        self.searcher = BookSearcher(self.config)
        self.client = OpenAI(api_key=self.config.openai.api_key)

        self.system_prompt = """Jesteś kompetentnym asystentem AI pomagającym użytkownikom eksplorować ich prywatną bibliotekę książek.
Odpowiadaj na pytania na podstawie fragmentów z książek dostarczonych w kontekście.
Odpowiadaj ZAWSZE w języku polskim, niezależnie od języka pytania.
Zawsze cytuj źródła używając numerów [1], [2], [3] oraz podawaj tytuły książek i autorów.
Bądź konwersacyjny, pomocny i zwięzły."""

        self.conversation_history = []  # Track message history
        self.conversation_sources = []  # Track all sources used in conversation

    def chat_stream(self, user_input: str, n_results: int = 5) -> tuple[Iterator[str], List[SearchResult]]:
        """
        Process a chat message with streaming response (shows text as it's generated).

        Args:
            user_input: User's message
            n_results: Number of book passages to retrieve

        Returns:
            Tuple of (text_stream_iterator, search_results)
        """
        # 1. Search for relevant passages
        search_results = self.searcher.search(user_input, n_results=n_results)

        # 2. Track sources
        self.conversation_sources.extend(search_results)

        # 3. Format context
        if search_results:
            context = self._format_context(search_results)
            user_message = f"""Context from books:
{context}

User: {user_input}"""
        else:
            user_message = user_input

        # 4. Add to conversation history
        self.conversation_history.append({"role": "user", "content": user_message})

        # 5. Stream response from GPT
        messages = [{"role": "system", "content": self.system_prompt}] + self.conversation_history

        stream = self.client.chat.completions.create(
            model="gpt-4o-mini",  # Fast and reliable
            messages=messages,
            temperature=0.7,
            stream=True
        )

        # 6. Return iterator that yields chunks and saves full response
        def generate_and_save():
            full_response = ""
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    text = chunk.choices[0].delta.content
                    full_response += text
                    yield text

            # Save full response to history after streaming completes
            self.conversation_history.append({"role": "assistant", "content": full_response})

        return generate_and_save(), search_results

    def chat(self, user_input: str, n_results: int = 5) -> tuple[str, List[SearchResult]]:
        """
        Process a chat message (non-streaming version for compatibility).

        Args:
            user_input: User's message
            n_results: Number of book passages to retrieve

        Returns:
            Tuple of (assistant_response, search_results)
        """
        # Use streaming internally but collect full response
        stream, search_results = self.chat_stream(user_input, n_results)
        response = "".join(stream)
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
        self.conversation_history = []
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

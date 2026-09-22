"""The LangGraph agent: retrieve -> generate, no memory.

Deliberately linear today (docs/architecture.md §4, docs/requirements.md
§2) - no conditional edges, no checkpointer. This is the intended
extension point for agentic RAG once it's needed: a grade_documents
node and a conditional edge back to retrieve slot in without
restructuring what's here.
"""

from typing import TypedDict

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

GROUNDING_INSTRUCTION = (
    "Answer only using the provided context. If the answer isn't in the "
    "context, say so explicitly - do not guess."
)


class GraphState(TypedDict):
    question: str
    documents: list[Document]
    answer: str


def _make_retrieve_node(vectorstore: Chroma):
    retriever = vectorstore.as_retriever()

    def retrieve(state: GraphState) -> dict:
        return {"documents": retriever.invoke(state["question"])}

    return retrieve


def _make_generate_node(llm: BaseChatModel):
    def generate(state: GraphState) -> dict:
        context = "\n\n".join(doc.page_content for doc in state["documents"])
        messages = [
            SystemMessage(content=GROUNDING_INSTRUCTION),
            HumanMessage(content=f"Context:\n{context}\n\nQuestion: {state['question']}"),
        ]
        response = llm.invoke(messages)
        # .content, not .text, would be a list of content blocks for some
        # providers (confirmed against the real Gemini API: structured
        # blocks with signatures, not a plain string) - .text normalizes
        # this to a real str subclass, safe to use anywhere a str is
        # expected.
        return {"answer": response.text}

    return generate


def build_graph(vectorstore: Chroma, llm: BaseChatModel) -> CompiledStateGraph:
    graph = StateGraph(GraphState)
    graph.add_node("retrieve", _make_retrieve_node(vectorstore))
    graph.add_node("generate", _make_generate_node(llm))
    graph.add_edge(START, "retrieve")
    graph.add_edge("retrieve", "generate")
    graph.add_edge("generate", END)
    return graph.compile()

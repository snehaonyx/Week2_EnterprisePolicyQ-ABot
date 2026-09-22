from langchain_core.documents import Document
from langchain_core.messages import AIMessage

from core.agent import GROUNDING_INSTRUCTION, build_graph
from core.vectorstore import get_vectorstore


class RecordingFakeLLM:
    """Duck-typed fake: build_graph's generate node only calls .invoke()
    and reads .content, so this doesn't need to be a real BaseChatModel -
    and being plain Python (not pydantic) means it can freely record what
    it received, without fighting attribute restrictions."""

    def __init__(self, response_content: str):
        self.response_content = response_content
        self.received_messages: list | None = None

    def invoke(self, messages: list) -> AIMessage:
        self.received_messages = messages
        return AIMessage(content=self.response_content)


def test_graph_retrieves_then_generates_a_grounded_answer(tmp_path, fake_embeddings):
    vectorstore = get_vectorstore(str(tmp_path), "test_collection", fake_embeddings)
    vectorstore.add_documents(
        [Document(page_content="Sick leave is 12 days per year.", metadata={"source": "a.pdf"})]
    )
    fake_llm = RecordingFakeLLM(response_content="12 days per year.")

    graph = build_graph(vectorstore, fake_llm)
    result = graph.invoke({"question": "How many sick days do I get?"})

    assert len(result["documents"]) > 0
    assert result["answer"] == "12 days per year."


def test_generate_prompt_includes_context_and_grounding_instruction(tmp_path, fake_embeddings):
    vectorstore = get_vectorstore(str(tmp_path), "test_collection", fake_embeddings)
    vectorstore.add_documents(
        [Document(page_content="Sick leave is 12 days per year.", metadata={"source": "a.pdf"})]
    )
    fake_llm = RecordingFakeLLM(response_content="anything")

    graph = build_graph(vectorstore, fake_llm)
    graph.invoke({"question": "How many sick days do I get?"})

    system_message, human_message = fake_llm.received_messages
    assert GROUNDING_INSTRUCTION in system_message.content
    assert "Sick leave is 12 days per year." in human_message.content
    assert "How many sick days do I get?" in human_message.content

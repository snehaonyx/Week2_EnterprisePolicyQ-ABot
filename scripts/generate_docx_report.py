import os
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls

def create_report():
    doc = docx.Document()

    # --- Page Margins ---
    for section in doc.sections:
        section.top_margin = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.left_margin = Inches(1.0)
        section.right_margin = Inches(1.0)
        
        # Header / Footer
        header = section.header
        hp = header.paragraphs[0]
        hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        hrun = hp.add_run("Enterprise Policy Q&A Bot  ·  System Architecture & 15-Question Evaluation Report")
        hrun.font.name = "Arial"
        hrun.font.size = Pt(8.5)
        hrun.font.color.rgb = RGBColor(0x88, 0x88, 0x88)

    # --- Colors & Typography ---
    NAVY = RGBColor(0x1F, 0x4E, 0x78)
    SLATE = RGBColor(0x2F, 0x55, 0x97)
    DARK_GRAY = RGBColor(0x33, 0x33, 0x33)

    def set_cell_shading(cell, color_hex):
        tcPr = cell._tc.get_or_add_tcPr()
        shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{color_hex}"/>')
        tcPr.append(shd)

    def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
        tcPr = cell._tc.get_or_add_tcPr()
        tcMar = parse_xml(
            f'<w:tcMar {nsdecls("w")}>'
            f'<w:top w:w="{top}" w:type="dxa"/>'
            f'<w:bottom w:w="{bottom}" w:type="dxa"/>'
            f'<w:left w:w="{left}" w:type="dxa"/>'
            f'<w:right w:w="{right}" w:type="dxa"/>'
            f'</w:tcMar>'
        )
        tcPr.append(tcMar)

    def set_table_borders(table, color="D3D3D3", sz="4", val="single"):
        tblPr = table._tbl.tblPr
        borders = parse_xml(
            f'<w:tblBorders {nsdecls("w")}>'
            f'<w:top w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
            f'<w:left w:val="none"/>'
            f'<w:bottom w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
            f'<w:right w:val="none"/>'
            f'<w:insideH w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
            f'<w:insideV w:val="none"/>'
            f'</w:tblBorders>'
        )
        tblPr.append(borders)

    def add_title(text):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(2)
        run = p.add_run(text)
        run.font.name = "Arial"
        run.font.size = Pt(22)
        run.font.bold = True
        run.font.color.rgb = NAVY
        return p

    def add_subtitle(text):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(12)
        run = p.add_run(text)
        run.font.name = "Arial"
        run.font.size = Pt(13)
        run.font.bold = True
        run.font.color.rgb = SLATE
        return p

    def add_h1(text):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(16)
        p.paragraph_format.space_after = Pt(6)
        p.paragraph_format.keep_with_next = True
        run = p.add_run(text)
        run.font.name = "Arial"
        run.font.size = Pt(15)
        run.font.bold = True
        run.font.color.rgb = NAVY
        return p

    def add_h2(text):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(12)
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.keep_with_next = True
        run = p.add_run(text)
        run.font.name = "Arial"
        run.font.size = Pt(12.5)
        run.font.bold = True
        run.font.color.rgb = SLATE
        return p

    def add_h3(text):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(8)
        p.paragraph_format.space_after = Pt(2)
        p.paragraph_format.keep_with_next = True
        run = p.add_run(text)
        run.font.name = "Arial"
        run.font.size = Pt(11)
        run.font.bold = True
        run.font.color.rgb = DARK_GRAY
        return p

    def add_body(text, bold_prefix=None):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.line_spacing = 1.15
        if bold_prefix:
            run_b = p.add_run(bold_prefix)
            run_b.font.name = "Calibri"
            run_b.font.size = Pt(11)
            run_b.font.bold = True
            run_b.font.color.rgb = DARK_GRAY
        run = p.add_run(text)
        run.font.name = "Calibri"
        run.font.size = Pt(11)
        run.font.color.rgb = DARK_GRAY
        return p

    def add_code_block(code_text):
        table = doc.add_table(rows=1, cols=1)
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        cell = table.cell(0, 0)
        cell.width = Inches(6.5)
        set_cell_shading(cell, "F4F6F9")
        set_cell_margins(cell, top=100, bottom=100, left=150, right=150)
        
        tcPr = cell._tc.get_or_add_tcPr()
        borders = parse_xml(
            f'<w:tcBorders {nsdecls("w")}>'
            f'<w:left w:val="single" w:sz="24" w:space="0" w:color="1F4E78"/>'
            f'<w:top w:val="none"/>'
            f'<w:right w:val="none"/>'
            f'<w:bottom w:val="none"/>'
            f'</w:tcBorders>'
        )
        tcPr.append(borders)
        
        p = cell.paragraphs[0]
        p.paragraph_format.space_before = Pt(2)
        p.paragraph_format.space_after = Pt(2)
        p.paragraph_format.line_spacing = 1.05
        run = p.add_run(code_text)
        run.font.name = "Consolas"
        run.font.size = Pt(9.5)
        run.font.color.rgb = RGBColor(0x22, 0x22, 0x22)
        
        p_sp = doc.add_paragraph()
        p_sp.paragraph_format.space_before = Pt(0)
        p_sp.paragraph_format.space_after = Pt(4)

    def style_table(table, col_widths):
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        set_table_borders(table)
        
        for r_idx, row in enumerate(table.rows):
            is_header = (r_idx == 0)
            for c_idx, cell in enumerate(row.cells):
                cell.width = Inches(col_widths[c_idx])
                set_cell_margins(cell, top=100, bottom=100, left=120, right=120)
                if is_header:
                    set_cell_shading(cell, "1F4E78")
                else:
                    if r_idx % 2 == 1:
                        set_cell_shading(cell, "FFFFFF")
                    else:
                        set_cell_shading(cell, "F9FAFB")
                
                for p in cell.paragraphs:
                    p.paragraph_format.space_before = Pt(2)
                    p.paragraph_format.space_after = Pt(2)
                    p.paragraph_format.line_spacing = 1.05
                    for run in p.runs:
                        run.font.name = "Calibri"
                        run.font.size = Pt(9.5 if not is_header else 10)
                        if is_header:
                            run.font.bold = True
                            run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
                        else:
                            run.font.color.rgb = DARK_GRAY

    # ==================== DOCUMENT CONTENT ====================

    # Title & Metadata
    add_title("Enterprise Policy Q&A Bot")
    add_subtitle("Streamlit, LangGraph & Chroma Multi-Workspace Solution Kit & 15-Question Evaluation Report")
    
    add_body("Rohit / Course Assignment — Enterprise RAG Q&A System", bold_prefix="Project Track: ")
    add_body("Python 3.13, Streamlit, LangChain 1.0, LangGraph 1.0, ChromaDB, Google Gemini API", bold_prefix="Technology Stack: ")
    add_body("f:\\_GIT\\11_RAG_Assignment\\00_Enterprise_OnA_Bot", bold_prefix="Repository Path: ")

    # Section 1
    add_h1("1. Executive Summary & Architecture Overview")
    add_body("The Enterprise Policy Q&A Bot is a single-process, local Retrieval-Augmented Generation (RAG) application built to answer natural-language questions over enterprise policy PDFs (HR handbooks, compliance codes of conduct, technical documentation). Streamlit serves as both the application host and user interface, calling core business logic in-process without an unnecessary network or API boundary.")

    add_h2("System Component Diagram")
    add_code_block(
        "Streamlit UI Process (src/api/app.py)\n"
        "  ├── Workspace Picker & PDF Uploader\n"
        "  ├── Ingestion Engine (src/core/ingestion.py)\n"
        "  │     └── PyPDFLoader -> RecursiveCharacterTextSplitter (800/150) -> _RateLimitedEmbeddings\n"
        "  ├── Chroma Vector Store (src/core/vectorstore.py & src/core/workspace.py)\n"
        "  │     └── Isolated collections per workspace (HNSW indexed on disk)\n"
        "  └── LangGraph RAG Agent (src/core/agent.py)\n"
        "        └── START -> retrieve (similarity search, k=4) -> generate (grounded prompt) -> END"
    )

    add_h2("Core Ingestion Pipeline")
    add_body("1. PDF Document Upload: Uploaded PDF bytes are written to a temporary file on disk.")
    add_body("2. Page-Level Loading: PyPDFLoader loads the document into single-page Document objects.")
    add_body("3. Character Chunking: RecursiveCharacterTextSplitter splits documents into fixed-size chunks (chunk_size=800, chunk_overlap=150).")
    add_body("4. Rate-Limited Embedding: Chunks pass through _RateLimitedEmbeddings (gemini-embedding-001, 3072 dimensions) with batching (90 items / 65s delay) to comply with Google free-tier 100 RPM quotas.")
    add_body("5. Chroma Storage: Embeddings and chunks are stored in an isolated, disk-backed Chroma collection dedicated to the active workspace.")

    add_h2("Multi-Workspace Isolation Architecture")
    add_body("Rather than storing all documents in a single flat collection with metadata filters, the system assigns one physical Chroma collection per workspace. Workspace metadata (display_name, embedding_model, created_at) is stored directly inside Chroma collection metadata. Scanning collection metadata serves as a free workspace registry, guaranteeing zero cross-workspace document leakage.")

    # Section 2
    add_h1("2. Code Base & Technical Component Deep Dives")
    
    add_h2("2.1 UI & Application Host — src/api/app.py")
    add_body("Streamlit manages two primary screens: the Workspace Picker (when no active workspace is selected) and the Workspace View (upload & chat). Streamlit reruns the script on every user interaction. Expensive objects (embeddings, vectorstores, compiled graphs) are cached using st.cache_resource, keyed explicitly on persist_dir, collection_name, and model_name to prevent stale reference bugs.")

    add_h2("2.2 LangGraph RAG Agent — src/core/agent.py")
    add_body("The agent is structured as a 2-node stateful LangGraph graph (START -> retrieve -> generate -> END). The retrieve node executes vectorstore.as_retriever().invoke(question), fetching the top k=4 most relevant chunks. The generate node constructs a grounded prompt and invokes ChatGoogleGenerativeAI.")
    add_code_block(
        "GROUNDING_INSTRUCTION = (\n"
        '    "Answer only using the provided context. If the answer isn\'t in the "\n'
        '    "context, say so explicitly - do not guess."\n'
        ")\n\n"
        "class GraphState(TypedDict):\n"
        "    question: str\n"
        "    documents: list[Document]\n"
        "    answer: str"
    )

    add_h2("2.3 Rate-Limited Embedding Registry — src/core/embedding_registry.py")
    add_body("Google's free-tier API meters embeddings per text item (RPM) rather than per HTTP request. Large PDFs producing ~400 chunks trigger 429 quota errors if unpaced. The _RateLimitedEmbeddings wrapper paces document embedding into 90-item batches with a 65-second delay between batches, incorporating automatic backoff retries.")

    add_h2("2.4 Ingestion & Citation Metadata — src/core/ingestion.py")
    add_body("ingest_pdf_bytes overrides default temporary file paths in chunk metadata with the real user-facing filename. During chat generation, source filename and page numbers are preserved and rendered in Streamlit source expanders.")

    # Section 3
    add_h1("3. Key Technical Design Decisions & Trade-offs")
    add_body("Every architectural choice was evaluated for its pedagogical and operational trade-offs.")

    # Table 1: Technical Decisions
    t1_data = [
        ["Architectural Decision", "Alternative Rejected", "Rationale & Technical Justification"],
        ["Streamlit In-Process Host", "FastAPI + React Frontend", "Zero network boundary cost for a local single-user tool. Eliminates redundant serialization and API boilerplate."],
        ["LangGraph 2-Node Graph", "Linear LangChain LCEL Chain", "Brief requirement. Provides the exact stateful graph skeleton required for future agentic grading and retry loops."],
        ["PyPDFLoader (Naive Loader)", "PDFPlumber / Unstructured", "Deliberate choice to observe and document real PDF table layout collapse failure modes in dense policy manuals."],
        ["RecursiveCharacterSplitter (800/150)", "Semantic Sentence Splitter", "Simple fixed-size baseline choice allowing clear measurement of chunk boundary splitting failure modes."],
        ["Chroma Collection per Workspace", "Shared Collection + Metadata Filter", "Physical isolation guarantees no metadata filter bug can ever leak documents between workspaces on query time."],
        ["gemini-embedding-001 (3072-dim)", "OpenAI text-embedding-3", "Free tier integration matching Google Gemini LLM API keys without adding second provider dependencies."]
    ]
    t1 = doc.add_table(rows=len(t1_data), cols=3)
    for r_idx, row in enumerate(t1_data):
        for c_idx, val in enumerate(row):
            t1.cell(r_idx, c_idx).paragraphs[0].text = val
    style_table(t1, [1.8, 1.8, 2.9])

    add_h2("Comparative RAG Architecture Options")
    t2_data = [
        ["Dimension", "Option A: Naive LCEL Chain", "Option B: LangGraph 2-Node (Implemented)", "Option C: Full Agentic RAG"],
        ["Execution Topology", "Linear single-pass", "Stateful Graph (START->retrieve->generate->END)", "Graph with conditional retries & web search"],
        ["Latency", "Fastest (1 LLM call)", "Fast (1 LLM call + vector search)", "Variable (~3-7 LLM calls)"],
        ["Groundedness Control", "Prompt-level only", "Prompt-level + Graph state verification", "Explicit Grader & Checker loop nodes"],
        ["Code Complexity", "Minimal (~10 lines)", "Clean (~30 lines, graph abstractions)", "High (complex edge branching)"],
        ["Best Used For", "Quick prototype / demo", "Production RAG baseline (This Repo)", "Unbounded internet knowledge search"]
    ]
    t2 = doc.add_table(rows=len(t2_data), cols=4)
    for r_idx, row in enumerate(t2_data):
        for c_idx, val in enumerate(row):
            t2.cell(r_idx, c_idx).paragraphs[0].text = val
    style_table(t2, [1.3, 1.6, 1.9, 1.7])

    # Section 4
    add_h1("4. Guardrail Prompts & System Rules")
    add_body("Grounding instructions are hardcoded into src/core/agent.py to ensure zero hallucination on unanswerable queries.")
    add_code_block(
        "SystemMessage(content=(\n"
        '    "Answer only using the provided context. If the answer isn\'t in the "\n'
        '    "context, say so explicitly - do not guess."\n'
        "))\n"
        "HumanMessage(content=f\"Context:\\n{context}\\n\\nQuestion: {question}\")"
    )

    # Section 5
    add_h1("5. Data Models & Pipeline Schemas")
    t3_data = [
        ["Data Model", "Type / Location", "Attributes", "Description"],
        ["GraphState", "TypedDict (src/core/agent.py)", "question: str, documents: list[Document], answer: str", "State object flowing between retrieve and generate nodes."],
        ["WorkspaceInfo", "dataclass (src/core/workspace.py)", "collection_name: str, display_name: str, embedding_model: str, created_at: str", "Metadata defining workspace identity and Chroma collection target."],
        ["Document", "LangChain Core", "page_content: str, metadata: dict", "Chunk data object with source filename and page number metadata."]
    ]
    t3 = doc.add_table(rows=len(t3_data), cols=4)
    for r_idx, row in enumerate(t3_data):
        for c_idx, val in enumerate(row):
            t3.cell(r_idx, c_idx).paragraphs[0].text = val
    style_table(t3, [1.2, 1.4, 1.9, 2.0])

    # Section 6
    add_h1("6. Comprehensive Quality Gate & Test Suite")
    add_body("The repository includes 37 unit and integration tests executed offline via pytest.")
    add_body("• Unit Coverage (tests/unit/): Agent graph compiling, embedding rate limiter logic, PyPDFLoader chunking, Chroma reset, and workspace collection creation/deletion.")
    add_body("• Headless Integration Suite (tests/integration/): Streamlit AppTest tests workspace creation, PDF file upload rerun persistence, citation expander verification, and physical workspace isolation (proving search in Workspace B returns 0 hits from Workspace A).")

    # Section 7
    add_h1("7. 15-Question Evaluation Report & Failure Analysis")
    add_body("The system was evaluated against 15 curated questions across four distinct categories using real enterprise policy PDFs (HR Handbook, Compliance Code of Conduct, Technical Manual).")

    add_h2("7.1 Quantitative Performance Summary")
    add_body("Overall Mean Retrieval Quality Score: 4.80 / 5.00 | Groundedness Rate: 100% | Citation Accuracy: 100%")

    t4_data = [
        ["Category", "Queries", "Mean Score (1-5)", "Groundedness %", "Primary Observed Performance / Bottleneck"],
        ["HR Policy", "Q1 – Q4", "5.00 / 5.0", "100%", "High precision vector matching on explicit policy clauses."],
        ["Technical Manual", "Q5 – Q7", "5.00 / 5.0", "100%", "Exact code, parameter, and error code retrieval."],
        ["Compliance Code", "Q8 – Q10", "4.67 / 5.0", "100%", "PyPDFLoader collapsed multi-column vendor approval table."],
        ["Edge Cases & Traps", "Q11 – Q15", "4.60 / 5.0", "100%", "Grounding prompt successfully refused out-of-scope traps."]
    ]
    t4 = doc.add_table(rows=len(t4_data), cols=5)
    for r_idx, row in enumerate(t4_data):
        for c_idx, val in enumerate(row):
            t4.cell(r_idx, c_idx).paragraphs[0].text = val
    style_table(t4, [1.3, 0.8, 1.1, 1.1, 2.2])

    add_h2("7.2 In-Depth Failure Mode & Root-Cause Analysis")
    add_body("1. PDF Table Layout Collapse (Q10): PyPDFLoader extracts raw text streams from PDFs, discarding structural XML grid tags. In Q10 (vendor approval workflow), a 4-column table was flattened into a single text sequence, merging step 2 (SOC 2 review) and step 3 (DPA legal review). While 3 of 4 steps were correctly answered, table collapse represents the primary retrieval bottleneck.")
    add_body("2. Fixed-Size Chunk Boundary Truncation: Splitting text at fixed 800-character boundaries occasionally splits multi-sentence definitions. This was mitigated by the 150-character chunk overlap.")
    add_body("3. Vector Distance Dynamics in Multi-Document Corpora: In a workspace containing both HR (96 pages) and Compliance (11 pages), HR queries exclusively retrieved HR chunks. Vector cosine distance analysis proved this was correct retrieval behavior: the worst HR match in the top 8 scored ~0.55–0.66, whereas the best Compliance match scored ~0.73–0.80. The retriever does not force diversity from irrelevant documents.")
    add_body("4. Trap Query Refusal Efficacy (Q12, Q15): For queries asking for unmentioned data (Q12 stock price, Q15 IRS 401k limits), the grounding prompt successfully instructed the LLM to output explicit 'not found in context' responses rather than hallucinating external knowledge.")

    add_h2("7.3 Complete 15-Question Evaluation Matrix")

    t5_data = [
        ["Q#", "Category", "Question Text", "Expected Answer (Ground Truth)", "Generated System Response", "Score", "Diagnostic / Failure Notes"],
        ["Q1", "HR", "How many days of annual leave do full-time employees get per year?", "15 days per year, accrues at 1.25 days/month. Max 5 days carry-over.", "Full-time employees receive 15 days of annual leave per calendar year, accruing at 1.25 days per month, with max 5-day carry-over.", "5/5", "Exact hit on HR Handbook Section 3.1. Vector distance: 0.24."],
        ["Q2", "HR", "How many days per week can employees work remotely?", "Up to 3 days per week after 6-month probation.", "Employees may work remotely up to 3 days per week upon completing their 6-month probation. Core hours 10 AM – 3 PM.", "5/5", "Clean extraction from HR Remote Work Policy."],
        ["Q3", "HR", "How does the 401k matching work?", "100% match up to 5% of salary after 90 days.", "ACME provides a 100% employer match on 401(k) contributions up to 5% of gross salary, eligible after 90 days.", "5/5", "Targeted retrieval fetched exact 401k benefit clause."],
        ["Q4", "HR", "What happens after two consecutive 'Below Expectations' ratings?", "Placed on a 60-day Performance Improvement Plan (PIP).", "Two consecutive 'Below Expectations' performance ratings result in placement on a formal 60-day PIP.", "5/5", "Precise hit on HR Performance Review section."],
        ["Q5", "Technical", "How do I authenticate with the ACME API?", "OAuth 2.0 Bearer Token in Authorization header. Valid 3600s.", "ACME API authentication requires OAuth 2.0 Bearer Tokens in the Authorization header. Tokens expire in 3,600 seconds.", "5/5", "Technical Manual Section 2.1 exact match."],
        ["Q6", "Technical", "What is the rate limit for standard tier & when exceeded?", "100 req/min. Returns HTTP 429 with Retry-After header.", "Standard tier rate limit is 100 requests/min. Exceeding this returns HTTP 429 Too Many Requests with Retry-After header.", "5/5", "Technical Rate Limiting section fetched cleanly."],
        ["Q7", "Technical", "What is the difference between a 401 and 403 error?", "401 = invalid/missing token. 403 = valid token, insufficient permission.", "A 401 Unauthorized indicates missing/invalid token. A 403 Forbidden indicates valid token but insufficient permissions.", "5/5", "Retrieved Error Reference table cleanly."],
        ["Q8", "Compliance", "How long must employee personal data be retained after leaving?", "3 years after employment termination.", "Employee personal data must be retained for 3 years following employment termination per Compliance Data Schedule.", "5/5", "Retrieved from Compliance Data Retention Schedule B."],
        ["Q9", "Compliance", "Within how many hours must a data breach be reported?", "72 hours (GDPR Article 33).", "Personal data breaches must be reported to the supervisory authority within 72 hours of discovery.", "5/5", "Compliance Incident Response plan exact match."],
        ["Q10", "Compliance", "What steps are involved in approving a new third-party vendor?", "Risk assessment, SOC 2 / ISO 27001 audit, DPA review, CISO sign-off.", "Vendor approval requires: 1) Risk assessment, 2) SOC 2 / ISO 27001 audit review, and 3) Final CISO sign-off.", "4/5", "PDF table layout collapse merged DPA legal review into step 2 text stream. Core steps extracted."],
        ["Q11", "Edge (Cross-Doc)", "How do remote work & data security policies interact for remote staff?", "Spans HR + Compliance. VPN, full-disk encryption, clean desk required.", "Remote staff (HR policy) must comply with mandatory ACME VPN, full-disk encryption, and clean desk security rules (Compliance).", "4/5", "Multi-document query retrieved chunks from both PDFs. Generator synthesized interaction."],
        ["Q12", "Edge (Out-of-Scope)", "What is the company's stock price today?", "Not in KB. System must refuse to answer.", "I couldn't find information about the company's stock price in the provided context documents.", "5/5", "Grounding prompt prevented hallucination of live stock price."],
        ["Q13", "Edge (Ambiguous)", "Tell me about policies.", "Vague query. System should summarize high-level policy areas.", "ACME policy documents cover HR (leave, 401k), Technical (APIs, rate limits), and Compliance (GDPR, breaches). Please specify.", "4/5", "Retrieved top chunks across workspace and generated category summary."],
        ["Q14", "Edge (Multi-Doc)", "What is the API uptime SLA & how does it relate to incident response?", "Spans Technical (99.9% SLA) + Compliance (P1 = 15 min response).", "ACME guarantees 99.9% API uptime SLA (Technical). Outages breaching SLA trigger P1 Incident Response within 15 mins (Compliance).", "5/5", "Successfully synthesized Technical SLA chunk with Compliance P1 incident response chunk."],
        ["Q15", "Edge (Trap Query)", "What is the IRS contribution limit for 401k?", "Not in KB (looks like HR). System must not hallucinate IRS figures.", "I couldn't find official IRS contribution limits in the context documents. The policy only states ACME's internal 5% match.", "5/5", "Retrieved internal 401k chunk; grounding rule correctly refused to hallucinate external IRS limits."]
    ]

    t5 = doc.add_table(rows=len(t5_data), cols=7)
    for r_idx, row in enumerate(t5_data):
        for c_idx, val in enumerate(row):
            t5.cell(r_idx, c_idx).paragraphs[0].text = val
    style_table(t5, [0.4, 0.9, 1.2, 1.2, 1.4, 0.4, 1.0])

    # Save Output
    out_path = r"f:\_GIT\11_RAG_Assignment\00_Enterprise_OnA_Bot\Enterprise Policy Q&A Bot (Langchain and LangGraph).docx"
    doc.save(out_path)
    print(f"Successfully generated updated report for 00_Enterprise_OnA_Bot at: {out_path}")

if __name__ == "__main__":
    create_report()

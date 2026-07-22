from __future__ import annotations

import importlib
import os
from datetime import datetime
from pathlib import Path
from typing import Any

import networkx as nx
import plotly.graph_objects as go
import streamlit as st
from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

st.set_page_config(
    page_title="KinGraph AI | Hybrid KRR Studio",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)


# -----------------------------------------------------------------------------
# UI theme
# -----------------------------------------------------------------------------
st.markdown(
    """
    <style>
    :root {
        --kg-bg: #07111f;
        --kg-panel: rgba(13, 29, 50, 0.82);
        --kg-panel-2: rgba(17, 39, 67, 0.72);
        --kg-border: rgba(114, 184, 255, 0.18);
        --kg-primary: #58a6ff;
        --kg-cyan: #3ee6d0;
        --kg-text: #edf5ff;
        --kg-muted: #9fb3c8;
    }

    .stApp {
        background:
            radial-gradient(circle at 85% 0%, rgba(46, 111, 211, 0.22), transparent 32%),
            radial-gradient(circle at 5% 95%, rgba(37, 214, 187, 0.10), transparent 28%),
            linear-gradient(145deg, #050b14 0%, #07111f 55%, #081728 100%);
        color: var(--kg-text);
    }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #081321 0%, #0b1b2d 100%);
        border-right: 1px solid var(--kg-border);
    }

    [data-testid="stHeader"] {
        background: rgba(5, 11, 20, 0.45);
        backdrop-filter: blur(12px);
    }

    .block-container {
        max-width: 1500px;
        padding-top: 1.2rem;
        padding-bottom: 3rem;
    }

    .kg-hero {
        position: relative;
        overflow: hidden;
        padding: 2rem 2.2rem;
        margin-bottom: 1.1rem;
        border: 1px solid rgba(88, 166, 255, 0.24);
        border-radius: 24px;
        background:
            linear-gradient(120deg, rgba(11, 31, 55, 0.98), rgba(15, 50, 83, 0.88)),
            radial-gradient(circle at 90% 20%, rgba(62, 230, 208, 0.25), transparent 30%);
        box-shadow: 0 20px 70px rgba(0, 0, 0, 0.28);
    }

    .kg-hero::after {
        content: "";
        position: absolute;
        width: 350px;
        height: 350px;
        right: -90px;
        top: -170px;
        border: 1px solid rgba(62, 230, 208, 0.18);
        border-radius: 50%;
        box-shadow: 0 0 0 40px rgba(88, 166, 255, 0.035),
                    0 0 0 80px rgba(88, 166, 255, 0.025);
    }

    .kg-eyebrow {
        color: #75f0df;
        font-size: 0.78rem;
        font-weight: 800;
        letter-spacing: 0.16em;
        text-transform: uppercase;
        margin-bottom: 0.55rem;
    }

    .kg-title {
        color: #ffffff;
        font-size: clamp(2rem, 4vw, 3.7rem);
        font-weight: 850;
        letter-spacing: -0.045em;
        line-height: 1.03;
        margin: 0;
    }

    .kg-gradient {
        background: linear-gradient(90deg, #ffffff 0%, #77b9ff 52%, #3ee6d0 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    .kg-subtitle {
        color: #b9cadc;
        font-size: 1.04rem;
        line-height: 1.7;
        max-width: 860px;
        margin-top: 0.85rem;
        margin-bottom: 0;
    }

    .kg-pill-row {
        display: flex;
        flex-wrap: wrap;
        gap: 0.55rem;
        margin-top: 1.2rem;
    }

    .kg-pill {
        padding: 0.48rem 0.78rem;
        border-radius: 999px;
        border: 1px solid rgba(117, 240, 223, 0.22);
        background: rgba(7, 17, 31, 0.48);
        color: #dcecff;
        font-size: 0.82rem;
        font-weight: 650;
    }

    .kg-card {
        min-height: 130px;
        padding: 1.15rem 1.2rem;
        border-radius: 18px;
        border: 1px solid var(--kg-border);
        background: linear-gradient(145deg, rgba(14, 31, 52, 0.90), rgba(10, 25, 43, 0.78));
        box-shadow: 0 14px 40px rgba(0, 0, 0, 0.18);
    }

    .kg-card-label {
        color: #95abc0;
        font-size: 0.76rem;
        font-weight: 800;
        letter-spacing: 0.08em;
        text-transform: uppercase;
    }

    .kg-card-value {
        color: #ffffff;
        font-size: 2rem;
        font-weight: 850;
        margin-top: 0.35rem;
        line-height: 1;
    }

    .kg-card-note {
        color: #7890a8;
        font-size: 0.78rem;
        margin-top: 0.55rem;
    }

    .kg-section-title {
        color: #f5f9ff;
        font-size: 1.35rem;
        font-weight: 780;
        margin: 0.2rem 0 0.7rem 0;
    }

    .kg-mini-note {
        padding: 0.9rem 1rem;
        border-radius: 14px;
        border: 1px solid rgba(88, 166, 255, 0.16);
        background: rgba(12, 30, 50, 0.66);
        color: #a9bed3;
        line-height: 1.55;
    }

    .kg-status-ok {
        padding: 0.72rem 0.85rem;
        border-radius: 13px;
        border: 1px solid rgba(62, 230, 208, 0.20);
        background: rgba(24, 128, 111, 0.13);
        color: #8ef8e8;
        font-weight: 700;
    }

    .kg-status-bad {
        padding: 0.72rem 0.85rem;
        border-radius: 13px;
        border: 1px solid rgba(255, 107, 129, 0.22);
        background: rgba(150, 37, 58, 0.13);
        color: #ff9dae;
        font-weight: 700;
    }

    div[data-testid="stMetric"] {
        border: 1px solid var(--kg-border);
        background: rgba(12, 28, 48, 0.72);
        padding: 0.85rem 1rem;
        border-radius: 16px;
    }

    div[data-testid="stForm"] {
        border: 1px solid var(--kg-border);
        background: rgba(10, 24, 41, 0.65);
        border-radius: 20px;
        padding: 1rem;
    }

    div[data-testid="stChatMessage"] {
        border: 1px solid rgba(88, 166, 255, 0.12);
        border-radius: 18px;
        background: rgba(11, 27, 46, 0.62);
    }

    .stButton > button,
    .stFormSubmitButton > button {
        border-radius: 12px;
        border: 1px solid rgba(88, 166, 255, 0.32);
        background: linear-gradient(135deg, #175fa8, #147b91);
        color: white;
        font-weight: 750;
        transition: 0.18s ease;
    }

    .stButton > button:hover,
    .stFormSubmitButton > button:hover {
        border-color: #75f0df;
        transform: translateY(-1px);
        box-shadow: 0 8px 25px rgba(37, 176, 201, 0.20);
    }

    div[data-baseweb="tab-list"] {
        gap: 0.35rem;
    }

    button[data-baseweb="tab"] {
        border-radius: 12px;
        padding-left: 1rem;
        padding-right: 1rem;
        background: rgba(11, 26, 44, 0.56);
    }

    code {
        color: #86d7ff !important;
    }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
    """,
    unsafe_allow_html=True,
)


# -----------------------------------------------------------------------------
# Engine initialization
# -----------------------------------------------------------------------------
REQUIRED_FILES = [
    BASE_DIR / "middle_layer.py",
    BASE_DIR / "family_kb.pl",
    BASE_DIR / "chat.aiml",
    BASE_DIR / "dataentry.aiml",
]


@st.cache_resource(show_spinner=False)
def initialize_engine():
    """Load the existing AIML, Neo4j and Prolog project once per app process."""
    module = importlib.import_module("middle_layer")
    module.load_kb(str(BASE_DIR / "family_kb.pl"))
    module.load_bot(
        [
            str(BASE_DIR / "chat.aiml"),
            str(BASE_DIR / "dataentry.aiml"),
        ]
    )
    return module


def ensure_project_files() -> list[str]:
    return [path.name for path in REQUIRED_FILES if not path.exists()]


def test_database(engine: Any) -> tuple[bool, str]:
    try:
        engine.execute_cypher("RETURN 1 AS connected")
        return True, "Neo4j graph engine connected"
    except Exception as error:
        return False, str(error)


def get_metrics(engine: Any) -> dict[str, int]:
    defaults = {
        "nodes": 0,
        "relationships": 0,
        "explicit": 0,
        "inferred": 0,
    }

    try:
        rows = engine.execute_cypher(
            """
            MATCH (p:Person)
            WITH count(p) AS node_count
            OPTIONAL MATCH ()-[r]->()
            RETURN node_count,
                   count(r) AS relationship_count,
                   sum(CASE WHEN type(r) STARTS WITH 'INFERRED_' THEN 1 ELSE 0 END) AS inferred_count
            """
        )

        if rows:
            defaults["nodes"] = rows[0].get("node_count", 0) or 0
            defaults["relationships"] = rows[0].get("relationship_count", 0) or 0
            defaults["inferred"] = rows[0].get("inferred_count", 0) or 0
            defaults["explicit"] = max(
                defaults["relationships"] - defaults["inferred"], 0
            )
    except Exception:
        pass

    return defaults


def get_graph_data(engine: Any, max_nodes: int = 80, max_edges: int = 160):
    nodes = engine.execute_cypher(
        """
        MATCH (p:Person)
        RETURN p.name AS id,
               coalesce(p.display_name, p.name) AS label,
               coalesce(p.gender, 'unknown') AS gender,
               p.dob AS dob
        ORDER BY label
        LIMIT $limit
        """,
        {"limit": max_nodes},
    )

    valid_ids = [node["id"] for node in nodes]

    if not valid_ids:
        return [], []

    edges = engine.execute_cypher(
        """
        MATCH (a:Person)-[r]->(b:Person)
        WHERE a.name IN $valid_ids AND b.name IN $valid_ids
        RETURN a.name AS source,
               b.name AS target,
               type(r) AS relation
        LIMIT $limit
        """,
        {"valid_ids": valid_ids, "limit": max_edges},
    )
    return nodes, edges


def build_graph_figure(nodes: list[dict], edges: list[dict]) -> go.Figure:
    graph = nx.DiGraph()

    for node in nodes:
        graph.add_node(
            node["id"],
            label=node["label"],
            gender=node.get("gender", "unknown"),
            dob=node.get("dob"),
        )

    for edge in edges:
        graph.add_edge(
            edge["source"],
            edge["target"],
            relation=edge["relation"],
        )

    positions = nx.spring_layout(graph, seed=17, k=1.25, iterations=80)

    edge_x: list[float | None] = []
    edge_y: list[float | None] = []
    midpoint_x: list[float] = []
    midpoint_y: list[float] = []
    midpoint_text: list[str] = []

    for source, target, data in graph.edges(data=True):
        x0, y0 = positions[source]
        x1, y1 = positions[target]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])
        midpoint_x.append((x0 + x1) / 2)
        midpoint_y.append((y0 + y1) / 2)
        midpoint_text.append(
            f"{graph.nodes[source]['label']} → {graph.nodes[target]['label']}"
            f"<br><b>{data['relation']}</b>"
        )

    edge_trace = go.Scatter(
        x=edge_x,
        y=edge_y,
        mode="lines",
        line=dict(width=1.15, color="rgba(105, 174, 255, 0.34)"),
        hoverinfo="skip",
    )

    edge_hover_trace = go.Scatter(
        x=midpoint_x,
        y=midpoint_y,
        mode="markers",
        marker=dict(size=12, color="rgba(0,0,0,0)"),
        text=midpoint_text,
        hovertemplate="%{text}<extra></extra>",
    )

    node_x: list[float] = []
    node_y: list[float] = []
    node_text: list[str] = []
    node_labels: list[str] = []
    node_colors: list[str] = []
    node_sizes: list[int] = []

    color_map = {
        "male": "#56a7ff",
        "female": "#f58ac7",
        "unknown": "#59dfc8",
    }

    for node_id, data in graph.nodes(data=True):
        x, y = positions[node_id]
        degree = graph.degree(node_id)
        node_x.append(x)
        node_y.append(y)
        node_labels.append(data["label"])
        node_colors.append(color_map.get(str(data["gender"]).lower(), "#59dfc8"))
        node_sizes.append(min(28 + (degree * 3), 55))
        dob_text = data["dob"] if data["dob"] else "Not stored"
        node_text.append(
            f"<b>{data['label']}</b>"
            f"<br>Gender: {str(data['gender']).title()}"
            f"<br>Year of birth: {dob_text}"
            f"<br>Connections: {degree}"
        )

    node_trace = go.Scatter(
        x=node_x,
        y=node_y,
        mode="markers+text",
        text=node_labels,
        textposition="top center",
        textfont=dict(size=11, color="#dcecff"),
        hovertext=node_text,
        hovertemplate="%{hovertext}<extra></extra>",
        marker=dict(
            size=node_sizes,
            color=node_colors,
            line=dict(width=1.8, color="rgba(235, 247, 255, 0.72)"),
        ),
    )

    figure = go.Figure(data=[edge_trace, edge_hover_trace, node_trace])
    figure.update_layout(
        height=650,
        margin=dict(l=10, r=10, t=20, b=10),
        showlegend=False,
        hovermode="closest",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(4,12,22,0.32)",
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        dragmode="pan",
    )
    return figure


def run_chat(engine: Any, prompt: str) -> None:
    prompt = prompt.strip()
    if not prompt:
        return

    st.session_state.messages.append({"role": "user", "content": prompt})

    try:
        with st.spinner("Reasoning across AIML, Neo4j and Prolog..."):
            response = engine.chat(prompt)
    except Exception as error:
        response = f"The reasoning pipeline returned an error: {error}"

    st.session_state.messages.append({"role": "assistant", "content": response})


def flash(message: str, level: str = "success") -> None:
    st.session_state.flash_message = message
    st.session_state.flash_level = level


# -----------------------------------------------------------------------------
# Startup checks
# -----------------------------------------------------------------------------
missing_files = ensure_project_files()

if missing_files:
    st.error("The following required files are missing from the app folder:")
    st.code("\n".join(missing_files))
    st.stop()

try:
    with st.spinner("Booting the hybrid reasoning engine..."):
        engine = initialize_engine()
except SystemExit:
    st.error(
        "The existing middle_layer.py stopped execution while connecting to Neo4j. "
        "Apply the environment-variable connection patch shown in the setup guide."
    )
    st.stop()
except Exception as startup_error:
    st.error("KinGraph AI could not initialize.")
    st.exception(startup_error)
    st.stop()

connected, connection_message = test_database(engine)

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": (
                "Assalam-o-Alaikum! I am KinGraph AI. Add family knowledge in natural "
                "language, ask relationship questions, or explore the inferred graph."
            ),
        }
    ]

if "flash_message" in st.session_state:
    level = st.session_state.pop("flash_level", "success")
    message = st.session_state.pop("flash_message")
    getattr(st, level)(message)


# -----------------------------------------------------------------------------
# Sidebar
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown("## 🧠 KinGraph AI")
    st.caption("Hybrid Knowledge Representation & Reasoning Studio")
    st.write("")

    if connected:
        st.markdown(
            '<div class="kg-status-ok">● Neo4j connected and ready</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div class="kg-status-bad">● Neo4j connection unavailable</div>',
            unsafe_allow_html=True,
        )
        st.caption(connection_message)

    st.write("")
    st.markdown("### Quick prompts")

    examples = [
        "Fayz is brother of Ismail",
        "Liaqat is the father of Fayz",
        "Who is the grandfather of Fayz?",
        "Who is the sister of Ismail?",
        "List all males",
        "Find mutual between Fayz and Ismail",
    ]

    for index, example in enumerate(examples):
        if st.button(example, key=f"example_{index}", use_container_width=True):
            run_chat(engine, example)
            st.rerun()

    st.divider()

    if st.button("🧹 Clear conversation", use_container_width=True):
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": "Conversation cleared. The knowledge graph itself was not deleted.",
            }
        ]
        st.rerun()

    if st.button("🔄 Refresh graph view", use_container_width=True):
        st.rerun()

    st.divider()
    st.caption("AIML · Python · Neo4j · Cypher · Pytholog")
    st.caption("Designed by Fayz Liaqat")


# -----------------------------------------------------------------------------
# Header and metrics
# -----------------------------------------------------------------------------
st.markdown(
    """
    <div class="kg-hero">
        <div class="kg-eyebrow">Symbolic AI · Knowledge Graphs · Hybrid Inference</div>
        <h1 class="kg-title"><span class="kg-gradient">KinGraph AI</span></h1>
        <p class="kg-subtitle">
            A local graph-based reasoning workspace that turns natural-language family facts
            into Neo4j relationships, applies Prolog inference rules, and explains hidden
            multi-hop connections through an interactive conversational interface.
        </p>
        <div class="kg-pill-row">
            <span class="kg-pill">AIML Conversation Layer</span>
            <span class="kg-pill">Neo4j Graph Storage</span>
            <span class="kg-pill">Cypher Traversal</span>
            <span class="kg-pill">Prolog Inference</span>
            <span class="kg-pill">100% Local</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

metrics = get_metrics(engine)
metric_columns = st.columns(4)
metric_data = [
    ("Person Nodes", metrics["nodes"], "Stored identities"),
    ("Graph Relations", metrics["relationships"], "All active edges"),
    ("Explicit Facts", metrics["explicit"], "User-entered structure"),
    ("Inferred Facts", metrics["inferred"], "Prolog-discovered edges"),
]

for column, (label, value, note) in zip(metric_columns, metric_data):
    with column:
        st.markdown(
            f"""
            <div class="kg-card">
                <div class="kg-card-label">{label}</div>
                <div class="kg-card-value">{value}</div>
                <div class="kg-card-note">{note}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.write("")


# -----------------------------------------------------------------------------
# Main workspace
# -----------------------------------------------------------------------------
chat_tab, entry_tab, graph_tab, guide_tab = st.tabs(
    [
        "💬 Reasoning Assistant",
        "➕ Knowledge Entry",
        "🕸️ Graph Explorer",
        "📘 Command Guide",
    ]
)

with chat_tab:
    left, right = st.columns([1.55, 0.65], gap="large")

    with left:
        st.markdown('<div class="kg-section-title">Conversational Reasoning</div>', unsafe_allow_html=True)
        st.caption(
            "Enter facts or ask questions in natural language. The response is produced by "
            "your existing AIML → Python → Neo4j → Prolog pipeline."
        )

        for message in st.session_state.messages:
            avatar = "🧑" if message["role"] == "user" else "🧠"
            with st.chat_message(message["role"], avatar=avatar):
                st.markdown(message["content"])

        prompt = st.chat_input(
            "Example: Pareeshay is sister of Fayz / Who is the grandson of Hussain?"
        )
        if prompt:
            run_chat(engine, prompt)
            st.rerun()

    with right:
        st.markdown('<div class="kg-section-title">System Intelligence</div>', unsafe_allow_html=True)
        st.markdown(
            """
            <div class="kg-mini-note">
                <b>Knowledge acquisition</b><br>
                Natural-language facts are converted into graph nodes, properties and edges.
            </div>
            <br>
            <div class="kg-mini-note">
                <b>Hybrid inference</b><br>
                Explicit Neo4j facts are synchronized into a temporary Prolog knowledge base.
            </div>
            <br>
            <div class="kg-mini-note">
                <b>Knowledge discovery</b><br>
                Derived family relations are merged back into Neo4j as inferred edges.
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.write("")
        st.markdown("#### Useful examples")
        st.code(
            "Fayz is male\n"
            "Pareeshay is sister of Fayz\n"
            "Liaqat is father of Fayz\n"
            "Who is grandfather of Fayz?\n"
            "Is Fayz brother of Ismail?\n"
            "Find mutual between Fayz and Ismail",
            language="text",
        )

with entry_tab:
    st.markdown('<div class="kg-section-title">Structured Knowledge Entry</div>', unsafe_allow_html=True)
    st.caption(
        "These forms call the same backend functions as the chatbot but provide a simpler "
        "dashboard workflow for demonstrations."
    )

    profile_column, relation_column = st.columns(2, gap="large")

    with profile_column:
        st.markdown("### Create or update a person")
        with st.form("person_form", clear_on_submit=True):
            person_name = st.text_input("Full name", placeholder="e.g. Fayz Liaqat")
            gender = st.selectbox("Gender", ["Not specified", "Male", "Female"])
            include_dob = st.checkbox("Add year of birth")
            dob = st.number_input(
                "Year of birth",
                min_value=1900,
                max_value=datetime.now().year,
                value=2000,
                disabled=not include_dob,
            )
            person_submit = st.form_submit_button(
                "Save person", use_container_width=True
            )

        if person_submit:
            if not person_name.strip():
                st.warning("Enter a valid person name.")
            else:
                responses = []
                try:
                    if gender == "Male":
                        responses.append(engine.process_add("ADD_MALE", person_name))
                    elif gender == "Female":
                        responses.append(engine.process_add("ADD_FEMALE", person_name))

                    if include_dob:
                        responses.append(
                            engine.process_add("ADD_DOB", person_name, str(int(dob)))
                        )

                    if gender == "Not specified" and not include_dob:
                        st.warning("Choose a gender or provide a year of birth to create the node.")
                    else:
                        flash("\n\n".join(responses), "success")
                        st.rerun()
                except Exception as error:
                    st.error(f"Could not save the person: {error}")

    with relation_column:
        st.markdown("### Create a relationship")
        relation_map = {
            "Father of": "ADD_FATHER",
            "Mother of": "ADD_MOTHER",
            "Parent of": "ADD_PARENT",
            "Brother of": "ADD_BROTHER",
            "Sister of": "ADD_SISTER",
            "Sibling of": "ADD_SIBLING",
            "Married to": "ADD_MARRIED",
            "Friend of": "ADD_FRIEND",
        }

        with st.form("relation_form", clear_on_submit=True):
            first_person = st.text_input(
                "First person", placeholder="e.g. Liaqat", key="relation_p1"
            )
            relation_label = st.selectbox(
                "Relationship", list(relation_map.keys())
            )
            second_person = st.text_input(
                "Second person", placeholder="e.g. Fayz", key="relation_p2"
            )
            relation_submit = st.form_submit_button(
                "Create relationship", use_container_width=True
            )

        if relation_submit:
            if not first_person.strip() or not second_person.strip():
                st.warning("Both person names are required.")
            else:
                try:
                    response = engine.process_add(
                        relation_map[relation_label],
                        first_person,
                        second_person,
                    )
                    flash(response, "success")
                    st.rerun()
                except Exception as error:
                    st.error(f"Could not create the relationship: {error}")

    st.write("")
    st.info(
        "Every successful update triggers your existing hybrid synchronization lifecycle, "
        "which recalculates inferred relationships and merges them back into Neo4j."
    )

with graph_tab:
    st.markdown('<div class="kg-section-title">Interactive Knowledge Graph</div>', unsafe_allow_html=True)
    st.caption(
        "Pan, zoom and hover over nodes or relationship paths. The visualization reads "
        "directly from the local Neo4j database."
    )

    try:
        graph_nodes, graph_edges = get_graph_data(engine)

        relation_types = sorted({edge["relation"] for edge in graph_edges})
        selected_relation = st.selectbox(
            "Filter relationship type",
            ["All relationships"] + relation_types,
        )

        filtered_edges = graph_edges
        if selected_relation != "All relationships":
            filtered_edges = [
                edge for edge in graph_edges if edge["relation"] == selected_relation
            ]

        if not graph_nodes:
            st.info(
                "The graph is empty. Add a few people and relationships from the Knowledge Entry tab."
            )
        else:
            graph_figure = build_graph_figure(graph_nodes, filtered_edges)
            st.plotly_chart(
                graph_figure,
                use_container_width=True,
                config={
                    "displaylogo": False,
                    "scrollZoom": True,
                    "responsive": True,
                },
            )

            node_table, edge_table = st.columns(2, gap="large")
            with node_table:
                st.markdown("### Person nodes")
                st.dataframe(
                    graph_nodes,
                    use_container_width=True,
                    hide_index=True,
                )

            with edge_table:
                st.markdown("### Relationship edges")
                st.dataframe(
                    filtered_edges,
                    use_container_width=True,
                    hide_index=True,
                )
    except Exception as graph_error:
        st.error(f"Graph visualization could not be generated: {graph_error}")

with guide_tab:
    st.markdown('<div class="kg-section-title">Supported Commands</div>', unsafe_allow_html=True)

    guide_left, guide_right = st.columns(2, gap="large")

    with guide_left:
        st.markdown("### Add knowledge")
        st.code(
            "Ali is male\n"
            "Sara is female\n"
            "Liaqat is father of Fayz\n"
            "Ayesha is mother of Fayz\n"
            "Fayz is brother of Ismail\n"
            "Pareeshay is sister of Fayz\n"
            "Ali is married to Sara\n"
            "Ahmed was born in 2001",
            language="text",
        )

        st.markdown("### System commands")
        st.code("help\ncommands\nList all males\nList all females", language="text")

    with guide_right:
        st.markdown("### Ask questions")
        st.code(
            "Who is Fayz?\n"
            "Who is father of Fayz?\n"
            "Who is grandfather of Fayz?\n"
            "Who is chacha of Fayz?\n"
            "Who is cousin of Fayz?\n"
            "Is Fayz brother of Ismail?\n"
            "Find mutual between Fayz and Ismail",
            language="text",
        )

        st.markdown("### Inference coverage")
        st.markdown(
            "Father, mother, son, daughter, brother, sister, grandparents, "
            "paternal and maternal relatives, in-laws, nephews, nieces, cousins, "
            "great-grandparents, ancestors and descendants."
        )

    st.warning(
        "This application is designed for local academic demonstration. Do not store "
        "sensitive real-world family information in a public or shared Neo4j database."
    )

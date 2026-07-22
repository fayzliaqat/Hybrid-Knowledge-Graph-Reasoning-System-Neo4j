# ---------------------------------------------------------
# MIDDLE LAYER — Connects AIML bot to Neo4j & Prolog Graph
# ---------------------------------------------------------

import os
import sys
import re
import contextlib
import pytholog as pl
from aiml import Kernel
from neo4j import GraphDatabase
from dotenv import load_dotenv

# -----------------------------------------------
# NEO4J DATABASE CONNECTION PROFILE CONFIGURATION
# -----------------------------------------------

load_dotenv(
    os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        ".env"
    )
)

NEO4J_URI = os.getenv(
    "NEO4J_URI",
    "neo4j://127.0.0.1:7687"
)

NEO4J_USER = os.getenv(
    "NEO4J_USER",
    "neo4j"
)

NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

driver = None


def get_driver():
    """Create and reuse the local Neo4j driver safely."""
    global driver

    if driver is None:
        if not NEO4J_PASSWORD:
            raise RuntimeError(
                "NEO4J_PASSWORD is missing. "
                "Add it to the .env file in the project folder."
            )

        driver = GraphDatabase.driver(
            NEO4J_URI,
            auth=(NEO4J_USER, NEO4J_PASSWORD),
        )

        driver.verify_connectivity()

    return driver


def execute_cypher(query, parameters=None):
    with get_driver().session() as session:
        result = session.run(
            query,
            parameters or {}
        )

        return [
            dict(record)
            for record in result
        ]


def close_neo4j():
    """Safely terminate the active Neo4j connection pool."""
    global driver

    if driver is not None:
        driver.close()
        driver = None

        print(
            "[Neo4j] Graph driver session "
            "successfully terminated."
        )


@contextlib.contextmanager
def suppress_stdout():
    """Context manager to silence pytholog's terminal diagnostic prints."""
    with open(os.devnull, "w") as devnull:
        old_stdout = sys.stdout
        sys.stdout = devnull
        try:
            yield
        finally:
            sys.stdout = old_stdout

# ---------------------------------------------------------
# UTILITIES AND EXHAUSTIVE MAPPING LAYERS
# ---------------------------------------------------------
RELATION_MAP = {
    "father": "father", "mother": "mother", "son": "son", "daughter": "daughter",
    "child": "child", "brother": "brother", "sister": "sister", "sibling": "sibling",
    "friend": "friend", "friends": "friend", "best friend": "friend", "best friends": "friend",
    "grandfather": "grandparent", "grandmother": "grandparent", "grandchild": "grandchild",
    "grandson": "grandson", "granddaughter": "granddaughter", "husband": "husband",
    "wife": "wife", "spouse": "spouse", "uncle": "uncle", "aunt": "aunt",
    "chacha": "chacha", "taya": "taya", "phupho": "phupho", "phuphi": "phupho",
    "maama": "maamu", "mamu": "maamu", "maamu": "maamu", "khala": "khala",
    "cousin": "cousin", "nephew": "nephew", "niece": "niece",
    "bhatija": "bhatija", "bhatiji": "bhatiji", "bhanja": "bhanja", "bhanji": "bhanji",
    "dada": "dada", "dadi": "dadi", "nana": "nana", "nani": "nani",
    "chachi": "chachi", "tai": "tai", "phupha": "phupha", "mami": "mami", "khalu": "khalu",
    "sasur": "sasur", "saas": "saas", "bhabhi": "bhabhi", "bahnoi": "bahnoi", "behnoi": "bahnoi",
    "bahu": "bahu", "damad": "damad", "great grandfather": "great_grandfather",
    "great grandmother": "great_grandmother", "great uncle": "great_uncle",
    "great aunt": "great_aunt", "cousin once removed": "cousin_once_removed",
    "father in law": "sasur", "father-in-law": "sasur",
    "mother in law": "saas", "mother-in-law": "saas",
    "brother in law": "bahnoi", "brother-in-law": "bahnoi",
    "sister in law": "bhabhi", "sister-in-law": "bhabhi"
}

bot = None
KB_RULE_CONTENT = ""
KB_FILE_PATH = "family_kb.pl"

HELP_TEXT = """
----------------- FAMILY GRAPH CHATBOT HELP -----------------

DATA ENTRY

• X is male
• Y is female
• X is father of Y
• X is mother of Y
• X is married to Y
• X and Y are siblings
• X is brother of Y
• X is sister of Y
• X was born in Y

QUERYING

• Who is Ali
• Who is father of Ahmed
• Who is mother of Ahmed
• Who is grandfather of Ahmed
• Who is chacha of Ahmed
• Who is khala of Ahmed
• Who is cousin of Ahmed
• Is Ali father of Ahmed
• Is Ali married to Sara
• List all males
• List all females

SYSTEM

help
commands
bye
exit
quit

----------------------------------------
"""

def load_kb(kb_path="family_kb.pl"):
    global KB_RULE_CONTENT, KB_FILE_PATH
    KB_FILE_PATH = kb_path
    with open(kb_path, "r") as f:
        KB_RULE_CONTENT = f.read()
    print(f"[KB] Rule templates loaded from: {kb_path}")
    sync_and_infer_hybrid()

def load_bot(aiml_paths):
    global bot
    bot = Kernel()
    if isinstance(aiml_paths, str):
        aiml_paths = [aiml_paths]
    for path in aiml_paths:
        bot.learn(path)
    print(f"[Bot] Evaluated and compiled {len(aiml_paths)} conversational patterns.")

def clean(text):
    if not text: return ""
    return text.strip().lower().replace("?", "").replace("'s", "").replace("'", "").replace(" ", "_")

def format_display_name(name_str):
    if not name_str: return ""
    return name_str.replace("_", " ").title()

KNOWN_STARTERS = {
    "who", "what", "when", "where", "how", "is", "are", "was", "tell", "find", 
    "give", "show", "list", "do", "can", "could", "whether", "between", "help", 
    "hi", "hey", "hello", "helo", "salam", "assalam", "asalam", "aoa", "bye", 
    "exit", "quit", "commands", "parents", "spouse", "dob", "age", "born",
    "add", "register", "marry", "date", "graph", "metrics"
}

DATA_ENTRY_KEYWORDS = [
    "is a male", "is male", "is a female", "is female",
    "is a boy", "is a man", "is a girl", "is a woman",
    "is the friend of", "is friend of", "is a friend of", "are friends",
    "are friends with each other", "is friends with"
    "was born in", "is born in",
    "is the parent of", "is parent of",
    "is the father of", "is father of",
    "is the mother of", "is mother of",
    "is married to",
    "is the sibling of", "is sibling of", "is the brother of", "is brother of", "is the sister of", "is sister of",
    "are siblings", "are married to each other", "are siblings of each other",
    "are related", "is related to", "is related", "is a relative of", "is relative of",
    "is the brother of", "is brother of", "is the sister of", "is sister of",
    "is the son of", "is son of", "is the daughter of", "is daughter of",
    "is the uncle of", "is uncle of", "is the aunt of", "is aunt of",
    "is the chacha of", "is chacha of", "is the taya of", "is taya of",
    "is the phupho of", "is phupho of", "is the maamu of", "is maamu of", "is the khala of",
    "is khala of", "is the cousin of", "is cousin of", "is the nephew of", "is nephew of",
    "is the niece of", "is niece of", "is the father-in-law of", "is father-in-law of",
    "is the mother-in-law of", "is mother-in-law of", "is the brother-in-law of", "is brother-in-law of",
    "is the sister-in-law of", "is sister-in-law of",
    "is the father in law of", "is father in law of",
    "is the mother in law of", "is mother in law of", "is the brother in law of", "is brother in law of",
    "is the sister in law of", "is sister in law of", "is the ancestor of", "is ancestor of",
    "is the descendant of", "is descendant of", "is the paternal grandfather of", "is paternal grandfather of",
    "is the paternal grandmother of", "is paternal grandmother of", "is the maternal grandfather of",
    "is maternal grandfather of", "is the maternal grandmother of", "is maternal grandmother of"
]

def preprocess(text):
    text = text.strip()
    if not text: return text
    first_word = text.split()[0].lower()
    text_lower = text.lower()

    if first_word not in KNOWN_STARTERS:
        for keyword in DATA_ENTRY_KEYWORDS:
            if keyword in text_lower:
                return text
        return "WHO IS " + text
    return text

# ---------------------------------------------------------
# DATA ACQUISITION & GRAPH WRITING
# ---------------------------------------------------------
def process_add(mode, p1, p2=""):
    p1_clean = clean(p1)
    p2_clean = clean(p2)
    disp_p1 = format_display_name(p1_clean)
    disp_p2 = format_display_name(p2_clean)

    if p1_clean and p2_clean and p1_clean == p2_clean:
        return "A person cannot have a relationship with themselves."

    two_person_modes = {"ADD_PARENT", "ADD_FATHER", "ADD_MOTHER", "ADD_MARRIED", "ADD_SIBLING", "ADD_BROTHER", "ADD_SISTER", "ADD_FRIEND"}
    if mode in two_person_modes and not p2_clean and "_" in p1_clean:
        parts = p1_clean.split("_")
        if len(parts) == 2:
            p1_clean, p2_clean = parts[0], parts[1]
            disp_p1 = format_display_name(p1_clean)
            disp_p2 = format_display_name(p2_clean)

    if mode == "ADD_MALE":
        existing = execute_cypher(
            "MATCH (p:Person {name:$name}) RETURN p.gender AS gender",
            {"name": p1_clean}
        )

        if existing and existing[0]["gender"] == "female":
            return f"Gender conflict: `{disp_p1}` is already registered as female."

        execute_cypher(
            "MERGE (p:Person {name: $name}) SET p.gender = 'male', p.display_name = $disp",
            {"name": p1_clean, "disp": disp_p1}
        )
        msg = f"Logged male node: `{disp_p1}` into the graph database."

    elif mode == "ADD_FEMALE":
        existing = execute_cypher(
            "MATCH (p:Person {name:$name}) RETURN p.gender AS gender",
            {"name": p1_clean}
        )

        if existing and existing[0]["gender"] == "male":
            return f"Gender conflict: `{disp_p1}` is already registered as male."

        execute_cypher(
            "MERGE (p:Person {name: $name}) SET p.gender = 'female', p.display_name = $disp",
            {"name": p1_clean, "disp": disp_p1}
        )
        msg = f"Logged female node: `{disp_p1}` into the graph database."

    elif mode == "ADD_DOB":
        year_str = p2_clean.replace("_", "")
        try:
            year = int(year_str)
        except ValueError:
            return f"Error: `{p2}` is an invalid year specification."
        execute_cypher(
            "MERGE (p:Person {name: $name}) SET p.dob = $dob, p.display_name = $disp",
            {"name": p1_clean, "dob": year, "disp": disp_p1}
        )
        msg = f"Updated structural property: `{disp_p1}` DOB -> `{year}`."

    elif mode == "ADD_RENAME":
        if not p1_clean or not p2_clean:
            return "Rename requires old name and new name."

        old_exists = execute_cypher(
            "MATCH (p:Person {name:$old}) RETURN p",
            {"old": p1_clean}
        )

        if not old_exists:
            return f"`{disp_p1}` does not exist in the knowledge graph."

        new_exists = execute_cypher(
            "MATCH (p:Person {name:$new}) RETURN p",
            {"new": p2_clean}
        )

        if new_exists:
            return f"`{disp_p2}` already exists. Rename cancelled to avoid duplicate nodes."

        execute_cypher(
            """
            MATCH (p:Person {name:$old})
            SET p.name = $new, p.display_name = $newDisplay
            """,
            {"old": p1_clean, "new": p2_clean, "newDisplay": disp_p2}
        )

        msg = f"Renamed graph node: `{disp_p1}` -> `{disp_p2}`."

    elif mode == "ADD_PARENT":
        if not p1_clean or not p2_clean:
            return "Parent relationship requires two valid names."
        cycle = execute_cypher(
            """
            MATCH (child:Person {name:$child})-[:PARENT_OF*]->(parent:Person {name:$parent})
            RETURN parent
            LIMIT 1
            """,
            {
                "parent": p1_clean,
                "child": p2_clean
            }
        )
        if cycle:
            return "Cannot create relationship because it would create a family cycle."
        execute_cypher(
            "MERGE (p1:Person {name: $n1}) SET p1.display_name = $d1 "
            "MERGE (p2:Person {name: $n2}) SET p2.display_name = $d2 "
            "MERGE (p1)-[:PARENT_OF]->(p2)",
            {"n1": p1_clean, "d1": disp_p1, "n2": p2_clean, "d2": disp_p2}
        )
        msg = f"Created graph edge: `({disp_p1})-[:PARENT_OF]->({disp_p2})`."

    elif mode == "ADD_FATHER":
        cycle = execute_cypher(
            """
            MATCH (child:Person {name:$child})-[:PARENT_OF*]->(parent:Person {name:$parent})
            RETURN parent
            LIMIT 1
            """,
            {
                "parent": p1_clean,
                "child": p2_clean
            }
        )

        if cycle:
            return "Cannot create relationship because it would create a family cycle."
        execute_cypher(
            "MERGE (p1:Person {name: $n1}) SET p1.gender = 'male', p1.display_name = $d1 "
            "MERGE (p2:Person {name: $n2}) SET p2.display_name = $d2 "
            "MERGE (p1)-[:PARENT_OF]->(p2)",
            {"n1": p1_clean, "d1": disp_p1, "n2": p2_clean, "d2": disp_p2}
        )
        msg = f"Created structural relationship: `({disp_p1})` is father of `({disp_p2})`."

    elif mode == "ADD_MOTHER":
        cycle = execute_cypher(
            """
            MATCH (child:Person {name:$child})-[:PARENT_OF*]->(parent:Person {name:$parent})
            RETURN parent
            LIMIT 1
            """,
            {
                "parent": p1_clean,
                "child": p2_clean
            }
        )

        if cycle:
            return "Cannot create relationship because it would create a family cycle."

        execute_cypher(
            "MERGE (p1:Person {name: $n1}) SET p1.gender = 'female', p1.display_name = $d1 "
            "MERGE (p2:Person {name: $n2}) SET p2.display_name = $d2 "
            "MERGE (p1)-[:PARENT_OF]->(p2)",
            {"n1": p1_clean, "d1": disp_p1, "n2": p2_clean, "d2": disp_p2}
        )
        msg = f"Created structural relationship: `({disp_p1})` is mother of `({disp_p2})`."

    elif mode == "ADD_MARRIED":
        execute_cypher(
            "MERGE (p1:Person {name: $n1}) SET p1.display_name = $d1 "
            "MERGE (p2:Person {name: $n2}) SET p2.display_name = $d2 "
            "MERGE (p1)-[:MARRIED_TO]->(p2) "
            "MERGE (p2)-[:MARRIED_TO]->(p1)",
            {"n1": p1_clean, "d1": disp_p1, "n2": p2_clean, "d2": disp_p2}
        )
        msg = f"Created bidirectional graph marriage bounds: `({disp_p1}) <-> ({disp_p2})`."

    elif mode == "ADD_SIBLING":
        execute_cypher(
            "MERGE (p1:Person {name: $n1}) SET p1.display_name = $d1 "
            "MERGE (p2:Person {name: $n2}) SET p2.display_name = $d2 "
            "MERGE (p1)-[:SIBLING_OF]->(p2) "
            "MERGE (p2)-[:SIBLING_OF]->(p1)",
            {"n1": p1_clean, "d1": disp_p1, "n2": p2_clean, "d2": disp_p2}
        )
        msg = f"Created bidirectional sibling paths: `({disp_p1}) <-> ({disp_p2})`."

    elif mode == "ADD_BROTHER":
        execute_cypher(
            "MERGE (p1:Person {name: $n1}) SET p1.gender = 'male', p1.display_name = $d1 "
            "MERGE (p2:Person {name: $n2}) SET p2.display_name = $d2 "
            "MERGE (p1)-[:SIBLING_OF]->(p2) "
            "MERGE (p2)-[:SIBLING_OF]->(p1)",
            {"n1": p1_clean, "d1": disp_p1, "n2": p2_clean, "d2": disp_p2}
        )
        msg = f"Created sibling bounds and male fact: `({disp_p1})` registered as brother of `({disp_p2})`."

    elif mode == "ADD_SISTER":
        execute_cypher(
            "MERGE (p1:Person {name: $n1}) SET p1.gender = 'female', p1.display_name = $d1 "
            "MERGE (p2:Person {name: $n2}) SET p2.display_name = $d2 "
            "MERGE (p1)-[:SIBLING_OF]->(p2) "
            "MERGE (p2)-[:SIBLING_OF]->(p1)",
            {"n1": p1_clean, "d1": disp_p1, "n2": p2_clean, "d2": disp_p2}
        )
        msg = f"Created sibling bounds and female fact: `({disp_p1})` registered as sister of `({disp_p2})`."

    elif mode == "ADD_FRIEND":
        if not p1_clean or not p2_clean:
            return "Friend relationship requires two valid names."

        execute_cypher(
            "MERGE (p1:Person {name: $n1}) SET p1.display_name = $d1 "
            "MERGE (p2:Person {name: $n2}) SET p2.display_name = $d2 "
            "MERGE (p1)-[:FRIEND_OF]->(p2) "
            "MERGE (p2)-[:FRIEND_OF]->(p1)",
            {"n1": p1_clean, "d1": disp_p1, "n2": p2_clean, "d2": disp_p2}
        )

        msg = f"Created bidirectional friendship edge: `({disp_p1}) <-> ({disp_p2})`."

    elif mode == "SHOW_FACTS":
        return get_graph_analytics_summary()

    sync_and_infer_hybrid()
    return msg

# =========================================================
# EXHAUSTIVE HYBRID INFERENCE LIFE-CYCLE ENGINE
# =========================================================
def sync_and_infer_hybrid():
    try:
        nodes = execute_cypher("MATCH (p:Person) RETURN p.name as name, p.gender as gender, p.dob as dob")
        parents = execute_cypher("MATCH (a:Person)-[:PARENT_OF]->(b:Person) RETURN a.name as p, b.name as c")
        marriages = execute_cypher("MATCH (a:Person)-[:MARRIED_TO]->(b:Person) RETURN a.name as h, b.name as w")
        siblings = execute_cypher("MATCH (a:Person)-[:SIBLING_OF]->(b:Person) RETURN a.name as s1, b.name as s2")
    except Exception:
        return

    facts = []
    for n in nodes:
        if n['gender'] == 'male': facts.append(f"male({n['name']}).")
        elif n['gender'] == 'female': facts.append(f"female({n['name']}).")
        if n['dob']: facts.append(f"dob({n['name']},{n['dob']}).")
    for p in parents: facts.append(f"parent({p['p']},{p['c']}).")
    for m in marriages: facts.append(f"married({m['h']},{m['w']}).")
    for s in siblings: facts.append(f"sibling({s['s1']},{s['s2']}).")

    runtime_kb_string = KB_RULE_CONTENT + "\n" + "\n".join(facts)
    with open("runtime_kb_tmp.pl", "w") as tmp_f:
        tmp_f.write(runtime_kb_string)
    
    tmp_kb = pl.KnowledgeBase("HybridInferenceRuntime")
    with suppress_stdout():
        tmp_kb.from_file("runtime_kb_tmp.pl")

    # CLEANED MATRIX ARRAY — Step & Half relationship types purged
    inferred_relations = [
        "father", "mother", "uncle", "aunt", "friend", "chacha", "taya", "phupho", "maamu", "khala",
        "cousin", "grandfather", "grandmother", "brother", "sister", "husband", "wife", 
        "son", "daughter", "grandson", "granddaughter", "grandchild", "chachi", "tai",
        "phupha", "mami", "khalu", "sasur", "saas", "bhabhi", "bahnoi", "bahu", "damad",
        "great_grandfather", "great_grandmother", "great_uncle", "great_aunt", 
        "cousin_once_removed", "bhatija", "bhatiji", "bhanja", "bhanji"
    ]

    try:
        execute_cypher(
            "MATCH (a:Person)-[r]->(b:Person) "
            "WHERE NOT type(r) IN ['PARENT_OF', 'MARRIED_TO', 'SIBLING_OF', 'FRIEND_OF'] "
            "DELETE r"
        )
    except Exception as e:
        print("[Inference]", e)

    for p in nodes:
        person_name = p['name']
        for rel in inferred_relations:
            try:
                with suppress_stdout():
                    res = tmp_kb.query(pl.Expr(f"{rel}(X,{person_name})"))
                if res and res not in ([False], ['No'], [None], None):
                    for derivation in res:
                        if isinstance(derivation, dict) and 'X' in derivation:
                            x = derivation['X']
                            if x == person_name: 
                                continue
                            edge_label = f"INFERRED_{rel.upper()}"
                            execute_cypher(
                                f"MATCH (a:Person {{name: $x}}), (b:Person {{name: $y}}) "
                                f"MERGE (a)-[:{edge_label}]->(b)",
                                {"x": x, "y": person_name}
                            )
            except Exception:
                continue

def get_graph_analytics_summary():
    try:
        node_count = execute_cypher("MATCH (n:Person) RETURN count(n) as c")[0]['c']
        edge_count = execute_cypher("MATCH (a)-[r]->(b) RETURN count(r) as c")[0]['c']
        nodes_data = execute_cypher("MATCH (p:Person) RETURN p.display_name as name, p.gender as g")
    except Exception:
        return "Graph database pristine."
        
    lines = [f"=== Graph Infrastructure Topology Summary ===", f"Total Active Nodes (:Person): {node_count}", f"Total Operational Structural Edges: {edge_count}\n", "Registered Entities:"]
    for nd in nodes_data:
        gender_lbl = nd['g'] if nd['g'] else "Unspecified"
        lines.append(f" - {nd['name']} ({gender_lbl.capitalize()})")
    return "\n".join(lines)

# =========================================================
# CONVERSATIONAL SEARCH RETRIEVAL ROUTER
# =========================================================
def process_query(mode, rel, p1, p2=""):
    p1_clean = clean(p1)
    p2_clean = clean(p2)

    try:
        if mode == "LIST_ALL":
            if rel in ["males", "male", "men", "boys", "man"]:
                res = execute_cypher("MATCH (p:Person {gender: 'male'}) RETURN p.display_name as name")
                names = ", ".join([r['name'] for r in res])
                return f"Graph Nodes matching [Male]: {names}." if names else "No registered male records found."
            elif rel in ["females", "female", "women", "girls", "woman"]:
                res = execute_cypher("MATCH (p:Person {gender: 'female'}) RETURN p.display_name as name")
                names = ", ".join([r['name'] for r in res])
                return f"Graph Nodes matching [Female]: {names}." if names else "No registered female records found."
            elif rel in ["married", "couples", "marriages"]:
                res = execute_cypher("MATCH (a:Person)-[:MARRIED_TO]->(b:Person) WHERE a.name < b.name RETURN a.display_name as n1, b.display_name as n2")
                pairs = ", ".join([f"{r['n1']} & {r['n2']}" for r in res])
                return f"Active Bidirectional Marriage Edges: {pairs}." if pairs else "No operational marriage edges discovered."
            return "Bulk search type unsupported."

        elif mode == "IDENTITY":
            res = execute_cypher("MATCH (p:Person {name: $name}) RETURN p.display_name as name, p.gender as g, p.dob as dob", {"name": p1_clean})
            if not res: return f"Entity `{format_display_name(p1_clean)}` does not exist in the Neo4j Graph DB."
            p_data = res[0]
            gender = p_data['g'] if p_data['g'] else "unspecified gender"
            dob_str = f", born in {p_data['dob']}" if p_data['dob'] else ""
            
            p_res = execute_cypher("MATCH (parent:Person)-[:PARENT_OF]->(p:Person {name: $name}) RETURN parent.display_name as name", {"name": p1_clean})
            parent_lbl = f", child of {' and '.join([r['name'] for r in p_res])}" if p_res else ""
            return f"Graph Node Identification -> {p_data['name']} is a {gender}{parent_lbl}{dob_str}."

        elif mode == "PARENTS":
            res = execute_cypher("MATCH (p:Person)-[:PARENT_OF]->(c:Person {name: $name}) RETURN p.display_name as name", {"name": p1_clean})
            if res: return f"{' and '.join([r['name'] for r in res])} are registered parents of {format_display_name(p1_clean)}."
            return f"No parent nodes link to {format_display_name(p1_clean)}."

        elif mode == "GENDER":
            expected = "male" if rel in ["male", "boy", "man"] else "female"
            res = execute_cypher("MATCH (p:Person {name: $name}) RETURN p.gender as g", {"name": p1_clean})
            if res and res[0]['g'] == expected: return "Affirmative. Match confirmed inside graph topology."
            return "Negative. Match violates stored properties."

        elif mode == "MARRIED":
            if not p2_clean or p2_clean == "unknown":
                res = execute_cypher("MATCH (p:Person {name: $name})-[:MARRIED_TO]->(s:Person) RETURN s.display_name as name", {"name": p1_clean})
                if res: return f"{format_display_name(p1_clean)} is currently married to {res[0]['name']}."
                return f"No marital path details found for {format_display_name(p1_clean)}."
            res = execute_cypher("MATCH (a:Person {name: $n1})-[:MARRIED_TO]->(b:Person {name: $n2}) RETURN a", {"n1": p1_clean, "n2": p2_clean})
            return f"Confirmed. Marriage edge exists between {format_display_name(p1_clean)} and {format_display_name(p2_clean)}." if res else "No path matches."

        elif mode == "DOB":
            res = execute_cypher("MATCH (p:Person {name: $name}) RETURN p.dob as dob", {"name": p1_clean})
            if res and res[0]['dob']:
                yr = res[0]['dob']
                return f"{format_display_name(p1_clean)} was born in {yr} (approx. {2026 - yr} years old)."
            return f"No birth metrics found for {format_display_name(p1_clean)}."

        elif mode == "BORN_IN":
            try:
                target_year = int(p1_clean.replace("_", ""))
            except ValueError: return "Year cast format exception."
            res = execute_cypher("MATCH (p:Person {dob: $yr}) RETURN p.display_name as name", {"yr": target_year})
            if res: return f"Nodes born in {target_year}: {', '.join([r['name'] for r in res])}."
            return f"No nodes match birth property year {target_year}."

        elif mode == "OLDER":
            r1 = execute_cypher("MATCH (p:Person {name: $n}) RETURN p.dob as dob", {"n": p1_clean})
            r2 = execute_cypher("MATCH (p:Person {name: $n}) RETURN p.dob as dob", {"n": p2_clean})
            if not r1 or not r2 or not r1[0]['dob'] or not r2[0]['dob']: return "One of the target nodes lacks year values."
            y1, y2 = r1[0]['dob'], r2[0]['dob']
            if y1 < y2: return f"{format_display_name(p1_clean)} is older than {format_display_name(p2_clean)}."
            if y2 < y1: return f"{format_display_name(p2_clean)} is older than {format_display_name(p1_clean)}."
            return f"Both profiles match exact same age metric ({y1})."

        elif mode == "OLDER_CHECK":
            r1 = execute_cypher("MATCH (p:Person {name: $n}) RETURN p.dob as dob", {"n": p1_clean})
            r2 = execute_cypher("MATCH (p:Person {name: $n}) RETURN p.dob as dob", {"n": p2_clean})
            if not r1 or not r2 or not r1[0]['dob'] or not r2[0]['dob']: return "Comparison parameter error."
            return "Yes, target condition holds." if r1[0]['dob'] < r2[0]['dob'] else "No, condition invalid."


        elif mode == "CONFIRM":
            prolog_rel = RELATION_MAP.get(rel, rel)
            supported = {
                "father", "mother", "brother", "sister", "son", "daughter",
                "grandfather", "grandmother", "grandson", "granddaughter",
                "grandchild", "husband", "wife", "spouse", "cousin",
                "uncle", "aunt", "chacha", "taya", "phupho", "maamu",
                "khala", "chachi", "tai", "phupha", "mami", "khalu",
                "sasur", "saas", "bhabhi", "bahnoi", "behnoi" "bahu", "damad",
                "bhatija", "bhatiji", "bhateeja", "bhateeji", "bhanja", "bhanji",
                "great_grandfather", "great_grandmother",
                "great_uncle", "great_aunt",
                "cousin_once_removed",
                "parent", "sibling", "married", "friend"
            }

            if prolog_rel not in supported:
                return f"Relationship '{rel}' is not supported."

            exists = execute_cypher(
                """
                MATCH (a:Person {name:$n1}), (b:Person {name:$n2})
                RETURN a, b
                """,
                {"n1": p1_clean, "n2": p2_clean}
            )
            if not exists:
                return "One or both people are not present in the knowledge graph."

            edge_label = f"INFERRED_{prolog_rel.upper()}"

            if prolog_rel == "parent":
                edge_label = "PARENT_OF"

            elif prolog_rel == "sibling":
                edge_label = "SIBLING_OF"

            elif prolog_rel == "married":
                edge_label = "MARRIED_TO"

            elif prolog_rel == "friend":
                edge_label = "FRIEND_OF"

            res = execute_cypher(
                f"""
                MATCH (a:Person {{name: $n1}})-[:{edge_label}]->(b:Person {{name: $n2}})
                RETURN a
                """,
                {"n1": p1_clean, "n2": p2_clean}
            )
            if res:
                return f"Confirmed. Relationship '{rel}' matches path properties between {format_display_name(p1_clean)} and {format_display_name(p2_clean)}."
            return f"No graph relation matches '{rel}' between {format_display_name(p1_clean)} and {format_display_name(p2_clean)}."

        elif mode == "STANDARD":
            prolog_rel = RELATION_MAP.get(rel, rel)
            rel = rel.lower().strip()
            rel = rel.replace("is the ", "")
            rel = rel.replace("is a ", "")
            rel = rel.replace("is ", "")
            rel = rel.replace(p1_clean.replace("_", " "), "")
            rel = rel.strip()
            prolog_rel = RELATION_MAP.get(rel, rel)
            supported = {
                "father", "mother", "brother", "sister", "friend", "son", "daughter",
                "grandfather", "grandmother", "grandson", "granddaughter",
                "grandchild", "husband", "wife", "spouse", "cousin",
                "uncle", "aunt", "chacha", "taya", "phupho", "maamu",
                "khala", "chachi", "tai", "phupha", "mami", "khalu",
                "sasur", "saas", "bhabhi", "bahnoi", "behnoi", "bahu", "damad",
                "bhatija", "bhatiji", "bhateeji", "bhateeja", "bhanja", "bhanji",
                "great_grandfather", "great_grandmother", "great_uncle",
                "great_aunt", "cousin_once_removed", "parent", "sibling"
            }

            if prolog_rel not in supported:
                return f"Relationship '{rel}' is not supported."

            exists = execute_cypher(
                "MATCH (p:Person {name:$name}) RETURN p",
                {"name": p1_clean}
            )

            if not exists:
                return f"{format_display_name(p1_clean)} is not present in the knowledge graph."

            edge_label = f"INFERRED_{prolog_rel.upper()}"

            if prolog_rel == "parent":
                edge_label = "PARENT_OF"

            elif prolog_rel == "sibling":
                edge_label = "SIBLING_OF"

            elif prolog_rel == "friend":
                edge_label = "FRIEND_OF"

            elif prolog_rel == "married":
                edge_label = "MARRIED_TO"

            res = execute_cypher(
                f"MATCH (x:Person)-[:{edge_label}]->(p:Person {{name: $name}}) RETURN x.display_name as name",
                {"name": p1_clean}
            )

            if res:
                return f"{', '.join([r['name'] for r in res])} is the detected {rel} of {format_display_name(p1_clean)}."

            return f"Could not compute structural path matching '{rel}' for target {format_display_name(p1_clean)}."

        elif mode == "CONFIRM":
            prolog_rel = RELATION_MAP.get(rel, rel)
            rel = rel.lower().strip()
            rel = rel.replace("is the ", "")
            rel = rel.replace("is a ", "")
            rel = rel.replace("is ", "")
            rel = rel.replace(p1_clean.replace("_", " "), "")
            rel = rel.strip()
            prolog_rel = RELATION_MAP.get(rel, rel)
            supported = {
                "father", "mother", "brother", "friend", "sister", "son", "daughter",
                "grandfather", "grandmother", "grandson", "granddaughter",
                "grandchild", "husband", "wife", "spouse", "cousin",
                "uncle", "aunt", "chacha", "taya", "phupho", "maamu",
                "khala", "chachi", "tai", "phupha", "mami", "khalu",
                "sasur", "saas", "bhabhi", "bahnoi", "behnoi", "bahu", "damad",
                "bhatija", "bhatiji", "bhateeja", "bhateeji", "bhanja", "bhanji",
                "great_grandfather", "great_grandmother",
                "great_uncle", "great_aunt",
                "cousin_once_removed",
                "parent", "sibling", "married"
            }

            if prolog_rel not in supported:
                return f"Relationship '{rel}' is not supported."

            exists = execute_cypher(
                """
                MATCH (a:Person {name:$n1}), (b:Person {name:$n2})
                RETURN a, b
                """,
                {"n1": p1_clean, "n2": p2_clean}
            )
            if not exists:
                return "One or both people are not present in the knowledge graph."

            edge_label = f"INFERRED_{prolog_rel.upper()}"
            if prolog_rel == "parent":
                edge_label = "PARENT_OF"
            elif prolog_rel == "sibling":
                edge_label = "SIBLING_OF"
            elif prolog_rel == "friend":
                edge_label = "FRIEND_OF"

            elif prolog_rel == "married":
                edge_label = "MARRIED_TO"

            res = execute_cypher(
                f"""
                    MATCH (a:Person {{name: $n1}})-[:{edge_label}]->(b:Person {{name: $n2}})
                    RETURN a
                    """,
                {"n1": p1_clean, "n2": p2_clean}
            )

            if res:
                return f"Confirmed. Relationship '{rel}' matches path properties between {format_display_name(p1_clean)} and {format_display_name(p2_clean)}."
            return f"No graph relation matches '{rel}' between {format_display_name(p1_clean)} and {format_display_name(p2_clean)}."

        elif mode == "REVERSE":
            prolog_rel = RELATION_MAP.get(rel, rel)
            rel = rel.lower().strip()
            rel = rel.replace("is the ", "")
            rel = rel.replace("is a ", "")
            rel = rel.replace("is ", "")
            rel = rel.replace(p1_clean.replace("_", " "), "")
            rel = rel.strip()
            prolog_rel = RELATION_MAP.get(rel, rel)
            supported = {
                "father", "mother", "brother", "friend", "sister", "son", "daughter",
                "grandfather", "grandmother", "grandson", "granddaughter",
                "grandchild", "husband", "wife", "spouse", "cousin",
                "uncle", "aunt", "chacha", "taya", "phupho", "maamu",
                "khala", "chachi", "tai", "phupha", "mami", "khalu",
                "sasur", "saas", "bhabhi", "bahnoi", "behnoi", "bahu", "damad",
                "bhatija", "bhatiji", "bhateeja", "bhateeji", "bhanja", "bhanji",
                "great_grandfather", "great_grandmother",
                "great_uncle", "great_aunt",
                "cousin_once_removed",
                "parent", "sibling"
            }

            if prolog_rel not in supported:
                return f"Relationship '{rel}' is not supported."

            exists = execute_cypher(
                "MATCH (p:Person {name:$name}) RETURN p",
                {"name": p1_clean}
            )

            if not exists:
                return f"{format_display_name(p1_clean)} is not present in the knowledge graph."
            edge_label = f"INFERRED_{prolog_rel.upper()}"

            if prolog_rel == "parent":
                edge_label = "PARENT_OF"

            elif prolog_rel == "sibling":
                edge_label = "SIBLING_OF"

            elif prolog_rel == "friend":
                edge_label = "FRIEND_OF"

            res = execute_cypher(
                f"MATCH (p:Person {{name: $name}})-[:{edge_label}]->(x:Person) RETURN x.display_name as name",
                {"name": p1_clean}
            )
            if res:
                return f"{format_display_name(p1_clean)} is verified as the {rel} of {', '.join([r['name'] for r in res])}."
            return f"{format_display_name(p1_clean)} does not map as a {rel} path element to any node."

    except Exception:
        return "Empty pipeline response. Populated relationship edges required to activate search maps."
    return "Processing pipeline failure."

def find_mutual_connections(p1, p2):
    n1 = clean(p1)
    n2 = clean(p2)
    try:
        query = (
            "MATCH (p1:Person {name: $n1})-[r1]-(mutual:Person)-[r2]-(p2:Person {name: $n2}) "
            "RETURN DISTINCT mutual.display_name as name"
        )
        records = execute_cypher(query, {"n1": n1, "n2": n2})
        if records:
            names = ", ".join([r['name'] for r in records])
            return f"Discovered mutual connection vertices between {format_display_name(n1)} and {format_display_name(n2)}: {names}."
    except Exception as e:
        print("[Inference]", e)
    return f"No intersecting mutual paths found between {format_display_name(n1)} and {format_display_name(n2)}."

def chat(user_input):
    raw_input = user_input.strip()

    if not raw_input:
        return "Empty input stream."

    dob_match = re.match(
        r"^(.+?)\s+(?:was\s+born\s+in|was\s+born\s+on|is\s+born\s+in|is\s+born\s+on|born\s+in|born\s+on)\s+(\d{4})\??$",
        raw_input.lower()
    )
    if dob_match:
        return process_add("ADD_DOB", dob_match.group(1), dob_match.group(2))

    rename_match = re.match(
        r"^(?:rename|change name of)\s+(.+?)\s+(?:to|as)\s+(.+?)\??$",
        raw_input.lower()
    )

    if rename_match:
        return process_add("ADD_RENAME", rename_match.group(1), rename_match.group(2))
    
    processed = preprocess(user_input)
    if not processed: return "Empty input stream."

    if processed.lower().startswith("find mutual between "):
        parts = processed.lower().replace("find mutual between ", "").split(" and ")
        if len(parts) == 2:
            return find_mutual_connections(parts[0], parts[1])

    friend_check = re.match(
        r"^is\s+(.+?)\s+(?:the\s+)?(?:a\s+)?friend\s+of\s+(.+?)\??$",
        processed.lower()
    )

    if friend_check:
        return process_query(
            "CONFIRM",
            "friend",
            friend_check.group(1),
            friend_check.group(2)
        )

    aiml_raw = bot.respond(processed)
    rel = bot.getPredicate("rel")
    p1  = bot.getPredicate("p1")
    p2  = bot.getPredicate("p2")

    for pred in ("rel", "p1", "p2"):
        bot.setPredicate(pred, "")

    if "|" in aiml_raw:
        mode = aiml_raw.split("|")[0].strip()
        if mode == "SYSTEM_HELP": return HELP_TEXT
        if mode.startswith("ADD_") or mode == "SHOW_FACTS":
            return process_add(mode, p1, p2)
        return process_query(mode, rel, p1, p2)
    elif "SYSTEM_HELP" in aiml_raw:
        return HELP_TEXT

    return aiml_raw
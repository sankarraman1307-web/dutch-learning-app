import streamlit as st
import sqlite3
import random
import json
import os

st.set_page_config(page_title="Dutchify : Nederlands Leren", layout="centered", page_icon="🇳🇱")

# ==========================================
# 1. DATABASE SETUP & THREADING FIX
# ==========================================
@st.cache_resource
def get_db_connection():
    return sqlite3.connect('dutch_learning.db', check_same_thread=False)

conn = get_db_connection()
c = conn.cursor()

c.execute('''CREATE TABLE IF NOT EXISTS nouns (id INTEGER PRIMARY KEY, dutch TEXT, english TEXT, article TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS verbs (id INTEGER PRIMARY KEY, infinitive TEXT, pronoun TEXT, tense TEXT, conjugation TEXT, translation TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS prepositions (id INTEGER PRIMARY KEY, sentence_nl TEXT, prep_missing TEXT, sentence_en TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS sentences (id INTEGER PRIMARY KEY, sentence_nl TEXT, english TEXT)''')
conn.commit()

# ==========================================
# 2. EXTERNAL JSON AUTO-SEEDER
# ==========================================
c.execute("SELECT COUNT(*) FROM nouns")
if c.fetchone()[0] == 0:
    st.info("Eerste keer opgestart: Database wordt geladen vanuit data.json...")
    if os.path.exists("data.json"):
        with open("data.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            
        c.executemany("INSERT INTO nouns (dutch, english, article) VALUES (?, ?, ?)", data.get("nouns", []))
        c.executemany("INSERT INTO verbs (infinitive, pronoun, tense, conjugation, translation) VALUES (?, ?, ?, ?, ?)", data.get("verbs", []))
        c.executemany("INSERT INTO prepositions (sentence_nl, prep_missing, sentence_en) VALUES (?, ?, ?)", data.get("prepositions", []))
        c.executemany("INSERT INTO sentences (sentence_nl, english) VALUES (?, ?)", data.get("sentences", []))
        
        conn.commit()
        st.success("Database succesvol geladen! Applicatie herstarten...")
        st.rerun()
    else:
        st.error("Fout: 'data.json' is niet gevonden! Zorg ervoor dat het bestand in dezelfde map staat als app.py.")
        st.stop()

# ==========================================
# 3. STATE MANAGEMENT & ROUTING
# ==========================================
if 'page' not in st.session_state: st.session_state.page = "home"
if 'noun' not in st.session_state: st.session_state.noun = None
if 'verb' not in st.session_state: st.session_state.verb = None
if 'prep' not in st.session_state: st.session_state.prep = None
if 'sent' not in st.session_state: st.session_state.sent = None
if 'dehet_score' not in st.session_state: st.session_state.dehet_score = 0
if 'dehet_feedback' not in st.session_state: st.session_state.dehet_feedback = None

def go_to(page_name):
    st.session_state.page = page_name
    st.rerun()

# ==========================================
# 4. GLOBAL CSS & THEME OVERRIDES
# ==========================================
colors = {
    "home": "#F7F9FC",      # Off-white / light gray
    "dehet": "#E3F2FD",     # Light Blue
    "verbs": "#FFF3E0",     # Light Orange
    "preps": "#E8F5E9",     # Light Green
    "sents": "#F3E5F5"      # Light Purple
}
bg_color = colors.get(st.session_state.page, "#F7F9FC")

st.markdown(f"""
<style>
    /* Force the background color properly */
    [data-testid="stAppViewContainer"] {{
        background-color: {bg_color} !important;
    }}
    /* Hide top header bar to look like an app */
    [data-testid="stHeader"] {{
        background-color: transparent !important;
    }}
    /* FORCE ALL TEXT TO BE DARK (Fixes dark mode text issues) */
    .stApp, .stApp p, .stApp h1, .stApp h2, .stApp h3, .stApp label, .stMarkdown {{
        color: #1E1E1E !important;
    }}
    /* FORCE ALL BUTTONS TO BE LIGHT WITH DARK TEXT */
    div[data-testid="stButton"] button {{
        background-color: #FFFFFF !important;
        color: #1E1E1E !important;
        border: 1px solid #CCCCCC !important;
    }}
    div[data-testid="stButton"] button p {{
        color: #1E1E1E !important;
    }}
    /* Hide default Streamlit menus */
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 5. PAGE RENDERERS
# ==========================================

if st.session_state.page != "home":
    if st.button("⬅️ Terug naar Home"):
        go_to("home")
    st.markdown("---")

# --- HOME SCREEN ---
if st.session_state.page == "home":
    st.markdown("<h2 style='text-align: center;'>🇳🇱 Dutchify : Nederlands Leren</h2>", unsafe_allow_html=True)
    st.write("Kies een oefening:")
    
    # CSS to make buttons massive and 3D (Duolingo style) ONLY on the home page
    st.markdown("""
    <style>
        div[data-testid="stButton"] button {
            height: 160px !important;
            border-radius: 24px !important;
            border: 2px solid #E5E5E5 !important;
            border-bottom: 8px solid #E5E5E5 !important; /* 3D bottom edge */
            transition: all 0.1s ease-in-out !important;
        }
        div[data-testid="stButton"] button:active {
            border-bottom: 2px solid #E5E5E5 !important;
            transform: translateY(6px) !important; /* Button presses down */
        }
        div[data-testid="stButton"] button p {
            font-size: 22px !important;
            font-weight: 800 !important;
            white-space: pre-wrap !important; /* Allows line breaks in the button */
        }
    </style>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🎮\n\nDe of Het", use_container_width=True): go_to("dehet")
        if st.button("📍\n\nVoorzetsels", use_container_width=True): go_to("preps")
    with col2:
        if st.button("✍️\n\nWerkwoorden", use_container_width=True): go_to("verbs")
        if st.button("🧩\n\nZinnen Bouwen", use_container_width=True): go_to("sents")

# --- FEATURE 1: DE OF HET ---
elif st.session_state.page == "dehet":
    st.header("Is het De of Het?")
    
    if st.session_state.noun is None:
        c.execute("SELECT dutch, article, english FROM nouns ORDER BY RANDOM() LIMIT 1")
        st.session_state.noun = c.fetchone()
        st.session_state.dehet_feedback = None
        
    nl_word, correct_art, en_word = st.session_state.noun
    
    st.markdown(f"<h1 style='text-align: center; font-size: 60px;'>{nl_word}</h1>", unsafe_allow_html=True)
    with st.expander("Uitleg in het Engels (English Explanation)"):
        st.write(f"**Translation:** {en_word}")
        
    if st.session_state.dehet_feedback is None:
        col1, col2 = st.columns(2)
        def check_noun(guess):
            if guess == correct_art:
                st.session_state.dehet_score += 1
                st.session_state.dehet_feedback = ("success", "✅ Goed zo!")
            else:
                st.session_state.dehet_score = 0
                st.session_state.dehet_feedback = ("error", f"❌ Fout! Het is {correct_art} {nl_word}.")
                
        col1.button("DE", use_container_width=True, on_click=check_noun, args=("de",))
        col2.button("HET", use_container_width=True, on_click=check_noun, args=("het",))
    else:
        status, msg = st.session_state.dehet_feedback
        if status == "success":
            st.success(msg)
        else:
            st.error(msg)
            
        if st.button("Volgende ⏭️", use_container_width=True):
            st.session_state.noun = None
            st.rerun()

    st.metric("Huidige Reeks (Current Streak)", st.session_state.dehet_score)

# --- FEATURE 2: WERKWOORDEN ---
elif st.session_state.page == "verbs":
    st.header("Vervoeg het Werkwoord")
    
    if st.session_state.verb is None:
        c.execute("SELECT infinitive, pronoun, tense, conjugation, translation FROM verbs ORDER BY RANDOM() LIMIT 1")
        st.session_state.verb = c.fetchone()
        
    inf, pronoun, tense, correct_conj, trans = st.session_state.verb
    st.markdown(f"### **{inf}**")
    
    tense_nl = {"Present": "Tegenwoordige Tijd", "Past": "Verleden Tijd", "Perfect": "Voltooid Tegenwoordige Tijd"}.get(tense, tense)
    st.write(f"**Tijd:** {tense_nl}")
    
    with st.expander("Uitleg in het Engels (English Explanation)"):
        st.write(f"**Meaning:** {trans}")
    
    user_conj = st.text_input(f"{pronoun} ...", key=f"verb_{inf}_{pronoun}_{tense}").strip().lower()
    
    col1, col2 = st.columns([1, 1])
    if col1.button("Controleer Antwoord"):
        if user_conj == correct_conj.lower():
            st.success("✅ Goed gedaan!")
        else:
            st.error(f"❌ Fout. Het juiste antwoord is: **{pronoun} {correct_conj}**")
            
    if col2.button("Volgende ⏭️"):
        st.session_state.verb = None
        st.rerun()

# --- FEATURE 3: VOORZETSELS ---
elif st.session_state.page == "preps":
    st.header("Vul het Voorzetsel in")
    
    if st.session_state.prep is None:
        c.execute("SELECT sentence_nl, prep_missing, sentence_en FROM prepositions ORDER BY RANDOM() LIMIT 1")
        st.session_state.prep = c.fetchone()
        
    sent_nl, prep_missing, sent_en = st.session_state.prep
    display_sent = sent_nl.replace("___", " **[ ? ]** ")
    
    st.markdown(f"### {display_sent}")
    with st.expander("Uitleg in het Engels (English Explanation)"):
        st.write(f"**Translation:** {sent_en}")
    
    user_prep = st.text_input("Ontbrekend woord:", key=f"prep_{sent_nl}").strip().lower()
    
    col1, col2 = st.columns([1, 1])
    if col1.button("Controleer Antwoord"):
        if user_prep == prep_missing:
            st.success("✅ Helemaal goed!")
        else:
            st.error(f"❌ Fout. Het moet zijn: **{prep_missing}**")
            
    if col2.button("Volgende ⏭️"):
        st.session_state.prep = None
        st.rerun()

# --- FEATURE 4: ZINNEN BOUWEN ---
elif st.session_state.page == "sents":
    st.header("Maak de Zin Compleet")
    
    if st.session_state.sent is None:
        c.execute("SELECT sentence_nl, english FROM sentences ORDER BY RANDOM() LIMIT 1")
        st.session_state.sent = c.fetchone()
        
    full_nl, en_trans = st.session_state.sent
    words = full_nl.split()
    
    if len(words) > 2 and 'missing_idx' not in st.session_state:
        st.session_state.missing_idx = random.randint(1, len(words)-2)
        
    idx = st.session_state.get('missing_idx', 1)
    correct_word = words[idx].strip('.,?!')
    
    display_words = words.copy()
    display_words[idx] = "______"
    
    st.markdown(f"### {' '.join(display_words)}")
    with st.expander("Uitleg in het Engels (English Explanation)"):
        st.write(f"**Translation:** {en_trans}")
    
    user_word = st.text_input("Ontbrekend woord:", key=f"sent_{full_nl}_{idx}").strip().lower()
    
    col1, col2 = st.columns([1, 1])
    if col1.button("Controleer Antwoord"):
        if user_word == correct_word.lower():
            st.success("✅ Perfect!")
        else:
            st.error(f"❌ Fout. Het ontbrekende woord is: **{correct_word}**")
            
    if col2.button("Volgende ⏭️"):
        if 'missing_idx' in st.session_state: del st.session_state.missing_idx
        st.session_state.sent = None
        st.rerun()

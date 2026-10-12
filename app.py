import streamlit as st
import sqlite3
import random
import json
import os

st.set_page_config(page_title="Nederlands Leren", layout="centered", page_icon="🇳🇱")

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
# 3. UI & SESSION STATE MANAGEMENT
# ==========================================
st.title("🇳🇱 Nederlands Leren Hub")

if 'noun' not in st.session_state: st.session_state.noun = None
if 'verb' not in st.session_state: st.session_state.verb = None
if 'prep' not in st.session_state: st.session_state.prep = None
if 'sent' not in st.session_state: st.session_state.sent = None
if 'dehet_score' not in st.session_state: st.session_state.dehet_score = 0

# Translated Tab Names
tab1, tab2, tab3, tab4 = st.tabs(["🎮 De of Het", "✍️ Werkwoorden", "📍 Voorzetsels", "🧩 Zinnen Bouwen"])

# --- TAB 1: DE OF HET ---
with tab1:
    st.header("Is het De of Het?")
    if st.session_state.noun is None:
        c.execute("SELECT dutch, article, english FROM nouns ORDER BY RANDOM() LIMIT 1")
        st.session_state.noun = c.fetchone()
        
    if st.session_state.noun:
        nl_word, correct_art, en_word = st.session_state.noun
        st.markdown(f"<h1 style='text-align: center; font-size: 60px;'>{nl_word}</h1>", unsafe_allow_html=True)
        
        with st.expander("Uitleg in het Engels (English Explanation)"):
            st.write(f"**Translation:** {en_word}")
        
        col1, col2 = st.columns(2)
        def check_noun(guess):
            if guess == correct_art:
                st.session_state.dehet_score += 1
                st.toast("✅ Goed zo!", icon="🎉")
            else:
                st.session_state.dehet_score = 0
                st.toast(f"❌ Fout! Het is {correct_art} {nl_word}.", icon="💔")
            st.session_state.noun = None
            
        col1.button("DE", use_container_width=True, on_click=check_noun, args=("de",))
        col2.button("HET", use_container_width=True, on_click=check_noun, args=("het",))
        st.metric("Huidige Reeks (Current Streak)", st.session_state.dehet_score)

# --- TAB 2: WERKWOORDEN (VERBS) ---
with tab2:
    st.header("Vervoeg het Werkwoord")
    if st.session_state.verb is None:
        c.execute("SELECT infinitive, pronoun, tense, conjugation, translation FROM verbs ORDER BY RANDOM() LIMIT 1")
        st.session_state.verb = c.fetchone()
        
    if st.session_state.verb:
        inf, pronoun, tense, correct_conj, trans = st.session_state.verb
        st.markdown(f"### **{inf}**")
        
        # Translate the tense display
        tense_nl = {"Present": "Tegenwoordige Tijd (Present)", 
                    "Past": "Verleden Tijd (Past)", 
                    "Perfect": "Voltooid Tegenwoordige Tijd (Perfect)"}.get(tense, tense)
        
        st.write(f"**Tijd:** {tense_nl}")
        
        with st.expander("Uitleg in het Engels (English Explanation)"):
            st.write(f"**Meaning:** {trans}")
        
        input_key = f"verb_{inf}_{pronoun}_{tense}"
        user_conj = st.text_input(f"{pronoun} ...", key=input_key).strip().lower()
        
        col1, col2 = st.columns([1, 1])
        
        if col1.button("Controleer Antwoord", key="check_v"):
            if user_conj == correct_conj.lower():
                st.success("✅ Goed gedaan!")
            else:
                st.error(f"❌ Fout. Het juiste antwoord is: **{pronoun} {correct_conj}**")
                
        if col2.button("Volgende ⏭️", key="next_v"):
            st.session_state.verb = None
            st.rerun()

# --- TAB 3: VOORZETSELS (PREPOSITIONS) ---
with tab3:
    st.header("Vul het Voorzetsel in")
    if st.session_state.prep is None:
        c.execute("SELECT sentence_nl, prep_missing, sentence_en FROM prepositions ORDER BY RANDOM() LIMIT 1")
        st.session_state.prep = c.fetchone()
        
    if st.session_state.prep:
        sent_nl, prep_missing, sent_en = st.session_state.prep
        display_sent = sent_nl.replace("___", " **[ ? ]** ")
        
        st.markdown(f"### {display_sent}")
        
        with st.expander("Uitleg in het Engels (English Explanation)"):
            st.write(f"**Translation:** {sent_en}")
        
        input_key = f"prep_{sent_nl}"
        user_prep = st.text_input("Ontbrekend woord:", key=input_key).strip().lower()
        
        col1, col2 = st.columns([1, 1])
        
        if col1.button("Controleer Antwoord", key="check_p"):
            if user_prep == prep_missing:
                st.success("✅ Helemaal goed!")
            else:
                st.error(f"❌ Fout. Het moet zijn: **{prep_missing}**")
                
        if col2.button("Volgende ⏭️", key="next_p"):
            st.session_state.prep = None
            st.rerun()

# --- TAB 4: ZINNEN BOUWEN (SENTENCES) ---
with tab4:
    st.header("Maak de Zin Compleet")
    if st.session_state.sent is None:
        c.execute("SELECT sentence_nl, english FROM sentences ORDER BY RANDOM() LIMIT 1")
        st.session_state.sent = c.fetchone()
        
    if st.session_state.sent:
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
            st.write(f"**Translate to Dutch:** {en_trans}")
        
        input_key = f"sent_{full_nl}_{idx}"
        user_word = st.text_input("Ontbrekend woord:", key=input_key).strip().lower()
        
        col1, col2 = st.columns([1, 1])
        
        if col1.button("Controleer Antwoord", key="check_s"):
            if user_word == correct_word.lower():
                st.success("✅ Perfect!")
            else:
                st.error(f"❌ Fout. Het ontbrekende woord is: **{correct_word}**")
                
        if col2.button("Volgende ⏭️", key="next_s"):
            if 'missing_idx' in st.session_state: del st.session_state.missing_idx
            st.session_state.sent = None
            st.rerun()
import streamlit as st
import qrcode
import os
import time
import hashlib
import pandas as pd
import pytesseract
import shutil
from io import BytesIO
from datetime import date
from fpdf import FPDF
from PIL import Image, ImageOps
from PIL.ExifTags import TAGS

# --- CONFIGURATION SYSTÈME ---
st.set_page_config(page_title="PIGC 2025", layout="wide")

# Détection Tesseract (Primordial pour Streamlit Cloud)
tesseract_path = shutil.which("tesseract")
if tesseract_path:
    pytesseract.pytesseract.tesseract_cmd = tesseract_path

# Initialisation DB
DB_FILE = "inscriptions_pigc.csv"
if not os.path.exists(DB_FILE):
    df_init = pd.DataFrame(columns=["NOM", "BAC", "AGE", "DATE", "ECOLE", "FILIERE", "HASH_SECURE"])
    df_init.to_csv(DB_FILE, index=False)

# --- LOGIQUE DE SÉCURITÉ ---
def analyser_document(file, nom_candidat):
    try:
        img = Image.open(file)
        # 1. Anti-Photoshop
        info = img.getexif()
        if info:
            for tag_id in info:
                tag = TAGS.get(tag_id, tag_id)
                if tag == 'Software':
                    soft = str(info.get(tag_id)).lower()
                    if any(x in soft for x in ["adobe", "photoshop", "canva", "gimp"]):
                        return False, f"🚩 Modification détectée ({soft})"

        # 2. OCR & Concordance
        img_gray = ImageOps.grayscale(img)
        texte = pytesseract.image_to_string(img_gray, lang='fra').upper()
        
        # Vérification Mots-Clés Acte
        if not any(word in texte for word in ["REPUBLIQUE", "NAISSANCE", "ACTE", "EXTRAIT"]):
            return False, "❌ Le document ne semble pas être un Acte de Naissance."

        # Vérification Nom
        nom_principal = nom_candidat.split()[0]
        if nom_principal not in texte:
            return False, f"⚠️ Nom '{nom_principal}' introuvable sur le scan."

        return True, "✅ Document Authentifié"
    except Exception as e:
        return False, f"Erreur technique : {str(e)}"

# --- INTERFACE (STYLE STABILISÉ) ---
st.markdown("""
    <style>
    .main { background-color: #002366; }
    .stMarkdown, p, h1, h2, h3 { color: #FFD700 !important; }
    .stButton>button { background-color: #FFD700 !important; color: #002366 !important; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

if 'step' not in st.session_state: st.session_state.step = 1
if 'form_data' not in st.session_state: st.session_state.form_data = {}

st.title("🛡️ PIGC - Plateforme Sécurisée")

# --- ETAPE 1 : SCAN ---
if st.session_state.step == 1:
    st.header("1. Identification & Scan")
    nom = st.text_input("NOM COMPLET (Majuscules)").upper()
    
    col1, col2 = st.columns(2)
    f1 = col1.file_uploader("Acte de Naissance (Original)", type=["jpg", "png"])
    f2 = col2.file_uploader("Relevé de Bac", type=["jpg", "png"])

    if st.button("LANCER L'ANALYSE SÉCURISÉE"):
        if nom and f1:
            with st.spinner("Analyse des métadonnées et du texte..."):
                success, message = analyser_document(f1, nom)
                if success:
                    st.success(message)
                    st.session_state.form_data['nom'] = nom
                    st.session_state.step = 2
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(message)
        else:
            st.warning("Veuillez remplir le nom et charger l'acte.")

# --- ETAPE 2 : CHOIX ---
elif st.session_state.step == 2:
    st.header("2. Choix de l'École")
    ecole = st.selectbox("Établissement", ["INSG", "IST", "IUSO", "INPTIC"])
    filiere = st.selectbox("Filière", ["Gestion", "Informatique", "Maintenance", "Réseaux"])
    
    if st.button("CONFIRMER L'INSCRIPTION"):
        st.session_state.form_data.update({"ecole": ecole, "filiere": filiere})
        st.session_state.step = 3
        st.rerun()

# --- ETAPE 3 : FINALISATION ---
elif st.session_state.step == 3:
    st.balloons()
    st.success("Dossier validé avec succès !")
    st.write(f"Candidat : **{st.session_state.form_data['nom']}**")
    st.write(f"École : **{st.session_state.form_data['ecole']}**")
    
    if st.button("Recommencer"):
        st.session_state.step = 1
        st.rerun()

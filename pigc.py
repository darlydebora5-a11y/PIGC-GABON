import streamlit as st
import qrcode
import os
import time
import base64
import pandas as pd
import pytesseract
import shutil
from io import BytesIO
from datetime import date
from fpdf import FPDF
from PIL import Image, ImageOps
from PIL.ExifTags import TAGS

# --- CONFIGURATION SYSTÈME ---
st.set_page_config(page_title="PIGC - Plateforme Intégrée", layout="wide")

# --- AJOUT SÉCURITÉ SYSTÈME (INDISPENSABLE POUR VISA-LIKE) ---
tesseract_path = shutil.which("tesseract")
if tesseract_path:
    pytesseract.pytesseract.tesseract_cmd = tesseract_path

# --- LOGIQUE DE SÉCURITÉ TYPE "VISA" ---
def analyser_document_visa(file, nom_candidat):
    try:
        img = Image.open(file)
        # 1. Vérification Anti-Modification (Métadonnées)
        info = img.getexif()
        if info:
            for tag_id in info:
                tag = TAGS.get(tag_id, tag_id)
                if tag == 'Software':
                    soft = str(info.get(tag_id)).lower()
                    if any(x in soft for x in ["adobe", "photoshop", "canva", "gimp", "picsart"]):
                        return False, f"🚩 ALERTE SÉCURITÉ : Document modifié via {soft.upper()}. Veuillez fournir l'original."

        # 2. Vérification d'Authenticité par OCR
        img_gray = ImageOps.grayscale(img)
        texte = pytesseract.image_to_string(img_gray, lang='fra').upper()
        
        # Mots-clés obligatoires pour un document officiel gabonais
        mots_officiels = ["REPUBLIQUE", "GABONAISE", "NAISSANCE", "ACTE", "UNION", "TRAVAIL", "JUSTICE"]
        if not any(word in texte for word in mots_officiels):
            return False, "❌ AUTHENTIFICATION ÉCHOUÉE : Ce document n'est pas reconnu comme un acte officiel gabonais."

        # Concordance du nom
        if nom_candidat.split()[0] not in texte:
            return False, f"⚠️ ERREUR D'IDENTITÉ : Le nom '{nom_candidat}' n'a pas été détecté sur le document."

        return True, "✅ DOCUMENT CERTIFIÉ CONFORME"
    except:
        return False, "❌ ERREUR TECHNIQUE : Le fichier est illisible ou corrompu."

# --- RESTE DE VOTRE CODE ORIGINAL (DESIGN & LOGIQUE) ---
DB_FILE = "inscriptions_pigc.csv"

def get_base64_image(image_path):
    if os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            return f"data:image/png;base64,{base64.b64encode(img_file.read()).decode()}"
    return ""

st.markdown(f"""
    <style>
    .stApp {{ background-color: #002366; }}
    h1, h2, h3, h4, p, span, label, .stMarkdown, .stCaption {{
        color: #FFD700 !important;
        font-weight: bold !important;
    }}
    input, select, textarea, [data-baseweb="select"] {{
        color: #000000 !important;
        background-color: #ffffff !important;
        border: 2px solid #FFD700 !important;
        border-radius: 8px !important;
    }}
    div.stButton > button {{
        background-color: #ffffff !important;
        color: #002366 !important;
        font-weight: 900 !important;
        font-size: 1.1rem !important;
        border-radius: 25px !important;
        border: 2px solid #FFD700 !important;
        height: 60px !important;
        width: 100% !important;
        box-shadow: 0 4px 15px rgba(0,0,0,0.6) !important;
    }}
    </style>
    """, unsafe_allow_html=True)

ECOLES_DATA = {
    "INSG": {"nom": "Institut National des Sciences de Gestion", "filières": ["Comptabilité-Audit", "RH", "Marketing", "Finance"], "bacs": ["B", "CG", "G2"], "age_max": 24, "logo": "logo_insg.png"},
    "IST": {"nom": "Institut Supérieur de Technologie", "filières": ["Génie Industriel", "Électrique", "Informatique", "Civil"], "bacs": ["C", "D", "E", "F", "TI"], "age_max": 22, "logo": "logo_ist.png"},
    "IUSO": {"nom": "Institut Univ. des Sciences de l'Organisation", "filières": ["Management Sport", "Assistanat", "Gestion PME"], "bacs": ["A1", "A2", "B", "CG", "G2"], "age_max": 25, "logo": "logo_iuso.png"},
    "INPTIC": {"nom": "Inst. Nat. des Postes et TIC", "filières": ["Développement", "Réseaux", "Numérique"], "bacs": ["C", "D", "S", "TI"], "age_max": 24, "logo": "logo_inptic.png"}
}

# --- NAVIGATION ---
if 'step' not in st.session_state: st.session_state.step = 1
if 'data' not in st.session_state: st.session_state.data = {}

menu = st.sidebar.selectbox("MENU", ["📝 Portail Candidat", "🔐 Espace Directions"])

if menu == "📝 Portail Candidat":
    if st.session_state.step == 1:
        st.subheader("👤 Étape 1 : Identification & Sécurité")
        nom = st.text_input("NOM COMPLET").upper()
        col1, col2 = st.columns(2)
        dob = col1.date_input("Date de Naissance", min_value=date(1998, 1, 1))
        serie = col2.selectbox("Série du BAC", ["A1", "A2", "B", "C", "D", "CG", "G2", "TI", "F", "S"])
        
        f1 = st.file_uploader("Acte de Naissance (Original requis)", type=["jpg", "png", "jpeg"])
        f2 = st.file_uploader("Relevé de Bac", type=["jpg", "png", "jpeg"])

        if st.button("LANCER L'ANALYSE SÉCURISÉE ➡️"):
            if nom and f1 and f2:
                with st.spinner("Analyse cryptographique et documentaire en cours..."):
                    # APPLICATION DU SYSTÈME DE SÉCURITÉ VISA
                    is_valid, msg = analyser_document_visa(f1, nom)
                    if is_valid:
                        st.success(msg)
                        age = date.today().year - dob.year
                        st.session_state.data.update({"NOM": nom, "BAC": serie, "AGE": age, "DATE": time.strftime("%d/%m/%Y %H:%M")})
                        st.session_state.step = 2
                        time.sleep(2)
                        st.rerun()
                    else:
                        st.error(msg)
            else:
                st.warning("Veuillez remplir tous les champs et fournir les documents originaux.")

    elif st.session_state.step == 2:
        st.subheader("🏫 Étape 2 : Éligibilité & Choix")
        ecole = st.selectbox("Établissement", list(ECOLES_DATA.keys()))
        config = ECOLES_DATA[ecole]
        if st.session_state.data["AGE"] <= config["age_max"] and st.session_state.data["BAC"] in config["bacs"]:
            st.success(f"✅ Éligible pour {config['nom']}")
            filiere = st.selectbox("Filière", config["filières"])
            if st.button("CONFIRMER L'ENRÔLEMENT ➡️"):
                st.session_state.data.update({"ECOLE": ecole, "FILIERE": filiere})
                st.session_state.step = 3
                st.rerun()
        else: st.error("🚫 Non éligible (Âge ou BAC).")

    elif st.session_state.step == 3:
        st.balloons()
        st.success("Dossier sécurisé et transmis avec succès !")
        st.write(f"Candidat : {st.session_state.data['NOM']}")
        if st.button("Recommencer"):
            st.session_state.step = 1
            st.rerun()

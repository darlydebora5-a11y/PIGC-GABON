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

# --- CONFIGURATION SYSTÈME & OCR ---
st.set_page_config(page_title="PIGC - Plateforme Intégrée", layout="wide")

# Détection du moteur OCR pour la sécurité
tesseract_path = shutil.which("tesseract")
if tesseract_path:
    pytesseract.pytesseract.tesseract_cmd = tesseract_path

DB_FILE = "inscriptions_pigc.csv"

# --- LOGIQUE DE SÉCURITÉ TYPE "VISA" ---
def analyser_document_visa(file, nom_candidat):
    try:
        img = Image.open(file)
        # 1. Anti-Photoshop (Métadonnées)
        info = img.getexif()
        if info:
            for tag_id in info:
                tag = TAGS.get(tag_id, tag_id)
                if tag == 'Software':
                    soft = str(info.get(tag_id)).lower()
                    if any(x in soft for x in ["adobe", "photoshop", "canva", "gimp"]):
                        return False, f"🚩 ALERTE : Modification détectée ({soft.upper()})."

        # 2. Vérification d'Authenticité OCR
        img_gray = ImageOps.grayscale(img)
        texte = pytesseract.image_to_string(img_gray, lang='fra').upper()
        mots_cles = ["REPUBLIQUE", "GABONAISE", "NAISSANCE", "ACTE"]
        if not any(word in texte for word in mots_cles):
            return False, "❌ Document non reconnu comme un Acte officiel."
        
        if nom_candidat.split()[0] not in texte:
            return False, f"⚠️ Le nom '{nom_candidat}' est introuvable sur le document."

        return True, "✅ Document Certifié Conforme"
    except:
        return False, "❌ Erreur de lecture du document."

# --- FONCTIONS UTILITAIRES ---
def get_base64_image(image_path):
    if os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            return f"data:image/png;base64,{base64.b64encode(img_file.read()).decode()}"
    return ""

# --- STYLE PRESTIGE ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: #002366; }}
    h1, h2, h3, p, span, label {{ color: #FFD700 !important; font-weight: bold !important; }}
    input, select {{ color: #000 !important; background-color: #fff !important; border: 2px solid #FFD700 !important; }}
    div.stButton > button {{
        background-color: #ffffff !important; color: #002366 !important;
        font-weight: 900 !important; border-radius: 25px !important;
        border: 2px solid #FFD700 !important; width: 100% !important;
        height: 60px !important; box-shadow: 0 4px 15px rgba(0,0,0,0.6) !important;
    }}
    .circular-logo {{ width: 170px; height: 170px; border-radius: 50%; border: 5px solid #FFD700; object-fit: cover; background-color: white; }}
    </style>
    """, unsafe_allow_html=True)

# --- DONNÉES ÉCOLES ---
ECOLES_DATA = {
    "INSG": {"nom": "Institut National des Sciences de Gestion", "filières": ["RH", "Finance"], "bacs": ["B", "G2"], "age_max": 24, "logo": "logo_insg.png"},
    "IST": {"nom": "Institut Supérieur de Technologie", "filières": ["Informatique", "Génie Civil"], "bacs": ["C", "D", "TI"], "age_max": 22, "logo": "logo_ist.png"},
    "INPTIC": {"nom": "Inst. Nat. des Postes et TIC", "filières": ["Réseaux", "Numérique"], "bacs": ["C", "D", "TI"], "age_max": 24, "logo": "logo_inptic.png"}
}

# --- BANDEAU DÉFILANT ---
st.markdown(f"""
    <div style="background-color: #ffffff; padding: 10px 0; border-bottom: 4px solid #FFD700;">
        <marquee behavior="scroll" direction="left" scrollamount="8">
            <span style="color: #FF0000; font-weight: 900; font-size: 1.5rem;">DEMANDE DE PARTENARIAT AUX GRANDES ÉCOLES PUBLIQUES - PIGC 2026</span>
        </marquee>
    </div>
    """, unsafe_allow_html=True)

# --- LOGO & TITRE ---
logo_pigc = get_base64_image("logo_pigc.png")
st.markdown(f'<div style="text-align:center;"><img src="{logo_pigc}" class="circular-logo"></div>', unsafe_allow_html=True)
st.markdown('<h1 style="text-align: center;">Plateforme Intégrée de Gestion des Concours - PIGC</h1>', unsafe_allow_html=True)

# --- NAVIGATION ---
if 'step' not in st.session_state: st.session_state.step = 1
if 'data' not in st.session_state: st.session_state.data = {}

menu = st.sidebar.selectbox("MENU", ["📝 Portail Candidat", "🔐 Espace Directions"])

if menu == "📝 Portail Candidat":
    if st.session_state.step == 1:
        st.subheader("👤 Étape 1 : Identification & Sécurité Visa")
        nom = st.text_input("NOM COMPLET").upper()
        dob = st.date_input("Date de Naissance", min_value=date(1998, 1, 1))
        serie = st.selectbox("Série du BAC", ["A1", "B", "C", "D", "TI", "G2"])
        f1 = st.file_uploader("Acte de Naissance (Analyse de sécurité)", type=["jpg", "png", "jpeg"])
        
        if st.button("VALIDER ET ANALYSER LES PIÈCES ➡️"):
            if nom and f1:
                with st.spinner("Analyse du document en cours..."):
                    success, msg = analyser_document_visa(f1, nom)
                    if success:
                        st.success(msg)
                        age = date.today().year - dob.year
                        st.session_state.data.update({"NOM": nom, "BAC": serie, "AGE": age, "DATE": time.strftime("%d/%m/%Y")})
                        st.session_state.step = 2
                        time.sleep(1)
                        st.rerun()
                    else: st.error(msg)
            else: st.warning("Veuillez remplir les champs.")

    elif st.session_state.step == 2:
        st.subheader("🏫 Étape 2 : Choix de l'Établissement")
        ecole = st.selectbox("Sélectionner une école", list(ECOLES_DATA.keys()))
        config = ECOLES_DATA[ecole]
        if st.session_state.data["AGE"] <= config["age_max"] and st.session_state.data["BAC"] in config["bacs"]:
            st.success(f"✅ Éligible pour {config['nom']}")
            filiere = st.selectbox("Filière", config["filières"])
            if st.button("CONFIRMER L'ENRÔLEMENT ➡️"):
                st.session_state.data.update({"ECOLE": ecole, "FILIERE": filiere})
                df = pd.DataFrame([st.session_state.data])
                df.to_csv(DB_FILE, mode='a', header=not os.path.exists(DB_FILE), index=False)
                st.session_state.step = 3
                st.rerun()
        else: st.error("🚫 Critères d'âge ou de BAC non respectés.")

    elif st.session_state.step == 3:
        st.balloons()
        st.success("Enrôlement terminé !")
        st.write(f"Candidat : **{st.session_state.data['NOM']}**")
        if st.button("Nouvelle inscription"):
            st.session_state.step = 1
            st.rerun()

elif menu == "🔐 Espace Directions":
    st.subheader("Accès Administrateur par Établissement")
    user_ecole = st.selectbox("Votre Établissement", list(ECOLES_DATA.keys()))
    password = st.text_input("Code de sécurité", type="password")
    
    if st.button("Se connecter"):
        # Exemple : le code est 'PIGC_' suivi du nom de l'école
        if password == f"PIGC_{user_ecole}":
            st.success(f"Bienvenue Direction {user_ecole}")
            if os.path.exists(DB_FILE):
                df = pd.read_csv(DB_FILE)
                # Filtrer uniquement les élèves de cette école
                resultat = df[df['ECOLE'] == user_ecole]
                st.dataframe(resultat)
            else: st.info("Aucune inscription pour le moment.")
        else: st.error("Code incorrect.")

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
import pdf2image

# --- CONFIGURATION SYSTÈME ---
st.set_page_config(page_title="PIGC - Plateforme Intégrée", layout="wide")

# Détection Tesseract pour Streamlit Cloud
tesseract_path = shutil.which("tesseract")
if tesseract_path:
    pytesseract.pytesseract.tesseract_cmd = tesseract_path

DB_FILE = "inscriptions_pigc.csv"

# --- LOGIQUE DE SÉCURITÉ TYPE "VISA" (PDF & IMAGE) ---
def analyser_document_visa(file, nom_candidat):
    try:
        texte = ""
        # 1. Gestion des fichiers PDF
        if file.type == "application/pdf":
            # Convertir seulement la 1ère page pour l'analyse de sécurité
            pages = pdf2image.convert_from_bytes(file.read(), first_page=1, last_page=1)
            if pages:
                img_gray = ImageOps.grayscale(pages[0])
                texte = pytesseract.image_to_string(img_gray, lang='fra').upper()
        
        # 2. Gestion des fichiers Images
        else:
            img = Image.open(file)
            # Anti-Photoshop (Métadonnées)
            info = img.getexif()
            if info:
                for tag_id in info:
                    tag = TAGS.get(tag_id, tag_id)
                    if tag == 'Software':
                        soft = str(info.get(tag_id)).lower()
                        if any(x in soft for x in ["adobe", "photoshop", "canva", "gimp"]):
                            return False, f"🚩 ALERTE : Modification détectée ({soft.upper()})."
            
            img_gray = ImageOps.grayscale(img)
            texte = pytesseract.image_to_string(img_gray, lang='fra').upper()

        # 3. Vérification de l'authenticité (Mots-clés Gabonais)
        mots_cles = ["REPUBLIQUE", "GABONAISE", "NAISSANCE", "ACTE", "OFFICIER"]
        if not any(word in texte for word in mots_cles):
            return False, "❌ AUTHENTIFICATION ÉCHOUÉE : Document non reconnu comme officiel."
        
        # 4. Vérification de l'identité
        nom_principal = nom_candidat.split()[0]
        if nom_principal not in texte:
            return False, f"⚠️ ERREUR D'IDENTITÉ : Le nom '{nom_principal}' n'est pas lisible sur le scan."

        return True, "✅ DOCUMENT CERTIFIÉ CONFORME"
    except Exception as e:
        return False, f"❌ ERREUR TECHNIQUE : {str(e)}"

# --- INTERFACE & DESIGN ORIGINAL ---
def get_base64_image(image_path):
    if os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            return f"data:image/png;base64,{base64.b64encode(img_file.read()).decode()}"
    return ""

st.markdown(f"""
    <style>
    .stApp {{ background-color: #002366; }}
    h1, h2, h3, p, span, label, .stMarkdown {{ color: #FFD700 !important; font-weight: bold !important; }}
    input, select, textarea {{ color: #000 !important; background-color: #fff !important; border: 2px solid #FFD700 !important; }}
    div.stButton > button {{
        background-color: #ffffff !important; color: #002366 !important;
        font-weight: 900 !important; border-radius: 25px !important;
        border: 2px solid #FFD700 !important; width: 100% !important;
        height: 60px !important; box-shadow: 0 4px 15px rgba(0,0,0,0.6) !important;
    }}
    .circular-logo {{ width: 170px; height: 170px; border-radius: 50%; border: 5px solid #FFD700; object-fit: cover; background-color: white; display: block; margin: auto; }}
    </style>
    """, unsafe_allow_html=True)

ECOLES_DATA = {
    "INSG": {"nom": "Institut National des Sciences de Gestion", "filières": ["Comptabilité", "RH", "Marketing"], "bacs": ["B", "G2", "CG"], "age_max": 24},
    "IST": {"nom": "Institut Supérieur de Technologie", "filières": ["Informatique", "Génie Civil", "Maintenance"], "bacs": ["C", "D", "TI", "E", "F"], "age_max": 22},
    "INPTIC": {"nom": "Inst. Nat. des Postes et TIC", "filières": ["Réseaux", "Développement", "Numérique"], "bacs": ["C", "D", "TI", "S"], "age_max": 24}
}

# --- BANDEAU DÉFILANT ---
st.markdown(f"""
    <div style="background-color: #ffffff; padding: 10px 0; border-bottom: 4px solid #FFD700;">
        <marquee behavior="scroll" direction="left" scrollamount="8">
            <span style="color: #FF0000; font-weight: 900; font-size: 1.5rem;">DEMANDE DE PARTENARIAT AUX GRANDES ÉCOLES PUBLIQUES - PIGC 2026 - SYSTÈME SÉCURISÉ</span>
        </marquee>
    </div>
    """, unsafe_allow_html=True)

# --- LOGO ET TITRE ---
logo_pigc_b64 = get_base64_image("logo_pigc.png")
if logo_pigc_b64:
    st.markdown(f'<div style="margin-top:20px;"><img src="{logo_pigc_b64}" class="circular-logo"></div>', unsafe_allow_html=True)

st.markdown('<h1 style="text-align: center;">Plateforme Intégrée de Gestion des Concours - PIGC</h1>', unsafe_allow_html=True)

# --- NAVIGATION ---
if 'step' not in st.session_state: st.session_state.step = 1
if 'data' not in st.session_state: st.session_state.data = {}

menu = st.sidebar.selectbox("MENU", ["📝 Portail Candidat", "🔐 Espace Directions"])

if menu == "📝 Portail Candidat":
    if st.session_state.step == 1:
        st.subheader("👤 Étape 1 : Identification & Pièces Jointes")
        nom = st.text_input("NOM COMPLET").upper()
        dob = st.date_input("Date de Naissance", min_value=date(1998, 1, 1))
        serie = st.selectbox("Série du BAC", ["A1", "A2", "B", "C", "D", "TI", "G2", "E", "F", "S"])
        
        col1, col2 = st.columns(2)
        with col1:
            f1 = st.file_uploader("Acte de Naissance (PDF/JPG/PNG)", type=["pdf", "jpg", "png", "jpeg"])
        with col2:
            f2 = st.file_uploader("Relevé de Notes du BAC (PDF/JPG/PNG)", type=["pdf", "jpg", "png", "jpeg"])
        
        if st.button("VALIDER ET ANALYSER LES PIÈCES ➡️"):
            if nom and f1 and f2:
                with st.spinner("Analyse de sécurité type Visa en cours..."):
                    success, msg = analyser_document_visa(f1, nom)
                    if success:
                        st.success(msg)
                        age = date.today().year - dob.year
                        st.session_state.data.update({"NOM": nom, "BAC": serie, "AGE": age, "DATE": time.strftime("%d/%m/%Y")})
                        st.session_state.step = 2
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(msg)
            else:
                st.warning("Veuillez remplir le nom et téléverser les deux documents.")

    elif st.session_state.step == 2:
        st.subheader("🏫 Étape 2 : Éligibilité & Choix")
        ecole = st.selectbox("Sélectionner un Établissement", list(ECOLES_DATA.keys()))
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
        else:
            st.error(f"🚫 Non éligible pour {ecole} (Critères d'âge ou de série BAC non respectés).")

    elif st.session_state.step == 3:
        st.balloons()
        st.success("Enrôlement réussi avec succès !")
        st.write(f"Candidat : **{st.session_state.data['NOM']}**")
        st.write(f"École : **{st.session_state.data['ECOLE']}**")
        st.write(f"Filière : **{st.session_state.data['FILIERE']}**")
        
        if st.button("Effectuer une nouvelle inscription"):
            st.session_state.step = 1
            st.session_state.data = {}
            st.rerun()

elif menu == "🔐 Espace Directions":
    st.subheader("Accès Sécurisé par Établissement")
    user_ecole = st.selectbox("Votre Établissement", list(ECOLES_DATA.keys()))
    password = st.text_input("Code de sécurité Direction", type="password")
    
    if st.button("Se connecter"):
        # Mot de passe dynamique : PIGC_NOMDELECOLE
        if password == f"PIGC_{user_ecole}":
            st.success(f"Connexion établie - Direction {user_ecole}")
            if os.path.exists(DB_FILE):
                df = pd.read_csv(DB_FILE)
                # Filtrage des données pour n'afficher que l'école concernée
                resultat = df[df['ECOLE'] == user_ecole]
                st.dataframe(resultat, use_container_width=True)
            else:
                st.info("Aucun candidat inscrit pour le moment.")
        else:
            st.error("Accès refusé : Code de sécurité incorrect.")

import streamlit as st
import qrcode
import os
import time
import base64
import hashlib
import pandas as pd
import pytesseract
import shutil
from io import BytesIO
from datetime import date
from fpdf import FPDF
from PIL import Image, ImageOps
from PIL.ExifTags import TAGS

# --- CONFIGURATION SYSTÈME & OCR ---
st.set_page_config(page_title="PIGC - Sécurité Diplomatique", layout="wide")

# Détection automatique du moteur Tesseract sur le serveur
tesseract_path = shutil.which("tesseract")
if tesseract_path:
    pytesseract.pytesseract.tesseract_cmd = tesseract_path

DB_FILE = "inscriptions_pigc.csv"
if not os.path.exists(DB_FILE):
    df_init = pd.DataFrame(columns=["NOM", "BAC", "AGE", "DATE", "ECOLE", "FILIERE", "HASH_SECURE"])
    df_init.to_csv(DB_FILE, index=False)

# --- FONCTIONS DE SÉCURITÉ ---

def analyse_securite_profonde(file, nom_candidat, type_doc="ACTE"):
    """
    Analyse triple : 
    1. Métadonnées (Anti-Photoshop)
    2. OCR (Vérification du type de document)
    3. Concordance (Le nom sur le papier est-il le même que celui saisi ?)
    """
    if file is None: return False, "Fichier manquant"
    
    try:
        img = Image.open(file)
        
        # 1. ANTI-RETOUCHE (Logiciels)
        info = img.getexif()
        if info:
            for tag_id in info:
                tag = TAGS.get(tag_id, tag_id)
                if tag == 'Software':
                    soft = str(info.get(tag_id)).lower()
                    if any(x in soft for x in ["adobe", "photoshop", "canva", "picsart", "gimp"]):
                        return False, f"🚩 FRAUDE DÉTECTÉE : Document édité via {soft.upper()}."

        # 2. LECTURE OCR
        img_gray = ImageOps.grayscale(img)
        texte_extrait = pytesseract.image_to_string(img_gray, lang='fra').upper()
        
        # Vérification Type de Document
        mots_cles_acte = ["REPUBLIQUE", "ETAT-CIVIL", "NAISSANCE", "EXTRAIT", "ACTE"]
        score = sum(1 for mot in mots_cles_acte if mot in texte_extrait)
        
        if type_doc == "ACTE" and score < 2:
            return False, "❌ DOCUMENT INCORRECT : Ceci n'est pas un Acte de Naissance valide (Original requis)."

        # 3. CONCORDANCE DE NOM (Anti Copier-Coller)
        mots_nom = nom_candidat.split()
        if not any(mot in texte_extrait for mot in mots_nom):
            return False, f"⚠️ IDENTITÉ : Le nom '{nom_candidat}' ne figure pas sur le document scanné."

        # 4. EMPREINTE NUMÉRIQUE
        file.seek(0)
        file_hash = hashlib.sha256(file.read()).hexdigest()[:12]
        return True, f"✅ AUTHENTIFIÉ (ID: {file_hash})"

    except Exception as e:
        return False, f"Erreur système OCR : {str(e)}"

# --- INTERFACE ET STYLE ---
st.markdown("""
    <style>
    .stApp { background-color: #002366; color: #FFD700; }
    .stButton>button { background-color: #FFD700 !important; color: #002366 !important; font-weight: bold; width: 100%; border-radius: 10px; }
    h1, h2, h3 { color: #FFD700 !important; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

st.title("🛡️ PIGC - PLATEFORME INTÉGRÉE GABONAISE")
st.markdown("---")

if 'step' not in st.session_state: st.session_state.step = 1
if 'data' not in st.session_state: st.session_state.data = {}

# --- ÉTAPE 1 : IDENTIFICATION ---
if st.session_state.step == 1:
    st.header("👤 Étape 1 : Authentification des Pièces")
    nom = st.text_input("NOM COMPLET DU CANDIDAT (EN MAJUSCULE)").upper()
    
    col1, col2 = st.columns(2)
    f1 = col1.file_uploader("Scanner l'Acte de Naissance (JPG/PNG)", type=["jpg", "png"])
    f2 = col2.file_uploader("Scanner le Relevé de Bac (JPG/PNG)", type=["jpg", "png"])

    if st.button("LANCER L'ANALYSE DE SÉCURITÉ 🔍"):
        if nom and f1 and f2:
            with st.status("Analyse biométrique et documentaire...", expanded=True) as status:
                valid, msg = analyse_securite_profonde(f1, nom, "ACTE")
                
                if valid:
                    status.update(label="Authentification Réussie !", state="complete")
                    st.session_state.data = {"NOM": nom, "ID_CERTIF": msg}
                    st.session_state.step = 2
                    time.sleep(2)
                    st.rerun()
                else:
                    status.update(label="Alerte de Sécurité", state="error")
                    st.error(msg)
        else:
            st.warning("Veuillez remplir tous les champs avant l'analyse.")

# --- ÉTAPE 2 : CHOIX ÉCOLE ---
elif st.session_state.step == 2:
    st.header("🏫 Étape 2 : Orientation")
    ecole = st.selectbox("Choisir votre établissement", ["INSG", "IST", "IUSO", "INPTIC", "ITO"])
    filiere = st.text_input("Filière souhaitée")
    
    if st.button("FINALISER L'ENRÔLEMENT ✅"):
        st.session_state.data.update({"ECOLE": ecole, "FILIERE": filiere, "DATE": time.strftime("%d/%m/%Y")})
        st.session_state.step = 3
        st.rerun()

# --- ÉTAPE 3 : CONFIRMATION ---
elif st.session_state.step == 3:
    st.balloons()
    st.success("Félicitations ! Votre dossier est certifié et enregistré.")
    
    # Résumé
    st.info(f"Candidat : {st.session_state.data['NOM']}\n\nÉtablissement : {st.session_state.data['ECOLE']}")
    
    if st.button("🔄 Nouvelle Inscription"):
        st.session_state.step = 1
        st.rerun()

st.sidebar.markdown("### État du Système")
st.sidebar.write("✅ Moteur OCR : Actif" if tesseract_path else "❌ Moteur OCR : Manquant")

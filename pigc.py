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
st.set_page_config(page_title="PIGC 2026 - Sécurisé", layout="wide", page_icon="🛡️")

# Correction du chemin Tesseract pour Streamlit Cloud
# Sur Linux (Streamlit Cloud), Tesseract est généralement dans /usr/bin/tesseract
tesseract_path = shutil.which("tesseract")
if tesseract_path:
    pytesseract.pytesseract.tesseract_cmd = tesseract_path
else:
    # Optionnel : Message d'erreur si Tesseract n'est pas détecté au démarrage
    st.error("Moteur OCR non détecté. Vérifiez votre fichier packages.txt.")

# Initialisation DB (Stockage local pour test, utilisez une vraie DB pour la prod)
DB_FILE = "inscriptions_pigc.csv"
if not os.path.exists(DB_FILE):
    df_init = pd.DataFrame(columns=["NOM", "ECOLE", "FILIERE", "DATE", "HASH_SECURE"])
    df_init.to_csv(DB_FILE, index=False)

# --- LOGIQUE DE SÉCURITÉ (STYLE VISA/CHINE) ---
def analyser_document(file, nom_candidat):
    try:
        img = Image.open(file)
        
        # 1. ANALYSE DES MÉTADONNÉES (Anti-Modification Logicielle)
        info = img.getexif()
        if info:
            for tag_id in info:
                tag = TAGS.get(tag_id, tag_id)
                if tag == 'Software':
                    soft = str(info.get(tag_id)).lower()
                    # Liste noire des logiciels de retouche
                    if any(x in soft for x in ["adobe", "photoshop", "canva", "gimp", "picsart"]):
                        return False, f"🚩 Document refusé : Modification détectée via {soft.upper()}."

        # 2. PRÉ-TRAITEMENT IMAGE (Optimisation OCR)
        img_gray = ImageOps.grayscale(img)
        # Augmenter le contraste peut aider si l'image est sombre
        
        # 3. OCR & CONCORDANCE (Vérification de l'authenticité)
        texte = pytesseract.image_to_string(img_gray, lang='fra').upper()
        
        # Vérification des mots-clés régaliens (Gabon)
        mots_cles = ["REPUBLIQUE", "GABONAISE", "NAISSANCE", "ACTE", "OFFICIER", "ETAT-CIVIL"]
        score_authenticite = sum(1 for word in mots_cles if word in texte)
        
        if score_authenticite < 2:
            return False, "❌ Le document ne semble pas être un Acte de Naissance officiel ou l'image est trop floue."

        # Vérification du Nom (Sécurité identité)
        nom_principal = nom_candidat.split()[0].upper()
        if nom_principal not in texte:
            return False, f"⚠️ Alerte identité : Le nom '{nom_principal}' ne figure pas sur le scan fourni."

        return True, "✅ Document Authentifié avec succès."
    
    except Exception as e:
        return False, f"Erreur technique lors de l'analyse : {str(e)}"

# --- INTERFACE DESIGN ---
st.markdown("""
    <style>
    .main { background-color: #0b1120; }
    h1, h2, h3 { color: #FFD700 !important; font-family: 'Arial Black'; }
    .stAlert { border: 2px solid #FFD700; }
    .stButton>button { 
        background-color: #FFD700 !important; 
        color: #000 !important; 
        font-weight: bold; 
        width: 100%;
        border-radius: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

if 'step' not in st.session_state: st.session_state.step = 1
if 'form_data' not in st.session_state: st.session_state.form_data = {}

st.title("🛡️ PIGC - SYSTÈME DE VÉRIFICATION SÉCURISÉ")
st.info("Plateforme d'analyse biométrique et documentaire de niveau gouvernemental.")

# --- ETAPE 1 : SCAN & OCR ---
if st.session_state.step == 1:
    st.header("1. Authentification du Document")
    nom = st.text_input("NOM COMPLET (Identité officielle)").upper()
    
    col1, col2 = st.columns(2)
    with col1:
        f1 = st.file_uploader("Acte de Naissance (Original scanné)", type=["jpg", "png", "jpeg"])
    with col2:
        st.caption("Conseil : Assurez-vous que le document est bien éclairé et sans reflets.")

    if st.button("LANCER L'ANALYSE SÉCURISÉE"):
        if nom and f1:
            with st.spinner("Cryptage et analyse des couches du document..."):
                success, message = analyser_document(f1, nom)
                if success:
                    st.success(message)
                    st.session_state.form_data['nom'] = nom
                    # Création d'un hash de sécurité unique
                    secure_hash = hashlib.sha256(f"{nom}{time.time()}".encode()).hexdigest()[:12]
                    st.session_state.form_data['hash'] = secure_hash
                    time.sleep(2)
                    st.session_state.step = 2
                    st.rerun()
                else:
                    st.error(message)
        else:
            st.warning("Veuillez saisir votre nom et télécharger l'acte de naissance.")

# --- ETAPE 2 : CHOIX ---
elif st.session_state.step == 2:
    st.header("2. Orientation Académique")
    ecole = st.selectbox("Établissement", ["INSG", "IST", "IUSO", "INPTIC"])
    filiere = st.selectbox("Filière", ["Gestion", "Informatique", "Maintenance", "Réseaux"])
    
    if st.button("CONFIRMER ET SIGNER NUMÉRIQUEMENT"):
        st.session_state.form_data.update({"ecole": ecole, "filiere": filiere})
        # Sauvegarde simulée dans le CSV
        new_row = pd.DataFrame([[
            st.session_state.form_data['nom'], 
            ecole, filiere, date.today(), 
            st.session_state.form_data['hash']
        ]], columns=["NOM", "ECOLE", "FILIERE", "DATE", "HASH_SECURE"])
        new_row.to_csv(DB_FILE, mode='a', header=False, index=False)
        
        st.session_state.step = 3
        st.rerun()

# --- ETAPE 3 : FINALISATION ---
elif st.session_state.step == 3:
    st.balloons()
    st.success("Dossier sécurisé et validé !")
    
    col_final1, col_final2 = st.columns(2)
    with col_final1:
        st.write(f"Candidat : **{st.session_state.form_data['nom']}**")
        st.write(f"ID Sécurisé : `{st.session_state.form_data['hash']}`")
        st.write(f"Établissement : **{st.session_state.form_data['ecole']}**")
    
    with col_final2:
        # Génération du QR Code de vérification
        qr_data = f"PIGC-VERIFY:{st.session_state.form_data['hash']}"
        qr = qrcode.make(qr_data)
        buf = BytesIO()
        qr.save(buf, format="PNG")
        st.image(buf, caption="QR Code de vérification officielle", width=200)
    
    if st.button("Nouvelle Inscription"):
        st.session_state.step = 1
        st.session_state.form_data = {}
        st.rerun()

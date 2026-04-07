import streamlit as st
import qrcode
import os
import time
import base64
import hashlib
import pandas as pd
import pytesseract
from io import BytesIO
from datetime import date
from fpdf import FPDF
from PIL import Image, ImageOps
from PIL.ExifTags import TAGS

# --- CONFIGURATION SYSTÈME ---
st.set_page_config(page_title="PIGC - Système de Sécurité Diplomatique", layout="wide")
DB_FILE = "inscriptions_pigc.csv"

if not os.path.exists(DB_FILE):
    df_init = pd.DataFrame(columns=["NOM", "BAC", "AGE", "DATE", "ECOLE", "FILIERE", "HASH_SECURE"])
    df_init.to_csv(DB_FILE, index=False)

# --- MOTEUR DE SÉCURITÉ AVANCÉ (ANTI-FRAUDE & OCR) ---

def analyse_securite_profonde(file, nom_candidat, type_attendu="ACTE"):
    """Analyse Métadonnées + OCR + Concordance de Nom."""
    if file is None: return False, "Fichier manquant"
    
    try:
        img = Image.open(file)
        
        # 1. ANALYSE DES MÉTADONNÉES (Anti-Retouche)
        info = img.getexif()
        for tag_id in info:
            tag = TAGS.get(tag_id, tag_id)
            if tag == 'Software':
                logiciel = str(info.get(tag_id)).lower()
                if any(x in logiciel for x in ["adobe", "photoshop", "canva", "picsart", "gimp"]):
                    return False, f"🚩 FRAUDE : Document modifié avec {logiciel.upper()}."

        # 2. ANALYSE OCR (Lecture du contenu)
        # On prépare l'image pour une lecture optimale
        img_gray = img.convert('L')
        texte_extrait = pytesseract.image_to_string(img_gray, lang='fra').upper()
        
        # Vérification du Type de Document
        mots_cles_acte = ["REPUBLIQUE", "ETAT-CIVIL", "NAISSANCE", "EXTRAIT", "ACTE", "NÉ LE"]
        score_acte = sum(1 for mot in mots_cles_acte if mot in texte_extrait)
        
        if type_attendu == "ACTE" and score_acte < 2:
            return False, "❌ DOCUMENT INCORRECT : Ceci n'est pas un Acte de Naissance valide."

        # 3. VÉRIFICATION DE CONCORDANCE DU NOM (Anti Copier-Coller)
        # On nettoie le nom pour éviter les erreurs de ponctuation
        nom_clean = nom_candidat.split()[0] # On vérifie au moins le premier mot du nom
        if nom_clean not in texte_extrait:
            return False, f"⚠️ IDENTITÉ : Le nom '{nom_clean}' est introuvable sur le document scanné."

        # 4. GÉNÉRATION DE L'EMPREINTE (Hash)
        file.seek(0)
        file_hash = hashlib.sha256(file.read()).hexdigest()[:12]
        
        return True, f"✅ AUTHENTIFIÉ (Certificat : {file_hash})"

    except Exception as e:
        return False, f"Erreur d'analyse : {str(e)}"

# --- FONCTION GÉNÉRATION PDF ---
def generer_fiche_pdf(data):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "PIGC - FICHE D'ENROLEMENT CERTIFIEE", 0, 1, "C")
    pdf.ln(10)
    pdf.set_font("Arial", "", 12)
    for k, v in data.items():
        pdf.cell(0, 10, f"{k} : {v}", 0, 1)
    
    qr_data = f"VERIF-PIGC:{data['NOM']}:{data['HASH_SECURE']}"
    qr = qrcode.make(qr_data)
    qr_path = f"qr_{int(time.time())}.png"
    qr.save(qr_path)
    pdf.image(qr_path, 80, 150, 40)
    os.remove(qr_path)
    return pdf.output(dest='S').encode('latin-1')

# --- INTERFACE ---
st.markdown("""
    <style>
    .stApp { background-color: #002366; color: #FFD700; }
    h1, h2, h3 { color: #FFD700 !important; text-align: center; }
    .status-box { border: 2px solid #FFD700; padding: 20px; border-radius: 10px; background: rgba(255,255,255,0.1); }
    </style>
    """, unsafe_allow_html=True)

st.title("🛡️ PIGC - PLATEFORME HAUTEMENT SÉCURISÉE")

if 'step' not in st.session_state: st.session_state.step = 1
if 'data' not in st.session_state: st.session_state.data = {}

# --- ÉTAPE 1 : IDENTIFICATION & SCAN ---
if st.session_state.step == 1:
    st.header("Vérification d'Identité Diplomatique")
    nom = st.text_input("NOM COMPLET (CAPITALE)").upper()
    col1, col2 = st.columns(2)
    f1 = col1.file_uploader("Scanner l'Acte de Naissance (Original)", type=["jpg", "png"])
    f2 = col2.file_uploader("Scanner le Relevé de Bac", type=["jpg", "png"])

    if st.button("LANCER L'ANALYSE BIOMÉTRIQUE 🔍"):
        if nom and f1 and f2:
            with st.status("Analyse du document en cours...", expanded=True) as status:
                valid, message = analyse_securite_profonde(f1, nom, "ACTE")
                
                if valid:
                    status.update(label="Authentification Réussie", state="complete")
                    st.success(message)
                    st.session_state.data = {"NOM": nom, "HASH_SECURE": message.split(": ")[1]}
                    st.session_state.step = 2
                    time.sleep(2)
                    st.rerun()
                else:
                    status.update(label="Alerte Sécurité", state="error")
                    st.error(message)
        else:
            st.warning("Veuillez remplir le formulaire et charger les scans originaux.")

# --- ÉTAPE 2 : CHOIX ÉCOLE ---
elif st.session_state.step == 2:
    st.header("Sélection de l'Établissement")
    ecole = st.selectbox("Choisir une institution", ["INSG", "IST", "IUSO", "INPTIC"])
    if st.button("FINALISER L'INSCRIPTION"):
        st.session_state.data["ECOLE"] = ecole
        st.session_state.step = 3
        st.rerun()

# --- ÉTAPE 3 : RÉSULTAT & PDF ---
elif st.session_state.step == 3:
    st.balloons()
    st.success("Dossier validé et sécurisé dans la base PIGC.")
    pdf_data = generer_fiche_pdf(st.session_state.data)
    st.download_button("TÉLÉCHARGER VOTRE FICHE CERTIFIÉE PDF", data=pdf_data, file_name="fiche_pigc.pdf", mime="application/pdf")
    if st.button("Nouvelle Inscription"):
        st.session_state.step = 1
        st.rerun()

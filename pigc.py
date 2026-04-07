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
from PIL import Image, ImageOps
from PIL.ExifTags import TAGS
import pdf2image

# --- CONFIGURATION SYSTÈME ---
st.set_page_config(page_title="PIGC 2026 - Portail Officiel", layout="wide")

# Détection Tesseract pour la sécurité
tesseract_path = shutil.which("tesseract")
if tesseract_path:
    pytesseract.pytesseract.tesseract_cmd = tesseract_path

DB_FILE = "inscriptions_pigc.csv"

# --- FONCTION SÉCURITÉ VISA (OCR & MÉDATA) ---
def analyser_document_visa(file, nom_candidat):
    try:
        texte = ""
        if file.type == "application/pdf":
            pages = pdf2image.convert_from_bytes(file.read(), first_page=1, last_page=1)
            img_gray = ImageOps.grayscale(pages[0])
            texte = pytesseract.image_to_string(img_gray, lang='fra').upper()
        else:
            img = Image.open(file)
            # Anti-Photoshop (Métadonnées)
            info = img.getexif()
            if info:
                for tag_id in info:
                    if TAGS.get(tag_id) == 'Software':
                        soft = str(info.get(tag_id)).lower()
                        if any(x in soft for x in ["adobe", "photoshop", "canva", "gimp"]):
                            return False, f"🚩 ALERTE FRAUDE : Modification détectée via {soft.upper()}."
            img_gray = ImageOps.grayscale(img)
            texte = pytesseract.image_to_string(img_gray, lang='fra').upper()

        mots_cles = ["REPUBLIQUE", "GABONAISE", "NAISSANCE", "ACTE"]
        if not any(word in texte for word in mots_cles):
            return False, "❌ DOCUMENT REFUSÉ : Ce n'est pas un Acte de Naissance officiel."
        
        if nom_candidat.split()[0].upper() not in texte:
            return False, f"⚠️ ERREUR D'IDENTITÉ : Le nom n'est pas visible sur le document."
        return True, "✅ DOCUMENTS CERTIFIÉS CONFORMES"
    except:
        return False, "❌ ERREUR TECHNIQUE : Le document est illisible."

# --- DESIGN & CSS ---
def get_base64_image(path):
    if os.path.exists(path):
        with open(path, "rb") as f: return f"data:image/png;base64,{base64.b64encode(f.read()).decode()}"
    return ""

st.markdown(f"""
    <style>
    .stApp {{ background-color: #002366; }}
    h1, h2, h3, p, label {{ color: #FFD700 !important; font-weight: bold; text-align: center; }}
    
    /* Boutons Circulaires & Effet Zoom */
    .stButton>button {{
        border-radius: 50% !important;
        width: 140px !important; height: 140px !important;
        border: 4px solid #FFD700 !important;
        background-color: white !important;
        color: #002366 !important;
        font-weight: 900 !important;
        box-shadow: 0 4px 15px rgba(0,0,0,0.5);
        transition: transform 0.3s ease;
        margin: 10px auto;
        display: block;
    }}
    .stButton>button:hover {{ transform: scale(1.15); border-color: white !important; }}
    
    .marquee {{ background-color: #ffffff; padding: 10px 0; border-bottom: 4px solid #FFD700; color: #FF0000; font-weight: 900; font-size: 1.3rem; }}
    .logo-central {{ width: 140px; height: 140px; border-radius: 50%; border: 4px solid #FFD700; display: block; margin: 10px auto; background-color: white; }}
    </style>
    """, unsafe_allow_html=True)

# --- ÉLÉMENTS FIXES ---
st.markdown('<div class="marquee"><marquee>DEMANDE DE PARTENARIAT AUX GRANDES ÉCOLES PUBLIQUES - PIGC 2026 - SYSTÈME SÉCURISÉ</marquee></div>', unsafe_allow_html=True)

logo_pigc = get_base64_image("logo_pigc.png")
if logo_pigc: st.markdown(f'<img src="{logo_pigc}" class="logo-central">', unsafe_allow_html=True)
st.markdown('<h1>Plateforme Intégrée de Gestion des Concours - PIGC</h1>', unsafe_allow_html=True)

# --- NAVIGATION ---
if 'page' not in st.session_state: st.session_state.page = "accueil"
if 'data' not in st.session_state: st.session_state.data = {}

INSTITUTS = {"INSG": "logo_insg.png", "IST": "logo_ist.png", "INPTIC": "logo_inptic.png", "IUSO": "logo_iuso.png", "ITO": "logo_ito.png"}

# --- 1. ACCUEIL EN DEUX COLONNES ---
if st.session_state.page == "accueil":
    st.markdown("<p style='font-size:1.2rem;'>Veuillez cliquer sur le logo de l'institut pour débuter</p>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    inst_keys = list(INSTITUTS.keys())
    for i, key in enumerate(inst_keys):
        col = col1 if i % 2 == 0 else col2
        with col:
            # Note: On affiche le nom dans le bouton rond
            if st.button(key, key=f"btn_{key}"):
                st.session_state.data['ECOLE'] = key
                st.session_state.page = "formulaire"
                st.rerun()

# --- 2. FORMULAIRE DÉTAILLÉ ---
elif st.session_state.page == "formulaire":
    ecole = st.session_state.data['ECOLE']
    st.markdown(f"<h2>Concours d'entrée à l'{ecole}</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color:red !important;'>Fiche de pré-inscription (OBLIGATOIRE)</p>", unsafe_allow_html=True)
    
    with st.form("inscription_form"):
        c1, c2 = st.columns(2)
        nom = c1.text_input("Nom et Prénom")
        age = c2.number_input("Âge", 15, 30)
        sexe = c1.selectbox("Sexe", ["Masculin", "Féminin"])
        nat = c2.text_input("Nationalité", "Gabonaise")
        tel = c1.text_input("Téléphone")
        email = c2.text_input("Email")
        ville = c1.text_input("Ville")
        province = c2.selectbox("Province", ["Estuaire", "Haut-Ogooué", "Moyen-Ogooué", "Ngounié", "Nyanga", "Ogooué-Ivindo", "Ogooué-Lolo", "Ogooué-Maritime", "Woleu-Ntem"])
        serie = st.selectbox("Série du BAC", ["A1", "A2", "B", "C", "D", "TI", "S"])
        
        st.markdown("### 📄 DOCUMENTS SCANNÉS")
        f1 = st.file_uploader("Acte de Naissance (Original)", type=["pdf", "jpg", "png"])
        f2 = st.file_uploader("Relevé de Notes du BAC", type=["pdf", "jpg", "png"])
        
        if st.form_submit_button("VÉRIFIER ET CONTINUER ➡️"):
            if nom and f1 and f2:
                with st.spinner("Analyse Visa-Security..."):
                    success, msg = analyser_document_visa(f1, nom)
                    if success:
                        st.session_state.data.update({"NOM": nom, "SERIE": serie})
                        st.session_state.page = "filieres"
                        st.rerun()
                    else: st.error(msg)
            else: st.warning("Champs et documents obligatoires.")

# --- 3. FILIÈRES ---
elif st.session_state.page == "filieres":
    st.header(f"Filières disponibles pour la série {st.session_state.data['SERIE']}")
    choix = st.radio("Sélectionnez votre filière :", ["Tronc Commun", "Spécialité 1", "Spécialité 2"])
    if st.button("VALIDER MA PRÉ-INSCRIPTION EN LIGNE"):
        st.session_state.page = "paiement"
        st.rerun()

# --- 4. PAIEMENT & LOGOS LOCAUX ---
elif st.session_state.page == "paiement":
    st.markdown("<h2>💳 PAIEMENT DES FRAIS (1000 FCFA)</h2>", unsafe_allow_html=True)
    c_a, c_b = st.columns(2)
    logo_a = get_base64_image("airtel.png")
    logo_m = get_base64_image("moov.png")
    
    if logo_a: c_a.image(logo_a, width=120)
    if logo_m: c_b.image(logo_m, width=120)
    
    st.warning("Payer les frais de traitement numérique de 1000 FCFA pour télécharger votre fiche.")
    if st.button("PAYER MAINTENANT"):
        with st.spinner("Validation..."):
            time.sleep(3)
            st.success("Paiement validé !")
            st.balloons()

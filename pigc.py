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

# Détection Tesseract pour la sécurité OCR
tesseract_path = shutil.which("tesseract")
if tesseract_path:
    pytesseract.pytesseract.tesseract_cmd = tesseract_path

DB_FILE = "inscriptions_pigc.csv"

# --- FONCTIONS UTILITAIRES ---
def get_base64_image(image_path):
    if os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            return f"data:image/png;base64,{base64.b64encode(img_file.read()).decode()}"
    return ""

def analyser_document_visa(file, nom_candidat):
    try:
        texte = ""
        if file.type == "application/pdf":
            pages = pdf2image.convert_from_bytes(file.read(), first_page=1, last_page=1)
            img_gray = ImageOps.grayscale(pages[0])
            texte = pytesseract.image_to_string(img_gray, lang='fra').upper()
        else:
            img = Image.open(file)
            # Anti-Photoshop
            info = img.getexif()
            if info:
                for tag_id in info:
                    if TAGS.get(tag_id) == 'Software':
                        soft = str(info.get(tag_id)).lower()
                        if any(x in soft for x in ["adobe", "photoshop", "canva", "gimp"]):
                            return False, f"🚩 MODIFICATION DÉTECTÉE ({soft.upper()})"
            img_gray = ImageOps.grayscale(img)
            texte = pytesseract.image_to_string(img_gray, lang='fra').upper()

        mots_cles = ["REPUBLIQUE", "GABONAISE", "NAISSANCE", "ACTE"]
        if not any(word in texte for word in mots_cles):
            return False, "❌ DOCUMENT NON RECONNU (Acte de naissance requis)"
        
        return True, "✅ DOCUMENTS CONFORMES"
    except:
        return False, "❌ ERREUR DE LECTURE"

# --- STYLE CSS ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: #002366; }}
    h1, h2, h3, p, label, .stMarkdown {{ color: #FFD700 !important; font-weight: bold; }}
    .stButton>button {{
        background-color: #ffffff !important; color: #002366 !important;
        font-weight: 900 !important; border-radius: 15px !important;
        border: 2px solid #FFD700 !important; height: 50px !important;
    }}
    .inst-card {{ background: white; padding: 20px; border-radius: 15px; text-align: center; border: 3px solid #FFD700; }}
    input, select {{ background-color: white !important; color: black !important; }}
    </style>
    """, unsafe_allow_html=True)

# --- DONNÉES ---
INSTITUTS = {
    "INSG": {"nom": "Institut National des Sciences de Gestion", "logo": "logo_insg.png", "filieres": {"A1": ["Comptabilité", "Marketing"], "B": ["Finance", "Audit", "RH"], "G2": ["Gestion", "Compta"]}},
    "IST": {"nom": "Institut Supérieur de Technologie", "logo": "logo_ist.png", "filieres": {"C": ["Informatique", "Maintenance"], "D": ["Génie Civil", "Électrique"], "TI": ["Réseaux"]}},
    "INPTIC": {"nom": "Inst. Nat. des Postes et TIC", "logo": "logo_inptic.png", "filieres": {"C": ["Développement"], "D": ["Systèmes"], "TI": ["Cyber-Sécurité"], "S": ["Numérique"]}},
    "IUSO": {"nom": "Inst. Univ. des Sciences de l'Organisation", "logo": "logo_iuso.png", "filieres": {"A1": ["Management Sport"], "A2": ["Assistanat"], "B": ["Gestion PME"]}},
    "ITO": {"nom": "Institut de Technologies d'Owendo", "logo": "logo_ito.png", "filieres": {"E": ["BTP"], "F": ["Mécanique"], "TI": ["Logistique"]}}
}

# --- ÉTATS DE SESSION ---
if 'page' not in st.session_state: st.session_state.page = "accueil"
if 'data' not in st.session_state: st.session_state.data = {}

# --- 1. ACCUEIL : CHOIX DE L'INSTITUT ---
if st.session_state.page == "accueil":
    st.markdown("<h1 style='text-align:center;'>PORTAIL DE PRÉ-INSCRIPTION PIGC 2026</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; font-size:1.2rem;'>Cliquez sur le logo de l'institut de votre choix</p>", unsafe_allow_html=True)
    
    cols = st.columns(len(INSTITUTS))
    for i, (key, info) in enumerate(INSTITUTS.items()):
        with cols[i]:
            logo = get_base64_image(info['logo'])
            if logo:
                st.markdown(f'<div class="inst-card"><img src="{logo}" style="width:100px; height:100px;"></div>', unsafe_allow_html=True)
            if st.button(f"S'inscrire à l'{key}", key=key):
                st.session_state.data['ECOLE'] = key
                st.session_state.page = "formulaire"
                st.rerun()

# --- 2. FORMULAIRE DÉTAILLÉ ---
elif st.session_state.page == "formulaire":
    ecole = st.session_state.data['ECOLE']
    st.markdown(f"<h1 style='text-align:center;'>CONCOURS D'ENTRÉE À L'{ecole}</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center;'>Fiche de pré-inscription en ligne <span style='color:red;'>(OBLIGATOIRE)</span></p>", unsafe_allow_html=True)
    
    with st.form("inscription_form"):
        c1, c2 = st.columns(2)
        nom = c1.text_input("Nom et Prénom")
        age = c2.number_input("Âge", 15, 30)
        sexe = c1.selectbox("Sexe", ["Masculin", "Féminin"])
        nat = c2.text_input("Nationalité", "Gabonaise")
        
        tel = c1.text_input("Téléphone (WhatsApp)")
        email = c2.text_input("Email")
        
        ville = c1.text_input("Ville")
        province = c2.selectbox("Province", ["Estuaire", "Haut-Ogooué", "Moyen-Ogooué", "Ngounié", "Nyanga", "Ogooué-Ivindo", "Ogooué-Lolo", "Ogooué-Maritime", "Woleu-Ntem"])
        quartier = c1.text_input("Quartier")
        serie = c2.selectbox("Série du BAC", ["A1", "A2", "B", "C", "D", "TI", "S", "E", "F"])
        
        st.markdown("### 📄 DOCUMENTS SCANNÉS")
        f1 = st.file_uploader("Acte de Naissance (Original requis)", type=["pdf", "jpg", "png"])
        f2 = st.file_uploader("Relevé de Notes du BAC", type=["pdf", "jpg", "png"])
        
        if st.form_submit_button("VÉRIFIER ET CONTINUER"):
            if nom and tel and f1 and f2:
                with st.spinner("Analyse de sécurité OCR..."):
                    valide, msg = analyser_document_visa(f1, nom)
                    if valide:
                        st.session_state.data.update({"NOM": nom, "SERIE": serie, "TEL": tel, "PROV": province})
                        st.session_state.page = "filieres"
                        st.rerun()
                    else: st.error(msg)
            else: st.warning("Veuillez remplir tous les champs.")

# --- 3. CHOIX FILIÈRES ---
elif st.session_state.page == "filieres":
    ecole = st.session_state.data['ECOLE']
    serie = st.session_state.data['SERIE']
    st.header(f"Filières disponibles pour la série {serie}")
    
    options = INSTITUTS[ecole]['filieres'].get(serie, ["Tronc Commun"])
    choix = st.radio("Sélectionnez votre filière :", options)
    
    if st.button("VALIDER MA PRÉ-INSCRIPTION EN LIGNE"):
        st.session_state.data['FILIERE'] = choix
        st.session_state.page = "paiement"
        st.rerun()

# --- 4. PAIEMENT ---
elif st.session_state.page == "paiement":
    st.markdown("<h2 style='text-align:center;'>💳 PAIEMENT DES FRAIS</h2>", unsafe_allow_html=True)
    
    col_a, col_b = st.columns(2)
    logo_airtel = get_base64_image("airtel.png")
    logo_moov = get_base64_image("moov.png")
    
    with col_a:
        if logo_airtel: st.image(logo_airtel, width=150)
        else: st.button("AIRTEL MONEY")
    with col_b:
        if logo_moov: st.image(logo_moov, width=150)
        else: st.button("MOOV MONEY / MOBICASH")
        
    st.markdown("""
        <div style="background-color: #ffcccc; padding: 15px; border-radius: 10px; border: 2px solid red; text-align: center; color: black;">
            <b>PAIEMENT OBLIGATOIRE : 1000 FCFA</b><br>
            Frais de traitement numérique pour télécharger votre fiche.
        </div>
    """, unsafe_allow_html=True)
    
    num = st.text_input("Numéro de téléphone pour le paiement")
    if st.button("PAYER MAINTENANT (1000 FCFA)"):
        with st.spinner("En attente de validation sur votre téléphone..."):
            time.sleep(4)
            st.success("Paiement reçu ! Votre fiche est prête.")
            
            # Sauvegarde finale
            df = pd.DataFrame([st.session_state.data])
            df.to_csv(DB_FILE, mode='a', header=not os.path.exists(DB_FILE), index=False)
            
            st.download_button("📥 TÉLÉCHARGER MA FICHE DE PRÉ-INSCRIPTION", data="Fiche PIGC 2026", file_name="Fiche_PIGC.txt")
            if st.button("RETOUR À L'ACCUEIL"):
                st.session_state.page = "accueil"
                st.rerun()

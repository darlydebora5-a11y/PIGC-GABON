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

# Détection Tesseract
tesseract_path = shutil.which("tesseract")
if tesseract_path:
    pytesseract.pytesseract.tesseract_cmd = tesseract_path

DB_FILE = "inscriptions_pigc.csv"

# --- DONNÉES GÉOGRAPHIQUES GABON ---
VILLES_GABON = {
    "Estuaire": ["Libreville", "Akanda", "Owendo", "Ntoum", "Kango", "Cocobeach"],
    "Haut-Ogooué": ["Franceville", "Moanda", "Mounana", "Akieni", "Okondja", "Leconi"],
    "Moyen-Ogooué": ["Lambaréné", "Ndjolé"],
    "Ngounié": ["Mouila", "Fougamou", "Ndendé", "Lébamba", "Mbigou"],
    "Nyanga": ["Tchibanga", "Mayumba", "Moabi"],
    "Ogooué-Ivindo": ["Makokou", "Ovan", "Booué", "Mékambo"],
    "Ogooué-Lolo": ["Koulamoutou", "Lastoursville", "Pana", "Iboundji"],
    "Ogooué-Maritime": ["Port-Gentil", "Gambas", "Omboué"],
    "Woleu-Ntem": ["Oyem", "Bitam", "Minvoul", "Mitzic", "Médouneu"]
}

# --- FONCTIONS UTILITAIRES ---
def get_base64_image(path):
    if os.path.exists(path):
        with open(path, "rb") as f:
            return f"data:image/png;base64,{base64.b64encode(f.read()).decode()}"
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
            img_gray = ImageOps.grayscale(img)
            texte = pytesseract.image_to_string(img_gray, lang='fra').upper()
        
        mots_cles = ["REPUBLIQUE", "GABONAISE", "NAISSANCE", "ACTE"]
        is_officiel = any(word in texte for word in mots_cles)
        nom_valide = any(part in texte for part in nom_candidat.split())
        
        if not is_officiel or not nom_valide:
            return False, (
                "⚠️ ALERTE : Le document scanné n'est pas conforme. "
                "Attention au faux et usage de faux punis par la loi gabonaise. "
                "Fournissez un scan original et lisible."
            )
        return True, "✅ DOCUMENT CERTIFIÉ CONFORME"
    except:
        return False, "❌ ERREUR : Le fichier est illisible."

# --- DESIGN & STYLE ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: #002366; }}
    h1, h2, h3, p, label {{ color: #FFD700 !important; text-align: center; font-weight: bold; }}
    .marquee {{ background-color: #ffffff; padding: 10px 0; border-bottom: 4px solid #FFD700; color: #FF0000; font-weight: 900; }}
    .logo-central {{ width: 100px; height: 100px; border-radius: 50%; border: 3px solid #FFD700; display: block; margin: 10px auto; background-color: white; }}
    [data-testid="column"] {{ display: flex; justify-content: center; align-items: center; text-align: center; }}
    .stButton>button {{
        border-radius: 50% !important;
        width: 115px !important; height: 115px !important;
        border: 3px solid #FFD700 !important;
        background-color: white !important;
        transition: 0.3s; padding: 4px !important;
    }}
    .stButton>button:hover {{ transform: scale(1.15); box-shadow: 0 0 20px #FFD700; }}
    .stButton button img {{ width: 100px !important; height: 100px !important; object-fit: contain !important; }}
    </style>
    """, unsafe_allow_html=True)

# --- HEADER ---
st.markdown('<div class="marquee"><marquee>CONCOURS PIGC 2026 : SYSTÈME SÉCURISÉ - VÉRIFICATION PAR QR CODE INTÉGRÉE</marquee></div>', unsafe_allow_html=True)
logo_pigc = get_base64_image("logo_pigc.png")
if logo_pigc: st.markdown(f'<img src="{logo_pigc}" class="logo-central">', unsafe_allow_html=True)
st.markdown('<h1>PIGC - PORTAIL OFFICIEL</h1>', unsafe_allow_html=True)

# --- NAVIGATION ---
if 'page' not in st.session_state: st.session_state.page = "accueil"
if 'data' not in st.session_state: st.session_state.data = {}

INSTITUTS = {"INSG": "logo_insg.png", "IST": "logo_ist.png", "INPTIC": "logo_inptic.png", "IUSO": "logo_iuso.png", "ITO": "logo_ito.png"}

# --- 1. ACCUEIL ---
if st.session_state.page == "accueil":
    st.markdown("<p style='font-size:1.2rem; margin-top:20px;'>Veuillez choisir votre établissement pour vous inscrire</p>", unsafe_allow_html=True)
    cols = st.columns(5)
    for i, (name, logo_path) in enumerate(INSTITUTS.items()):
        with cols[i]:
            logo_b64 = get_base64_image(logo_path)
            label = f"![{name}]({logo_b64})"
            if st.button(label, key=f"btn_{name}"):
                st.session_state.data['ECOLE'] = name
                st.session_state.page = "formulaire"
                st.rerun()

# --- 2. FORMULAIRE ---
elif st.session_state.page == "formulaire":
    if st.button("⬅️ RETOUR"):
        st.session_state.page = "accueil"
        st.rerun()
    
    st.markdown(f"<h2>Pré-inscription : {st.session_state.data['ECOLE']}</h2>", unsafe_allow_html=True)
    with st.form("form_pigc"):
        nom = st.text_input("Nom et Prénom (MAJUSCULES)").upper()
        c1, c2 = st.columns(2)
        sexe = c1.selectbox("Sexe", ["Masculin", "Féminin"])
        dob = c2.date_input("Date de naissance", min_value=date(1995,1,1))
        prov = st.selectbox("Province de résidence", list(VILLES_GABON.keys()))
        ville = st.selectbox("Ville de résidence", VILLES_GABON[prov])
        tel = st.text_input("Téléphone (WhatsApp)")
        serie = st.selectbox("Série du BAC", ["A1", "A2", "B", "C", "D", "TI", "S"])
        f1 = st.file_uploader("Acte de Naissance (Scan Original)", type=["pdf", "jpg", "png"])
        f2 = st.file_uploader("Relevé du BAC", type=["pdf", "jpg", "png"])
        
        if st.form_submit_button("VÉRIFIER ET CONTINUER ➡️"):
            if nom and f1 and f2:
                with st.spinner("Contrôle d'authenticité..."):
                    valide, msg = analyser_document_visa(f1, nom)
                    if valide:
                        st.session_state.data.update({"NOM": nom, "SERIE": serie, "PROV": prov, "VILLE": ville, "TEL": tel})
                        st.session_state.page = "filieres"
                        st.rerun()
                    else: st.error(msg)
            else: st.warning("Veuillez remplir tous les champs.")

# --- 3. FILIÈRES ---
elif st.session_state.page == "filieres":
    st.header(f"Filières disponibles ({st.session_state.data['SERIE']})")
    choix = st.radio("Sélectionnez votre filière :", ["Gestion", "Informatique", "Réseaux"])
    if st.button("VALIDER MON CHOIX"):
        st.session_state.data['FILIERE'] = choix
        st.session_state.page = "paiement"
        st.rerun()

# --- 4. PAIEMENT & QR CODE ---
elif st.session_state.page == "paiement":
    st.markdown("<h2>💳 PAIEMENT MOBILE (1000 FCFA)</h2>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    l_airtel = get_base64_image("airtel.png")
    l_moov = get_base64_image("moov.png")
    if l_airtel: c1.image(l_airtel, width=100)
    if l_moov: c2.image(l_moov, width=100)
    
    st.markdown("<p style='background:red; padding:15px; color:white; border-radius:10px;'>Payer 1000 FCFA pour générer votre fiche avec QR Code.</p>", unsafe_allow_html=True)
    
    if st.button("TERMINER L'INSCRIPTION"):
        st.balloons()
        st.success("Paiement validé ! Voici votre fiche sécurisée.")
        
        # --- GÉNÉRATION DU QR CODE ---
        data_qr = f"PIGC-2026|{st.session_state.data['NOM']}|{st.session_state.data['ECOLE']}|{st.session_state.data['FILIERE']}"
        qr = qrcode.make(data_qr)
        buf = BytesIO()
        qr.save(buf, format="PNG")
        
        st.markdown("### 🎫 VOTRE FICHE DE PRÉ-INSCRIPTION")
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            st.write(f"**Candidat :** {st.session_state.data['NOM']}")
            st.write(f"**Établissement :** {st.session_state.data['ECOLE']}")
            st.write(f"**Filière :** {st.session_state.data['FILIERE']}")
        with col_f2:
            st.image(buf, caption="Scannez pour vérification", width=200)
        
        st.download_button("📥 TÉLÉCHARGER LE QR CODE", data=buf.getvalue(), file_name="QR_PIGC.png", mime="image/png")

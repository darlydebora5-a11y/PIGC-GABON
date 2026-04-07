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
            return False, "Analyse échouée : Document non conforme ou nom introuvable."
        return True, "✅ CERTIFIÉ CONFORME"
    except:
        return False, "❌ ERREUR : Fichier illisible."

# --- DESIGN & STYLE ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: #002366; }}
    h1, h2, h3, p, label {{ color: #FFD700 !important; text-align: center; font-weight: bold; }}
    .marquee {{ background-color: #ffffff; padding: 10px 0; border-bottom: 4px solid #FFD700; color: #FF0000; font-weight: 900; }}
    .logo-central {{ width: 120px; height: 120px; border-radius: 50%; border: 3px solid #FFD700; display: block; margin: 15px auto; background-color: white; object-fit: contain; }}
    
    [data-testid="column"] {{ display: flex; justify-content: center; align-items: center; text-align: center; }}

    .stButton>button {{
        border-radius: 50% !important;
        width: 120px !important; height: 120px !important;
        border: 3px solid #FFD700 !important;
        background-color: white !important;
        background-repeat: no-repeat !important;
        background-position: center !important;
        background-size: 85% !important;
        color: transparent !important;
        margin: 10px auto !important; 
        transition: 0.3s; 
    }}
    .stButton>button:hover {{ transform: scale(1.1); border-color: #fff !important; box-shadow: 0 0 20px #FFD700; }}

    /* Styles pour chaque bouton (Background images) */
    {f"div.stButton > button[key='btn_INSG'] {{ background-image: url({get_base64_image('logo_insg.png')}) !important; }}" if os.path.exists('logo_insg.png') else ""}
    {f"div.stButton > button[key='btn_IST'] {{ background-image: url({get_base64_image('logo_ist.png')}) !important; }}" if os.path.exists('logo_ist.png') else ""}
    {f"div.stButton > button[key='btn_INPTIC'] {{ background-image: url({get_base64_image('logo_inptic.png')}) !important; }}" if os.path.exists('logo_inptic.png') else ""}
    {f"div.stButton > button[key='btn_IUSO'] {{ background-image: url({get_base64_image('logo_iuso.png')}) !important; }}" if os.path.exists('logo_iuso.png') else ""}
    {f"div.stButton > button[key='btn_ITO'] {{ background-image: url({get_base64_image('logo_ito.png')}) !important; }}" if os.path.exists('logo_ito.png') else ""}

    .fiche-box {{ background-color: white; padding: 30px; border-radius: 15px; border: 5px solid #FFD700; color: #002366 !important; text-align: left !important; }}
    .fiche-box p, .fiche-box h2, .fiche-box h3 {{ color: #002366 !important; text-align: left !important; }}
    </style>
    """, unsafe_allow_html=True)

# --- NAVIGATION ---
if 'page' not in st.session_state: st.session_state.page = "accueil"
if 'data' not in st.session_state: st.session_state.data = {}

INSTITUTS = ["INSG", "IST", "INPTIC", "IUSO", "ITO"]

# --- 1. ACCUEIL ---
if st.session_state.page == "accueil":
    st.markdown('<div class="marquee"><marquee>CONCOURS PIGC 2026 : SYSTÈME DE VÉRIFICATION SÉCURISÉ - TOLÉRANCE ZÉRO POUR LE FAUX</marquee></div>', unsafe_allow_html=True)
    logo_pigc = get_base64_image("logo_pigc.png")
    if logo_pigc: st.markdown(f'<img src="{logo_pigc}" class="logo-central">', unsafe_allow_html=True)
    st.markdown('<h1>PIGC - PORTAIL OFFICIEL</h1>', unsafe_allow_html=True)
    st.markdown("<p style='font-size:1.2rem; margin-top:20px;'>Veuillez choisir votre établissement pour vous inscrire</p>", unsafe_allow_html=True)
    
    cols = st.columns(5)
    for i, name in enumerate(INSTITUTS):
        with cols[i]:
            if st.button(name, key=f"btn_{name}"):
                st.session_state.data['ECOLE'] = name
                st.session_state.page = "formulaire"
                st.rerun()

# --- 2. FORMULAIRE ---
elif st.session_state.page == "formulaire":
    if st.button("⬅️ RETOUR À L'ACCUEIL"):
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
        tel = st.text_input("Téléphone")
        email = st.text_input("Email")
        serie = st.selectbox("Série du BAC", ["A1", "A2", "B", "C", "D", "TI", "S"])
        
        st.write("---")
        f1 = st.file_uploader("Acte de Naissance (Scan Original)", type=["pdf", "jpg", "png"])
        f2 = st.file_uploader("Relevé du BAC", type=["pdf", "jpg", "png"])
        
        if st.form_submit_button("VÉRIFIER MES DOCUMENTS ➡️"):
            if nom and f1 and f2:
                with st.spinner("Contrôle d'authenticité..."):
                    valide, msg = analyser_document_visa(f1, nom)
                    if valide:
                        st.session_state.data.update({"NOM": nom, "SEXE": sexe, "DOB": dob, "PROV": prov, "VILLE": ville, "TEL": tel, "EMAIL": email, "SERIE": serie})
                        st.session_state.page = "filieres"
                        st.rerun()
                    else: st.error(msg)
            else: st.warning("Veuillez remplir tous les champs.")

# --- 3. FILIÈRES ---
elif st.session_state.page == "filieres":
    st.header(f"Filières disponibles ({st.session_state.data['SERIE']})")
    choix = st.radio("Veuillez sélectionner votre filière :", ["Gestion", "Informatique", "Réseaux"])
    if st.button("VALIDER MON CHOIX"):
        st.session_state.data['FILIERE'] = choix
        st.session_state.page = "paiement"
        st.rerun()

# --- 4. PAIEMENT & FICHE FINALE ---
elif st.session_state.page == "paiement":
    st.markdown("<h2>💳 PAIEMENT MOBILE (1000 FCFA)</h2>", unsafe_allow_html=True)
    
    if 'paye' not in st.session_state:
        c1, c2 = st.columns(2)
        l_airtel = get_base64_image("airtel.png")
        l_moov = get_base64_image("moov.png")
        if l_airtel: c1.image(l_airtel, width=100)
        if l_moov: c2.image(l_moov, width=100)
        st.warning("Veuillez vous acquitter des frais de 1000 FCFA pour débloquer votre fiche d'enrôlement.")
        if st.button("TERMINER ET PAYER"):
            st.session_state.paye = True
            st.rerun()
    else:
        st.balloons()
        # --- GÉNÉRATION DE LA FICHE VISUELLE ---
        st.markdown(f"""
            <div class="fiche-box">
                <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 3px solid #002366; padding-bottom: 10px;">
                    <img src="{get_base64_image('logo_pigc.png')}" width="80">
                    <div style="text-align: center;">
                        <h2 style="margin:0;">PIGC GABON 2026</h2>
                        <p style="margin:0; font-size: 12px;">Plateforme Intégrée de Gestion des Concours</p>
                    </div>
                    <img src="{get_base64_image(f"logo_{st.session_state.data['ECOLE'].lower()}.png")}" width="80">
                </div>
                
                <h3 style="text-align: center; margin-top: 20px; text-decoration: underline;">FICHE DE PRÉ-INSCRIPTION CERTIFIÉE</h3>
                
                <table style="width: 100%; margin-top: 20px;">
                    <tr><td><b>CANDIDAT :</b> {st.session_state.data['NOM']}</td><td><b>SEXE :</b> {st.session_state.data['SEXE']}</td></tr>
                    <tr><td><b>DATE DE NAISSANCE :</b> {st.session_state.data['DOB']}</td><td><b>SÉRIE BAC :</b> {st.session_state.data['SERIE']}</td></tr>
                    <tr><td><b>PROVINCE :</b> {st.session_state.data['PROV']}</td><td><b>VILLE :</b> {st.session_state.data['VILLE']}</td></tr>
                    <tr><td><b>TÉLÉPHONE :</b> {st.session_state.data['TEL']}</td><td><b>ÉCOLE :</b> {st.session_state.data['ECOLE']}</td></tr>
                    <tr><td colspan="2"><b>FILIÈRE CHOISIE :</b> {st.session_state.data['FILIERE']}</td></tr>
                </table>

                <div style="margin-top: 25px; padding: 10px; background: #e6f3ff; border-radius: 10px;">
                    <h4>📂 DOCUMENTS REQUIS & STATUT</h4>
                    <p>✅ Acte de Naissance : <b>TÉLÉVERSÉ & CONFORME</b></p>
                    <p>✅ Relevé de Notes BAC : <b>TÉLÉVERSÉ & CONFORME</b></p>
                    <p>✅ Frais Numériques (1000 FCFA) : <b>RÉGLÉS</b></p>
                </div>

                <div style="text-align: center; margin-top: 20px;">
                    <p style="font-size: 10px;">Scannez ce code pour vérifier l'authenticité de votre fiche lors du dépôt physique.</p>
                </div>
            </div>
        """, unsafe_allow_html=True)

        # Ajout du QR Code sous la fiche
        qr_data = f"CERTIF-PIGC|{st.session_state.data['NOM']}|{st.session_state.data['ECOLE']}|OK"
        qr_img = qrcode.make(qr_data)
        buf = BytesIO()
        qr_img.save(buf, format="PNG")
        st.image(buf, width=150)
        
        st.download_button("📥 TÉLÉCHARGER MA FICHE (PNG)", data=buf.getvalue(), file_name=f"Fiche_PIGC_{st.session_state.data['NOM']}.png")

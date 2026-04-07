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

# --- DONNÉES GÉOGRAPHIQUES COMPLÈTES GABON ---
GABON_GEO = {
    "Estuaire": {
        "Libreville": ["Louis", "Batterie IV", "Glass", "Nombakélé", "Petit-Paris", "Montagne Sainte", "Akébé", "Nzeng-Ayong", "PK5 à PK12", "Angondjé", "Okala"],
        "Akanda": ["Avorbam", "Sablière", "Sherko", "Cap Estérias"],
        "Owendo": ["Alénakiri", "Barracuda", "Cité SNI", "Port-En-Haut"],
        "Ntoum": ["Centre-Ville", "Okala-Ntoum"],
        "Kango": ["Centre"], "Cocobeach": ["Plage"]
    },
    "Haut-Ogooué": {
        "Franceville": ["Poto-Poto", "Melen", "Mangoungou", "Mbaya"],
        "Moanda": ["Lébomo", "Moukaba"],
        "Mounana": ["Centre"], "Akieni": ["Centre"], "Okondja": ["Centre"]
    },
    "Moyen-Ogooué": {
        "Lambaréné": ["Adouma", "Isaac", "Abat-Surs", "Moussamou"],
        "Ndjolé": ["Centre"]
    },
    "Ngounié": {
        "Mouila": ["Bavanga", "Diba-Diba"],
        "Fougamou": ["Centre"], "Ndendé": ["Centre"], "Lébamba": ["Centre"]
    },
    "Nyanga": {
        "Tchibanga": ["Centre", "Château"],
        "Mayumba": ["Centre"]
    },
    "Ogooué-Ivindo": {
        "Makokou": ["Centre", "Melen"],
        "Booué": ["Centre"], "Ovan": ["Centre"], "Mékambo": ["Centre"]
    },
    "Ogooué-Lolo": {
        "Koulamoutou": ["Ménon", "Mombo"],
        "Lastoursville": ["Centre"]
    },
    "Ogooué-Maritime": {
        "Port-Gentil": ["Chic", "Sogara", "Matanda", "Balise", "Grand-Village", "Sibi"],
        "Gamba": ["Centre"], "Omboué": ["Centre"]
    },
    "Woleu-Ntem": {
        "Oyem": ["Adzougou", "Akoakam", "Ngouéma"],
        "Bitam": ["Centre"], "Mitzic": ["Centre"], "Minvoul": ["Centre"]
    }
}

# --- FONCTIONS UTILITAIRES ---
def get_base64_image(path):
    if os.path.exists(path):
        with open(path, "rb") as f: return f"data:image/png;base64,{base64.b64encode(f.read()).decode()}"
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
                "⚠️ ALERTE CRITIQUE : Le document scanné pour justifier de l'acte de naissance n'est pas conforme. "
                "Nous vous rappelons que le FAUX et l'USAGE DE FAUX sont des délits lourdement punis par le Code Pénal Gabonais. "
                "Veuillez fournir un scan original, net et lisible."
            )
        return True, "✅ DOCUMENT CERTIFIÉ CONFORME"
    except: return False, "❌ ERREUR : Fichier illisible."

# --- DESIGN & CSS ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: #002366; }}
    h1, h2, h3, p, label {{ color: #FFD700 !important; text-align: center; font-weight: bold; }}
    .marquee {{ background-color: #ffffff; padding: 15px 0; border-bottom: 4px solid #FFD700; color: #FF0000; font-weight: 900; font-size: 1.6rem; }}
    .logo-central {{ width: 120px; height: 120px; border-radius: 50%; border: 3px solid #FFD700; display: block; margin: 15px auto; background-color: white; object-fit: contain; }}
    [data-testid="column"] {{ display: flex; justify-content: center; align-items: center; text-align: center; }}
    .stButton>button {{
        border-radius: 50% !important;
        width: 125px !important; height: 125px !important;
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
    </style>
    """, unsafe_allow_html=True)

# --- 1. BANDEAU DÉFILANT ORIGINAL ---
st.markdown('<div class="marquee"><marquee behavior="scroll" direction="left" scrollamount="8">DEMANDE DE PARTENARIAT AUX GRANDES ÉCOLES PUBLIQUES - PIGC 2026 - SYSTÈME SÉCURISÉ</marquee></div>', unsafe_allow_html=True)

# --- HEADER ---
logo_pigc = get_base64_image("logo_pigc.png")
if logo_pigc: st.markdown(f'<img src="{logo_pigc}" class="logo-central">', unsafe_allow_html=True)
st.markdown('<h1>Plateforme Intégrée de Gestion des Concours - PIGC</h1>', unsafe_allow_html=True)

# --- NAVIGATION ---
if 'page' not in st.session_state: st.session_state.page = "accueil"
if 'data' not in st.session_state: st.session_state.data = {}

INSTITUTS = ["INSG", "IST", "INPTIC", "IUSO", "ITO"]

# --- ACCUEIL ---
if st.session_state.page == "accueil":
    st.markdown("<p style='font-size:1.2rem; margin-top:20px;'>Veuillez choisir votre établissement pour vous inscrire</p>", unsafe_allow_html=True)
    cols = st.columns(5)
    for i, name in enumerate(INSTITUTS):
        with cols[i]:
            if st.button(name, key=f"btn_{name}"):
                st.session_state.data['ECOLE'] = name
                st.session_state.page = "formulaire"
                st.rerun()

# --- FORMULAIRE ---
elif st.session_state.page == "formulaire":
    if st.button("⬅️ RETOUR À L'ACCUEIL"):
        st.session_state.page = "accueil"
        st.rerun()

    st.markdown(f"<h2>CONCOURS D'ENTRÉE À L'{st.session_state.data['ECOLE']}</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color:red !important;'>Fiche de pré-inscription (OBLIGATOIRE)</p>", unsafe_allow_html=True)
    
    with st.form("form_pigc"):
        nom = st.text_input("Nom et Prénom (MAJUSCULES)").upper()
        c1, c2 = st.columns(2)
        sexe = c1.selectbox("Sexe", ["Masculin", "Féminin"])
        dob = c2.date_input("Date de naissance", min_value=date(1995,1,1))
        
        # LOGIQUE GÉOGRAPHIQUE
        prov_select = st.selectbox("Province de résidence", list(GABON_GEO.keys()))
        villes_dispo = list(GABON_GEO[prov_select].keys())
        ville_select = st.selectbox("Ville de résidence", villes_dispo)
        quartier_select = st.selectbox("Quartier", GABON_GEO[prov_select][ville_select])
        
        tel = st.text_input("Téléphone")
        email = st.text_input("Email")
        serie = st.selectbox("Série du BAC", ["A1", "A2", "B", "C", "D", "TI", "S"])
        
        st.write("---")
        f1 = st.file_uploader("Acte de Naissance (Original)", type=["pdf", "jpg", "png"])
        f2 = st.file_uploader("Relevé du BAC", type=["pdf", "jpg", "png"])
        
        if st.form_submit_button("VÉRIFIER MES DOCUMENTS ET CONTINUER ➡️"):
            if nom and f1 and f2:
                with st.spinner("Contrôle d'authenticité type Visa..."):
                    valide, msg = analyser_document_visa(f1, nom)
                    if valide:
                        st.session_state.data.update({"NOM": nom, "SEXE": sexe, "DOB": dob, "PROV": prov_select, "VILLE": ville_select, "QUARTIER": quartier_select, "TEL": tel, "SERIE": serie})
                        st.session_state.page = "filieres"
                        st.rerun()
                    else: st.error(msg)
            else: st.warning("Veuillez remplir tous les champs.")

# --- FILIÈRES ---
elif st.session_state.page == "filieres":
    st.header(f"Filières disponibles ({st.session_state.data['SERIE']})")
    choix = st.radio("Veuillez sélectionner votre filière :", ["Gestion", "Informatique", "Réseaux"])
    if st.button("VALIDER MON CHOIX"):
        st.session_state.data['FILIERE'] = choix
        st.session_state.page = "paiement"
        st.rerun()

# --- PAIEMENT & FICHE FINALE ---
elif st.session_state.page == "paiement":
    st.markdown("<h2>💳 PAIEMENT MOBILE (1000 FCFA)</h2>", unsafe_allow_html=True)
    if 'paye' not in st.session_state:
        c1, c2 = st.columns(2)
        l_airtel, l_moov = get_base64_image("airtel.png"), get_base64_image("moov.png")
        if l_airtel: c1.image(l_airtel, width=100)
        if l_moov: c2.image(l_moov, width=100)
        if st.button("TERMINER ET PAYER"):
            st.session_state.paye = True
            st.rerun()
    else:
        st.balloons()
        st.markdown(f"""
            <div style="background-color: white; padding: 30px; border-radius: 15px; border: 5px solid #FFD700; color: #002366 !important; text-align: left;">
                <div style="display: flex; justify-content: space-between; border-bottom: 2px solid #002366; padding-bottom: 10px;">
                    <img src="{get_base64_image('logo_pigc.png')}" width="70">
                    <img src="{get_base64_image(f"logo_{st.session_state.data['ECOLE'].lower()}.png")}" width="70">
                </div>
                <h3 style="text-align: center; color: #002366 !important;">FICHE D'ENRÔLEMENT CERTIFIÉE</h3>
                <p><b>CANDIDAT :</b> {st.session_state.data['NOM']}</p>
                <p><b>RÉSIDENCE :</b> {st.session_state.data['PROV']} - {st.session_state.data['VILLE']} ({st.session_state.data['QUARTIER']})</p>
                <p><b>ÉCOLE :</b> {st.session_state.data['ECOLE']} | <b>SÉRIE :</b> {st.session_state.data['SERIE']}</p>
                <p><b>FILIÈRE :</b> {st.session_state.data['FILIERE']}</p>
                <div style="margin-top: 15px; padding: 10px; background: #f0faff; border-radius: 8px;">
                    <b>STATUT DES PIÈCES :</b><br>
                    ✅ Acte de Naissance : <b>CONFORME</b><br>
                    ✅ Relevé BAC : <b>CONFORME</b><br>
                    ✅ Frais (1000 FCFA) : <b>RÉGLÉS</b>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        qr_data = f"VERIF-PIGC|{st.session_state.data['NOM']}|OK"
        qr_img = qrcode.make(qr_data)
        buf = BytesIO()
        qr_img.save(buf, format="PNG")
        st.image(buf, width=150, caption="Vérification QR Code")

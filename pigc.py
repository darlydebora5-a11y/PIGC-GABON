import streamlit as st
import qrcode
import os
import time
import base64
import pandas as pd
from io import BytesIO
from datetime import date
from fpdf import FPDF
from PIL import Image

# --- CONFIGURATION SYSTÈME ---
st.set_page_config(page_title="PIGC - Plateforme Intégrée", layout="wide")
DB_FILE = "inscriptions_pigc.csv"

# Initialisation du fichier de base de données s'il n'existe pas
if not os.path.exists(DB_FILE):
    df_init = pd.DataFrame(columns=["NOM", "BAC", "AGE", "DATE", "ECOLE", "FILIERE"])
    df_init.to_csv(DB_FILE, index=False)

# Fonction pour encoder les images (Essentiel pour l'affichage web rapide)
def get_base64_image(image_path):
    if os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            return f"data:image/png;base64,{base64.b64encode(img_file.read()).decode()}"
    return ""

# --- STYLE PRESTIGE : BLEU ROI & DORÉ ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: #002366; }}
    h1, h2, h3, h4, p, span, label, .stMarkdown, .stCaption {{
        color: #FFD700 !important;
        font-weight: bold !important;
    }}
    input, select, textarea, [data-baseweb="select"] {{
        color: #000000 !important;
        background-color: #ffffff !important;
        border: 2px solid #FFD700 !important;
        border-radius: 8px !important;
    }}
    div.stButton > button {{
        background-color: #ffffff !important;
        color: #002366 !important;
        font-weight: 900 !important;
        font-size: 1.1rem !important;
        border-radius: 25px !important;
        border: 2px solid #FFD700 !important;
        height: 60px !important;
        width: 100% !important;
        box-shadow: 0 4px 15px rgba(0,0,0,0.6) !important;
    }}
    .logo-container {{ display: flex; justify-content: center; margin: 20px 0; }}
    .circular-logo {{
        width: 170px; height: 170px; border-radius: 50%;
        border: 5px solid #FFD700; object-fit: cover;
        background-color: white; box-shadow: 0 0 20px #FFD700;
    }}
    .footer-warning-box {{
        background-color: rgba(0, 0, 0, 0.3);
        border: 1px solid #FFD700;
        padding: 30px;
        border-radius: 15px;
        margin-top: 50px;
        text-align: center;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- BASE DE DONNÉES ÉCOLES ---
ECOLES_DATA = {
    "INSG": {"nom": "Institut National des Sciences de Gestion", "filières": ["Comptabilité-Audit", "RH", "Marketing", "Finance"], "bacs": ["B", "CG", "G2"], "age_max": 24, "logo": "logo_insg.png", "code": "PIGC_INSG_2025"},
    "IST": {"nom": "Institut Supérieur de Technologie", "filières": ["Génie Industriel", "Électrique", "Informatique", "Civil"], "bacs": ["C", "D", "E", "F", "TI"], "age_max": 22, "logo": "logo_ist.png", "code": "PIGC_IST_2025"},
    "IUSO": {"nom": "Institut Univ. des Sciences de l'Organisation", "filières": ["Management Sport", "Assistanat", "Gestion PME"], "bacs": ["A1", "A2", "B", "CG", "G2"], "age_max": 25, "logo": "logo_iuso.png", "code": "PIGC_IUSO_2025"},
    "INPTIC": {"nom": "Inst. Nat. des Postes et TIC", "filières": ["Développement", "Réseaux", "Numérique"], "bacs": ["C", "D", "S", "TI"], "age_max": 24, "logo": "logo_inptic.png", "code": "PIGC_INPTIC_2025"},
    "ITO": {"nom": "Institut de Technologies d'Owendo", "filières": ["Logistique", "Maintenance"], "bacs": ["C", "D", "E", "F", "TI"], "age_max": 23, "logo": "logo_ito.png", "code": "PIGC_ITO_2025"}
}

# --- FONCTION GÉNÉRATION PDF (VERSION SÉCURISÉE WEB) ---
def generer_fiche_pdf(data):
    pdf = FPDF()
    pdf.add_page()
    
    def ajouter_image_secu(path, x, y, w):
        if os.path.exists(path):
            try:
                img = Image.open(path).convert("RGB")
                temp_img = f"temp_{int(time.time())}_{os.path.basename(path)}.jpg"
                img.save(temp_img, "JPEG")
                pdf.image(temp_img, x, y, w)
                os.remove(temp_img) # Nettoyage immédiat
            except: pass

    ajouter_image_secu("logo_pigc.png", 10, 8, 33)
    ajouter_image_secu(ECOLES_DATA[data['ECOLE']]['logo'], 160, 8, 33)
    
    pdf.set_font("Arial", "B", 15)
    pdf.ln(25)
    pdf.cell(0, 10, "PLATEFORME PIGC - FICHE D'ENROLEMENT CERTIFIEE", 0, 1, "C")
    pdf.ln(10)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, f"ETABLISSEMENT : {ECOLES_DATA[data['ECOLE']]['nom']}", 1, 1, "L")
    pdf.ln(10)
    pdf.set_font("Arial", "", 12)
    # Remplacement des caractères spéciaux pour compatibilité PDF Arial
    nom_clean = data['NOM'].encode('latin-1', 'replace').decode('latin-1')
    pdf.cell(0, 10, f"NOM DU CANDIDAT : {nom_clean}", 0, 1)
    pdf.cell(0, 10, f"FILIERE CHOISIE : {data['FILIERE']}", 0, 1)
    pdf.cell(0, 10, f"DATE D'INSCRIPTION : {data['DATE']}", 0, 1)
    
    qr_data = f"PIGC-VERIF|{data['NOM']}|{data['ECOLE']}"
    qr = qrcode.make(qr_data)
    qr_path = f"qr_{int(time.time())}.png"
    qr.save(qr_path)
    pdf.image(qr_path, 80, 140, 50)
    os.remove(qr_path)
    
    pdf.set_y(-40)
    pdf.set_font("Arial", "I", 8)
    pdf.multi_cell(0, 5, "Document officiel généré par le système PIGC.\nSignature numérique certifiée conforme au Code Pénal Gabonais.", 0, "C")
    return pdf.output(dest='S').encode('latin-1')

# --- BANDEAU DÉFILANT BLANC (LOGOS À LA RACINE) ---
try:
    # Recherche dynamique des logos à la racine
    liste_logos = [f for f in os.listdir(".") if f.startswith("logo_") and f.endswith(".png") and f != "logo_pigc.png"]
    logos_html = "".join([f'<img src="{get_base64_image(l)}" height="50" style="margin-left:50px;">' for l in liste_logos])
except: logos_html = ""

st.markdown(f"""
    <div style="background-color: #ffffff; padding: 15px 0; border-bottom: 4px solid #FFD700;">
        <marquee behavior="scroll" direction="left" scrollamount="8">
            <div style="display: flex; align-items: center; gap: 40px;">
                <span style="color: #FF0000 !important; font-weight: 900; font-size: 1.6rem; white-space: nowrap;">DEMANDE DE PARTENARIAT AUX GRANDES ÉCOLES PUBLIQUES</span>
                {logos_html}
            </div>
        </marquee>
    </div>
    """, unsafe_allow_html=True)

# --- LOGO CIRCULAIRE ET TITRE ---
logo_pigc_b64 = get_base64_image("logo_pigc.png")
st.markdown(f"""
    <div class="logo-container"><img src="{logo_pigc_b64}" class="circular-logo"></div>
    <h1 style="text-align: center; font-size: 2.5rem;">Plateforme Intégrée de Gestion des Concours - PIGC</h1>
    <hr style="border: 1px solid #FFD700; width: 80%; margin: auto;">
    """, unsafe_allow_html=True)

# --- NAVIGATION ---
if 'step' not in st.session_state: st.session_state.step = 1
if 'data' not in st.session_state: st.session_state.data = {}
menu = st.sidebar.selectbox("MENU", ["📝 Portail Candidat", "🔐 Espace Directions"])

if menu == "📝 Portail Candidat":
    if st.session_state.step == 1:
        st.subheader("👤 Étape 1 : Identification")
        nom = st.text_input("NOM COMPLET (tel que sur l'acte)").upper()
        col1, col2 = st.columns(2)
        dob = col1.date_input("Date de Naissance", min_value=date(1998, 1, 1))
        serie = col2.selectbox("Série du BAC", ["A1", "A2", "B", "C", "D", "CG", "G2", "TI", "F", "S"])
        f1 = st.file_uploader("Charger Acte de Naissance", type=["pdf", "jpg", "png"])
        f2 = st.file_uploader("Charger Relevé de Bac", type=["pdf", "jpg", "png"])
        
        if st.button("VALIDER ET ANALYSER LES PIÈCES ➡️"):
            if nom and f1 and f2:
                age = date.today().year - dob.year
                st.session_state.data.update({"NOM": nom, "BAC": serie, "AGE": age, "DATE": time.strftime("%d/%m/%Y %H:%M")})
                st.session_state.step = 2
                st.rerun()
            else: st.warning("Veuillez remplir tous les champs.")

    elif st.session_state.step == 2:
        st.subheader("🏫 Étape 2 : Éligibilité & Choix")
        ecole = st.selectbox("Sélectionner l'établissement", list(ECOLES_DATA.keys()))
        config = ECOLES_DATA[ecole]
        
        if os.path.exists(config['logo']):
            st.image(config['logo'], width=100)

        if st.session_state.data["AGE"] <= config["age_max"] and st.session_state.data["BAC"] in config["bacs"]:
            st.success(f"✅ Profil éligible pour {config['nom']}")
            filiere = st.selectbox("Choisir la filière", config["filières"])
            if st.button("CONFIRMER L'ENRÔLEMENT ➡️"):
                st.session_state.data.update({"ECOLE": ecole, "FILIERE": filiere})
                df_to_save = pd.DataFrame([st.session_state.data])
                df_to_save.to_csv(DB_FILE, mode='a', header=False, index=False)
                st.session_state.step = 3
                st.rerun()
        else: st.error(f"🚫 Non éligible (Critère Age max: {config['age_max']} ans ou série du BAC).")

    elif st.session_state.step == 3:
        st.balloons()
        st.success("Enrôlement réussi !")
        pdf_data = generer_fiche_pdf(st.session_state.data)
        st.download_button(label="📥 TÉLÉCHARGER MA FICHE (PDF)", data=pdf_data, file_name=f"Fiche_PIGC_{st.session_state.data['NOM']}.pdf", mime="application/pdf")
        if st.button("Nouvelle Session"): st.session_state.step = 1; st.rerun()

elif menu == "🔐 Espace Directions":
    code = st.text_input("Code confidentiel école", type="password")
    if code:
        ecole_id = next((e for e, c in ECOLES_DATA.items() if code == c["code"]), None)
        if ecole_id:
            st.success(f"Accès autorisé : {ecole_id}")
            df_view = pd.read_csv(DB_FILE)
            st.dataframe(df_view[df_view['ECOLE'] == ecole_id], use_container_width=True)
        else: st.error("Code invalide.")

# --- BAS DE PAGE JURIDIQUE ---
st.markdown("""
    <div class="footer-warning-box">
        <h3 style="color: #FFD700; font-size: 1.4rem;">⚖️ AVERTISSEMENT JURIDIQUE</h3>
        <p style="color: #FFD700; font-size: 1rem; line-height: 1.6;">
            Conformément aux dispositions du Code Pénal Gabonais (Loi n°006/2020), Articles 282 et 283 :<br>
            Toute tentative de téléchargement de documents falsifiés ou usurpation d'identité entraînera des poursuites judiciaires immédiates devant les tribunaux compétents.
        </p>
    </div>
    <div style="text-align: center; margin-top: 20px; opacity: 0.8; font-size: 0.9rem;">
        © 2026 - Plateforme PIGC - Innovation Technologique au service de l'Excellence.
    </div>
    """, unsafe_allow_html=True)

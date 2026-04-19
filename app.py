import streamlit as st
import google.generativeai as genai
import io, requests, re, random
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor

# 1. CONFIGURATION
genai.configure(api_key=st.secrets["API_KEY"])

# 2. MOTEUR DE DESIGN (Bandeau bleu pour le cours / Bandeau rouge pour la correction)
def appliquer_style_cfa(slide, titre_texte, est_correction=False):
    couleur_fond = RGBColor(204, 0, 0) if est_correction else RGBColor(0, 82, 204)
    
    bandeau = slide.shapes.add_shape(1, 0, 0, Inches(10), Inches(0.8))
    bandeau.fill.solid()
    bandeau.fill.fore_color.rgb = couleur_fond
    bandeau.line.visible = False
    
    lisere = slide.shapes.add_shape(1, 0, Inches(0.8), Inches(10), Inches(0.05))
    lisere.fill.solid()
    lisere.fill.fore_color.rgb = RGBColor(255, 102, 0) # Orange
    lisere.line.visible = False

    txBox = slide.shapes.add_textbox(Inches(0.5), Inches(0.1), Inches(9), Inches(0.6))
    p = txBox.text_frame.paragraphs[0]
    p.text = "CORRIGÉ : " + titre_texte if est_correction else titre_texte
    p.font.bold, p.font.size, p.font.color.rgb = True, Pt(24), RGBColor(255, 255, 255)

def generer_pptx_complet(diplome, sujet, contenu_cours, contenu_correction):
    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(10), Inches(5.625)
    
    # --- CRÉATION DU COURS APPRENTI ---
    sections = contenu_cours.split('###')
    for section in sections:
        if len(section.strip()) > 10:
            lines = section.strip().split('\n')
            titre_s = lines[0].replace('**', '').strip()
            corps_brut = '\n'.join(lines[1:]).strip()
            paragraphes = [p.strip() for p in corps_brut.split('\n') if p.strip()]
            
            for i in range(0, max(1, len(paragraphes)), 5):
                slide = prs.slides.add_slide(prs.slide_layouts[6])
                appliquer_style_cfa(slide, titre_s + (f" (suite {i//5 + 1})" if i > 0 else ""))
                txBox = slide.shapes.add_textbox(Inches(0.5), Inches(1.2), Inches(9), Inches(4))
                tf = txBox.text_frame
                tf.word_wrap = True
                for p_text in paragraphes[i:i+5]:
                    p = tf.add_paragraph()
                    p.text = "• " + p_text.replace('*', '').strip()
                    p.font.size, p.font.color.rgb = Pt(17), RGBColor(30, 30, 30)

    # --- AJOUT DES DIAPOS DE CORRECTION (À la fin) ---
    slide_transition = prs.slides.add_slide(prs.slide_layouts[6])
    slide_transition.shapes.add_textbox(Inches(2), Inches(2), Inches(6), Inches(2)).text = "SECTION FORMATEUR (CORRECTIONS)"
    
    corriges = contenu_correction.split('###')
    for corr in corriges:
        if len(corr.strip()) > 10:
            lines = corr.strip().split('\n')
            titre_c = lines[0].replace('**', '').strip()
            slide = prs.slides.add_slide(prs.slide_layouts[6])
            appliquer_style_cfa(slide, titre_c, est_correction=True)
            txBox = slide.shapes.add_textbox(Inches(0.5), Inches(1.2), Inches(9), Inches(4))
            txBox.text_frame.text = '\n'.join(lines[1:]).strip()

    buf = io.BytesIO()
    prs.save(buf)
    buf.seek(0)
    return buf

# 3. INTERFACE STREAMLIT
st.set_page_config(page_title="Générateur de cours", layout="wide")
st.title("🛠️ Générateur de cours")

if 'liste' not in st.session_state:
    st.session_state.liste = ["BP Boucher", "BP Boulanger", "Bac Pro Maintenance Véhicule", "BTS Maintenance Véhicule", "CAP EPC", "BP Coiffure", "AMLHR"]

with st.sidebar:
    st.header("⚙️ Paramètres")
    nouveau = st.text_input("Ajouter un diplôme :")
    if st.button("Ajouter") and nouveau:
        st.session_state.liste.append(nouveau)
        st.rerun()

diplome = st.selectbox("Diplôme visé :", st.session_state.liste)
sujet = st.text_input("Sujet de la leçon :")

if st.button("🚀 GÉNÉRER LE PACK COMPLET"):
    if sujet:
        with st.spinner("L'IA prépare le cours et vos antisèches..."):
            moteur = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods][0]
            model = genai.GenerativeModel(moteur)
            
            prompt = f"""
            Tu es un expert en pédagogie pour le CFA de Chartres. 
            Crée un cours de 60 minutes pour des apprentis en {diplome} sur {sujet}.
            
            PARTIE 1 : CONTENU APPRENTI (Sans réponses)
            - ### 1. L'Accroche (Humour, localisé Chartres)
            - ### 2. Référentiel (Compétences visées)
            - ### 3. Mission (Mise en situation)
            - ### 4. Exercice d'Application (Enoncés uniquement)
            - ### 5. Quiz QCM (Questions sans réponses)
            - ### 6. Vrai ou Faux (Enoncés sans réponses)
            - ### 7. Activité Pédagogique (Consignes FOAD)
            - ### 8. Synthèse (Points clés)
            
            PARTIE 2 : ESPACE FORMATEUR (Corrections et Conseils)
            - ### 1. Corrigé de l'Exercice (Détail des calculs/gestes)
            - ### 2. Réponses au Quiz et Vrai/Faux
            - ### 3. Conseils au formateur (Comment animer, pièges à éviter pour le niveau {diplome})
            
            Sépare clairement les deux parties avec la balise [SEP_FORMATEUR].
            """
            
            res = model.generate_content(prompt).text
            parts = res.split('[SEP_FORMATEUR]')
            cours_txt = parts[0]
            formateur_txt = parts[1] if len(parts) > 1 else "Pas de correction générée."

            tab1, tab2 = st.tabs(["📖 Cours Apprenti", "👨‍🏫 Espace Formateur"])
            with tab1:
                st.markdown(cours_txt)
            with tab2:
                st.info("Cette partie est réservée au formateur.")
                st.markdown(formateur_txt)
            
            file = generer_pptx_complet(diplome, sujet, cours_txt, formateur_txt)
            st.download_button("📥 Télécharger le Pack PowerPoint (Cours + Corrigés)", file, f"Cours_Complet_{sujet}.pptx")

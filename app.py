import streamlit as st
import google.generativeai as genai
import io, requests, re, random
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor

# 1. CONFIGURATION
genai.configure(api_key=st.secrets["API_KEY"])

# 2. DESIGN DU POWERPOINT (Style CFA Chartres)
def appliquer_style_perso(slide, titre_texte, est_correction=False):
    couleur_fond = RGBColor(180, 0, 0) if est_correction else RGBColor(0, 82, 204)
    bandeau = slide.shapes.add_shape(1, 0, 0, Inches(10), Inches(0.7))
    bandeau.fill.solid()
    bandeau.fill.fore_color.rgb = couleur_fond
    bandeau.line.visible = False
    lisere = slide.shapes.add_shape(1, 0, Inches(0.7), Inches(10), Inches(0.05))
    lisere.fill.solid()
    lisere.fill.fore_color.rgb = RGBColor(255, 102, 0)
    lisere.line.visible = False
    txBox = slide.shapes.add_textbox(Inches(0.5), Inches(0.05), Inches(9), Inches(0.6))
    p = txBox.text_frame.paragraphs[0]
    p.text = ("CORRIGÉ : " if est_correction else "") + titre_texte
    p.font.bold, p.font.size, p.font.color.rgb = True, Pt(22), RGBColor(255, 255, 255)

def ajouter_slide_texte(prs, titre, paragraphes, est_correction=False, prompt_img=None):
    for i in range(0, len(paragraphes), 4):
        slide = prs.slides.add_slide(prs.slide_layouts[6])
        t_final = titre + (f" (suite {i//4 + 1})" if i > 0 else "")
        appliquer_style_perso(slide, t_final, est_correction)
        has_img = False
        if i == 0 and prompt_img and not est_correction:
            seed = random.randint(1, 9999)
            url = f"https://image.pollinations.ai/prompt/professional_vibrant_illustration_{prompt_img.replace(' ', '_')}?width=512&height=512&nologo=true&seed={seed}"
            try:
                img_data = requests.get(url, timeout=5).content
                slide.shapes.add_picture(io.BytesIO(img_data), Inches(5.6), Inches(1.2), width=Inches(4))
                has_img = True
            except: pass
        width = Inches(4.8) if has_img else Inches(9)
        txBox = slide.shapes.add_textbox(Inches(0.5), Inches(1.2), width, Inches(4))
        tf = txBox.text_frame
        tf.word_wrap = True
        for p_text in paragraphes[i:i+4]:
            p = tf.add_paragraph()
            p.text = "• " + p_text.replace('*', '').strip()
            p.font.size, p.font.color.rgb = Pt(16), RGBColor(30, 30, 30)
            p.space_after = Pt(10)

def generer_pptx_v11(diplome, sujet, cours_txt, formateur_txt):
    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(10), Inches(5.625)
    sections = cours_txt.split('###')
    for sec in sections:
        if len(sec.strip()) > 10:
            lines = sec.strip().split('\n')
            titre = lines[0].strip()
            corps = '\n'.join(lines[1:]).strip()
            img_match = re.search(r'\[IMG:(.*?)\]', corps)
            p_img = img_match.group(1) if img_match else sujet
            clean_txt = corps.replace(f"[IMG:{p_img}]", "").strip()
            paras = [p.strip() for p in clean_txt.split('\n') if p.strip()]
            ajouter_slide_texte(prs, titre, paras, False, p_img)
    corriges = formateur_txt.split('###')
    for corr in corriges:
        if len(corr.strip()) > 10:
            lines = corr.strip().split('\n')
            paras = [p.strip() for p in lines[1:] if p.strip()]
            ajouter_slide_texte(prs, lines[0].strip(), paras, True)
    buf = io.BytesIO()
    prs.save(buf)
    buf.seek(0)
    return buf

# 3. INTERFACE
st.set_page_config(page_title="Générateur de cours", layout="wide")
st.title("🛠️ Générateur de cours")

if 'liste' not in st.session_state:
    st.session_state.liste = ["BP Boucher", "BP Boulanger", "Bac Pro Maintenance Véhicule", "BTS Maintenance Véhicule", "CAP EPC", "BP Coiffure", "AMLHR"]

with st.sidebar:
    st.header("⚙️ Configuration")
    nouveau = st.text_input("Nouveau diplôme :")
    if st.button("Ajouter") and nouveau:
        st.session_state.liste.append(nouveau)
        st.rerun()

col1, col2 = st.columns(2)
with col1:
    diplome = st.selectbox("Diplôme :", st.session_state.liste)
    sujet = st.text_input("Sujet de la leçon :")
with col2:
    lieu = st.text_input("Lieu du scénario :", value="Chartres")

if st.button("🚀 GÉNÉRER LE PACK COMPLET"):
    if sujet:
        with st.spinner("Analyse du référentiel et rédaction..."):
            moteur = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods][0]
            model = genai.GenerativeModel(moteur)
            
            prompt = f"""
            Tu es un expert pédagogique. Crée un cours de 60min pour {diplome} sur {sujet}.
            
            CONSIGNE CRITIQUE : Identifie et mentionne explicitement les parties ciblées du référentiel officiel {diplome} (Blocs de compétences, Savoirs, Savoir-faire).
            Le ton est ludique, humour, scénario à {lieu}.
            
            PARTIE APPRENTI :
            ### 1. L'Accroche [IMG: colorful illustration of {sujet}]
            ### 2. Parties du Référentiel ciblées
            (Mentionne les codes de compétences, par ex: C3.1, et les intitulés officiels du programme).
            ### 3. Mission Professionnelle (À {lieu}) [IMG: photo of {sujet}]
            ### 4. Exercice d'Application (Énoncé)
            ### 5. Quiz QCM (3 questions)
            ### 6. Le Vrai ou Faux (5 points)
            ### 7. Travail en Autonomie (60 min)
            ### 8. La Synthèse
            
            [SEP_FORMATEUR]
            
            PARTIE FORMATEUR (CORRIGÉS ET CONSEILS) :
            ### 1. Corrigé de l'Exercice
            ### 2. Réponses au Quiz et Vrai/Faux
            ### 3. Conseils pédagogiques (Niveau {diplome})
            """
            
            res = model.generate_content(prompt).text
            parts = res.split('[SEP_FORMATEUR]')
            cours_txt, formateur_txt = parts[0], parts[1] if len(parts)>1 else ""
            t1, t2 = st.tabs(["📖 Cours", "👨‍🏫 Corrigés"])
            t1.markdown(cours_txt); t2.markdown(formateur_txt)
            file = generer_pptx_v11(diplome, sujet, cours_txt, formateur_txt)
            st.download_button("📥 Télécharger le PowerPoint", file, f"Cours_{sujet}.pptx")

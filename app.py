import streamlit as st
import google.generativeai as genai
import io, requests, re, random
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor

# 1. CONFIGURATION
genai.configure(api_key=st.secrets["API_KEY"])

# 2. DESIGN INTERACTIF (Bleu Question / Rouge Réponse)
def appliquer_style_cfa(slide, titre_texte, est_reponse=False):
    couleur_fond = RGBColor(180, 0, 0) if est_reponse else RGBColor(0, 82, 204)
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
    p.text = ( "CORRECTION : " if est_reponse else "DÉFI : ") + titre_texte
    p.font.bold, p.font.size, p.font.color.rgb = True, Pt(22), RGBColor(255, 255, 255)

def ajouter_paire_slides(prs, titre, question_txt, reponse_txt, img_prompt=None):
    # SLIDE DÉFI
    slide_q = prs.slides.add_slide(prs.slide_layouts[6])
    appliquer_style_cfa(slide_q, titre, est_reponse=False)
    has_img = False
    if img_prompt:
        seed = random.randint(1, 99999)
        url = f"https://image.pollinations.ai/prompt/cute_vibrant_cartoon_illustration_of_{img_prompt.replace(' ', '_')}?width=512&height=512&nologo=true&seed={seed}"
        try:
            img_data = requests.get(url, timeout=5).content
            slide_q.shapes.add_picture(io.BytesIO(img_data), Inches(5.6), Inches(1.2), width=Inches(4))
            has_img = True
        except: pass
    txBox_q = slide_q.shapes.add_textbox(Inches(0.5), Inches(1.2), Inches(4.8) if has_img else Inches(9), Inches(4))
    tf_q = txBox_q.text_frame
    tf_q.word_wrap = True
    for l in question_txt.split('\n'):
        if l.strip():
            p = tf_q.add_paragraph()
            p.text = "• " + l.replace('*', '').strip()
            p.font.size, p.font.color.rgb = Pt(17), RGBColor(30, 30, 30)

    # SLIDE RÉPONSE
    slide_r = prs.slides.add_slide(prs.slide_layouts[6])
    appliquer_style_cfa(slide_r, titre, est_reponse=True)
    txBox_r = slide_r.shapes.add_textbox(Inches(0.5), Inches(1.2), Inches(9), Inches(4))
    tf_r = txBox_r.text_frame
    tf_r.word_wrap = True
    for l in reponse_txt.split('\n'):
        if l.strip():
            p = tf_r.add_paragraph()
            p.text = "✔ " + l.replace('*', '').strip()
            p.font.size, p.font.color.rgb = Pt(17), RGBColor(0, 100, 0)

# 3. INTERFACE
st.set_page_config(page_title="Générateur de cours CFA", layout="wide")
st.title("🛠️ Générateur de cours interactif")

diplome = st.selectbox("Diplôme :", ["BP Boucher", "BP Boulanger", "Bac Pro Maintenance", "BTS Maintenance", "CAP EPC", "BP Coiffure", "AMLHR"])
sujet = st.text_input("Sujet de la leçon :")
lieu = st.text_input("Lieu du scénario :", value="Chartres")

if st.button("🚀 GÉNÉRER LE PACK COMPLET"):
    if sujet:
        with st.spinner("Conception en cours..."):
            moteur = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods][0]
            model = genai.GenerativeModel(moteur)
            prompt = f"Expert pédagogie CFA Chartres. Cours interactif pour {diplome} sur {sujet}. Ancrage référentiel {diplome} obligatoire. Humour, à {lieu}. STRUCTURE : ### SECTION: [Titre] IMAGE: [Description cartoon] QUESTION: [Défi + codes référentiel] REPONSE: [Solution] ### (5 sections minimum)"
            res = model.generate_content(prompt).text
            
            prs = Presentation()
            prs.slide_width, prs.slide_height = Inches(10), Inches(5.625)
            duels = res.split('###')
            for d in duels:
                if "SECTION:" in d:
                    try:
                        titre = re.search(r"SECTION:(.*)", d).group(1).strip()
                        img = re.search(r"IMAGE:(.*)", d).group(1).strip()
                        ques = re.search(r"QUESTION:([\s\S]*?)REPONSE:", d).group(1).strip()
                        rep = re.search(r"REPONSE:([\s\S]*)", d).group(1).strip()
                        
                        st.info(f"📖 {titre}")
                        st.write(ques)
                        
                        ajouter_paire_slides(prs, titre, ques, rep, img)
                    except: pass
            
            buf = io.BytesIO()
            prs.save(buf)
            buf.seek(0)
            st.download_button("📥 Télécharger le PowerPoint Studio V15", buf, f"Cours_Interactif_{sujet}.pptx")

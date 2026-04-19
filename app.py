import streamlit as st
import google.generativeai as genai
import io, requests, re
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN

# 1. CONFIGURATION
genai.configure(api_key=st.secrets["API_KEY"])

# 2. FONCTION DE DESIGN AVANCÉ
def appliquer_style_cfa(slide, titre_texte):
    # Ajouter un bandeau bleu en haut
    shape = slide.shapes.add_shape(1, 0, 0, Inches(10), Inches(0.8))
    shape.fill.solid()
    shape.fill.foreground_color.rgb = RGBColor(0, 82, 204) # Bleu CFA
    shape.line.fill.background()
    
    # Titre stylisé dans le bandeau
    title_shape = slide.shapes.title
    title_shape.text = titre_texte
    title_para = title_shape.text_frame.paragraphs[0]
    title_para.font.bold = True
    title_para.font.size = Pt(28)
    title_para.font.color.rgb = RGBColor(255, 255, 255) # Blanc
    title_shape.left = Inches(0.5)
    title_shape.top = Inches(0.1)

def generer_pptx_premium(diplome, sujet, contenu):
    prs = Presentation()
    prs.slide_width = Inches(10)
    prs.slide_height = Inches(5.625) # Format 16:9

    sections = contenu.split('###')
    for section in sections:
        if len(section.strip()) > 10:
            slide = prs.slides.add_slide(prs.slide_layouts[5]) # Layout vide avec titre
            lignes = section.strip().split('\n')
            titre_s = lignes[0].replace('**', '').strip()
            corps_s = '\n'.join(lignes[1:]).strip()
            
            appliquer_style_cfa(slide, titre_s)
            
            # Gestion Image
            image_match = re.search(r'\[IMG:(.*?)\]', corps_s)
            has_image = False
            if image_match:
                prompt_img = image_match.group(1).strip()
                corps_s = corps_s.replace(image_match.group(0), '').strip()
                url = f"https://image.pollinations.ai/prompt/{prompt_img.replace(' ', '%20')}?width=600&height=450&nologo=true&seed=42"
                try:
                    img_data = requests.get(url, timeout=10).content
                    slide.shapes.add_picture(io.BytesIO(img_data), Inches(5.2), Inches(1.2), width=Inches(4.5))
                    has_image = True
                except: pass

            # Gestion Texte (Double colonne ou plein écran)
            width = Inches(4.5) if has_image else Inches(9)
            txBox = slide.shapes.add_textbox(Inches(0.5), Inches(1.2), width, Inches(4))
            tf = txBox.text_frame
            tf.word_wrap = True
            
            # Nettoyage et découpage intelligent du texte
            paragraphes = [p for p in corps_s.split('\n') if p.strip()]
            for p_text in paragraphes[:7]: # Max 7 points pour éviter le débordement
                p = tf.add_paragraph()
                p.text = p_text.replace('*', '').replace('-', '').strip()
                p.font.size = Pt(20)
                p.font.color.rgb = RGBColor(40, 40, 40)
                if '-' in p_text or '*' in p_text: # Si c'était une liste
                    p.level = 0
                    p.font.size = Pt(18)

    buf = io.BytesIO()
    prs.save(buf)
    buf.seek(0)
    return buf

# 3. INTERFACE
st.set_page_config(page_title="Craie-ative AI Premium", layout="wide")
st.title("🎨 Craie-ative AI : Édition Studio Chartres")

if 'liste' not in st.session_state:
    st.session_state.liste = ["BP Boucher", "BP Boulanger", "Bac Pro Maintenance", "BTS Maintenance"]

with st.sidebar:
    st.header("⚙️ Configuration")
    nouveau = st.text_input("Ajouter un diplôme :")
    if st.button("Ajouter") and nouveau:
        st.session_state.liste.append(nouveau)
        st.rerun()

diplome = st.selectbox("Diplôme :", st.session_state.liste)
sujet = st.text_input("Sujet de la mission :")

if st.button("🚀 Lancer la production Premium"):
    model = genai.GenerativeModel([m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods][0])
    prompt = f"""Expert pédagogie CFA Chartres. Cours FOAD 60min pour {diplome} sur {sujet}. 
    Ton ludique, jeux de mots, localisé à Chartres. Pas de salutations.
    Structure ### 1. Accroche, ### 2. Mission, ### 3. Exercice, ### 4. Synthèse.
    Pour chaque section, termine par [IMG: professional photorealistic 4k {sujet} {diplome} bright colors].
    Utilise des listes à puces courtes."""
    
    res = model.generate_content(prompt)
    st.markdown(res.text)
    file = generer_pptx_premium(diplome, sujet, res.text)
    st.download_button("📥 Télécharger le PowerPoint Studio", file, f"{sujet}.pptx")

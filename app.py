import streamlit as st
import google.generativeai as genai
import io, requests, re
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor

# 1. CONFIGURATION
genai.configure(api_key=st.secrets["API_KEY"])

# 2. MOTEUR DE DESIGN ROBUSTE (Zéro AttributeError)
def appliquer_style_cfa(slide, titre_texte):
    # Création manuelle du bandeau bleu (Rectangle)
    bandeau = slide.shapes.add_shape(1, 0, 0, Inches(10), Inches(0.8))
    bandeau.fill.solid()
    bandeau.fill.foreground_color.rgb = RGBColor(0, 82, 204) # Bleu CFA
    bandeau.line.visible = False
    
    # Création manuelle de la boîte de titre par-dessus
    txBox = slide.shapes.add_textbox(Inches(0.5), Inches(0.1), Inches(9), Inches(0.6))
    tf = txBox.text_frame
    p = tf.paragraphs[0]
    p.text = titre_texte
    p.font.bold = True
    p.font.size = Pt(28)
    p.font.color.rgb = RGBColor(255, 255, 255) # Blanc

def generer_pptx_premium(diplome, sujet, contenu):
    prs = Presentation()
    prs.slide_width = Inches(10)
    prs.slide_height = Inches(5.625)

    sections = contenu.split('###')
    for section in sections:
        if len(section.strip()) > 10:
            slide = prs.slides.add_slide(prs.slide_layouts[6]) # Layout totalement VIDE
            lignes = section.strip().split('\n')
            titre_s = lignes[0].replace('**', '').strip()
            corps_s = '\n'.join(lignes[1:]).strip()
            
            appliquer_style_cfa(slide, titre_s)
            
            # Gestion Image (Améliorée pour éviter le "nul")
            image_match = re.search(r'\[IMG:(.*?)\]', corps_s)
            has_image = False
            if image_match:
                prompt_img = image_match.group(1).strip()
                corps_s = corps_s.replace(image_match.group(0), '').strip()
                # On booste le prompt d'image en coulisse
                url = f"https://image.pollinations.ai/prompt/high_quality_professional_photography_{prompt_img.replace(' ', '_')}_cinematic_lighting?width=600&height=450&nologo=true"
                try:
                    img_data = requests.get(url, timeout=10).content
                    slide.shapes.add_picture(io.BytesIO(img_data), Inches(5.2), Inches(1.2), width=Inches(4.5))
                    has_image = True
                except: pass

            # Gestion Texte
            width = Inches(4.5) if has_image else Inches(9)
            txBox = slide.shapes.add_textbox(Inches(0.5), Inches(1.2), width, Inches(4))
            tf = txBox.text_frame
            tf.word_wrap = True
            
            paragraphes = [p for p in corps_s.split('\n') if p.strip()]
            for p_text in paragraphes[:8]:
                p = tf.add_paragraph()
                p.text = "• " + p_text.replace('*', '').replace('-', '').strip()
                p.font.size = Pt(18)
                p.font.color.rgb = RGBColor(30, 30, 30)

    buf = io.BytesIO()
    prs.save(buf)
    buf.seek(0)
    return buf

# 3. INTERFACE
st.set_page_config(page_title="Craie-ative AI Studio", layout="wide")
st.title("🎨 Craie-ative AI : Édition Studio Chartres")

if 'liste' not in st.session_state:
    st.session_state.liste = ["BP Boucher", "BP Boulanger", "Bac Pro Maintenance", "BTS Maintenance", "CAP EPC"]

with st.sidebar:
    st.header("⚙️ Menu")
    nouveau = st.text_input("Nouveau diplôme :")
    if st.button("Ajouter") and nouveau:
        st.session_state.liste.append(nouveau)
        st.rerun()

diplome = st.selectbox("Diplôme :", st.session_state.liste)
sujet = st.text_input("Sujet de la mission :")

if st.button("🚀 Lancer la production Premium"):
    if sujet:
        with st.spinner("L'IA forge vos diapositives..."):
            try:
                moteurs = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                model = genai.GenerativeModel(moteurs[0])
                prompt = f"Expert pédagogie CFA Chartres. Cours 60min pour {diplome} sur {sujet}. Humour et jeux de mots. Structure ### 1. Accroche, ### 2. Mission, ### 3. Exercice, ### 4. Synthèse. Ajoute [IMG: professional photography of {sujet}] à chaque fin de section."
                res = model.generate_content(prompt)
                st.markdown(res.text)
                file = generer_pptx_premium(diplome, sujet, res.text)
                st.download_button("📥 Télécharger le PowerPoint Studio", file, f"Cours_{sujet}.pptx")
            except Exception as e:
                st.error(f"Erreur : {e}")

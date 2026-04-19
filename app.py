import streamlit as st
import google.generativeai as genai
import io, requests, re, random
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor

# 1. CONFIGURATION
genai.configure(api_key=st.secrets["API_KEY"])

# 2. DESIGN PREMIUM (Bandeau bleu + Liseré orange)
def appliquer_style_cfa(slide, titre_texte):
    bandeau = slide.shapes.add_shape(1, 0, 0, Inches(10), Inches(0.8))
    bandeau.fill.solid()
    bandeau.fill.fore_color.rgb = RGBColor(0, 82, 204) # Bleu CFA
    bandeau.line.visible = False
    
    lisere = slide.shapes.add_shape(1, 0, Inches(0.8), Inches(10), Inches(0.05))
    lisere.fill.solid()
    lisere.fill.fore_color.rgb = RGBColor(255, 102, 0) # Orange
    lisere.line.visible = False

    txBox = slide.shapes.add_textbox(Inches(0.5), Inches(0.1), Inches(9), Inches(0.6))
    p = txBox.text_frame.paragraphs[0]
    p.text = titre_texte
    p.font.bold, p.font.size, p.font.color.rgb = True, Pt(24), RGBColor(255, 255, 255)

def generer_pptx_premium(diplome, sujet, contenu):
    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(10), Inches(5.625)
    
    sections = contenu.split('###')
    for section in sections:
        if len(section.strip()) > 10:
            lines = section.strip().split('\n')
            titre_s = lines[0].replace('**', '').strip()
            corps_brut = '\n'.join(lines[1:]).strip()
            
            # Extraction du prompt d'image
            img_match = re.search(r'\[IMG:(.*?)\]', corps_brut)
            prompt_img = img_match.group(1) if img_match else sujet
            corps_propre = corps_brut.replace(f"[IMG:{prompt_img}]", "").strip()
            
            # Découpage auto : max 5 paragraphes par slide
            paragraphes = [p.strip() for p in corps_propre.split('\n') if p.strip()]
            for i in range(0, max(1, len(paragraphes)), 5):
                slide = prs.slides.add_slide(prs.slide_layouts[6])
                t_suffixe = f" (suite {i//5 + 1})" if i > 0 else ""
                appliquer_style_cfa(slide, titre_s + t_suffixe)
                
                has_img = False
                if i == 0:
                    seed = random.randint(1, 1000)
                    url = f"https://image.pollinations.ai/prompt/vibrant_colorful_digital_art_{prompt_img.replace(' ', '_')}_happy_lighting?width=512&height=512&nologo=true&seed={seed}"
                    try:
                        img_data = requests.get(url, timeout=10).content
                        slide.shapes.add_picture(io.BytesIO(img_data), Inches(5.5), Inches(1.2), width=Inches(4))
                        has_img = True
                    except: pass

                txBox = slide.shapes.add_textbox(Inches(0.5), Inches(1.2), Inches(4.8) if has_img else Inches(9), Inches(4))
                tf = txBox.text_frame
                tf.word_wrap = True
                for p_text in paragraphes[i:i+5]:
                    p = tf.add_paragraph()
                    p.text = "• " + p_text.replace('*', '').strip()
                    p.font.size, p.font.color.rgb = Pt(17), RGBColor(30, 30, 30)
    
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
    st.header("⚙️ Paramètres")
    nouveau = st.text_input("Ajouter un diplôme :")
    if st.button("Ajouter") and nouveau:
        st.session_state.liste.append(nouveau)
        st.rerun()

diplome = st.selectbox("Diplôme visé :", st.session_state.liste)
sujet = st.text_input("Sujet de la leçon :", placeholder="ex: La gestion des stocks")

if st.button("🚀 GÉNÉRER LE COURS COMPLET"):
    if sujet:
        with st.spinner("Construction du cours selon le référentiel..."):
            moteur = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods][0]
            model = genai.GenerativeModel(moteur)
            
            prompt = f"""
            Tu es un expert en pédagogie pour le CFA de Chartres. 
            Crée un cours de 60 minutes ultra-complet pour des apprentis en {diplome}. Sujet : {sujet}.
            
            CONSIGNES :
            - Respecte scrupuleusement le référentiel du diplôme {diplome}.
            - Adapte le vocabulaire et la complexité au niveau (CAP, BP ou BTS).
            - Ton ludique, humour, jeux de mots, localisé à Chartres.
            - Ne salue pas. Ne nomme jamais 'Manu'.
            
            STRUCTURE OBLIGATOIRE (utilise ### pour chaque section) :
            ### 1. L'Accroche
            (Scénario drôle. [IMG: colorful cartoon of {sujet}])
            
            ### 2. Rappel du Référentiel
            (Les compétences visées par ce cours).
            
            ### 3. La Mission Professionnelle
            (Détails du travail à accomplir. [IMG: professional bright photo of {sujet} at work])
            
            ### 4. Exercice d'Application
            (Mise en situation concrète avec calculs ou manipulation).
            
            ### 5. Quiz Interactif (QCM)
            (3 questions avec 3 choix possibles).
            
            ### 6. Le Vrai ou Faux
            (5 affirmations à valider).
            
            ### 7. Activité Pédagogique (FOAD 60min)
            (Consignes pour un travail en autonomie).
            
            ### 8. La Synthèse
            (L'essentiel à retenir).
            """
            
            res = model.generate_content(prompt)
            st.markdown(res.text)
            file = generer_pptx_premium(diplome, sujet, res.text)
            st.download_button("📥 Télécharger le PowerPoint Complet", file, f"Cours_{sujet}.pptx")

import streamlit as st
import google.generativeai as genai
import io, requests, re, random
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor

# 1. CONFIGURATION
genai.configure(api_key=st.secrets["API_KEY"])

# 2. DESIGN PREMIUM AVEC LISERÉ ORANGE
def appliquer_style_cfa(slide, titre_texte):
    # Bandeau bleu
    bandeau = slide.shapes.add_shape(1, 0, 0, Inches(10), Inches(0.8))
    bandeau.fill.solid()
    bandeau.fill.fore_color.rgb = RGBColor(0, 82, 204) # Bleu CFA
    bandeau.line.visible = False
    
    # Liseré orange (Pour la gaieté !)
    lisere = slide.shapes.add_shape(1, 0, Inches(0.8), Inches(10), Inches(0.05))
    lisere.fill.solid()
    lisere.fill.fore_color.rgb = RGBColor(255, 102, 0) # Orange dynamique
    lisere.line.visible = False

    # Titre
    txBox = slide.shapes.add_textbox(Inches(0.5), Inches(0.1), Inches(9), Inches(0.6))
    p = txBox.text_frame.paragraphs[0]
    p.text = titre_texte
    p.font.bold, p.font.size, p.font.color.rgb = True, Pt(26), RGBColor(255, 255, 255)

def generer_pptx_premium(diplome, sujet, contenu):
    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(10), Inches(5.625)
    
    sections = contenu.split('###')
    for section in sections:
        if len(section.strip()) > 10:
            lines = section.strip().split('\n')
            titre_s = lines[0].replace('**', '').strip()
            # Nettoyage du texte et retrait des balises images pour le traitement texte
            corps_brut = '\n'.join(lines[1:]).strip()
            img_match = re.search(r'\[IMG:(.*?)\]', corps_brut)
            prompt_img = img_match.group(1) if img_match else sujet
            corps_propre = corps_brut.replace(f"[IMG:{prompt_img}]", "").strip()
            
            # DÉCOUPAGE INTELLIGENT (Max 5 paragraphes par slide)
            paragraphes = [p.strip() for p in corps_propre.split('\n') if p.strip()]
            for i in range(0, max(1, len(paragraphes)), 5):
                slide = prs.slides.add_slide(prs.slide_layouts[6])
                t_suffixe = f" (suite {i//5 + 1})" if i > 0 else ""
                appliquer_style_cfa(slide, titre_s + t_suffixe)
                
                # IMAGE (Seulement sur la première slide de la section)
                has_img = False
                if i == 0:
                    seed = random.randint(1, 1000) # Pour éviter que ce soit toujours la même image
                    # Prompt "Anti-glauque" : Couleurs vives, style cartoon ou pro lumineux
                    url = f"https://image.pollinations.ai/prompt/vibrant_colorful_digital_art_style_{prompt_img.replace(' ', '_')}_happy_atmosphere_bright_lighting?width=512&height=512&nologo=true&seed={seed}"
                    try:
                        img_data = requests.get(url, timeout=10).content
                        slide.shapes.add_picture(io.BytesIO(img_data), Inches(5.5), Inches(1.2), width=Inches(4))
                        has_img = True
                    except: pass

                # TEXTE
                txBox = slide.shapes.add_textbox(Inches(0.5), Inches(1.2), Inches(4.8) if has_img else Inches(9), Inches(4))
                tf = txBox.text_frame
                tf.word_wrap = True
                for p_text in paragraphes[i:i+5]:
                    p = tf.add_paragraph()
                    p.text = "• " + p_text.replace('*', '').strip()
                    p.font.size, p.font.color.rgb = Pt(18), RGBColor(40, 40, 40)
    
    buf = io.BytesIO()
    prs.save(buf)
    buf.seek(0)
    return buf

# 3. INTERFACE STREAMLIT
st.set_page_config(page_title="Craie-ative AI Studio V5", layout="wide")
st.title("🎨 Craie-ative AI : Édition Studio Premium")

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
        with st.spinner("L'IA mixe les couleurs et ajuste le texte..."):
            moteur = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods][0]
            model = genai.GenerativeModel(moteur)
            # Prompt forçant la brièveté et le style joyeux
            prompt = f"Expert pédagogie CFA Chartres. Cours 60min pour {diplome} sur {sujet}. Humour, jeux de mots, Chartres. STRUCTURE : ### 1. L'Accroche, ### 2. La Mission, ### 3. L'Exercice Pratique, ### 4. La Synthèse. Écris des paragraphes COURTS. Ajoute [IMG: a very colorful and happy cartoon of {sujet}] à chaque section."
            res = model.generate_content(prompt)
            st.markdown(res.text)
            file = generer_pptx_premium(diplome, sujet, res.text)
            st.download_button("📥 Télécharger le PowerPoint Studio V5", file, f"Cours_{sujet}.pptx")

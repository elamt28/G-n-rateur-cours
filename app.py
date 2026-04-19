import streamlit as st
import google.generativeai as genai
import io, requests, re, random
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor

# 1. CONFIGURATION
genai.configure(api_key=st.secrets["API_KEY"])

# 2. DESIGN ALTERNÉ (Bleu pour Question / Rouge pour Réponse)
def appliquer_style_interactif(slide, titre_texte, est_reponse=False):
    couleur_fond = RGBColor(180, 0, 0) if est_reponse else RGBColor(0, 82, 204)
    
    # Bandeau
    bandeau = slide.shapes.add_shape(1, 0, 0, Inches(10), Inches(0.7))
    bandeau.fill.solid()
    bandeau.fill.fore_color.rgb = couleur_fond
    bandeau.line.visible = False
    
    # Liseré Orange
    lisere = slide.shapes.add_shape(1, 0, Inches(0.7), Inches(10), Inches(0.05))
    lisere.fill.solid()
    lisere.fill.fore_color.rgb = RGBColor(255, 102, 0)
    lisere.line.visible = False

    # Titre
    txBox = slide.shapes.add_textbox(Inches(0.5), Inches(0.05), Inches(9), Inches(0.6))
    p = txBox.text_frame.paragraphs[0]
    p.text = ("RÉPONSE : " if est_reponse else "DÉFI : ") + titre_texte
    p.font.bold, p.font.size, p.font.color.rgb = True, Pt(22), RGBColor(255, 255, 255)

def ajouter_paire_slides(prs, titre, texte_question, texte_reponse, prompt_img=None):
    # --- 1. Slide Question (Bleue) ---
    slide_q = prs.slides.add_slide(prs.slide_layouts[6])
    appliquer_style_interactif(slide_q, titre, est_reponse=False)
    
    has_img = False
    if prompt_img:
        seed = random.randint(1, 9999)
        url = f"https://image.pollinations.ai/prompt/vibrant_colorful_cartoon_of_{prompt_img.replace(' ', '_')}?width=512&height=512&nologo=true&seed={seed}"
        try:
            img_data = requests.get(url, timeout=5).content
            slide_q.shapes.add_picture(io.BytesIO(img_data), Inches(5.6), Inches(1.2), width=Inches(4))
            has_img = True
        except: pass

    txBox_q = slide_q.shapes.add_textbox(Inches(0.5), Inches(1.2), Inches(4.8) if has_img else Inches(9), Inches(4))
    tf_q = txBox_q.text_frame
    tf_q.word_wrap = True
    for line in texte_question.split('\n'):
        if line.strip():
            p = tf_q.add_paragraph()
            p.text = "• " + line.replace('*', '').strip()
            p.font.size, p.font.color.rgb = Pt(18), RGBColor(30, 30, 30)

    # --- 2. Slide Réponse (Rouge) ---
    slide_r = prs.slides.add_slide(prs.slide_layouts[6])
    appliquer_style_interactif(slide_r, titre, est_reponse=True)
    txBox_r = slide_r.shapes.add_textbox(Inches(0.5), Inches(1.2), Inches(9), Inches(4))
    tf_r = txBox_r.text_frame
    tf_r.word_wrap = True
    for line in texte_reponse.split('\n'):
        if line.strip():
            p = tf_r.add_paragraph()
            p.text = "✔ " + line.replace('*', '').strip()
            p.font.size, p.font.color.rgb = Pt(18), RGBColor(0, 100, 0) # Vert foncé pour la réussite

def generer_pptx_interactif(cours_dict):
    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(10), Inches(5.625)
    
    for section in cours_dict:
        ajouter_paire_slides(
            prs, 
            section['titre'], 
            section['question'], 
            section['reponse'], 
            section.get('img')
        )
        
    buf = io.BytesIO()
    prs.save(buf)
    buf.seek(0)
    return buf

# 3. INTERFACE
st.set_page_config(page_title="Générateur de cours", layout="wide")
st.title("🛠️ Générateur de cours")

diplome = st.selectbox("Diplôme :", ["BP Boucher", "BP Boulanger", "Bac Pro Maintenance", "BTS Maintenance", "CAP EPC", "BP Coiffure", "AMLHR"])
sujet = st.text_input("Sujet de la leçon :")
lieu = st.text_input("Lieu du scénario :", value="Chartres")

if st.button("🚀 GÉNÉRER LE COURS INTERACTIF"):
    if sujet:
        with st.spinner("Préparation du duel pédagogique..."):
            moteur = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods][0]
            model = genai.GenerativeModel(moteur)
            
            prompt = f"""Expert pédagogique CFA Chartres. Sujet: {sujet} pour {diplome} à {lieu}.
            Crée un cours sous forme de DUELS (Question puis Réponse).
            
            Format de réponse obligatoire par section :
            SECTION: [Titre de la section]
            IMAGE: [Description cartoon]
            QUESTION: [Enoncé du défi ou de la question pour l'apprenti]
            REPONSE: [La correction détaillée pour le formateur]
            ### (Utilise ### pour séparer les duels)
            
            Prévoyez 5 duels : 
            1. L'Accroche (Scénario humour)
            2. La Mission (Problème technique ou de gestion)
            3. Le Quiz QCM
            4. Le Vrai ou Faux
            5. L'Exercice de Synthèse
            """
            
            res = model.generate_content(prompt).text
            st.markdown(res) # Affichage pour contrôle
            
            # Parsing intelligent
            duels = res.split('###')
            data_cours = []
            for d in duels:
                if "SECTION:" in d:
                    try:
                        titre = re.search(r"SECTION:(.*)", d).group(1).strip()
                        img = re.search(r"IMAGE:(.*)", d).group(1).strip()
                        ques = re.search(r"QUESTION:([\s\S]*?)REPONSE:", d).group(1).strip()
                        rep = re.search(r"REPONSE:([\s\S]*)", d).group(1).strip()
                        data_cours.append({'titre': titre, 'question': ques, 'reponse': rep, 'img': img})
                    except: pass

            file = generer_pptx_interactif(data_cours)
            st.download_button("📥 Télécharger le PowerPoint Interactif", file, f"Duel_{sujet}.pptx")

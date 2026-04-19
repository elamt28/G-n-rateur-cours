import streamlit as st
import google.generativeai as genai
import io
import requests
import re
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor

# 1. CONFIGURATION
# Remplacer par la vraie clé API (ex: "AIzaSy...")
API_KEY = st.secrets["API_KEY"]
genai.configure(api_key=API_KEY)

# 2. LE MOTEUR POWERPOINT (Anti-débordement + Images)
def generer_pptx_parfait(diplome, sujet, contenu):
    prs = Presentation()
    
    # --- Diapo de Titre ---
    slide_titre = prs.slides.add_slide(prs.slide_layouts[0])
    slide_titre.shapes.title.text = f"🎯 MISSION : {sujet.upper()}"
    slide_titre.shapes.title.text_frame.paragraphs[0].font.color.rgb = RGBColor(0, 82, 204)
    slide_titre.placeholders[1].text = f"Formation : {diplome}\nCFA Interpro de Chartres\nDurée : 60 minutes"

    # --- Découpage par grandes sections (###) ---
    sections = contenu.split('###')
    for section in sections:
        if len(section.strip()) > 10:
            parties = section.strip().split('\n')
            titre_brut = parties[0].replace('**', '').strip()
            corps_brut = '\n'.join(parties[1:]).strip()
            
            # Recherche d'une image demandée par l'IA
            image_match = re.search(r'\[IMG:(.*?)\]', corps_brut)
            image_url = None
            if image_match:
                prompt_img = image_match.group(1).strip()
                corps_brut = corps_brut.replace(image_match.group(0), '').strip()
                image_url = f"https://image.pollinations.ai/prompt/{prompt_img.replace(' ', '%20')}?width=400&height=300&nologo=true"

            # SOLUTION ANTI-DÉBORDEMENT : Coupe tous les 6 paragraphes
            lignes = [l for l in corps_brut.split('\n') if l.strip() != '']
            max_lignes = 6 
            
            for i in range(0, max(1, len(lignes)), max_lignes):
                slide = prs.slides.add_slide(prs.slide_layouts[1])
                
                # Gestion du titre (ajoute "suite" si on déborde sur plusieurs slides)
                t = slide.shapes.title
                t.text = f"{titre_brut} (suite)" if i > 0 else titre_brut
                t.text_frame.paragraphs[0].font.color.rgb = RGBColor(255, 102, 0)
                
                # Boîte de texte
                tf = slide.placeholders[1]
                chunk = lignes[i:i + max_lignes]
                
                # Insertion de l'image (uniquement sur la première diapo de la section)
                if i == 0 and image_url:
                    tf.width = Inches(5) # Réduit le texte pour faire de la place
                    try:
                        rep = requests.get(image_url, timeout=10)
                        img_stream = io.BytesIO(rep.content)
                        slide.shapes.add_picture(img_stream, Inches(5.5), Inches(2), width=Inches(4))
                    except Exception as e:
                        pass # Si le réseau coupe, on ignore l'image sans bloquer le cours

                # Ajout du texte
                tf.text = '\n'.join(chunk).replace('**', '')
                for p in tf.text_frame.paragraphs:
                    p.font.size = Pt(20)

    buf = io.BytesIO()
    prs.save(buf)
    buf.seek(0)
    return buf

# 3. INTERFACE STREAMLIT
st.set_page_config(page_title="Craie-ative AI", page_icon="🎓", layout="wide")
st.title("🛠️ Assistant Pédagogique CFA Chartres")
st.markdown("---")

col1, col2 = st.columns(2)
with col1:
    diplome = st.selectbox("Sélectionnez le diplôme :", [
        "BP Boucher", "BP Boulanger", "BM Boulanger", "CAP EPC", 
        "BP Coiffure", "Bac Pro Maintenance Véhicule", 
        "BTS Maintenance Véhicule", "Carrossier/Peintre", "AMLHR"
    ])
with col2:
    sujet = st.text_input("Sujet de la leçon :", placeholder="ex: La gestion des stocks")

if st.button("🚀 GÉNÉRER LE COURS & LE POWERPOINT"):
    if sujet:
        with st.spinner("L'IA génère les textes, structure les diapos et dessine les images..."):
            try:
                # Scanner de moteur
                moteurs_dispos = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                model = genai.GenerativeModel(moteurs_dispos[0])
                
                # PROMPT VERROUILLÉ
                prompt = f"""
                Tu es un expert en pédagogie pour le CFA de Chartres. 
                Crée un cours FOAD détaillé de 60 minutes pour des apprentis en {diplome}. Sujet : {sujet}.
                
                CONSIGNES STRICTES :
                - Ton ludique, avec humour et jeux de mots.
                - Localise l'action près de Chartres.
                - Ne salue pas. Ne nomme jamais 'Manu'.
                - Fais des phrases courtes ou des listes à puces pour que le texte soit aéré.
                
                TU DOIS IMPÉRATIVEMENT UTILISER CES 4 TITRES AVEC LA BALISE ### :
                
                ### 1. L'Accroche
                (Texte drôle). Ajoute à la fin : [IMG: a funny cartoon style drawing of a {diplome} dealing with {sujet}]
                
                ### 2. La Mission
                (Détails du travail). Ajoute à la fin : [IMG: professional bright photography of {diplome} at work in Chartres]
                
                ### 3. L'Exercice Pratique (60 min)
                (Consignes étape par étape). Ajoute à la fin : [IMG: 3d cartoon style illustration of a clipboard and tools]
                
                ### 4. La Synthèse
                (Résumé des points clés à retenir absolument).
                """
                
                response = model.generate_content(prompt)
                st.session_state.cours = response.text
                
                st.success("✅ Cours complet généré avec succès !")
                st.markdown(st.session_state.cours)
                
                pptx_file = generer_pptx_parfait(diplome, sujet, st.session_state.cours)
                
                st.download_button(
                    label="📥 TÉLÉCHARGER LE POWERPOINT (.pptx)",
                    data=pptx_file,
                    file_name=f"Cours_Complet_{sujet.replace(' ', '_')}.pptx",
                    mime="application/vnd.openxmlformats-officedocument.presentationml.presentation"
                )
            except Exception as e:
                st.error(f"Erreur de communication : {e}")
    else:
        st.error("Veuillez saisir un sujet et configurer votre clé API !")

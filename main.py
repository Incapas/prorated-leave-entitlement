"""Point d'entrée de l'application : `streamlit run main.py`.

Calcule un nombre de congés annuels et de RTT proratisé sur une année de référence,
à partir de périodes d'activité affectées chacune d'une quotité de travail.

Deux pages sont proposées : une présentation du fonctionnement, servie en accueil,
et le formulaire de calcul.
"""

import streamlit as st

st.set_page_config(page_title="Congés et RTT proratisés", page_icon="🗓️")

about_page = st.Page(
    "app/about.py",
    title="À propos",
    icon=":material/info:",
    default=True,
)

calculator_page = st.Page(
    "app/calculator.py",
    title="Périodes d'activité",
    icon=":material/calculate:",
)

st.navigation([about_page, calculator_page]).run()

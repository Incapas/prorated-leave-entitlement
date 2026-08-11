"""Page de calcul : saisie des périodes et restitution des droits annuels."""

import streamlit as st

from app.calculations import build_summary
from app.ui import (
    render_details,
    render_diagnostics,
    render_metrics,
    render_period_rows,
    render_sidebar,
)


def render_calculator() -> None:
    """Affiche la page « Périodes d'activité ».

    Enchaîne les paramètres annuels, la saisie des périodes, le calcul et sa
    restitution. Le résultat est recalculé à chaque interaction : aucune
    validation n'est à déclencher.
    """
    st.title("Périodes d'activité")
    st.divider()

    settings = render_sidebar()
    periods = render_period_rows(settings)
    summary = build_summary(periods, settings)

    st.divider()
    render_metrics(summary)
    st.divider()

    render_diagnostics(summary)
    render_details(summary)


render_calculator()

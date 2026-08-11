"""Composants Streamlit : saisie des périodes et restitution des résultats."""

from datetime import date

import streamlit as st

from app.models import MONTHS_PER_YEAR, AnnualSummary, Period, Settings

DATE_FORMAT: str = "DD/MM/YYYY"
"""Format d'affichage des dates dans les widgets."""

EMPTY_CELL: str = "—"
"""Marque affichée dans le tableau à la place d'un champ non renseigné."""

FIELD_PREFIXES: tuple[str, ...] = ("start", "end", "rate")
"""Préfixes des clés de widgets composant une ligne."""

DEFAULT_MIN_RATE: int = 50
"""Quotité minimale sélectionnable, en pourcentage."""

DEFAULT_MAX_RATE: int = 100
"""Quotité maximale sélectionnable, en pourcentage."""


def _initialise_rows() -> None:
    """Crée la première ligne au premier affichage de l'application.

    Chaque ligne porte un identifiant stable, jamais réutilisé, ce qui garantit
    l'unicité des clés de widgets même après suppression.
    """
    if "row_ids" not in st.session_state:
        st.session_state.row_ids = [0]
        st.session_state.next_row_id = 1


def _initialise_row_state(row_id: int) -> None:
    """Initialise les trois champs d'une ligne à vide, sans écraser une saisie."""
    for prefix in FIELD_PREFIXES:
        st.session_state.setdefault(f"{prefix}_{row_id}", None)


def _add_row() -> None:
    """Ajoute une ligne vierge à la fin du formulaire."""
    st.session_state.row_ids.append(st.session_state.next_row_id)
    st.session_state.next_row_id += 1


def _remove_row(row_id: int) -> None:
    """Supprime une ligne et les valeurs de ses widgets."""
    st.session_state.row_ids.remove(row_id)
    for prefix in FIELD_PREFIXES:
        st.session_state.pop(f"{prefix}_{row_id}", None)


def _clear_dates_on_year_change(year: int) -> None:
    """Vide les dates saisies lorsque l'année de référence change.

    Les dates de l'ancienne année sortiraient des bornes autorisées par les
    widgets, ce qui empêcherait leur affichage.
    """
    if st.session_state.get("applied_year") == year:
        return
    for row_id in st.session_state.row_ids:
        st.session_state[f"start_{row_id}"] = None
        st.session_state[f"end_{row_id}"] = None
    st.session_state.applied_year = year


def render_sidebar() -> Settings:
    """Affiche les paramètres annuels et retourne les valeurs choisies.

    Returns:
        L'année de référence et les droits annuels à taux plein.
    """
    with st.sidebar:
        st.header("Paramètres")
        year = st.number_input(
            label="Année de référence",
            min_value=2000,
            max_value=2100,
            value=date.today().year,
            step=1,
            key="year",
        )
        annual_leave_allowance = st.number_input(
            label="Droit congés annuels (jours / an)",
            min_value=0.0,
            value=25.0,
            step=0.5,
            key="annual_leave_allowance",
            help="Congés annuels pour un temps plein (100%)"
        )
        rtt_allowance = st.number_input(
            label="Droit RTT (jours / an)",
            min_value=0.0,
            value=15.0,
            step=0.5,
            key="rtt_allowance",
            help="Droit RTT pour un temps plein (100%)"
        )

    return Settings(
        year=int(year),
        annual_leave_allowance=float(annual_leave_allowance),
        rtt_allowance=float(rtt_allowance),
    )


def render_period_rows(settings: Settings) -> list[Period]:
    """Affiche le tableau de saisie des périodes et retourne les valeurs saisies.

    Les dates sont bornées à l'année de référence : aucune saisie n'est possible
    avant le 01/01 ni après le 31/12.

    Args:
        settings: Année de référence et droits annuels à taux plein.

    Returns:
        Une période par ligne affichée, dans l'ordre de saisie, champs vides compris.
    """
    _initialise_rows()
    _clear_dates_on_year_change(settings.year)

    st.button("➕ Ajouter une ligne", on_click=_add_row, type='tertiary')

    for index, row_id in enumerate(st.session_state.row_ids):
        _initialise_row_state(row_id)
        # Libellés affichés uniquement sur la première ligne
        visibility = "visible" if index == 0 else "collapsed"
        start_column, end_column, rate_column, delete_column = st.columns(
            [3, 3, 3, 1], vertical_alignment="bottom"
        )

        with start_column:
            st.date_input(
                label="Début",
                key=f"start_{row_id}",
                label_visibility=visibility,
                format=DATE_FORMAT,
                min_value=settings.first_day,
                max_value=settings.last_day,
            )

        with end_column:
            st.date_input(
                label="Fin",
                key=f"end_{row_id}",
                label_visibility=visibility,
                format=DATE_FORMAT,
                min_value=settings.first_day,
                max_value=settings.last_day,
            )

        with rate_column:
            st.number_input(
                label="Quotité",
                min_value=DEFAULT_MIN_RATE,
                max_value=DEFAULT_MAX_RATE,
                step=10,
                key=f"rate_{row_id}",
                label_visibility=visibility,
            )

        with delete_column:
            st.button(
                "🗑️",
                key=f"delete_{row_id}",
                on_click=_remove_row,
                args=(row_id,),
                disabled=len(st.session_state.row_ids) == 1,
            )

    return [
        Period(
            start=st.session_state[f"start_{row_id}"],
            end=st.session_state[f"end_{row_id}"],
            rate=st.session_state[f"rate_{row_id}"],
        )
        for row_id in st.session_state.row_ids
    ]


def render_metrics(summary: AnnualSummary) -> None:
    """Affiche les droits annuels et le compteur de couverture.

    Args:
        summary: Récapitulatif annuel à afficher.
    """
    leave_column, rtt_column, coverage_column = st.columns(3)
    leave_column.metric("Congés proratisés", f"{summary.annual_leave} j")
    rtt_column.metric("RTT proratisés", f"{summary.rtt} j")
    coverage_column.metric(
        "Couverture annuelle",
        f"{summary.total_months:.2f} / {MONTHS_PER_YEAR} mois",
    )


def render_diagnostics(summary: AnnualSummary) -> None:
    """Affiche les erreurs de saisie et l'état de la couverture annuelle.

    Args:
        summary: Récapitulatif annuel à contrôler.
    """
    for error in summary.errors:
        st.error(error)

    year = summary.settings.year
    if summary.is_fully_covered:
        if not summary.errors:
            st.success(f"Année {year} intégralement couverte (12,00 mois).")
    elif summary.coverage_gap < 0:
        st.warning(
            f"Année incomplète : il manque {-summary.coverage_gap:.2f} mois de "
            f"couverture entre le 01/01/{year} et le 31/12/{year}."
        )
    else:
        st.error(
            f"Année dépassée de {summary.coverage_gap:.2f} mois : "
            "les périodes se recouvrent."
        )


def render_details(summary: AnnualSummary) -> None:
    """Affiche le détail ligne par ligne, sans arrondi.

    Args:
        summary: Récapitulatif annuel dont afficher le détail.
    """
    st.dataframe(
        [
            {
                "Début": (
                    f"{entitlement.period.start:%d/%m/%Y}"
                    if entitlement.period.start
                    else EMPTY_CELL
                ),
                "Fin": (
                    f"{entitlement.period.end:%d/%m/%Y}"
                    if entitlement.period.end
                    else EMPTY_CELL
                ),
                "Quotité": (
                    f"{entitlement.period.rate} %"
                    if entitlement.period.rate is not None
                    else EMPTY_CELL
                ),
                "Mois": f"{entitlement.months:.4f}",
                "Congés": f"{entitlement.annual_leave:.2f}",
                "RTT": f"{entitlement.rtt:.2f}",
            }
            for entitlement in summary.entitlements
        ],
        hide_index=True,
        width="stretch",
    )

    st.caption(
        "Les congés et RTT par ligne sont détaillés sans arrondi ; "
        "l'arrondi à l'entier le plus proche n'est appliqué qu'au total."
    )

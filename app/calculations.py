"""Calcul du prorata de congés annuels et de RTT sur une année de référence."""

from calendar import monthrange
from datetime import date
from math import floor

from app.models import (
    MONTHS_PER_YEAR,
    AnnualSummary,
    Period,
    PeriodEntitlement,
    Settings,
)
from app.validation import validate_periods


def month_fraction(start: date, end: date, year: int) -> float:
    """Nombre de mois couverts entre deux dates, bornes incluses.

    Applique la formule de référence : mois complets, plus la fraction des mois
    partiels (jours couverts divisés par le nombre de jours du mois). Le calcul
    est mené mois par mois sur l'année de référence, un mois entièrement couvert
    valant exactement 1. Une période du 01/01 au 31/12 vaut donc 12, et un
    découpage contigu de l'année redonne toujours 12 au total.

    Les portions de période situées hors de l'année de référence sont ignorées.

    Args:
        start: Date de début, incluse.
        end: Date de fin, incluse.
        year: Année de référence sur laquelle projeter la période.

    Returns:
        Le nombre de mois couverts, entre 0 et 12.
    """
    total = 0.0
    for month in range(1, MONTHS_PER_YEAR + 1):
        days_in_month = monthrange(year, month)[1]
        covered_start = max(start, date(year, month, 1))
        covered_end = min(end, date(year, month, days_in_month))
        if covered_start > covered_end:
            continue
        total += ((covered_end - covered_start).days + 1) / days_in_month
    return total


def round_to_nearest(value: float) -> int:
    """Arrondit à l'entier le plus proche, les demis étant arrondis au supérieur.

    `round` de la bibliothèque standard arrondit les demis vers l'entier pair
    (2,5 donne 2), ce qui ne correspond pas à l'usage attendu sur des jours de
    congés.

    Args:
        value: Valeur à arrondir, positive ou négative.

    Returns:
        L'entier le plus proche de la valeur.
    """
    return floor(value + 0.5)


def compute_entitlement(period: Period, settings: Settings) -> PeriodEntitlement:
    """Calcule les droits générés par une période.

    Une période incomplète ou dont les dates sont inversées ne génère aucun
    droit : elle est signalée par la validation, pas par le calcul.

    Args:
        period: Période saisie sur une ligne du formulaire.
        settings: Année de référence et droits annuels à taux plein.

    Returns:
        Le détail des mois couverts et des droits, sans arrondi.
    """
    if not period.is_usable:
        return PeriodEntitlement(period=period, months=0.0, annual_leave=0.0, rtt=0.0)

    months = month_fraction(period.start, period.end, settings.year)
    share = months / MONTHS_PER_YEAR * period.rate / 100
    return PeriodEntitlement(
        period=period,
        months=months,
        annual_leave=settings.annual_leave_allowance * share,
        rtt=settings.rtt_allowance * share,
    )


def build_summary(periods: list[Period], settings: Settings) -> AnnualSummary:
    """Consolide toutes les périodes en un résultat annuel.

    Les droits sont sommés sur l'ensemble des périodes, plafonnés au droit annuel
    à taux plein, puis arrondis à l'entier le plus proche. L'arrondi n'intervient
    donc qu'une seule fois, sur le total.

    Args:
        periods: Périodes saisies, y compris les lignes vides ou incohérentes.
        settings: Année de référence et droits annuels à taux plein.

    Returns:
        Le récapitulatif annuel, avec le détail par période et les erreurs de saisie.
    """
    entitlements = [compute_entitlement(period, settings) for period in periods]
    total_months = sum(entitlement.months for entitlement in entitlements)
    capped_annual_leave = min(
        sum(entitlement.annual_leave for entitlement in entitlements),
        settings.annual_leave_allowance,
    )
    capped_rtt = min(
        sum(entitlement.rtt for entitlement in entitlements),
        settings.rtt_allowance,
    )

    return AnnualSummary(
        settings=settings,
        entitlements=entitlements,
        total_months=total_months,
        annual_leave=round_to_nearest(capped_annual_leave),
        rtt=round_to_nearest(capped_rtt),
        errors=validate_periods(periods),
    )

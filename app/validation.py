"""Contrôles de cohérence appliqués aux périodes saisies, en temps réel."""

from app.models import Period

INCOMPLETE_ROW_MESSAGE: str = (
    "Une ligne est incomplète : début, fin et quotité sont requis."
)

REVERSED_DATES_MESSAGE: str = (
    "Une période a une date de fin antérieure à sa date de début."
)


def _overlap_message(earlier: Period, later: Period) -> str:
    """Compose le message signalant le chevauchement de deux périodes."""
    return (
        "Chevauchement entre les périodes "
        f"{earlier.start:%d/%m/%Y}–{earlier.end:%d/%m/%Y} et "
        f"{later.start:%d/%m/%Y}–{later.end:%d/%m/%Y}."
    )


def find_overlaps(periods: list[Period]) -> list[str]:
    """Recherche les recouvrements entre périodes exploitables.

    Les périodes sont triées par date de début, puis comparées deux à deux : il y
    a chevauchement dès qu'une période commence avant la fin de la précédente.
    Deux périodes adjacentes (le 31/03 puis le 01/04) ne se chevauchent pas.

    Args:
        periods: Périodes saisies ; les lignes incomplètes ou incohérentes sont ignorées.

    Returns:
        Un message par couple de périodes qui se chevauchent.
    """
    usable = sorted(
        (period for period in periods if period.is_usable),
        key=lambda period: period.start,
    )
    return [
        _overlap_message(earlier, later)
        for earlier, later in zip(usable, usable[1:])
        if later.start <= earlier.end
    ]


def validate_periods(periods: list[Period]) -> list[str]:
    """Rassemble toutes les erreurs de saisie des périodes.

    Une ligne entièrement vierge n'est pas une erreur : elle vient d'être ajoutée
    et n'est simplement pas prise en compte dans le calcul.

    Args:
        periods: Périodes saisies, dans l'ordre d'affichage.

    Returns:
        Les messages d'erreur à afficher, dans l'ordre : dates inversées,
        lignes incomplètes, puis chevauchements. Liste vide si la saisie est saine.
    """
    errors: list[str] = []

    if any(period.is_reversed for period in periods):
        errors.append(REVERSED_DATES_MESSAGE)

    if any(not period.is_complete and not period.is_empty for period in periods):
        errors.append(INCOMPLETE_ROW_MESSAGE)

    errors.extend(find_overlaps(periods))
    return errors

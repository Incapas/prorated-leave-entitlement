"""Structures de données partagées par le calcul, la validation et l'interface."""

from dataclasses import dataclass
from datetime import date

MONTHS_PER_YEAR: int = 12
"""Nombre de mois d'une année complète, cible du compteur de couverture."""

COVERAGE_TOLERANCE: float = 1e-6
"""Marge admise sur le total de mois, pour absorber les erreurs d'arrondi flottant."""


@dataclass(frozen=True)
class Settings:
    """Paramètres annuels saisis dans la barre latérale."""

    year: int
    """Année de référence : aucune date ne peut sortir de cette année."""

    annual_leave_allowance: float
    """Droit à congés annuels pour une année pleine à 100 %, en jours."""

    rtt_allowance: float
    """Droit à RTT pour une année pleine à 100 %, en jours."""

    @property
    def first_day(self) -> date:
        """Premier jour de l'année de référence (01/01)."""
        return date(self.year, 1, 1)

    @property
    def last_day(self) -> date:
        """Dernier jour de l'année de référence (31/12)."""
        return date(self.year, 12, 31)


@dataclass(frozen=True)
class Period:
    """Une période d'activité saisie sur une ligne du formulaire.

    Les trois champs sont vides tant que l'utilisateur n'a rien saisi, d'où les
    valeurs optionnelles.
    """

    start: date | None
    """Date de début, incluse dans la période."""

    end: date | None
    """Date de fin, incluse dans la période."""

    rate: int | None
    """Quotité de travail sur la période, en pourcentage (50 à 100)."""

    @property
    def is_empty(self) -> bool:
        """Vrai si aucun des trois champs n'est renseigné (ligne vierge)."""
        return self.start is None and self.end is None and self.rate is None

    @property
    def is_complete(self) -> bool:
        """Vrai si les trois champs sont renseignés."""
        return self.start is not None and self.end is not None and self.rate is not None

    @property
    def is_reversed(self) -> bool:
        """Vrai si la date de fin précède la date de début."""
        return (
            self.start is not None and self.end is not None and self.end < self.start
        )

    @property
    def is_usable(self) -> bool:
        """Vrai si la période peut entrer dans le calcul (complète et cohérente)."""
        return self.is_complete and not self.is_reversed


@dataclass(frozen=True)
class PeriodEntitlement:
    """Droits calculés pour une période, avant arrondi et avant plafonnement."""

    period: Period
    """Période à l'origine du calcul."""

    months: float
    """Nombre de mois couverts, mois complets plus fractions des mois partiels."""

    annual_leave: float
    """Congés annuels proratisés sur la période, en jours."""

    rtt: float
    """RTT proratisés sur la période, en jours."""


@dataclass(frozen=True)
class AnnualSummary:
    """Résultat consolidé de toutes les périodes d'une année."""

    settings: Settings
    """Paramètres utilisés pour le calcul."""

    entitlements: list[PeriodEntitlement]
    """Détail ligne par ligne, dans l'ordre de saisie."""

    total_months: float
    """Somme des mois couverts par les périodes exploitables."""

    annual_leave: int
    """Congés annuels de l'année, plafonnés puis arrondis à l'entier le plus proche."""

    rtt: int
    """RTT de l'année, plafonnés puis arrondis à l'entier le plus proche."""

    errors: list[str]
    """Messages d'erreur de saisie, vides si le formulaire est cohérent."""

    @property
    def coverage_gap(self) -> float:
        """Écart entre les mois couverts et les 12 mois attendus.

        Négatif si l'année est incomplète, positif si les périodes se recouvrent.
        """
        return self.total_months - MONTHS_PER_YEAR

    @property
    def is_fully_covered(self) -> bool:
        """Vrai si les périodes couvrent exactement les 12 mois de l'année."""
        return abs(self.coverage_gap) < COVERAGE_TOLERANCE

    @property
    def is_valid(self) -> bool:
        """Vrai si la saisie est exploitable : aucune erreur et année complète."""
        return not self.errors and self.is_fully_covered

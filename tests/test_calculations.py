"""Tests du calcul des mois couverts et du prorata de congés et RTT."""

import unittest
from datetime import date

from app.calculations import (
    build_summary,
    compute_entitlement,
    month_fraction,
    round_to_nearest,
)
from app.models import Period, Settings

YEAR: int = 2026
"""Année de référence non bissextile utilisée par défaut dans les tests."""

LEAP_YEAR: int = 2024
"""Année bissextile, pour vérifier le nombre de jours de février."""


def make_settings(
    year: int = YEAR,
    annual_leave_allowance: float = 25.0,
    rtt_allowance: float = 15.0,
) -> Settings:
    """Construit des paramètres annuels avec les valeurs par défaut de l'application."""
    return Settings(
        year=year,
        annual_leave_allowance=annual_leave_allowance,
        rtt_allowance=rtt_allowance,
    )


class MonthFractionTest(unittest.TestCase):
    """Comportement de `month_fraction`."""

    def test_full_year_is_twelve_months(self) -> None:
        """Du 01/01 au 31/12, la période vaut exactement 12 mois."""
        self.assertEqual(
            month_fraction(date(YEAR, 1, 1), date(YEAR, 12, 31), YEAR), 12.0
        )

    def test_single_full_month_is_one_month(self) -> None:
        """Un mois entièrement couvert vaut 1, quel que soit son nombre de jours."""
        self.assertEqual(
            month_fraction(date(YEAR, 2, 1), date(YEAR, 2, 28), YEAR), 1.0
        )

    def test_bounds_are_inclusive(self) -> None:
        """Une période d'un seul jour couvre un jour, pas zéro."""
        self.assertAlmostEqual(
            month_fraction(date(YEAR, 1, 1), date(YEAR, 1, 1), YEAR), 1 / 31
        )

    def test_partial_month_is_prorated_on_its_own_length(self) -> None:
        """Le mois partiel est rapporté au nombre de jours de ce mois."""
        # Du 15/01 au 31/01 : 17 jours sur les 31 de janvier.
        self.assertAlmostEqual(
            month_fraction(date(YEAR, 1, 15), date(YEAR, 1, 31), YEAR), 17 / 31
        )

    def test_full_months_and_partial_months_are_added(self) -> None:
        """Mois complets et fractions se cumulent, conformément à la formule."""
        # Du 15/01 au 31/12 : 11 mois complets, plus 17/31 de janvier.
        self.assertAlmostEqual(
            month_fraction(date(YEAR, 1, 15), date(YEAR, 12, 31), YEAR),
            11 + 17 / 31,
        )

    def test_contiguous_split_covers_exactly_twelve_months(self) -> None:
        """Un découpage contigu de l'année redonne 12 mois au total."""
        first = month_fraction(date(YEAR, 1, 1), date(YEAR, 6, 14), YEAR)
        second = month_fraction(date(YEAR, 6, 15), date(YEAR, 12, 31), YEAR)
        self.assertAlmostEqual(first + second, 12.0)

    def test_february_uses_leap_year_length(self) -> None:
        """En année bissextile, février compte 29 jours."""
        self.assertAlmostEqual(
            month_fraction(date(LEAP_YEAR, 2, 1), date(LEAP_YEAR, 2, 15), LEAP_YEAR),
            15 / 29,
        )

    def test_days_outside_reference_year_are_ignored(self) -> None:
        """Une période débordant de l'année est tronquée à l'année de référence."""
        self.assertEqual(
            month_fraction(date(YEAR - 1, 6, 1), date(YEAR + 1, 6, 30), YEAR), 12.0
        )


class RoundToNearestTest(unittest.TestCase):
    """Comportement de `round_to_nearest`."""

    def test_rounds_down_below_half(self) -> None:
        """En dessous d'un demi, la valeur est arrondie à l'entier inférieur."""
        self.assertEqual(round_to_nearest(17.49), 17)

    def test_rounds_up_above_half(self) -> None:
        """Au dessus d'un demi, la valeur est arrondie à l'entier supérieur."""
        self.assertEqual(round_to_nearest(17.51), 18)

    def test_rounds_half_up(self) -> None:
        """Un demi exact est arrondi au supérieur, contrairement à `round`."""
        self.assertEqual(round_to_nearest(17.5), 18)
        self.assertEqual(round_to_nearest(2.5), 3)

    def test_keeps_integers_unchanged(self) -> None:
        """Une valeur entière n'est pas modifiée."""
        self.assertEqual(round_to_nearest(7.0), 7)


class ComputeEntitlementTest(unittest.TestCase):
    """Comportement de `compute_entitlement`."""

    def test_full_year_at_full_rate_gives_full_allowance(self) -> None:
        """Une année pleine à 100 % donne l'intégralité des droits."""
        period = Period(date(YEAR, 1, 1), date(YEAR, 12, 31), 100)
        entitlement = compute_entitlement(period, make_settings())
        self.assertEqual(entitlement.months, 12.0)
        self.assertAlmostEqual(entitlement.annual_leave, 25.0)
        self.assertAlmostEqual(entitlement.rtt, 15.0)

    def test_rate_is_applied_to_the_prorated_amount(self) -> None:
        """La quotité multiplie le prorata de mois."""
        period = Period(date(YEAR, 1, 1), date(YEAR, 12, 31), 80)
        entitlement = compute_entitlement(period, make_settings())
        self.assertAlmostEqual(entitlement.annual_leave, 20.0)
        self.assertAlmostEqual(entitlement.rtt, 12.0)

    def test_half_year_gives_half_the_allowance(self) -> None:
        """Six mois à taux plein donnent la moitié des droits."""
        period = Period(date(YEAR, 1, 1), date(YEAR, 6, 30), 100)
        entitlement = compute_entitlement(period, make_settings())
        self.assertAlmostEqual(entitlement.months, 6.0)
        self.assertAlmostEqual(entitlement.annual_leave, 12.5)

    def test_incomplete_period_generates_nothing(self) -> None:
        """Une ligne incomplète ne génère aucun droit."""
        entitlement = compute_entitlement(
            Period(date(YEAR, 1, 1), None, 100), make_settings()
        )
        self.assertEqual(entitlement.months, 0.0)
        self.assertEqual(entitlement.annual_leave, 0.0)
        self.assertEqual(entitlement.rtt, 0.0)

    def test_reversed_period_generates_nothing(self) -> None:
        """Une période dont la fin précède le début ne génère aucun droit."""
        entitlement = compute_entitlement(
            Period(date(YEAR, 6, 30), date(YEAR, 1, 1), 100), make_settings()
        )
        self.assertEqual(entitlement.months, 0.0)


class BuildSummaryTest(unittest.TestCase):
    """Comportement de `build_summary`."""

    def test_contiguous_periods_cover_the_year(self) -> None:
        """Deux périodes contiguës à taux plein couvrent les 12 mois."""
        periods = [
            Period(date(YEAR, 1, 1), date(YEAR, 6, 30), 100),
            Period(date(YEAR, 7, 1), date(YEAR, 12, 31), 100),
        ]
        summary = build_summary(periods, make_settings())
        self.assertAlmostEqual(summary.total_months, 12.0)
        self.assertTrue(summary.is_fully_covered)
        self.assertTrue(summary.is_valid)
        self.assertEqual(summary.annual_leave, 25)
        self.assertEqual(summary.rtt, 15)

    def test_rounding_happens_once_on_the_total(self) -> None:
        """L'arrondi porte sur la somme, pas sur chaque ligne.

        Deux semestres à 70 % donnent 8,75 jours chacun : arrondir ligne à ligne
        donnerait 9 + 9 = 18, alors que le total attendu est 17,5 arrondi à 18.
        Le test vérifie surtout que le détail reste non arrondi.
        """
        periods = [
            Period(date(YEAR, 1, 1), date(YEAR, 6, 30), 70),
            Period(date(YEAR, 7, 1), date(YEAR, 12, 31), 70),
        ]
        summary = build_summary(periods, make_settings())
        self.assertAlmostEqual(summary.entitlements[0].annual_leave, 8.75)
        self.assertAlmostEqual(summary.entitlements[1].annual_leave, 8.75)
        self.assertEqual(summary.annual_leave, 18)

    def test_mixed_rates_are_prorated_per_period(self) -> None:
        """Chaque période applique sa propre quotité."""
        periods = [
            Period(date(YEAR, 1, 1), date(YEAR, 6, 30), 100),
            Period(date(YEAR, 7, 1), date(YEAR, 12, 31), 50),
        ]
        summary = build_summary(periods, make_settings())
        # Congés : 12,5 jours à 100 % puis 6,25 jours à 50 %, soit 18,75.
        self.assertEqual(summary.annual_leave, 19)
        # RTT : 7,5 jours puis 3,75 jours, soit 11,25.
        self.assertEqual(summary.rtt, 11)

    def test_annual_cap_limits_the_total(self) -> None:
        """Le total ne peut jamais dépasser le droit annuel à taux plein."""
        periods = [
            Period(date(YEAR, 1, 1), date(YEAR, 12, 31), 100),
            Period(date(YEAR, 1, 1), date(YEAR, 12, 31), 100),
        ]
        summary = build_summary(periods, make_settings())
        self.assertEqual(summary.annual_leave, 25)
        self.assertEqual(summary.rtt, 15)

    def test_empty_row_is_ignored(self) -> None:
        """Une ligne vierge n'empêche pas la couverture d'être complète."""
        periods = [
            Period(date(YEAR, 1, 1), date(YEAR, 12, 31), 100),
            Period(None, None, None),
        ]
        summary = build_summary(periods, make_settings())
        self.assertAlmostEqual(summary.total_months, 12.0)
        self.assertEqual(summary.errors, [])
        self.assertTrue(summary.is_valid)

    def test_coverage_gap_reports_missing_months(self) -> None:
        """Une année partiellement couverte remonte un écart négatif."""
        summary = build_summary(
            [Period(date(YEAR, 1, 1), date(YEAR, 6, 30), 100)], make_settings()
        )
        self.assertAlmostEqual(summary.coverage_gap, -6.0)
        self.assertFalse(summary.is_fully_covered)
        self.assertFalse(summary.is_valid)

    def test_overlapping_periods_are_invalid_despite_full_coverage(self) -> None:
        """Un chevauchement invalide la saisie même si le compteur atteint 12."""
        periods = [
            Period(date(YEAR, 1, 1), date(YEAR, 7, 31), 100),
            Period(date(YEAR, 7, 1), date(YEAR, 12, 31), 100),
        ]
        summary = build_summary(periods, make_settings())
        self.assertGreater(summary.coverage_gap, 0)
        self.assertFalse(summary.is_valid)

    def test_custom_allowances_are_used(self) -> None:
        """Les droits annuels paramétrés remplacent les valeurs par défaut."""
        summary = build_summary(
            [Period(date(YEAR, 1, 1), date(YEAR, 12, 31), 100)],
            make_settings(annual_leave_allowance=30.0, rtt_allowance=12.0),
        )
        self.assertEqual(summary.annual_leave, 30)
        self.assertEqual(summary.rtt, 12)


if __name__ == "__main__":
    unittest.main()

"""Tests des contrôles de cohérence appliqués aux périodes saisies."""

import unittest
from datetime import date

from app.models import Period
from app.validation import (
    INCOMPLETE_ROW_MESSAGE,
    REVERSED_DATES_MESSAGE,
    find_overlaps,
    validate_periods,
)

YEAR: int = 2026
"""Année de référence utilisée dans les tests."""


class PeriodStateTest(unittest.TestCase):
    """États d'une période selon les champs renseignés."""

    def test_blank_period_is_empty(self) -> None:
        """Une ligne sans aucune saisie est vierge."""
        period = Period(None, None, None)
        self.assertTrue(period.is_empty)
        self.assertFalse(period.is_complete)
        self.assertFalse(period.is_usable)

    def test_partially_filled_period_is_neither_empty_nor_complete(self) -> None:
        """Une ligne à moitié saisie n'est ni vierge ni exploitable."""
        period = Period(date(YEAR, 1, 1), None, 100)
        self.assertFalse(period.is_empty)
        self.assertFalse(period.is_complete)
        self.assertFalse(period.is_usable)

    def test_reversed_dates_are_detected(self) -> None:
        """Une fin antérieure au début est signalée comme incohérente."""
        period = Period(date(YEAR, 6, 30), date(YEAR, 1, 1), 100)
        self.assertTrue(period.is_complete)
        self.assertTrue(period.is_reversed)
        self.assertFalse(period.is_usable)

    def test_single_day_period_is_usable(self) -> None:
        """Une période d'un jour, début et fin identiques, est valide."""
        period = Period(date(YEAR, 3, 15), date(YEAR, 3, 15), 100)
        self.assertFalse(period.is_reversed)
        self.assertTrue(period.is_usable)


class FindOverlapsTest(unittest.TestCase):
    """Comportement de `find_overlaps`."""

    def test_contiguous_periods_do_not_overlap(self) -> None:
        """Deux périodes qui se suivent au jour près ne se chevauchent pas."""
        periods = [
            Period(date(YEAR, 1, 1), date(YEAR, 3, 31), 100),
            Period(date(YEAR, 4, 1), date(YEAR, 12, 31), 100),
        ]
        self.assertEqual(find_overlaps(periods), [])

    def test_shared_day_is_an_overlap(self) -> None:
        """Une seule journée commune suffit à constituer un chevauchement."""
        periods = [
            Period(date(YEAR, 1, 1), date(YEAR, 4, 1), 100),
            Period(date(YEAR, 4, 1), date(YEAR, 12, 31), 100),
        ]
        self.assertEqual(len(find_overlaps(periods)), 1)

    def test_overlap_is_detected_whatever_the_input_order(self) -> None:
        """Les périodes sont triées avant comparaison."""
        periods = [
            Period(date(YEAR, 4, 1), date(YEAR, 12, 31), 100),
            Period(date(YEAR, 1, 1), date(YEAR, 6, 30), 100),
        ]
        self.assertEqual(len(find_overlaps(periods)), 1)

    def test_incomplete_periods_are_ignored(self) -> None:
        """Une ligne incomplète ne participe pas à la recherche de chevauchement."""
        periods = [
            Period(date(YEAR, 1, 1), date(YEAR, 12, 31), 100),
            Period(date(YEAR, 6, 1), None, None),
        ]
        self.assertEqual(find_overlaps(periods), [])

    def test_message_names_both_periods(self) -> None:
        """Le message d'erreur cite les deux périodes en cause."""
        periods = [
            Period(date(YEAR, 1, 1), date(YEAR, 12, 31), 100),
            Period(date(YEAR, 1, 1), date(YEAR, 12, 31), 100),
        ]
        message = find_overlaps(periods)[0]
        self.assertIn("01/01/2026", message)
        self.assertIn("31/12/2026", message)

    def test_three_overlapping_periods_report_two_pairs(self) -> None:
        """Chaque couple consécutif en recouvrement est signalé."""
        periods = [
            Period(date(YEAR, 1, 1), date(YEAR, 6, 30), 100),
            Period(date(YEAR, 5, 1), date(YEAR, 9, 30), 100),
            Period(date(YEAR, 8, 1), date(YEAR, 12, 31), 100),
        ]
        self.assertEqual(len(find_overlaps(periods)), 2)


class ValidatePeriodsTest(unittest.TestCase):
    """Comportement de `validate_periods`."""

    def test_valid_periods_produce_no_error(self) -> None:
        """Une saisie contiguë et complète ne remonte aucune erreur."""
        periods = [
            Period(date(YEAR, 1, 1), date(YEAR, 6, 30), 100),
            Period(date(YEAR, 7, 1), date(YEAR, 12, 31), 80),
        ]
        self.assertEqual(validate_periods(periods), [])

    def test_blank_row_is_not_an_error(self) -> None:
        """Une ligne fraîchement ajoutée ne déclenche pas de message."""
        periods = [
            Period(date(YEAR, 1, 1), date(YEAR, 12, 31), 100),
            Period(None, None, None),
        ]
        self.assertEqual(validate_periods(periods), [])

    def test_partially_filled_row_is_reported(self) -> None:
        """Une ligne à moitié saisie remonte le message d'incomplétude."""
        periods = [Period(date(YEAR, 1, 1), date(YEAR, 12, 31), None)]
        self.assertIn(INCOMPLETE_ROW_MESSAGE, validate_periods(periods))

    def test_missing_rate_alone_is_reported(self) -> None:
        """La quotité manquante suffit à rendre la ligne incomplète."""
        periods = [Period(None, None, 80)]
        self.assertIn(INCOMPLETE_ROW_MESSAGE, validate_periods(periods))

    def test_reversed_dates_are_reported(self) -> None:
        """Des dates inversées remontent leur propre message."""
        periods = [Period(date(YEAR, 12, 31), date(YEAR, 1, 1), 100)]
        self.assertIn(REVERSED_DATES_MESSAGE, validate_periods(periods))

    def test_incomplete_row_is_reported_only_once(self) -> None:
        """Plusieurs lignes incomplètes ne produisent qu'un seul message."""
        periods = [
            Period(date(YEAR, 1, 1), None, None),
            Period(None, date(YEAR, 12, 31), None),
        ]
        self.assertEqual(validate_periods(periods).count(INCOMPLETE_ROW_MESSAGE), 1)

    def test_all_error_types_are_cumulated(self) -> None:
        """Les différents types d'erreur sont remontés ensemble."""
        periods = [
            Period(date(YEAR, 1, 1), date(YEAR, 12, 31), 100),
            Period(date(YEAR, 6, 1), date(YEAR, 12, 31), 100),
            Period(date(YEAR, 3, 1), None, None),
            Period(date(YEAR, 5, 1), date(YEAR, 2, 1), 100),
        ]
        errors = validate_periods(periods)
        self.assertIn(REVERSED_DATES_MESSAGE, errors)
        self.assertIn(INCOMPLETE_ROW_MESSAGE, errors)
        self.assertEqual(len(errors), 3)


if __name__ == "__main__":
    unittest.main()

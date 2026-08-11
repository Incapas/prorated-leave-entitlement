# Congés et RTT proratisés

> Sachez combien de jours de congés et de RTT vous restent dus quand votre quotité de travail change en cours d'année.

Application web qui reconstitue une année de référence en périodes d'activité, chacune affectée de sa quotité, et en déduit les jours de congés annuels et de RTT acquis au prorata du temps réellement travaillé. Le calcul se met à jour à chaque saisie et signale immédiatement les trous, les recouvrements et les lignes incohérentes.

![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.61-FF4B4B?logo=streamlit&logoColor=white)
![Tests](https://img.shields.io/badge/tests-42%20passing-16a34a)
![Couverture métier](https://img.shields.io/badge/couverture%20m%C3%A9tier-98%25-16a34a)

---

## Le problème

Un temps partiel, un passage à 80 % au 1er avril, un retour à temps plein en septembre : dès que la quotité change en cours d'année, les congés annuels et les RTT ne s'acquièrent plus au même rythme sur toute l'année. Le calcul se fait alors à la main, période par période, avec les pièges habituels — un mois partiel compté au jour près, un arrondi appliqué trop tôt sur chaque ligne, une période oubliée entre deux contrats.

Cette application fait le calcul à la place de l'utilisateur et vérifie que les périodes saisies couvrent bien l'année, sans trou ni recouvrement.

## Fonctionnalités

- **Année découpée en périodes** — une ligne par période, avec date de début, date de fin (toutes deux incluses) et quotité de 50 à 100 %. Les dates sont bornées à l'année de référence.
- **Mois partiels comptés au jour près** — un mois entièrement couvert vaut 1, un mois partiel vaut ses jours couverts divisés par le nombre de jours du mois. Un découpage contigu de l'année redonne toujours 12,00 mois, quels que soient les points de coupure, années bissextiles comprises.
- **Arrondi appliqué une seule fois, sur le total** — les droits de chaque période sont sommés sans arrondi, plafonnés au droit annuel à taux plein, puis arrondis à l'entier le plus proche (12,5 donne 13). Le tableau de détail affiche les valeurs non arrondies.
- **Compteur de couverture annuelle** — l'écart aux 12 mois attendus est affiché en permanence : mois manquants, ou dépassement lorsque des périodes se recouvrent.
- **Anomalies signalées sans bloquer le calcul** — dates inversées, ligne incomplète, chevauchement daté (« Chevauchement entre les périodes 01/01/2026–30/06/2026 et 01/06/2026–31/12/2026 »). Une ligne vierge n'est pas une erreur : elle est simplement ignorée.
- **Paramètres annuels ajustables** — année de référence, droit à congés annuels et droit à RTT pour une année pleine à 100 % (25 et 15 jours par défaut).

## Technologies

| Outil | Rôle |
|---|---|
| Python 3.12.4 | Langage |
| Streamlit 1.61 | Interface web, navigation multipage et recalcul automatique |
| unittest | Tests (bibliothèque standard) |
| dataclasses | Modèles immuables partagés par le calcul, la validation et l'interface |

## Installation

Prérequis : Python 3.12.

```bash
git clone https://github.com/Incapas/prorated-leave-entitlement.git
cd prorated-leave-entitlement

python3.12 -m venv env
source env/bin/activate          # Windows : env\Scripts\activate
pip install -r requirements.txt
```

## Utilisation

```bash
streamlit run main.py
```

L'application s'ouvre dans le navigateur sur `http://localhost:8501`. La page **À propos**, servie en accueil, présente la méthode de calcul et un exemple chiffré ; la page **Périodes d'activité** ouvre le formulaire. Les paramètres annuels se règlent dans la barre latérale.

La commande doit être lancée depuis la racine du dépôt : les pages sont déclarées par leur chemin (`app/about.py`, `app/calculator.py`) et les imports partent du paquet `app`. Changer l'année de référence remet les dates déjà saisies à zéro, celles-ci sortant des bornes autorisées par les widgets.

## Tests

```bash
python -m unittest discover -v                  # les 42 tests
python -m unittest tests.test_calculations      # un module
python -m unittest tests.test_validation.FindOverlapsTest.test_shared_day_is_an_overlap

coverage run --branch --source=app -m unittest discover && coverage report -m
coverage html                                   # rapport détaillé dans htmlcov/
```

La couverture atteint **98 %**, lignes et branches, sur le cœur métier — `calculations.py` et `validation.py` à 100 %, `models.py` à 97 % —, et 49 % sur l'ensemble du code applicatif : l'interface Streamlit (`ui.py`, `about.py`, `calculator.py`) n'a pas de tests. Les 42 tests portent sur le décompte des mois, l'arrondi, le prorata, le plafonnement et les contrôles de cohérence.

## Structure du projet

```
main.py                Point d'entrée : configuration de la page et navigation
app/
  models.py            Dataclasses partagées (Settings, Period, PeriodEntitlement, AnnualSummary)
  calculations.py      Logique métier pure : mois couverts, prorata, arrondi, consolidation
  validation.py        Contrôles de cohérence : lignes incomplètes, dates inversées, chevauchements
  ui.py                Composants Streamlit : barre latérale, lignes de saisie, indicateurs, détail
  calculator.py        Page « Périodes d'activité » : enchaîne saisie, calcul et restitution
  about.py             Page « À propos » : présentation, méthode de calcul, exemple
tests/
  test_calculations.py Mois couverts, arrondi, droits par période, récapitulatif annuel
  test_validation.py   États d'une période, recherche de chevauchements, agrégation des erreurs
```

Le calcul est strictement séparé de l'affichage : `calculations.py` et `validation.py` ne connaissent ni Streamlit ni `st.session_state`, et ne dépendent que de `models.py`. Toute règle métier ajoutée doit rester dans ces modules, testable sans lancer l'application ; `ui.py` se contente de lire les widgets et d'afficher le résultat.

## Contributeurs

### Développeur

Conception, décisions et validation du produit :

- définition du besoin et des règles métier : importation de la formule principale développée sur Microsoft Excel ; périodes d'activité affectées d'une quotité, décompte des mois partiels au prorata des jours, plafonnement au droit annuel, arrondi unique sur le total ; 
- choix d'ergonomie : page d'accueil explicative servie par défaut, paramètres annuels en barre latérale, ajout et suppression de lignes, recalcul permanent sans bouton de validation, tableau de détail non arrondi ;
- choix techniques structurants : séparation du calcul et de l'affichage, paquets `app/` et `tests/`, modèles immuables, code et documentation en français ;
- recette de l'application et validation de chaque modification avant intégration.

### Agent de code — Claude Opus 5 via Claude Code (Application Desktop)

Réalisation sous la direction du développeur :

- implémentation des modèles, du calcul, de la validation et de l'interface Streamlit ;
- organisation du projet en paquets `app/` et `tests/`, avec la logique métier isolée de Streamlit ;
- rédaction des 42 tests couvrant le cœur métier ;
- documentation : docstrings de chaque module, fonction et attribut, page « À propos », et ce README.

Chaque modification a été relue et validée par le développeur avant intégration.

## Licence

GNU GENERAL PUBLIC LICENSE, Version 3, 29 June 2007
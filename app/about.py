"""Page d'accueil : présentation de l'application et de sa méthode de calcul."""

import streamlit as st

from app.models import MONTHS_PER_YEAR


def render_about() -> None:
    """Affiche la page « À propos ».

    Décrit l'objet de l'application, le déroulé de la saisie, la méthode de
    calcul appliquée et les contrôles de cohérence, puis illustre le tout par un
    exemple chiffré.
    """
    st.title("À propos")
    st.caption(
        "Calcul des congés annuels et des RTT proratisés sur une année de référence."
    )
    st.divider()

    st.markdown(
        """
        ## Ce que fait l'application

        Un travailleur dont la quotité de travail change en cours d'année n'acquiert pas
        ses congés au même rythme sur toute l'année. L'application reconstitue
        l'année en **périodes d'activité**, affecte à chacune sa quotité, puis
        calcule les droits acquis au prorata du temps effectivement travaillé.

        Elle produit deux résultats : un nombre de **jours de congés annuels** et un
        nombre de **jours de RTT**, arrondis à l'entier.
        """
    )

    st.divider()

    st.markdown("## Comment l'utiliser")

    st.markdown(
        """
        **1. Régler les paramètres annuels** — dans la barre latérale de la page
        *Périodes d'activité* : l'année de référence, le droit à congés annuels et
        le droit à RTT pour une année pleine à temps plein (100 %).

        **2. Saisir les périodes** — une ligne par période, avec une date de début,
        une date de fin (toutes deux incluses) et une quotité de 50 à 100 %. Le
        bouton **➕ Ajouter une ligne** crée une nouvelle période, l'icône 🗑️ la
        supprime. Les dates sont bornées à l'année de référence : changer d'année
        remet les dates à zéro.

        **3. Lire les résultats** — le calcul se met à jour à chaque saisie, sans
        validation à déclencher. Trois indicateurs sont affichés : congés
        proratisés, RTT proratisés et couverture annuelle. Le tableau du bas
        détaille chaque ligne, sans arrondi.
        """
    )

    st.divider()

    st.markdown(
        f"""
        ## La méthode de calcul

        **Mois couverts par une période.** Le décompte est mené mois par mois : un
        mois entièrement couvert vaut 1, un mois partiel vaut le nombre de jours
        couverts divisé par le nombre de jours de ce mois. Une période du 01/01 au
        31/12 vaut donc exactement {MONTHS_PER_YEAR}, et un découpage contigu de
        l'année redonne toujours {MONTHS_PER_YEAR} au total, quels que soient les
        points de coupure.

        **Droits acquis sur une période.**
        """
    )

    st.latex(
        r"\text{droit} = \text{droit annuel} \times "
        r"\frac{\text{mois couverts}}{12} \times \frac{\text{quotité}}{100}"
    )

    st.markdown(
        """
        **Total annuel.** Les droits de toutes les périodes sont additionnés, puis
        plafonnés au droit annuel à taux plein — les périodes qui se chevauchent ne
        peuvent pas produire plus qu'une année complète. L'arrondi à l'entier le
        plus proche n'intervient qu'une seule fois, sur ce total : les valeurs
        intermédiaires du tableau de détail restent non arrondies, ce qui évite
        d'accumuler les écarts d'arrondi ligne après ligne. Un demi-jour est
        arrondi au supérieur (12,5 donne 13).
        """
    )

    st.divider()

    st.markdown(
        """
        ## Les contrôles de cohérence

        La saisie est vérifiée en continu et les anomalies sont signalées sous les
        indicateurs :

        - **Ligne incomplète** — les trois champs sont requis pour qu'une période
          entre dans le calcul. Une ligne entièrement vierge n'est pas une erreur,
          elle est simplement ignorée.
        - **Dates inversées** — la date de fin précède la date de début.
        - **Chevauchement** — deux périodes se recouvrent. Deux périodes adjacentes
          (le 31/03 puis le 01/04) ne se chevauchent pas.
        - **Couverture annuelle** — l'écart au total de 12 mois est affiché en
          permanence : il manque des mois, ou l'année est dépassée. Les périodes
          incomplètes ou incohérentes ne comptent pas dans la couverture.
        """
    )

    st.divider()

    st.markdown(
        """
        ## Un exemple

        Année 2026, 25 jours de congés annuels et 15 jours de RTT à taux plein,
        avec un passage à mi-temps au 1er juillet :

        | Période | Quotité | Mois | Congés | RTT |
        | --- | --- | --- | --- | --- |
        | 01/01/2026 → 30/06/2026 | 100 % | 6,0000 | 12,50 | 7,50 |
        | 01/07/2026 → 31/12/2026 | 50 % | 6,0000 | 6,25 | 3,75 |
        | **Total** | | **12,0000** | **18,75 → 19 j** | **11,25 → 11 j** |

        L'année est intégralement couverte : les deux périodes totalisent 12 mois,
        sans trou ni recouvrement.
        """
    )

    st.page_link(
        "app/calculator.py",
        label="Passer au calcul",
        icon=":material/arrow_forward:",
    )


render_about()

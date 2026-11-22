# Équilibrage des classes et comparaison des stratégies

## 1. Objectif du notebook

Ce notebook a pour objectif d'étudier l'effet de différentes stratégies d'équilibrage des classes sur les performances des modèles de classification météorologique.

Les modèles étudiés sont :

- **KNN**
- **SVM**
- **Random Forest**

Les trois classes à prédire sont `Low`, `Medium` et `High`.

L'objectif n'est pas de refaire l'optimisation des hyperparamètres, mais de comparer plusieurs façons de traiter le déséquilibre des classes, en conservant les hyperparamètres définis précédemment.

Les stratégies comparées sont :

| Stratégie | Principe |
|---|---|
| `aucun` | Entraînement sans méthode d'équilibrage. |
| `class_weight` | Augmentation du poids des erreurs commises sur les classes moins représentées. |
| `undersampling` | Réduction du nombre d'observations des classes majoritaires. |
| `smote` | Génération d'observations synthétiques pour augmenter les classes minoritaires. |

La stratégie `class_weight` n'est pas applicable au KNN, car cet estimateur ne propose pas ce paramètre. Cette combinaison est donc ignorée.

---

## 2. Données utilisées

Le notebook utilise :

- `train_supervised.parquet` pour l'entraînement et la validation croisée ;
- `test_supervised.parquet` pour l'évaluation finale.

Contrairement à une expérimentation réalisée sur un échantillon de 30 000 lignes, la validation croisée de ce notebook est effectuée sur l'ensemble de `train_supervised`.

Le jeu de test reste séparé : il n'est pas utilisé pendant la validation croisée ni pour choisir la stratégie.

---

## 3. Construction des plis temporels

La validation croisée utilise `TimeSeriesSplit` avec trois plis et `gap=1`.

Le découpage est effectué dans l'ordre chronologique afin de respecter la nature temporelle des données. Pour chaque pli :

1. une période passée est utilisée pour l'entraînement ;
2. une période d'écart (`gap`) est laissée entre l'entraînement et la validation ;
3. une période ultérieure est utilisée pour la validation.

Les indices des lignes correspondant aux périodes de chaque pli sont ensuite récupérés pour construire les ensembles Train et Validation.

**Attention :** `gap=1` exclut une unité de la séquence fournie à `TimeSeriesSplit`. Si cette séquence contient des mois, cela correspond à un mois ; si elle contient des dates journalières, cela correspond à une journée.

Cette organisation évite d'entraîner le modèle sur des observations futures pour prédire des observations passées.

---

## 4. Analyse de la distribution des classes et des méthodes d'équilibrage

Avant la comparaison des modèles, la distribution des classes est examinée sur la partie entraînement du dernier pli temporel.

Cette étape permet d'illustrer l'effet des méthodes de rééchantillonnage :

- **RandomUnderSampler :** réduit les classes majoritaires jusqu'à atteindre l'effectif de la classe minoritaire. Cela équilibre les classes, mais entraîne une perte d'observations.
- **SMOTE :** génère des observations synthétiques pour augmenter les classes minoritaires jusqu'à atteindre l'effectif de la classe majoritaire. Les observations générées ne sont pas nécessairement des situations météorologiques réellement observées ; leur plausibilité doit donc être considérée avec prudence.

Dans l'expérimentation, les effectifs observés étaient les suivants :

| Méthode | Low | Medium | High | Total |
|---|---:|---:|---:|---:|
| Avant équilibrage | 3 515 | 9 705 | 9 153 | 22 373 |
| RandomUnderSampler | 3 515 | 3 515 | 3 515 | 10 545 |
| SMOTE | 9 705 | 9 705 | 9 705 | 29 115 |

Ces effectifs concernent uniquement la partie entraînement du dernier pli, et non la totalité du jeu d'entraînement.

### Application sans fuite de données

Les méthodes de rééchantillonnage sont intégrées dans un `ImbPipeline`.

Pendant chaque pli :

1. le rééchantillonnage est appliqué uniquement aux données d'entraînement ;
2. le modèle est entraîné sur les données rééquilibrées ;
3. les données de validation restent inchangées et conservent leur distribution réelle.

Cette précaution est essentielle : il ne faut jamais appliquer SMOTE ou undersampling avant de séparer les données d'entraînement et de validation. Cela risquerait de provoquer une fuite de données et de fausser l'évaluation.

---

## 5. Construction des modèles et stratégies

Une fonction `construire(nom_modele, strategie)` permet de construire le modèle correspondant à la combinaison demandée.

Les stratégies sont appliquées de la manière suivante :

- `aucun` : modèle sans rééchantillonnage ;
- `class_weight` : SVM avec `class_weight="balanced"` et Random Forest avec `class_weight="balanced_subsample"` ;
- `undersampling` : pipeline contenant `RandomUnderSampler`, suivi du modèle ;
- `smote` : pipeline contenant `SMOTE`, suivi du modèle.

Pour comparer les méthodes de manière cohérente, lorsque `undersampling` ou `smote` est utilisé, le paramètre `class_weight` est désactivé pour le SVM et le Random Forest. On évite ainsi de cumuler deux mécanismes de compensation du déséquilibre.

Les hyperparamètres des modèles sont conservés fixes pendant cette comparaison. Le but est d'isoler autant que possible l'effet de la stratégie d'équilibrage.

---

## 6. Métriques d'évaluation

La fonction `metriques(y_vrai, y_pred)` utilise `precision_recall_fscore_support` pour calculer les métriques par classe.

Cette fonction retourne quatre éléments :

- **Precision :** parmi les observations prédites comme appartenant à une classe, proportion de celles qui appartiennent réellement à cette classe.
- **Recall (rappel) :** parmi les observations appartenant réellement à une classe, proportion de celles qui ont été correctement détectées.
- **F1-score :** moyenne harmonique de la précision et du rappel.
- **Support :** nombre réel d'observations de chaque classe dans les étiquettes de référence.

Les métriques enregistrées dans le notebook sont :

| Métrique | Description |
|---|---|
| `macro_F1` | Moyenne des F1-scores des trois classes, avec le même poids pour chaque classe. |
| `accuracy` | Proportion totale de prédictions correctes. |
| `F1_Low`, `F1_Medium`, `F1_High` | F1-score calculé séparément pour chaque classe. |
| `precision_Low`, `precision_Medium`, `precision_High` | Précision calculée pour chaque classe. |
| `rappel_Low`, `rappel_Medium`, `rappel_High` | Rappel calculé pour chaque classe. |
| `temps_fit_s` | Temps d'entraînement du modèle. |
| `temps_pred_s` | Temps nécessaire pour effectuer les prédictions, lorsqu'il est mesuré. |

Le **Macro-F1** est particulièrement utile lorsque les classes sont déséquilibrées, car il donne la même importance à chaque classe, quelle que soit sa fréquence.

La précision et le rappel de la classe `Low` permettent également d'examiner plus précisément la capacité du modèle à détecter cette classe.

---

## 7. Comparaison par validation croisée

Pour chaque modèle et chaque stratégie applicable :

1. un nouvel estimateur est créé pour chaque pli ;
2. il est entraîné sur les données d'entraînement du pli ;
3. il prédit les classes des données de validation ;
4. les métriques sont calculées et enregistrées.

Les résultats sont ensuite regroupés pour calculer la moyenne et l'écart-type des performances sur les trois plis.

L'écart-type du Macro-F1 renseigne sur la variabilité des résultats entre les plis. Un écart-type plus faible indique des résultats plus réguliers sur ces plis, mais il ne constitue pas à lui seul une mesure de qualité du modèle.

Les résultats obtenus sur le jeu d'entraînement complet étaient les suivants :

| Modèle | Stratégie | Macro-F1 moyen | Accuracy |
|---|---|---:|---:|
| KNN | Aucun | 0.8412 | 0.8578 |
| KNN | Undersampling | 0.8346 | 0.8446 |
| KNN | SMOTE | 0.8419 | 0.8531 |
| SVM | Aucun | 0.8645 | 0.8798 |
| SVM | Class weight | 0.8625 | 0.8749 |
| SVM | Undersampling | 0.8603 | 0.8705 |
| SVM | SMOTE | 0.8624 | 0.8752 |
| Random Forest | Aucun | 0.8641 | 0.8790 |
| Random Forest | Class weight | 0.8648 | 0.8804 |
| Random Forest | Undersampling | 0.8602 | 0.8718 |
| Random Forest | SMOTE | 0.8632 | 0.8767 |

### Interprétation des résultats

- **KNN :** SMOTE obtient le meilleur Macro-F1 (0.8419), mais le gain par rapport à l'absence d'équilibrage (0.8412) est très faible. L'absence d'équilibrage reste donc une option simple et pertinente.
- **SVM :** l'absence d'équilibrage obtient le meilleur Macro-F1 (0.8645) et la meilleure Accuracy (0.8798). Les autres stratégies n'apportent pas d'amélioration globale.
- **Random Forest :** `class_weight` obtient le meilleur Macro-F1 (0.8648) et la meilleure Accuracy (0.8804). Toutefois, le gain par rapport à l'absence d'équilibrage est très faible.

Les méthodes de rééchantillonnage peuvent améliorer certaines métriques de la classe `Low`, notamment son rappel, mais cette amélioration ne se traduit pas nécessairement par une hausse du Macro-F1 global.

Les écarts observés restent descriptifs : avec seulement trois plis, il ne s'agit pas d'un test statistique permettant d'affirmer que les différences sont significatives.

### Choix provisoire des stratégies

Sur la base du Macro-F1 en validation croisée, les stratégies retenues sont :

- **KNN :** aucun équilibrage ;
- **SVM :** aucun équilibrage ;
- **Random Forest :** `class_weight`.

Ces choix sont provisoires et doivent être confirmés par l'évaluation finale sur le jeu de test, sans utiliser ce dernier pour modifier la sélection.

---

## 8. Évaluation finale sur le jeu de test

Après la comparaison par validation croisée, un modèle est entraîné sur la totalité de `train_supervised`, puis évalué sur `test_supervised`.

Le modèle final est construit avec la stratégie retenue et les hyperparamètres définis précédemment.

Le rééchantillonnage, lorsqu'il est utilisé, est effectué pendant l'entraînement sur les données de `train_supervised`, grâce au pipeline. Le jeu de test n'est jamais rééchantillonné.

L'évaluation finale permet de mesurer les performances sur des observations qui n'ont pas participé à l'entraînement.

**Point de vigilance :** si le code d'évaluation sur le test parcourt toutes les stratégies, il produit des scores de test pour toutes les combinaisons. Pour respecter strictement le protocole de sélection, il est préférable de présenter comme résultats finaux ceux des stratégies choisies à partir de la validation croisée. Les scores de test ne doivent pas servir à choisir a posteriori la meilleure stratégie.

---

## 9. Sauvegarde des résultats et des modèles

Pendant la validation croisée, les modèles sont construits et entraînés séparément pour chaque pli. Les métriques sont conservées, mais les modèles de chaque pli ne constituent pas le modèle final.

Le modèle final doit être entraîné à nouveau sur l'ensemble de `train_supervised`. Il peut ensuite être sauvegardé avec `joblib` pour être réutilisé sans devoir refaire l'entraînement.

Il faut distinguer :

- les résultats de validation croisée, utilisés pour comparer les stratégies ;
- le modèle final, entraîné sur toutes les données d'entraînement ;
- les résultats du test, utilisés pour rapporter la performance finale.

---

## Schéma global du processus

```text
NOTEBOOK 05 — APPRENTISSAGE SUPERVISÉ
-------------------------------------
Échantillon de 30 000 lignes
          |
          v
Validation croisée temporelle
(GridSearchCV : recherche des hyperparamètres)
          |
          v
Sélection des meilleurs hyperparamètres
          |
          v
Réentraînement automatique du meilleur modèle
sur les 30 000 lignes (refit)
          |
          v
Enregistrement des hyperparamètres et du modèle
          |
          v
Entraînement sur 100 % de train_supervised
          |
          v
Modèle entraîné sur le train complet


NOTEBOOK D'ÉQUILIBRAGE
----------------------
100 % de train_supervised
          |
          v
Validation croisée temporelle
(Comparaison des stratégies d'équilibrage)
          |
          v
Sélection de la stratégie
          |
          v
Entraînement sur 100 % de train_supervised
          |
          v
Modèle entraîné sur le train complet


ÉVALUATION FINALE COMMUNE
-------------------------
Modèle final
     |
     v
Prédictions sur test_supervised
     |
     v
Calcul des métriques finales
```

**En résumé :** le notebook 05 utilise la validation croisée pour trouver les meilleurs hyperparamètres, tandis que le notebook d'équilibrage l'utilise pour choisir la meilleure stratégie de traitement du déséquilibre. Dans les deux cas, après cette sélection, un nouveau modèle est entraîné sur la totalité de `train_supervised` avant l'évaluation finale sur `test_supervised`.

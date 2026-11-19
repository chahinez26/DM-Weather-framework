# Résumé du notebook `05_Supervised_Learning.ipynb`

Projet Data Mining (M2 SII, USTHB, 2026/2027) : prévision de la classe de température à 2 m du mois suivant sur l'Algérie (ERA5-Land, moyennes mensuelles).

## 1. Objectif

Prédire la classe **Low / Medium / High** de la température à 2 m du mois suivant. Les trois classes sont obtenues en découpant la plage de la variable continue en trois intervalles de largeur égale (bornes calculées sur le train). Trois modèles sont comparés : **KNN**, **SVM (noyau RBF)** et **Random Forest**.

## 2. Données (produites par `04_Feature_Engineering.ipynb`)

| Fichier | Contenu |
|---|---|
| `train_supervised.parquet` | train complet (≈ 602 000 lignes, 2015-2024) |
| `test_supervised.parquet` | test, chronologiquement après le train (2024-2026) |
| `train_sample_30k.parquet` | échantillon de 30 000 lignes du train, utilisé pour le réglage |
| `class_edges.json` | bornes des classes |
| `feature_sets.json` | 4 jeux de variables : `complet`, `reduit`, `reduit_sans_sp`, `strict_cours` |

## 3. Vérifications avant modélisation

1. La cible (`classe`, `t2m_next`) et `month`, `date` ne figurent dans aucun jeu de variables, pour éviter toute fuite.
2. Absence de chevauchement train/test : la cible du dernier mois du train ne tombe pas dans le test.
3. Répartition des classes comparée entre train, échantillon et test.

## 4. Baselines

- **Classe majoritaire** du train.
- **Classe majoritaire par mois** (calculée sur le train) : baseline saisonnière, plus exigeante.

Métriques : accuracy, **macro-F1** (moyenne non pondérée des F1 de Low, Medium, High, plus honnête que l'accuracy quand une classe est rare) et F1 par classe.

## 5. Validation chronologique

`TimeSeriesSplit` à **3 plis** appliqué aux mois, avec **un mois d'écart** (`gap=1`) entre apprentissage et validation : on apprend sur le passé et on valide sur le futur. Le test n'intervient pas à cette étape.

## 6. Choix du jeu de variables

Comparaison des 4 jeux, avec et sans `year`, par un Random Forest rapide (100 arbres, `min_samples_leaf=5`, `class_weight="balanced_subsample"`) sur l'échantillon. Macro-F1 moyen en validation :

| Jeu | Avec `year` | Sans `year` | Gain |
|---|---|---|---|
| complet | 0,8553 | 0,8689 | +0,0136 |
| reduit | 0,8563 | 0,8731 | +0,0168 |
| strict_cours | 0,8604 | 0,8725 | +0,0121 |
| reduit_sans_sp | 0,8385 | 0,8559 | +0,0174 |

Conclusions du notebook :

- `complet`, `reduit` et `strict_cours` sont équivalents (écart inférieur à l'écart-type entre plis, ≈ 0,006). Retirer `e`, `ro` et `sshf` ne fait pas perdre d'information : ces variables sont redondantes.
- Retirer `year` améliore le score dans les 4 jeux. Le test porte sur des années absentes du train : un arbre ne sait pas extrapoler, KNN et SVM voient leurs distances décalées, et le modèle risque de mémoriser des particularités d'années précises.
- Retirer `sp` dégrade le score : cette variable est utile malgré sa faible variabilité.

## 7. Configurations entraînées

Deux jeux de variables (`complet`, `reduit`) × avec / sans `year` = **4 configurations** :
`complet`, `complet_sans_year`, `reduit`, `reduit_sans_year`.

## 8. Entraînement (section 5 réécrite)

Une fonction unique `entrainer(modele, donnees)` boucle sur les 4 configurations.

| Modèle | Hyperparamètres réglés (grille) | Remarques |
|---|---|---|
| KNN | `n_neighbors` ∈ {15, 31, 51, 101, 201}, `weights` ∈ {uniform, distance} | `algorithm="brute"` sur le train complet |
| SVM (RBF) | `C` ∈ {1, 10}, `gamma` ∈ {scale, 0,3} | `class_weight="balanced"` ; `MAX_LIGNES_SVM = 100 000` sur le train complet (`None` = tout) |
| Random Forest | `max_depth` ∈ {10, 20, None}, `min_samples_leaf` ∈ {1, 10} | 200 arbres, `class_weight="balanced_subsample"` ; sur le train complet : 150 arbres, profondeur 25 si `None`, `min_samples_leaf` ≥ 5 |

Deux modes par modèle :

- `"echantillon"` : `GridSearchCV` sur l'échantillon de 30 000 lignes, 3 plis chronologiques, critère macro-F1 (refit sur le meilleur).
- `"train_complet"` : entraînement sur tout le train avec les hyperparamètres trouvés sur l'échantillon (pas de nouvelle grille, trop coûteuse).

Une configuration déjà enregistrée est ignorée (`refaire=True` pour la recalculer).

## 9. Enregistrement des modèles

Pour chaque entraînement, dans `results/models/<configuration>/` :

- `<modele>_<donnees>.pkl` : le modèle ;
- `<modele>_<donnees>.json` : la fiche (jeu, avec ou sans `year`, variables, nombre de lignes, période d'entraînement, hyperparamètres choisis et complets, score de validation, durée, graine, version de sklearn, date).

Les tableaux de réglage (toutes les combinaisons testées) sont écrits dans `results/tables/<modele>/reglage_<modele>_<configuration>.csv`.

## 10. Évaluation sur le test (section 6, inchangée)

Aucun ré-entraînement : tous les modèles enregistrés sont rechargés et prédisent le test avec les variables de leur fiche. Sorties :

- tableau comparatif (baselines + modèles) enregistré dans `results/tables/test/resultats_test.csv` ;
- meilleur modèle selon le macro-F1, avec son `classification_report` ;
- matrices de confusion normalisées (`results/figures/matrices_confusion_supervise.png`) ;
- accuracy par mois sur le test, avec la baseline saisonnière (`results/figures/accuracy_par_mois_supervise.png`).

## 11. Points d'attention

- **SVM sur train complet** : coût d'apprentissage très élevé ; d'où la limite `MAX_LIGNES_SVM`.
- **Échelle des variables** : KNN et SVM reposent sur des distances ; vérifier que `04_Feature_Engineering` standardise les variables (scaler ajusté sur le train uniquement).
- **Comparaison à nombre de lignes égal** : la fiche `.json` garde `n_lignes` pour interpréter les écarts entre échantillon, train partiel et train complet.
- **Textes à corriger** : la section 4 mentionne `strict_cours` seul alors que les 4 jeux sont comparés ; la définition de l'accuracy est restée inachevée dans la section 2.

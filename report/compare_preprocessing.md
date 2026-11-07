---
{
  "id": "file_lgar6tx2",
  "filetype": "document",
  "filename": "compare_preprocessing",
  "created_at": "2026-11-07T09:41:32.080Z",
  "updated_at": "2026-11-07T09:49:02.044Z",
  "meta": {
    "location": "/"
  }
}
---
voici une **comparaison approfondie** entre :

 votre notebook local (chahinez) \[03_Preprocessing.ipynb\](file:///c:/Users/chahi/Desktop/DM-Weather-framework/notebooks/03_Preprocessing.ipynb) 

 le notebook téléversé (nour) `Preprocessing.ipynb` (issu des travaux exploratoires de votre binôme).

---

### Synthèse globale

| Critère | Notebook local (`03_Preprocessing.ipynb`) | Notebook téléversé (`Preprocessing.ipynb`) |
| --- | --- | --- |
| **Rôle & Nature** | **Pipeline de production opérationnel** (prêt pour le ML). | **Cahier de recherche & R&D exploratoire**. |
| **Volume & Structure** | **24 cellules** (12 markdown, 12 code), très structuré, linéaire. | **101 cellules** (33 markdown, 68 code), itératif, verbeux. |
| **Environnement** | **Local & reproductible** (`DM-Weather-framework/data/processed`). | **Google Colab** (`drive.mount`, `apt-get libeccodes-dev`, chemins Colab). |
| **Contrôle correction ECMWF** | **Formel et automatisé** (diff avec l'EDA + test $Z\text{-score} > 3$ + figure PNG). | Absent (charge directement le fichier sans vérification différentielle). |
| **Analyse physique des outliers** | Synthétique et vectorisée (IQR global vs mensuel, taux de coïncidence). | **Ultra-détaillée et exhaustive** (explications thermodynamiques, décompositions mensuelles). |
| **Traitement des queues lourdes** | **Classe Scikit-Learn** `SignedLog1p` (mise à l'échelle sur le train). | Non implémenté (constat statistique sans transformation ML). |
| **Réduction de numérosité** | Échantillonnage stratifié et systématique implémentés (SVM / KNN). | Non implémenté. |
| **Sortie & Export** | Sauvegarde finale (`df_clean.parquet` / `.pkl`) prête pour le notebook `04`. | **Aucune sauvegarde finale**. |

---

### 1. Analyse thématique étape par étape

#### A. Environnement et portabilité

- **Notebook local :** Conçu pour fonctionner directement dans le dépôt local du framework. Il utilise des chemins relatifs ou configurés (`BASE / OUT_DIR`) sans dépendance propriétaire.
- **Notebook téléversé :** Développé sur **Google Colab** (`drive.mount('/content/drive')`, `!pip install ...`, `!apt-get libeccodes-dev`). Il ne peut pas s'exécuter localement sans modifications substantielles de ses premières cellules.

---

#### B. Données initiales et validation du correctif ECMWF

- **Notebook local (Cellules 1 à 3 & 10-11) :**
  - Effectue un **contrôle différentiel strict** entre le fichier brut de l'EDA (`PATH_EDA`) et le fichier corrigé (`PATH_CORR`).
  - Vérifie par assertion que **seules les 7 variables accumulées** (`slhf`, `sshf`, `ssr`, `str`, `e`, `ro`, `tp`) ont été modifiées et **uniquement sur la période d'anomalie** (septembre 2022 à février 2024).
  - Vérifie la disparition de la rupture via le $Z$-score mensuel robuste (médiane et MAD) et exporte la figure `figures/f20_variation_mensuelle_corrigee.png`.
- **Notebook téléversé (Cellules 4-5) :**
  - Ouvre directement le fichier corrigé sans vérifier son intégrité par rapport à l'EDA ni tracer le diagnostic de correction de la rupture 2022-2024.

---

#### C. Gestion des valeurs manquantes

- **Notebook local (Cellules 4-5) :**
  - Approche pragmatique orientée cours : calcule que sur les 9 568 points de grille, **4 143 points sont à 100 % NaN** (mer Méditerranée et pays voisins) et **5 425 points sont à 0 % NaN**.
  - Règle du cours appliquée directement : $> 50,%$ manquant $\rightarrow$ suppression directe ; aucun point n'étant entre $0,%$ et $50,%$, **aucune imputation n'est nécessaire**.
- **Notebook téléversé (Cellules 6 à 18) :**
  - **Approche géométrique et spatiale très riche :** Il recharge le shapefile de l'Algérie, applique le polygone, recalcule la boîte englobante et fait un `coarsen` spatial.
  - Il montre précisément l'origine des **5 cellules littorales particulières** qui se retrouvent en NaN à cause du découpage côtier du masque terre-mer d'ERA5-Land. C'est une excellente démonstration visuelle et explicative pour un rapport.

---

#### D. Contrôle qualité des données (Data Quality)

- **Notebook local (Cellules 8-9) :**
  - Regroupe tous les tests dans une fonction unique `quality_checks(df)` et construit une table formelle selon les critères académiques :
    - **Complétude :** NaN résiduels ($0$), mois manquants ($0$).
    - **Cohérence :** Doublons spatio-temporels ($0$), cohérence thermodynamique `t2m < d2m` ($0$).
    - **Exactitude :** Positivité des grandeurs `sp <= 0`, `tp < 0`, `ro < 0` ($0$), valeurs infinies ($0$).
  - Utilise une assertion `assert all(...)` pour bloquer le pipeline si une anomalie apparaît.
- **Notebook téléversé (Cellules 62 à 70) :**
  - Réalise exactement les mêmes vérifications physiques (`T2M < D2M`, `SP <= 0`, `TP < 0`, `RO < 0`, doublons, dates manquantes, variables constantes), mais réparties sur plusieurs cellules isolées. Les résultats numériques trouvés sont rigoureusement identiques ($0$ anomalie).

---

#### E. Valeurs aberrantes et analyse physique (Outliers)

C'est ici que réside la plus grande différence de style et de profondeur :

- **Notebook local (Cellules 12-13) :**
  - **Code condensé et vectorisé :** Calcule l'IQR global (`outlier_flags`) et l'IQR par point géographique et par mois (`temporal_flags`).
  - Calcule le taux de coïncidence entre les flux via `coincidence(a, b)` :
    - $\text{TP} \leftrightarrow \text{RO}$ : $94{,}12,%$
    - $\text{TP} \leftrightarrow \text{E}$ : $92{,}04,%$
    - $\text{E} \leftrightarrow \text{SLHF}$ : $100,%$
  - **Décision rapide et motivée :** Tous les extrêmes sont physiquement cohérents et interconnectés $\implies$ **aucun enregistrement n'est supprimé**.
- **Notebook téléversé (Cellules 19 à 55 puis 74 à 100) :**
  - **Enquête physique et thermodynamique poussée :** C'est le point fort du travail de la binôme.
  - Analyse détaillée du cycle de l'eau : corrélation entre les précipitations et le ruissellement selon les mois d'hiver vs d'été.
  - Explication physique du flux de chaleur latente (`slhf`) et de l'évaporation (`e`), justifiant pourquoi $128,044$ outliers coïncident à $100,%$ (seule 1 observation diffère).
  - Explication de la non-détection d'outliers sur `t2m` par l'IQR global (distribution gaussienne stable sur l'année), et croisement de `slhf` avec le point de rosée `d2m`.
  - **Partie** `# **PLUS**` **(Cellules 74 à 100) :** Classification fine des observations en « Normale », « Extrême simultanée » et « Suspecte - vérifier le contexte » avec graphiques en barres.

---

#### F. Traitement des queues lourdes (Skewness) & Variance

- **Notebook local (Cellules 14 à 17) :**
  - Démontre pourquoi un `log1p(x)` naïf échoue sur des variables en mètres (valeurs de l'ordre de $10^{-7}$ à $10^{-2}$).
  - Propose une transformation adaptée : $\text{sign}(x) \times \log\left(1 + \frac{|x|}{\text{scale}}\right)$.
  - Implémente la classe Scikit-Learn `SignedLog1p(BaseEstimator, TransformerMixin)` pour éviter tout data leakage (l'échelle `scale_` est apprise sur le jeu d'entraînement uniquement).
  - Montre dans la cellule 17 que la variance anormalement basse de `tp`, `ro`, `e`, `slhf` est un artefact des valeurs extrêmes, et qu'après transformation logarithmique, leur variance normalisée redevient saine.
- **Notebook téléversé (Cellules 56 à 61) :**
  - Calcule le coefficient de variation ($CV,%$) et la variabilité spatio-temporelle, constatant la faible variabilité de `sp` ($3{,}52,%$) et `str`.
  - **Lacune :** Ne propose aucune transformation mathématique pour normaliser les distributions asymétriques à queues lourdes.

---

#### G. Corrélations, Sélection de variables et Échantillonnage

- **Notebook local (Cellules 18 à 21) :**
  - Détecte les paires redondantes à $|\rho| > 0{,}90$ (Spearman) : `slhf` = `e` ($1{,}00$), `ro` $\approx$ `tp` ($0{,}98$), `ssr` $\leftrightarrow$ `sshf` ($-0{,}95$).
  - Prépare **4 sous-ensembles de features** (`complet`, `reduit`, `reduit_sans_sp`, `strict_cours`) pour permettre de tester différentes variantes dans la partie modélisation (Chapitre 3/4).
  - Fournit les fonctions d'échantillonnage `stratified_sample` et `systematic_sample` pour accélérer les algorithmes lents (SVM, KNN).
  - **Détails :**
    - `df[VARS]` : sélectionne les colonnes listées dans `VARS`.
    - `.corr(method="spearman")` : calcule les corrélations de Spearman entre toutes les paires de variables. Cette mesure repère les relations monotones, même si elles ne sont pas parfaitement linéaires.
    - `np.triu(..., 1)` : ne garde que le triangle supérieur de la matrice, sans la diagonale. Cela évite d'afficher chaque paire deux fois.
    - `.stack()` : transforme les paires restantes en série, avec les noms des deux variables comme index.
    - Le filtre `abs() > 0.9` : conserve les corrélations très fortes, positives ou négatives.
  - **Interprétation des résultats :**
    - `slhf` et `e` : sont parfaitement corrélées (`1.000`), elles semblent donc porter la même information.
    - `ro` et `tp` : sont très fortement corrélées (`0.981`).
    - `sshf` et `ssr` : sont fortement corrélées négativement (`-0.954`). Lorsque l'une augmente, l'autre tend à diminuer.
  - **Construction des listes de variables :**
    - `DROP = ["e", "ro"]` : indique les variables retirées des versions réduites. L'objectif est de limiter la redondance :
      - `e` est retirée car elle est un doublon de `slhf`.
      - `ro` est retirée car elle est très corrélée à `tp`.
    - `FEATURE_SETS` : contient plusieurs scénarios à comparer :

      | Liste | Contenu | But |
      | --- | --- | --- |
      | `complet` | Les 11 variables de `FEATURES_SUP` | Modèle de référence avec toutes les variables |
      | `reduit` | 9 variables, sans `e` ni `ro` | Réduire les variables redondantes |
      | `reduit_sans_sp` | 8 variables, sans `e`, `ro` ni `sp` | Tester aussi l’effet du retrait de `sp` |
      | `strict_cours` | 8 variables, sans `e`, `ro` ni `sshf` | Appliquer la règle du cours sur les corrélations supérieures à 90 % |
- **Notebook téléversé (Cellules 71 à 73) :**
  - Supprime `e` et `ro` pour créer `data_reduced`, mais ne crée pas de variantes de features (comme `strict_cours` sans `sshf`) ni de fonctions d'échantillonnage.

---

#### H. Sauvegarde et transition vers le Feature Engineering

- **Notebook local (Cellules 22-23) :**
  - Sauvegarde propre en Parquet (`df_clean.parquet`, dimension $764,925 \times 16$ ou $759,500 \times 16$).
  - Spécifie explicitement le contrat d'interface pour le notebook suivant `04_Feature_Engineering.ipynb` (construction de la cible `t2m_next`, découpage chronologique train/test, features cycliques sin/cos).
- **Notebook téléversé :**
  - **Aucun export.** Le notebook se termine sur des analyses mensuelles redondantes dans la section `# **PLUS**`. Les données nettoyées restent en mémoire vive et ne sont pas transmises au reste du projet.

---

### 2. Évaluation des points forts et limites

```
                    ┌────────────────────────────────────────────────────────┐
                    │               COMPARAISON STRATÉGIQUE                  │
                    └────────────────────────────────────────────────────────┘
                                      │
              ┌───────────────────────┴───────────────────────┐
              ▼                                               ▼
┌───────────────────────────┐                   ┌───────────────────────────┐
│ Notebook 03_Preprocessing │                   │ Preprocessing (téléversé) │
├───────────────────────────┤                   ├───────────────────────────┤
│ • Pipeline propre (24 c.) │                   │ • Exploration R&D (101 c.)│
│ • Sklearn SignedLog1p     │                   │ • Analyses physiques fines│
│ • Export Parquet final    │                   │ • Justifications cycle eau│
│ • Reproductible & modulaire│                   │ • Zéro export, code brut  │
└───────────────────────────┘                   └───────────────────────────┘
```

#### Ce que le Notebook Local apporte de supérieur :

1. **Intégration logicielle :** Il s'insère parfaitement dans la chaîne du framework (`01_Download` $\rightarrow$ `02_EDA` $\rightarrow$ `03_Preprocessing` $\rightarrow$ `04_Feature_Engineering` $\rightarrow$ `05_Modeling`).
2. **Respect des règles ML :** Création du transformateur `SignedLog1p` scikit-learn garantissant l'absence de fuite de données (*data leakage*).
3. **Robustesse :** Présence d'assertions de non-régression et de tests automatiques.
4. **Clarté :** Pas de doublons ni de cellules répétées.

#### Ce que le Notebook Téléversé apporte d'intéressant :

1. **Richesse explicative :** Les textes et visualisations sur la cohérence hydrologique ($\text{TP} \rightarrow \text{RO}$ et $\text{TP} \rightarrow \text{E}$) et thermique ($\text{E} \rightarrow \text{SLHF}$) sont précieux pour la documentation scientifique et la soutenance orale.
2. **Explication spatiale des NaNs :** La démonstration détaillée avec le shapefile met en évidence la réalité côtière des 5 mailles marines résiduelles.

---

### 3. Conclusion et Recommandation

> \[!TIP\]\
> \*\***Recommandation opérationnelle :**
>
> - **Pour le code exécutable du projet :** Conservez et exécutez \[03_Preprocessing.ipynb\](file:///c:/Users/chahi/Desktop/DM-Weather-framework/notebooks/03_Preprocessing.ipynb). C'est le seul qui produit le fichier de données propre nécessaire aux étapes suivantes et qui implémente les bons transformateurs de machine learning.
> - **Pour le rapport écrit et la soutenance :** Récupérez les explications thermodynamiques, les tableaux de coïncidence mensuelle et la classification des observations suspectes du notebook de votre binôme pour enrichir l'argumentation du rapport de Data Mining.
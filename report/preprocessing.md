# Prétraitement et Feature Engineering des données ERA5-Land

## 1. Objectif et point de départ

L'objectif du prétraitement est de passer des données ERA5-Land utilisées pendant l'EDA à un jeu de données propre, cohérent et exploitable pour les analyses et les étapes ultérieures du projet.

Le point de départ est le fichier NetCDF déjà corrigé par la binôme :

`era5land_algeria_masked_x2_corrected.nc`

Aucun nouveau téléchargement n'est effectué dans cette étape. Le fichier initial de l'EDA (`era5land_algeria_masked_x2.nc`) est utilisé uniquement pour vérifier les modifications apportées par la correction ECMWF.

Les variables étudiées sont :

| Variable | Description |
|---|---|
| `t2m` | Température à 2 mètres |
| `d2m` | Température du point de rosée |
| `sp` | Pression à la surface |
| `u10` | Composante zonale du vent à 10 mètres |
| `v10` | Composante méridienne du vent à 10 mètres |
| `slhf` | Flux de chaleur latente |
| `sshf` | Flux de chaleur sensible |
| `ssr` | Rayonnement solaire net |
| `str` | Rayonnement thermique net |
| `e` | Évaporation |
| `ro` | Ruissellement |
| `tp` | Précipitations totales |

Les variables `slhf`, `sshf`, `ssr`, `str`, `e`, `ro` et `tp` sont des variables accumulées. Elles étaient concernées par l'anomalie ECMWF étudiée.

---

## 2. Vérification du fichier corrigé

Le fichier corrigé est chargé avec `xarray`.

Les opérations suivantes sont effectuées :

- Renommage de la coordonnée `valid_time` en `time`, lorsqu'elle existe.
- Harmonisation des dates au début de chaque mois.
- Suppression des variables techniques `number` et `expver`, lorsqu'elles sont présentes.

Lorsque le fichier original de l'EDA est disponible, une comparaison est effectuée entre les deux fichiers :

- Vérification que les grilles de latitude et de longitude sont identiques.
- Comparaison des valeurs variable par variable.
- Identification du nombre de valeurs et de mois modifiés.

Le résultat attendu est que les modifications concernent uniquement les sept variables accumulées (`slhf`, `sshf`, `ssr`, `str`, `e`, `ro`, `tp`) et la période allant de septembre 2022 à février 2024.

Cette comparaison permet de vérifier que le fichier corrigé correspond bien au fichier utilisé pour l'EDA, avec les modifications attendues.

---

## 3. Traitement des valeurs manquantes

Le taux de valeurs manquantes est examiné pour chaque point de grille.

Dans ce jeu de données, les points sont répartis en deux catégories :

- Points entièrement manquants sur toute la période.
- Points ne présentant aucune valeur manquante.

Il n'y a pas de points présentant un taux intermédiaire de valeurs manquantes.

Conformément à la règle retenue dans le cours, les points entièrement manquants sont supprimés. Aucune imputation n'est nécessaire puisque les points conservés sont complets.

Les **4 143 points entièrement vides**, situés hors de la zone étudiée ou sur certains points du littoral nord, sont donc écartés.

Il reste **5 425 points de grille exploitables**.

> La suppression concerne des points géographiques entièrement vides, et non des mois isolés à remplacer par des valeurs estimées.

---

## 4. Conversion en DataFrame et conversion des unités

Les variables météorologiques sont converties en DataFrame avec les colonnes suivantes :

- `time`
- `latitude`
- `longitude`
- Les douze variables météorologiques.

Les lignes contenant des valeurs manquantes sont supprimées. Une vérification confirme ensuite l'absence de valeurs manquantes dans les variables retenues.

Les températures `t2m` et `d2m` sont initialement exprimées en Kelvin. Elles sont converties en degrés Celsius :

\[
T(°C) = T(K) - 273.15
\]

Une colonne `month` est ajoutée afin de faciliter les analyses temporelles et saisonnières.

Enfin, les observations sont triées par date, latitude et longitude.

Avec 5 425 points exploitables et 140 mois, le nombre attendu de lignes est :

\[
5\,425 \times 140 = 759\,500
\]

---

## 5. Contrôles de qualité

Plusieurs contrôles sont réalisés pour évaluer la complétude, la cohérence et l'exactitude des données.

| Dimension contrôlée | Vérification effectuée |
|---|---|
| Complétude | Absence de valeurs manquantes après suppression des points vides |
| Complétude temporelle | Vérification des mois manquants dans la période disponible |
| Cohérence | Absence de doublons selon `time`, `latitude` et `longitude` |
| Cohérence physique | Vérification de la relation `t2m >= d2m` |
| Exactitude / plausibilité | Vérification de `sp > 0`, `tp >= 0` et `ro >= 0` |
| Exactitude numérique | Absence de valeurs infinies |
| Variabilité | Vérification qu'aucune variable n'est constante |

Les contrôles ne mettent pas en évidence d'anomalies parmi les observations conservées.

La relation `t2m >= d2m` est utilisée comme contrôle de cohérence physique dans le cadre de ce jeu de données. Les vérifications de positivité permettent notamment de repérer des valeurs impossibles pour les variables concernées.

---

## 6. Contrôle de la correction ECMWF

La période de septembre 2022 à février 2024 fait l'objet d'une vérification temporelle spécifique, car elle correspond à la période concernée par l'anomalie des variables accumulées.

Deux analyses complémentaires sont réalisées.

### 6.1. Vérification statistique

Pour chaque variable accumulée, les moyennes spatiales mensuelles sont calculées.

Chaque mois est ensuite comparé à la distribution historique du même mois calendaire, à l'aide d'un z-score robuste fondé sur la médiane et la MAD (*Median Absolute Deviation*).

Cette méthode permet de repérer des mois atypiques par rapport aux autres occurrences du même mois de l'année.

### 6.2. Vérification visuelle

Les moyennes spatiales mensuelles des variables sont représentées sous forme de séries temporelles.

La période de septembre 2022 à février 2024 est mise en évidence sur les graphiques.

Ces deux vérifications permettent d'examiner si une rupture temporelle ou des valeurs inhabituellement élevées ou faibles persistent après correction.

**Limite de l'analyse :** le z-score et les graphiques vérifient la cohérence temporelle des données corrigées. Ils ne constituent pas, à eux seuls, une comparaison directe entre les anciennes et les nouvelles valeurs. La comparaison des deux fichiers, lorsqu'elle est disponible, est réalisée séparément à l'étape 2.

---

## 7. Séparation chronologique Train/Test et création de la cible

Cette séparation concerne la préparation supervisée, dans laquelle la température du mois suivant est utilisée comme cible.

### 7.1. Création de la cible

Pour chaque point géographique (`latitude`, `longitude`), les observations sont triées chronologiquement.

La colonne `t2m_next` est créée avec la température du mois suivant :

\[
t2m\_next(t) = t2m(t+1)
\]

La colonne `target_time` indique la date correspondant à cette cible.

Les observations pour lesquelles la cible du mois suivant n'existe pas sont retirées du jeu supervisé.

Une vérification garantit que la cible correspond bien au mois immédiatement suivant.

### 7.2. Séparation chronologique

Les dates disponibles sont triées et une séparation chronologique 80/20 est appliquée :

- **Train (80 % des dates)** : périodes les plus anciennes.
- **Test (20 % des dates)** : périodes les plus récentes.

Une séparation chronologique est préférable à une séparation aléatoire pour des données temporelles, car elle permet d'évaluer ultérieurement un modèle sur une période postérieure à celle utilisée pour son apprentissage.

La condition appliquée au Train impose que la date de l'observation et la date de sa cible soient toutes les deux antérieures à la date limite.

Ainsi, une observation dont la cible se situe dans la période Test n'est pas conservée dans Train.

**Précision concernant la frontière :**

Le mois exclu dépend de la valeur effective de `date_limite`.

Il faut donc consulter la date affichée par le notebook pour identifier précisément l'observation qui traverse la frontière entre Train et Test.

Par exemple, si la date limite est avril 2024 :

- Février 2024 : entrée février, cible mars. L'observation reste dans Train.
- Mars 2024 : entrée mars, cible avril. L'observation est exclue de Train.
- Avril 2024 : l'observation appartient à Test.

Cette précaution évite une fuite temporelle entre les deux ensembles.

---

## 8. Analyse et traitement des valeurs aberrantes

Les valeurs aberrantes sont examinées à l'aide de plusieurs approches complémentaires.

### 8.1. IQR global

Pour chaque variable, les bornes sont calculées avec la règle :

\[
IQR = Q_3 - Q_1
\]

\[
Borne_{inf} = Q_1 - 1.5 \times IQR
\]

\[
Borne_{sup} = Q_3 + 1.5 \times IQR
\]

Les observations situées en dehors de ces bornes sont signalées comme valeurs aberrantes statistiques.

### 8.2. IQR par point géographique et par mois

Une deuxième détection est réalisée séparément pour chaque combinaison de latitude, longitude et mois calendaire.

Cette approche tient compte des différences spatiales et saisonnières.

Une valeur élevée en été, par exemple, n'est pas nécessairement inhabituelle si elle est comparée à des observations d'hiver.

### 8.3. Analyse de la cohérence entre variables

Les valeurs extrêmes sont également examinées en tenant compte des relations physiques possibles entre variables.

| Variables comparées | Relation examinée |
|---|---|
| `tp` et `ro` | Des précipitations importantes peuvent être associées à un ruissellement important |
| `tp` et `e` | Relation entre précipitations et évaporation, à interpréter selon les conditions climatiques |
| `slhf` et `e` | Cohérence entre flux de chaleur latente et évaporation |
| `slhf`, `t2m` et `d2m` | Cohérence avec les conditions thermiques et l'humidité atmosphérique |

Les indicateurs d'asymétrie (*skewness*) et d'aplatissement (*kurtosis*) sont également calculés pour mieux décrire les distributions.

### 8.4. Décision

Les valeurs extrêmes détectées sont conservées lorsqu'elles restent physiquement plausibles et cohérentes avec le contexte climatique.

La règle IQR est donc utilisée comme **outil de diagnostic**, et non comme une règle de suppression automatique.

Une valeur extrême ne signifie pas nécessairement une erreur : elle peut correspondre à un événement météorologique réel.

Aucune variable ni observation n'est supprimée uniquement parce qu'elle dépasse les bornes IQR.

---

## 9. Transformation des variables à queues lourdes

L'analyse exploratoire a montré que certaines variables présentent des distributions très asymétriques et des queues lourdes, notamment :

- `ro`
- `tp`
- `slhf`
- `e`

Une transformation logarithmique peut réduire l'asymétrie.

Cependant, les variables concernées peuvent contenir des valeurs positives et négatives et leurs amplitudes sont très faibles. L'application directe de `log1p` aurait donc peu d'effet.

Une transformation logarithmique signée est utilisée :

\[
x' = sign(x) \times \log\left(1 + \frac{|x|}{s}\right)
\]

où \(s\) représente une échelle typique estimée à partir des données d'entraînement :

\[
s = median(|x|)
\]

Si cette médiane est nulle, la moyenne de \(|x|\) est utilisée comme solution de remplacement.

Cette transformation :

- conserve le signe des valeurs ;
- réduit l'influence des grandes amplitudes ;
- permet de traiter des valeurs positives et négatives ;
- ne supprime pas les observations extrêmes.

### 9.1. Prévention de la fuite de données

L'objet de transformation est ajusté uniquement sur Train :

```python
slog = SignedLog1p(HEAVY).fit(train)
```

Les paramètres appris sur Train sont ensuite réutilisés pour transformer Train et Test :

```python
train_t = slog.transform(train)
test_t = slog.transform(test)
```

Le jeu Test ne participe donc pas à l'estimation des échelles de transformation.

### 9.2. Application au jeu non supervisé

Pour le jeu non supervisé, si l'on souhaite conserver toutes les observations disponibles tout en appliquant exactement la même transformation, on réutilise le même objet `slog`, sans refaire `fit()` sur le jeu complet.

**Point de vigilance :** la copie destinée au jeu non supervisé doit être créée avant la création de `t2m_next` et `target_time`, ainsi qu'avant la suppression des lignes sans cible.

Par exemple :

```python
# À créer avant la création de t2m_next et target_time
df_full_clean = df.copy()

# Après l'ajustement de slog sur Train
df_unsup_preprocessed = slog.transform(df_full_clean)
```

Cette copie contient toutes les observations disponibles dans la source, y compris la dernière date qui ne possède pas encore de cible future.

Elle ne doit pas contenir de cible supervisée.

---

## 10. Analyse de la variabilité

La variabilité des variables est étudiée sur Train afin de repérer d'éventuelles variables presque constantes.

Deux indicateurs sont calculés.

### 10.1. Coefficient de variation

\[
CV = \frac{\sigma}{|\mu|} \times 100
\]

Il exprime l'écart-type relativement à la valeur absolue de la moyenne.

### 10.2. Variance après Min-Max

Les valeurs sont ramenées sur une échelle comprise entre 0 et 1, puis leur variance est calculée.

Cet indicateur permet de comparer la dispersion des variables indépendamment de leurs unités initiales.

Les variabilités temporelle et spatiale sont également examinées à partir des moyennes correspondantes.

La variance Min-Max des variables à queues lourdes est ensuite comparée avant et après la transformation SignedLog.

### Décision

Aucune variable n'est supprimée sur la seule base d'un faible coefficient de variation ou d'une faible variance Min-Max.

La décision de conserver ou non une variable doit aussi tenir compte de son intérêt climatique et de son utilité pour la tâche visée.

---

## 11. Analyse des corrélations et constitution de jeux de variables

Les corrélations de Spearman sont calculées sur Train.

Cette mesure permet d'évaluer les relations monotones entre variables, sans supposer qu'elles sont nécessairement linéaires.

Les paires présentant une corrélation absolue supérieure à 0,9 sont examinées.

L'analyse met notamment en évidence :

- Une relation très forte entre `e` et `slhf`.
- Une forte corrélation entre `ro` et `tp`.
- Une forte corrélation entre `ssr` et `sshf`.

Plusieurs ensembles de variables sont alors définis pour permettre une comparaison ultérieure :

| Ensemble | Variables retirées |
|---|---|
| `complet` | Aucune parmi les variables initialement retenues |
| `reduit` | `e` et `ro` |
| `reduit_sans_sp` | `e`, `ro` et `sp` |
| `strict_cours` | `e`, `ro` et `sshf` |

La définition de plusieurs ensembles permet de ne pas supprimer définitivement une variable sur la seule base d'une corrélation.

Le choix final pourra être évalué dans la suite du projet.

---

## 12. Réduction de la numérosité : méthodes préparées

Deux fonctions d'échantillonnage sont définies :

- **Échantillonnage stratifié** : conserve les proportions des classes dans un problème de classification.
- **Échantillonnage systématique** : sélectionne une observation toutes les \(k\) lignes.

Ces fonctions sont disponibles pour une utilisation ultérieure si la taille des données rend certains traitements trop coûteux.

À ce stade, elles sont seulement définies : aucun échantillonnage n'est effectué dans le code présenté.

L'échantillonnage stratifié suppose par ailleurs l'existence d'une variable de classe.

---

## 13. Sauvegarde des jeux préparés

Les jeux transformés sont enregistrés au format Parquet dans le dossier `processed/transformed/`.

| Fichier | Contenu |
|---|---|
| `train_transformed.parquet` | Jeu Train après transformation SignedLog |
| `test_transformed.parquet` | Jeu Test après transformation SignedLog |
| `dataset_unsupervised.parquet` | Jeu complet destiné à la préparation non supervisée, après transformation |

Le jeu non supervisé doit être construit à partir de `df_full_clean`, c'est-à-dire la copie créée avant la création de la cible et le filtrage supervisé.

Le format Parquet permet de conserver les types de données et de recharger efficacement les tableaux avec pandas.

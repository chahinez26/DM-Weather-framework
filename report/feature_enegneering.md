# Feature Engineering

## 1. Objectif

Le Feature Engineering consiste à transformer les données prétraitées en variables adaptées aux deux approches d'apprentissage envisagées.

Deux volets sont considérés :

- **Apprentissage supervisé :** prédire la température du mois suivant (`t2m_next`) à partir des variables météorologiques et des informations temporelles.
- **Apprentissage non supervisé :** extraire des caractéristiques à partir de la température à 2 mètres (`t2m`) et du rayonnement thermique sortant (`str`) afin d'étudier les tendances climatiques à long terme.

Le point de départ est constitué des datasets nettoyés et sauvegardés à la fin du preprocessing.

---

# Partie I – Feature Engineering pour l'apprentissage supervisé

L'objectif est de préparer les variables explicatives et la cible nécessaires à la prédiction de la température du mois suivant.

## 1. Chargement des données

Les jeux de données prétraités sont chargés depuis les fichiers Parquet :

- `train_transformed.parquet` : données d'entraînement.
- `test_transformed.parquet` : données de test.

La transformation `SignedLog1p` ayant déjà été appliquée aux variables concernées pendant le preprocessing, les données chargées contiennent ces variables transformées.

## 2. Création des variables temporelles et cycliques

Les informations temporelles permettent au modèle de prendre en compte l'évolution des conditions climatiques au cours du temps.

### 2.1. Extraction de l'année

La colonne `year` est extraite à partir de la colonne `time`.

Elle permet de conserver l'information sur l'année de l'observation et de représenter une tendance temporelle à long terme.

### 2.2. Encodage cyclique du mois

Le mois est une variable cyclique : décembre et janvier sont deux mois consécutifs dans le cycle annuel, même si leurs valeurs numériques sont éloignées.

Pour représenter cette périodicité, le mois est transformé en deux variables :

- `month_sin`
- `month_cos`

Les formules utilisées sont :

\[
month\_sin = \sin\left(\frac{2\pi \times month}{12}\right)
\]

\[
month\_cos = \cos\left(\frac{2\pi \times month}{12}\right)
\]

Cette représentation permet de conserver la proximité entre les mois dans le cycle annuel et d'éviter de considérer le mois comme une simple variable numérique linéaire.

## 3. Sélection des variables explicatives et de la cible

Les variables explicatives sélectionnées sont :

- Variables météorologiques : `d2m`, `slhf`, `ssr`, `str`, `sshf`, `ro`, `e`, `u10`, `v10`, `sp`, `tp`.
- Variables temporelles : `year`, `month_sin`, `month_cos`.

La variable cible est :

- `t2m_next` : température à 2 mètres du mois suivant.

Les ensembles obtenus sont :

- `X_train` : variables explicatives du jeu d'entraînement.
- `y_train` : cible du jeu d'entraînement.
- `X_test` : variables explicatives du jeu de test.
- `y_test` : cible du jeu de test.

La cible étant créée lors du preprocessing à partir du décalage temporel de `t2m`, elle représente la température du mois suivant pour chaque point géographique.

## 4. Normalisation avec RobustScaler

Les variables explicatives présentent des échelles et des distributions différentes. Une mise à l'échelle est donc appliquée à l'aide de `RobustScaler`.

Cette méthode utilise la médiane et l'écart interquartile (IQR) pour transformer les variables :

\[
X_{scaled} = \frac{X - Q_2(X)}{Q_3(X)-Q_1(X)}
\]

où :

- \(Q_2\) représente la médiane ;
- \(Q_1\) représente le premier quartile ;
- \(Q_3\) représente le troisième quartile.

L'utilisation de cette méthode est intéressante dans notre cas, car certaines variables météorologiques présentent des distributions asymétriques et des valeurs extrêmes.

**Prévention de la fuite de données :**

- Le `RobustScaler` est ajusté uniquement sur les données d'entraînement avec `fit_transform()`.
- Les données de test sont transformées avec le même scaler à l'aide de `transform()`.

Ainsi, les informations du jeu de test ne sont pas utilisées pour calculer les paramètres de normalisation.

## 5. Sauvegarde des données supervisées

Après la normalisation, les variables explicatives transformées sont regroupées avec leurs cibles respectives.

Deux fichiers sont sauvegardés :

- `train_supervised.parquet`
- `test_supervised.parquet`

Le scaler est également sauvegardé dans le fichier `robust_scaler.pkl`, afin de pouvoir réutiliser exactement les mêmes paramètres de transformation.

Ces fichiers constituent les jeux de données préparés pour la future étape de modélisation supervisée.

---

# Partie II – Feature Engineering pour l'apprentissage non supervisé

L'objectif de cette partie est de construire des caractéristiques permettant de représenter les profils climatiques annuels de chaque point géographique.

Contrairement à l'approche supervisée, cette analyse se concentre uniquement sur deux variables :

- `t2m` : température à 2 mètres.
- `str` : rayonnement thermique sortant à la surface.

## 1. Préparation des données

Le dataset non supervisé est chargé, puis les colonnes nécessaires sont conservées :

- `time`
- `latitude`
- `longitude`
- `t2m`
- `str`

À partir de la date, deux informations temporelles sont extraites :

- `year` : année de l'observation.
- `month` : mois de l'observation.

On obtient ainsi une observation par combinaison de date et de coordonnées géographiques.

## 2. Vérification de la structure des données

Avant de transformer les données, plusieurs vérifications sont effectuées.

### 2.1. Vérification des doublons

La combinaison `(time, latitude, longitude)` est vérifiée afin de s'assurer qu'une seule observation existe pour chaque point géographique et chaque mois.

Le résultat obtenu est de zéro doublon.

Cette vérification est importante, car la transformation `pivot()` nécessite une valeur unique pour chaque combinaison de l'index et de la colonne.

### 2.2. Régularité des observations

Le nombre d'observations est également vérifié pour chaque mois.

Les résultats montrent :

- 5 425 observations par mois.
- Un écart-type de zéro.

Cela signifie que chaque mois possède le même nombre de points géographiques.

La couverture spatiale est donc constante sur la période étudiée, ce qui facilite la comparaison des profils climatiques entre les années.

## 3. Transformation des données avec Pivot

Initialement, les données sont organisées sous un format long : chaque ligne représente un point géographique observé pendant un mois donné.

Pour construire des profils annuels, la fonction `pivot()` est utilisée afin de passer à un format large.

L'index est constitué de :

- `latitude`
- `longitude`
- `year`

Les colonnes correspondent aux mois de l'année et les valeurs sont les variables `t2m` et `str`.

Les colonnes obtenues sont renommées sous la forme :

- `t2m_month_01`, ..., `t2m_month_12`
- `str_month_01`, ..., `str_month_12`

Chaque ligne représente désormais un point géographique pour une année donnée, avec :

- 12 valeurs mensuelles de température.
- 12 valeurs mensuelles de rayonnement thermique sortant.

On obtient donc 24 caractéristiques mensuelles, auxquelles s'ajoutent les trois informations d'identification : latitude, longitude et année.

## 4. Conservation des années complètes

L'année 2026 ne contient pas encore les douze mois nécessaires à la construction d'un profil annuel complet.

Pour éviter de comparer des années complètes avec une année partielle, seules les années 2015 à 2025 sont conservées.

Les données retenues permettent ainsi de construire des profils annuels comparables, avec 12 mois disponibles pour chaque variable.

Les mois absents de 2026 ne sont pas imputés : l'année est simplement exclue de cette analyse des profils annuels complets.

## 5. Création des caractéristiques statistiques annuelles

Après la construction des profils mensuels, des statistiques descriptives sont calculées pour chaque point géographique et chaque année.

Ces caractéristiques permettent de résumer le comportement annuel de la température et du rayonnement thermique.

### 5.1. Statistiques annuelles de température

Pour `t2m`, cinq caractéristiques sont calculées :

- `t2m_mean` : température moyenne annuelle.
- `t2m_std` : écart-type annuel de la température.
- `t2m_min` : température minimale observée pendant l'année.
- `t2m_max` : température maximale observée pendant l'année.
- `t2m_amplitude` : différence entre la température maximale et minimale.

L'amplitude est calculée par :

\[
t2m\_amplitude = t2m\_max - t2m\_min
\]

Ces caractéristiques permettent de représenter le niveau thermique moyen, la variabilité et l'amplitude des températures au cours de l'année.

### 5.2. Statistiques annuelles du rayonnement thermique

Les mêmes statistiques sont calculées pour `str` :

- `str_mean` : rayonnement thermique moyen annuel.
- `str_std` : écart-type annuel du rayonnement.
- `str_min` : valeur minimale observée.
- `str_max` : valeur maximale observée.
- `str_amplitude` : différence entre les valeurs maximale et minimale.

L'amplitude est calculée par :

\[
str\_amplitude = str\_max - str\_min
\]

Ces caractéristiques permettent de résumer le comportement annuel du rayonnement thermique sortant.

## 6. Résultat du Feature Engineering non supervisé

À l'issue de ces transformations, chaque ligne représente un point géographique pour une année donnée.

Le dataset contient :

- 3 colonnes d'identification : `latitude`, `longitude`, `year`.
- 24 caractéristiques mensuelles : 12 pour `t2m` et 12 pour `str`.
- 10 caractéristiques statistiques annuelles : 5 pour chaque variable.

Le dataset final contient donc 37 colonnes.

Il permet de représenter à la fois les profils mensuels et les principales caractéristiques statistiques annuelles de chaque point géographique.

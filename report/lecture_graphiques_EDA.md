# Lecture des graphiques — analyse exploratoire ERA5-Land (Algérie)

Document de lecture des **22 figures** produites dans `notebooks/local/02_EDA_local.ipynb`. Chaque section décrit ce que le graphique montre, comment le lire, puis ce qu’on en retient.

Les images sont celles extraites de l’exécution du notebook (`notebooks/local/figures/lecture/`).

## Cadre de lecture

Jeu utilisé : ERA5-Land, Algérie masquée, grille 0,2°, janvier 2015 – septembre 2026 (149 mois). Douze variables :

| Code | Grandeur | Unité dans les graphiques |
|---|---|---|
| `t2m` | Température de l’air à 2 m | °C dans l’EDA (Kelvin sur la série mensuelle brute et sur la carte) |
| `d2m` | Point de rosée à 2 m | °C (Kelvin sur la série mensuelle brute) |
| `sp` | Pression de surface | Pa |
| `u10` | Vent zonal à 10 m (positif vers l’est) | m/s |
| `v10` | Vent méridien à 10 m (positif vers le nord) | m/s |
| `slhf` | Flux de chaleur latente en surface | J/m², **négatif** quand la surface perd de l’énergie par évaporation |
| `sshf` | Flux de chaleur sensible en surface | J/m², même convention de signe |
| `ssr` | Rayonnement solaire net en surface | J/m², positif reçu par la surface |
| `str` | Rayonnement thermique net en surface | J/m², en général **négatif** (la surface émet plus d’IR qu’elle n’en reçoit) |
| `e` | Évaporation | m, **négative** dans ERA5 quand l’eau quitte la surface |
| `ro` | Ruissellement | m |
| `tp` | Précipitations totales | m |

Deux tableaux :

- Analyse univariée : **808 325** lignes (un mois × un point de grille, après suppression des NaN).
- Analyse bivariée et multivariée : **759 500** lignes. On ne garde une ligne que si le mois suivant existe au même point. La cible `t2m_next` est la température du mois suivant.

Classes de `t2m_next`, découpage en trois intervalles de largeur égale sur [0,23 °C ; 41,03 °C] :

| Classe | Bornes | Effectif | Part |
|---|---|---|---|
| Low | 0,23 – 13,86 °C | 117 566 | 15,5 % |
| Medium | 13,86 – 27,44 °C | 331 669 | 43,7 % |
| High | 27,44 – 41,03 °C | 310 265 | 40,9 % |

`month` est le mois **courant**. La classe est celle du mois **suivant**. La barre « mars » décrit donc la température d’avril.

---

## 1. Boîtes à moustaches univariées

![Boîtes à moustaches des 12 variables](figures/lecture/01_boxplots.png)

Une boîte résume une variable : le trait orange est la médiane, la boîte va de Q1 à Q3 (50 % centraux), les moustaches vont jusqu’à la dernière valeur encore dans l’intervalle [Q1 − 1,5 IQR ; Q3 + 1,5 IQR], et les points au-delà sont des valeurs extrêmes.

| Variable | Min | Q1 | Médiane | Q3 | Max | IQR | Lecture de la boîte |
|---|---:|---:|---:|---:|---:|---:|---|
| `t2m` | 0,3 °C | 16,5 | 24,3 | 31,9 | 41,0 | 15,4 | Boîte large, médiane au centre, presque pas de points isolés. La température couvre toute l’année et tout le pays sans valeurs aberrantes au sens de l’IQR (0 % d’outliers). |
| `d2m` | −17,0 | −1,7 | 1,4 | 4,5 | 22,6 | 6,2 | Boîte étroite autour de 0 à 5 °C, moustaches longues des deux côtés. Le point de rosée varie moins que la température, avec quelques situations très sèches (jusqu’à −17 °C) et quelques situations humides (jusqu’à 23 °C). Outliers IQR : 1,2 %. |
| `sp` | 79 860 | 93 360 | 95 900 | 97 560 | 103 600 | 4 200 | Boîte calée vers le haut (autour de 96 kPa) et moustache basse jusqu’à ~80 kPa. La masse des points est en plaine ; la queue basse correspond aux reliefs (Atlas, Hoggar), où la pression de surface est plus faible. Outliers : 1,8 %. |
| `u10` | −6,7 | −2,1 | −1,0 | 0,1 | 7,5 | 2,2 | Boîte à cheval sur des valeurs négatives. Le vent zonal moyen vient de l’est. Quelques pointes au-delà de ±6 m/s (0,8 % d’outliers). |
| `v10` | −4,7 | −1,2 | −0,5 | 0,2 | 3,3 | 1,3 | Même forme, plus resserrée. Composante du nord dominante, faible en valeur absolue. Outliers : 1,1 %. |
| `slhf` | −1,1×10⁷ | −3,3×10⁵ | −1,9×10⁵ | −8,8×10⁴ | −3,6×10³ | 2,4×10⁵ | La boîte est écrasée près de 0. Une moustache très longue part vers −1×10⁷. L’évaporation est faible la plupart du temps, avec des épisodes intenses rares. Outliers : 16,5 %. |
| `sshf` | −1,4×10⁷ | −4,7×10⁶ | −3,5×10⁶ | −1,9×10⁶ | +5,9×10⁶ | 2,8×10⁶ | Boîte large, entièrement du côté négatif, et une moustache haute qui devient positive. Le flux sensible est le flux d’énergie le plus étalé après le rayonnement. Outliers : 0,8 %. |
| `ssr` | 2,8×10⁶ | 1,0×10⁷ | 1,4×10⁷ | 1,7×10⁷ | 2,5×10⁷ | 6,6×10⁶ | Boîte haute, tout est positif. Le solaire net est toujours un apport, fort en été, plus faible en hiver. Aucun outlier IQR. |
| `str` | −1,5×10⁷ | −1,2×10⁷ | −1,0×10⁷ | −8,0×10⁶ | −2,1×10⁶ | 3,6×10⁶ | Tout est négatif. La surface perd de l’énergie par infrarouge, davantage quand le déficit est grand (valeurs vers −1,5×10⁷). Outliers : 0,1 %. |
| `e` | −4,4×10⁻³ | −1,3×10⁻⁴ | −7,4×10⁻⁵ | −3,5×10⁻⁵ | −1,4×10⁻⁶ | 9,6×10⁻⁵ | Copie de `slhf` : boîte collée à 0, longue queue négative. Outliers : 16,5 %. |
| `ro` | 0 | ~0 | ~0 | ~0 | 4,8×10⁻³ | ~0 | Boîte invisible à l’échelle du maximum. Le ruissellement est nul ou infime, sauf une poignée d’événements. Outliers : 16,3 %. |
| `tp` | ~0 | ~0 | 1,8×10⁻⁵ | 1,0×10⁻⁴ | 1,2×10⁻² | 1,0×10⁻⁴ | Même dessin : médiane près de 0, nuage de points jusqu’à environ 12 mm. Outliers : 15,2 %. |

**À retenir.** Deux familles. Les variables « climatiques continues » (`t2m`, `d2m`, `sp`, vents, `sshf`, `ssr`, `str`) ont une boîte lisible. Les variables d’eau (`slhf`, `e`, `ro`, `tp`) sont des distributions à masse en zéro et à queue lourde : une moyenne y est tirée par les extrêmes, et un modèle linéaire brut sera fragile.

---

## 2. Courbes de quantiles (fréquence cumulée)

![Courbes des valeurs ordonnées](figures/lecture/02_quantiles.png)

En abscisse, le rang en pourcentage (`fi`) : 0 % = les plus petites valeurs, 100 % = les plus grandes. En ordonnée, la valeur. Les traits verticaux sont Q1 (25 %, orange), la médiane (50 %, rouge) et Q3 (75 %, orange). Une droite = répartition uniforme. Un plateau = beaucoup d’observations sur une petite plage de valeurs. Une montée verticale = une queue.

- **`t2m`.** Courbe en S régulier, de 0 à 41 °C. La médiane (~24 °C) est au milieu de la montée. Pas de plateau ni de cassure : la température est étalée sur toute son amplitude.
- **`d2m`.** Montée rapide sous 0 °C, long palier entre 0 et 5 °C, puis queue au-dessus de 10 °C après 90 %. La moitié des observations tient dans un intervalle étroit ; les extrêmes humides sont rares.
- **`sp`.** Montée très raide au début (les basses pressions, peu nombreuses), puis aplatissement au-dessus de 95 kPa. La médiane est déjà dans la zone haute. Confirme l’asymétrie à gauche : peu de points d’altitude, beaucoup de points de plaine.
- **`u10` et `v10`.** S symétrique, un peu plus pentu aux deux bouts. `v10` est plus plat au centre : la composante nord-sud est plus concentrée autour de sa médiane que la composante est-ouest.
- **`slhf` et `e`.** Décrochage vertical tout à gauche (quelques flux très négatifs), puis une droite horizontale collée à 0 sur presque tout le graphique. Plus de 80 % des valeurs sont indistinguables à cette échelle. Le trait de Q3 tombe dans ce plateau.
- **`sshf`.** Concave : chute forte sur les 20 % les plus négatifs, puis montée presque linéaire jusqu’à des valeurs proches de 0, et une petite queue positive à l’extrême droite.
- **`ssr`.** La plus proche d’une droite, de ~3×10⁶ à ~2,5×10⁷. Le rayonnement solaire est la variable la plus « uniformément » répartie.
- **`str`.** Montée régulière, avec un changement de pente vers 80 % : les 20 % les moins négatifs se redressent. On retrouvera cette bosse sur l’histogramme.
- **`ro` et `tp`.** Ligne confondue avec zéro jusqu’à environ 90–95 %, puis mur vertical. La quasi-totalité de l’information tient dans les 5 à 10 % d’observations les plus fortes. C’est pour cela que la variance après mise à l’échelle min-max est minuscule (`ro` 4,8×10⁻⁵, `tp` 0,0017) : le maximum, très rare, étire l’échelle et écrase le reste.

**À retenir.** Toute statistique qui suppose une répartition à peu près symétrique (`ro`, `tp`, `slhf`, `e`) décrit mal le corps des données. Pour ces quatre variables, un rang (Spearman) ou une transformation est plus honnête qu’une corrélation linéaire.

---

## 3. Histogrammes, moyenne, médiane, mode

![Histogrammes avec moyenne, médiane et mode](figures/lecture/03_histogrammes.png)

Trait rouge = moyenne, tirets verts = médiane, pointillés violets = mode (sommet de l’histogramme à 50 classes), bande orange = moyenne ± un écart-type.

Asymétrie et aplatissement calculés sur le tableau bivarié (même forme que sur le tableau univarié) :

| Variable | Skewness | Kurtosis | Lecture |
|---|---:|---:|---|
| `t2m` | −0,12 | −1,16 | À peu près symétrique, mais **plat** (kurtosis négatif) |
| `d2m` | +0,29 | +0,33 | Proche d’une cloche |
| `sp` | −0,84 | +0,47 | Queue à gauche, encore acceptable |
| `u10` | +0,08 | +0,15 | La plus gaussienne |
| `v10` | −0,24 | +0,04 | Proche d’une cloche |
| `sshf` | −0,46 | +0,26 | Légère queue à gauche |
| `ssr` | −0,20 | −0,84 | Un peu plat |
| `str` | +0,58 | −0,52 | Queue à droite, un peu plat |
| `slhf`, `e` | −4,1 | +20 | Très asymétriques, pic et queue |
| `tp` | +5,7 | +47 | Pic en 0, queue à droite |
| `ro` | +37 | +2 600 | Cas extrême |

Lecture panneau par panneau :

- **`t2m`.** L’histogramme est large et méplat entre environ 10 et 35 °C, avec un sommet vers 34–40 °C. La moyenne (24,0 °C) et la médiane (24,3 °C) sont au centre, le mode (34,1 °C) est sur le pic chaud. Ce n’est pas une contradiction : la distribution a un plateau, et la classe la plus haute de l’histogramme gagne. La bande ±σ couvre à peu près 15–33 °C. On voit le mélange Sahara / saisons, pas une seule normale.
- **`d2m`.** Vraie cloche, centrée vers 0–2 °C. Moyenne (1,5 °C), médiane (1,4 °C) et mode (0,8 °C) sont voisins. La bande orange contient l’essentiel du pic. Queue un peu plus longue à droite (air humide).
- **`sp`.** Cloche décalée vers 96–98 kPa, avec une aile gauche jusqu’à 80 kPa. Le mode (96,7 kPa) et la médiane (95,9 kPa) sont à droite de la moyenne (95,2 kPa) : les reliefs tirent la moyenne vers le bas.
- **`u10`.** Cloche légèrement à gauche de 0. Moyenne −1,0 m/s, médiane −1,0 m/s, mode près de 0. La bande orange va d’environ −2,6 à +0,6 m/s.
- **`v10`.** Cloche plus étroite, centrée juste sous 0 (moyenne −0,51, médiane −0,46, mode −0,44). Les trois repères se confondent.
- **`slhf` et `e`.** Une seule barre écrase l’échelle, collée à 0 (plusieurs centaines de milliers d’observations). La moyenne est tirée à gauche par la queue et tombe dans une zone presque vide ; la médiane et le mode restent dans le pic. La bande orange est large par rapport au pic et ne décrit pas « l’observation typique ».
- **`sshf`.** Cloche large, du côté négatif, moyenne et médiane presque superposées vers −3,5×10⁶, mode un peu plus à gauche (−4,1×10⁶). Petite aile positive.
- **`ssr`.** Histogramme large, légèrement méplat, sommet vers 1,6×10⁷. La moyenne (1,36×10⁷) est à gauche de la médiane (1,41×10⁷) et du mode (1,61×10⁷) : les hivers peu ensoleillés tirent la moyenne.
- **`str`.** Deux masses. Un pic principal vers −1,1×10⁷ et une bosse secondaire vers −0,6×10⁷. La moyenne (−9,6×10⁶) et la médiane (−1,0×10⁷) tombent entre les deux, le mode (−1,2×10⁷) sur le pic de gauche. Ce n’est pas une seule population : la bosse de droite réapparaît dans la rupture 2022–2024 de la série mensuelle.
- **`ro` et `tp`.** Une barre en 0 et rien de visible ensuite, alors que le maximum est loin. Moyenne, médiane et mode sont empilés sur le bord gauche. L’histogramme en 50 classes ne montre pas les événements : ils sont trop rares pour former un deuxième pic.

**À retenir.** Huit variables peuvent supporter une lecture « moyenne ± écart-type ». Quatre (`slhf`, `e`, `ro`, `tp`) non. `t2m` est symétrique mais trop plate pour être traitée comme une gaussienne, et `str` a deux bosses.

---

## 4. Matrices de corrélation Pearson et Spearman

![Pearson et Spearman](figures/lecture/04_correlations.png)

Chaque case est la corrélation entre deux colonnes, de −1 (bleu) à +1 (rouge). À gauche Pearson (relation linéaire, sensible aux extrêmes). À droite Spearman (relation monotone sur les rangs). La dernière ligne et la dernière colonne sont la cible `t2m_next`.

Les deux matrices racontent la même histoire sur le bloc radiatif, et divergent sur le bloc eau.

**Bloc radiatif, commun aux deux méthodes.**

- `ssr`–`sshf` ≈ −0,93 à −0,95 : plus le solaire net est fort, plus le flux sensible est négatif (la surface chauffe l’air).
- `ssr`–`str` ≈ −0,86 : soleil fort et déficit infrarouge fort vont ensemble.
- `sshf`–`str` ≈ +0,68 à +0,75.
- `t2m` avec ce bloc : +0,61 avec `ssr`, −0,57 à −0,65 avec `sshf` et `str`.

**Avec la cible `t2m_next` (Spearman, la référence retenue).**

| Force | Variables |
|---|---|
| Forte, \|ρ\| ≥ 0,65 | `t2m` +0,87 ; `str` −0,72 ; `ssr` +0,71 ; `sshf` −0,69 |
| Faible, 0,10 à 0,30 | `u10` −0,20 ; `ro` −0,19 ; `tp` −0,18 ; `slhf` et `e` −0,16 ; `d2m` +0,11 |
| Quasi nulle | `sp` +0,07 ; `v10` +0,06 |

La température du mois courant est, de loin, le meilleur précurseur de la température du mois suivant. Le rayonnement et le flux sensible apportent une information de même sens, en partie redondante avec `t2m`. La pression et le vent nord-sud n’annoncent presque rien.

**Là où Pearson et Spearman se contredisent.**

- `slhf` et `e` avec `t2m_next` : Pearson **+0,19**, Spearman **−0,16**. Le signe change. Les quelques épisodes d’évaporation extrême (très négatifs) tirent la droite de Pearson dans un sens ; le rang de la masse des points, collée à 0, donne l’autre sens. Aucun des deux chiffres n’est une pente exploitable. On le voit sur le nuage de points suivant.
- `slhf`–`e` = **1,00** dans les deux matrices. Ce n’est pas une corrélation météorologique : l’évaporation est le flux latent divisé par la chaleur latente de vaporisation. Garder les deux, c’est compter deux fois la même colonne. La PCA le confirme : PC12 a une valeur propre nulle.
- `ro`–`tp` : Pearson 0,53, Spearman **0,98**. En rang, le ruissellement suit les pluies. En valeur brute, quelques pics de `ro` cassent la droite, d’où le Pearson plus faible.
- `tp` avec `slhf` : Pearson −0,77, Spearman −0,74. Lien fort et stable : les mois pluvieux sont ceux où le flux latent s’écarte de zéro.

**À retenir.** Spearman est la matrice à citer. Le jeu contient un axe « chaleur / rayonnement » lié à la cible, et un axe « eau » (`tp`, `ro`, `slhf`, `e`) mal décrit par une droite. `e` peut être retiré sans perte d’information.

---

## 5. Nuages de points : chaque variable contre la cible

![Variables contre t2m du mois suivant](figures/lecture/05_scatter_cible.png)

5 000 points tirés au hasard. Abscisse = variable du mois courant, ordonnée = `t2m_next` (°C). Le Spearman du titre est celui de la matrice, calculé sur les 759 500 lignes.

- **`t2m` (0,87).** Bande épaisse qui monte de ~5 °C à ~40 °C. Ce n’est pas une droite fine : pour une même température actuelle, le mois suivant peut être plusieurs degrés plus chaud ou plus froid. Le nuage a la forme d’une boucle (printemps au-dessus, automne en dessous). `month` est donc nécessaire en plus de `t2m`.
- **`d2m` (0,11).** Ovale sans pente, de −15 à +20 °C en abscisse et de 5 à 40 °C en ordonnée. Le point de rosée du mois courant ne classe pas la température du mois suivant.
- **`sp` (0,07).** Rectangle incliné très faiblement. On devine un bord : au-dessus de ~95 kPa la cible couvre toute la gamme ; sous 85 kPa les points sont plus rares. Pas de relation utile.
- **`u10` (−0,20).** Nuage large. Les vents d’ouest marqués (`u10` > 0) sont un peu moins souvent associés aux cibles très chaudes. La pente est réelle mais noyée dans le bruit.
- **`v10` (0,06).** Disque. Aucune direction.
- **`slhf` (−0,16) et `e` (−0,16).** Un mur vertical contre 0, sur toute la gamme de `t2m_next`, et quelques points isolés très à gauche, plutôt entre 15 et 35 °C. Le coefficient, faible et de signe instable (voir Pearson), vient de ce mur et de ces points. Il n’y a pas de tendance à montrer à un lecteur.
- **`sshf` (−0,69).** Descente nette : vers −1×10⁷ la cible est souvent au-dessus de 30 °C, vers 0 elle redescend vers 10–20 °C. Deux amas se superposent (saisons ou régions).
- **`ssr` (0,71).** Montée nette, de ~5×10⁶ / 10 °C jusqu’à ~2×10⁷ / 35 °C, avec deux lobes. Le solaire du mois courant accompagne la température du mois suivant, sans la déterminer seul.
- **`str` (−0,72).** Descente, miroir de `ssr`. Le lobe le plus à droite (moins négatif, vers −0,4×10⁷) est plus dispersé : c’est la deuxième bosse de l’histogramme.
- **`ro` (−0,19) et `tp` (−0,18).** Mur en 0 identique à `slhf`, avec une poignée de points jusqu’à 0,005 m. Les fortes pluies ne s’alignent pas avec une température du mois suivant. Le Spearman légèrement négatif veut surtout dire que les rangs élevés de pluie tombent un peu plus souvent hors des mois très chauds.

**À retenir.** Quatre nuages ont une forme (`t2m`, `ssr`, `str`, `sshf`). Les huit autres sont soit un disque, soit un mur en zéro. Colorier ces quatre nuages par mois séparerait la boucle saisonnière du signal réellement précurseur.

---

## 6. Les six paires les plus liées entre elles

![Paires les plus corrélées](figures/lecture/06_scatter_paires.png)

Les six plus grands |Spearman| hors diagonale, sur un échantillon de 5 000 points.

1. **`slhf` contre `e` (1,00).** Un segment de droite parfait, de (−1×10⁷ ; −0,004) à (0 ; 0). Les deux séries sont la même quantité dans deux unités. On n’en garde qu’une.
2. **`ro` contre `tp` (0,98).** Un faisceau part de l’origine le long d’une droite, puis s’évase : à pluie égale, le ruissellement peut être presque nul ou atteindre ~0,006 m. Le rang est presque parfait (d’où 0,98), la proportion ne l’est pas (Pearson 0,53). Physiquement : il pleut, une part ruisselle, le reste s’infiltre ou s’évapore, et quelques cellules produisent un ruissellement disproportionné.
3. **`sshf` contre `ssr` (−0,95).** Bande étroite qui descend. Le solaire fixe presque le flux sensible. Le nuage s’épaissit aux faibles `ssr` (hiver, ciel couvert).
4. **`ssr` contre `str` (−0,86).** Deux bandes parallèles qui descendent, pas une seule. À ensoleillement égal, deux régimes de déficit infrarouge coexistent (saison, ou humidité, ou la rupture de série vue plus loin). Le coefficient est fort, la relation n’est pas une droite unique.
5. **`sshf` contre `str` (0,75).** Deux bandes qui montent, les mêmes deux populations. Les flux sensible et thermique partagent un axe, avec un décalage de régime.
6. **`slhf` contre `tp` (−0,74).** La masse est en (0 ; 0). Quand `tp` augmente, `slhf` devient plus négatif : les mois pluvieux sont aussi des mois où l’évaporation s’éloigne de zéro. Beaucoup de points restent à `tp` ≈ 0 avec un `slhf` déjà négatif (évaporation sans pluie du mois, sur sol encore humide ou par la rosée). La liaison est réelle et bornée par le mur de zéros.

**À retenir.** Trois redondances à trancher avant une modélisation : `e` ≡ `slhf`, `ro` ≈ `tp`, et le trio `ssr` / `sshf` / `str`. Les garder toutes les trois fait porter à la PCA un axe qui compte plusieurs fois le même phénomène.

---

## 7. Diagrammes quantile-quantile de paires de même nature

![Q-Q plots](figures/lecture/07_qqplots.png)

On compare les quantiles de deux variables qui ont la même unité. Si les points suivent la droite rouge `y = x`, les deux distributions sont les mêmes. Un décalage parallèle = même forme, autre niveau. Une pente ≠ 1 = même forme, autre dispersion. Une courbe = formes différentes.

- **`t2m` contre `d2m`.** Les points restent sous la droite et se courbent. Le point de rosée est toujours plus froid que l’air (écart de 10 à 25 °C), son étendue est plus courte (environ −10 à +18 °C contre 0 à 40 °C), et la courbe s’aplatit : `d2m` ne suit pas la queue chaude de `t2m`. L’air saharien est loin de la saturation. Les deux températures ne sont pas interchangeables.
- **`u10` contre `v10`.** Presque une droite, de pente inférieure à 1, qui coupe `y = x` près de l’origine. Même forme. `v10` est moins dispersé : ses quantiles extrêmes valent environ ±2,5 m/s quand ceux de `u10` vont vers ±4 m/s et au-delà. Le vent d’est-ouest porte plus de variabilité que le vent nord-sud.
- **`ssr` contre `str`.** Le nuage est entièrement sous la droite, dans un autre cadran de signe : `ssr` est positif (environ 0,3×10⁷ à 2,5×10⁷), `str` est négatif (environ −1,5×10⁷ à −0,3×10⁷). Les comparer sur la droite `y = x` montre surtout qu’elles n’ont pas le même sens physique, même si l’unité (J/m²) est commune. La forme est en plus coudée, à cause des deux régimes déjà vus.
- **`slhf` contre `sshf`.** Courbe en crosse. Sur la gauche, `slhf` décroche jusqu’à −1×10⁷ alors que `sshf` est déjà vers −1×10⁷ : les queues ne se correspondent pas. Sur la droite, `slhf` est empilé près de 0 pendant que `sshf` continue de s’étaler de −0,6×10⁷ à 0. Le flux latent est une distribution à pic, le flux sensible une distribution étalée. Les mettre dans un même modèle sans transformation leur donne des rôles très différents.

**À retenir.** Seuls `u10` et `v10` ont vraiment la même forme. `t2m` et `d2m` partagent l’unité et pas la distribution. Les deux paires de flux partagent l’unité et pas le signe, ni la forme.

---

## 8. Boîtes à moustaches par classe de température

![Boîtes par classe Low / Medium / High](figures/lecture/08_boxplots_classes.png)

Même boîte que la figure 1, séparée selon la classe de `t2m_next`. Une variable discrimine la classe quand les trois boîtes se décalent et se recouvrent peu.

Le test t de Welch dit que **toutes** les moyennes diffèrent (p-value affichée à 0), parce qu’il y a des centaines de milliers de lignes. Le critère utile est le d de Cohen sur la paire Low contre High : |d| ≈ 0,2 petit, 0,5 moyen, 0,8 grand.

| Variable | Sens Low → High | Cohen d (Low − High) | Ce que montrent les boîtes |
|---|---|---:|---|
| `t2m` | monte | −4,42 | Trois boîtes étagées. Low autour de 12 °C (moustache jusqu’à ~24 °C), Medium autour de 20 °C, High autour de 32 °C (plancher vers 18 °C). Le mois courant et le mois suivant se recouvrent : un mois à 22 °C peut précéder un Low ou un High. Meilleure séparation du jeu, et elle reste incomplète. |
| `ssr` | monte | −2,89 | Low centré vers 0,9×10⁷, Medium vers 1,3×10⁷, High vers 1,7×10⁷. Recouvrement des moustaches, médianes bien séparées. |
| `sshf` | descend | +2,70 | Low près de −0,1×10⁷, High près de −0,5×10⁷. Le flux sensible devient plus négatif quand le mois suivant est chaud. |
| `str` | descend | +2,23 | Même étagement que `sshf`, de environ −0,7×10⁷ (Low) à −1,2×10⁷ (High). |
| `u10` | descend, puis stagne | +0,74 | Low est décalé vers le haut (médiane proche de 0, voire positive). Medium et High se ressemblent, tous deux négatifs. Le vent d’est distingue surtout les mois qui précèdent un Low. |
| `tp` | descend | +0,65 | La boîte Low est un peu plus haute et porte les points jusqu’à 0,012 m. Medium et High sont écrasés à 0, avec des extrêmes plus petits. Il pleut davantage avant un mois frais. |
| `slhf`, `e` | boîte inchangée, queue plus longue en High | −0,61 | Les trois boîtes restent collées à 0. La classe High a la moustache négative la plus longue. L’effet est dans les extrêmes, pas dans la médiane. |
| `sp` | très léger | −0,27 | Trois boîtes presque superposées vers 95–97 kPa. Low a une médiane un peu plus basse. |
| `ro` | queue seulement | +0,23 | Boîtes invisibles. Les points extrêmes sont plus nombreux et plus hauts en Low. |
| `d2m` | aucun | −0,15 | Trois boîtes identiques, de −5 à +8 °C, mêmes moustaches. |
| `v10` | aucun | −0,10 | Trois boîtes identiques autour de 0. |

**À retenir.** Le mois suivant chaud est annoncé par un mois courant déjà chaud, un solaire fort, un flux sensible et un infrarouge plus négatifs. Le point de rosée, la pression et `v10` ne séparent pas les classes. Les variables d’eau ne séparent que par leurs queues.

---

## 9. Classe de température selon le mois

![Classes empilées par mois](figures/lecture/09_classe_par_mois.png)

Barres empilées à 100 %. Bleu = Low, gris = Medium, rouge = High. Le mois en abscisse est le mois courant ; la couleur est la classe du **mois suivant**.

Test du chi-deux sur le tableau 12 × 3 : χ² = 723 935, 22 degrés de liberté, p-value = 0, V de Cramér = **0,69**. L’effectif attendu minimal est 9 237, très au-dessus de 5 : le test est valide. Avec cet effectif, la p-value ne veut plus rien dire ; le V de Cramér, lui, dit que le lien est fort (0 = indépendance, 1 = lien parfait).

Parts lues sur le graphique (classe du mois d’après) :

| Mois courant | Classe décrite | Low | Medium | High |
|---|---|---:|---:|---:|
| Janvier | février | 34 % | 66 % | 0 % |
| Février | mars | 13 % | 86 % | ~1 % |
| Mars | avril | 4 % | 73 % | 23 % |
| Avril | mai | ~0 % | 33 % | 67 % |
| Mai | juin | 0 % | 12 % | 88 % |
| Juin | juillet | 0 % | 4 % | 96 % |
| Juillet | août | 0 % | 6 % | 94 % |
| Août | septembre | 0 % | 18 % | 82 % |
| Septembre | octobre | ~0 % | 72 % | 28 % |
| Octobre | novembre | 13 % | 87 % | 0 % |
| Novembre | décembre | 58 % | 42 % | 0 % |
| Décembre | janvier | 70 % | 30 % | 0 % |

Le cycle est celui de l’Algérie, décalé d’un mois. High n’existe quasiment que pour les cibles de mai à octobre. Low n’existe quasiment que pour les cibles de novembre à mars, et culmine pour janvier (barre de décembre). Medium occupe les transitions (février–avril et octobre–novembre) et reste présent toute l’année comme classe intermédiaire, surtout au nord et en altitude, là où l’été ne franchit pas 27 °C.

**À retenir.** La classe est d’abord un calendrier. Un modèle qui ne voit pas le mois peut sembler fort simplement parce que `t2m`, `ssr` et `sshf` portent déjà la saison. Pour juger un vrai pouvoir prédictif, il faudra comparer à une baseline « le mois suffit ».

---

## 10. Clustermap des corrélations de Spearman

![Clustermap](figures/lecture/10_clustermap.png)

Même matrice Spearman que la figure 4, réordonnée par un dendrogramme (liaison moyenne). Deux variables qui se rejoignent bas dans l’arbre sont proches. La couleur va de −1 à +1.

L’arbre se lit en quatre familles.

1. **`slhf` et `e`**, soudés tout en haut à gauche, corrélation 1,00. Branche suivante : ils s’opposent à `ro` et `tp` (−0,74).
2. **`sshf`, `str`, puis `t2m` et `ssr`.** `sshf` et `str` sont liés (+0,75) et tous deux opposés à `ssr` (−0,95 et −0,86). `t2m` rejoint `ssr` (+0,61) et s’oppose à `sshf` (−0,61) et `str` (−0,65). C’est la famille « chaleur ».
3. **`sp`**, proche de la famille radiative mais avec des corrélations faibles (au plus 0,28 avec `sshf`). La pression est presque isolée.
4. **`v10`, `d2m`, `u10`, puis `ro` et `tp`.** `d2m` et `u10` se rejoignent (0,42), `ro` et `tp` se rejoignent (0,98), et ce groupe « humidité / vent / pluie » ne rejoint le reste de l’arbre qu’en dernier. `v10` est le plus isolé du groupe (corrélations ≤ 0,27).

**À retenir.** Le dendrogramme justifie un résumé en deux ou trois blocs : eau (`slhf`/`e`/`ro`/`tp`), rayonnement et température (`ssr`/`sshf`/`str`/`t2m`), et un reste peu structuré (`sp`, `u10`, `v10`, `d2m`). C’est exactement ce que la PCA va séparer en PC1 et PC2.

---

## 11. Profil moyen standardisé par classe

![Profil des classes](figures/lecture/11_profil_classes.png)

Chaque case est la moyenne de la variable **centrée-réduite** dans la classe. 0 = la classe est au niveau du jeu entier. +1 = un écart-type au-dessus. Le bleu est en dessous de la moyenne, le rouge au-dessus.

| Variable | Low | Medium | High | Lecture |
|---|---:|---:|---:|---|
| `t2m` | −1,27 | −0,38 | +0,90 | La plus grande amplitude. Monotone. |
| `ssr` | −1,10 | −0,27 | +0,72 | Deuxième amplitude. Monotone. |
| `sshf` | +1,07 | +0,21 | −0,64 | Miroir de `ssr`. |
| `str` | +0,95 | +0,30 | −0,69 | Même miroir. |
| `u10` | +0,56 | −0,06 | −0,15 | Low se détache, Medium ≈ High. |
| `tp` | +0,54 | +0,05 | −0,26 | Plus de pluie avant un mois frais. |
| `slhf`, `e` | −0,31 | −0,09 | +0,21 | Petit décalage, identique pour les deux. |
| `sp` | −0,21 | +0,02 | +0,06 | Presque plat. |
| `ro` | +0,19 | +0,02 | −0,09 | Faible. |
| `v10` | +0,03 | −0,13 | +0,13 | Pas de sens monotone. |
| `d2m` | −0,00 | −0,11 | +0,11 | N’écarte aucune classe. |

Medium est toujours entre Low et High, et souvent proche de 0. La classe du milieu est un entre-deux, pas un régime à part.

**À retenir.** Quatre variables portent la classe : `t2m`, `ssr`, `sshf`, `str`. `u10` et `tp` aident surtout à reconnaître Low. Le reste peut être décrit comme non discriminant à l’échelle de la moyenne.

---

## 12. Variance expliquée par la PCA (éboulis)

![Scree plot](figures/lecture/12_scree.png)

Les 12 variables sont centrées-réduites, puis la PCA construit 12 axes orthogonaux, du plus informatif au moins informatif. À gauche, la part de variance de chaque axe. À droite, la part cumulée. Le trait rouge est le seuil de 90 %.

| Axe | Valeur propre | % variance | % cumulé |
|---|---:|---:|---:|
| PC1 | 3,65 | 30,4 | 30,4 |
| PC2 | 3,16 | 26,3 | 56,8 |
| PC3 | 1,44 | 12,0 | 68,7 |
| PC4 | 1,07 | 8,9 | 77,6 |
| PC5 | 0,79 | 6,6 | 84,2 |
| PC6 | 0,73 | 6,1 | 90,3 |
| PC7 | 0,50 | 4,2 | 94,5 |
| PC8 | 0,29 | 2,4 | 96,9 |
| PC9 | 0,21 | 1,8 | 98,6 |
| PC10 | 0,16 | 1,4 | 100,0 |
| PC11 | ~0 | 0,01 | 100 |
| PC12 | 0 | 0 | 100 |

PC1 et PC2 portent à eux deux **57 %**. Le coude visuel est après PC2 : PC3 tombe à 12 %. Le critère de Kaiser (valeur propre > 1) garde **4** axes, soit 78 %. Le seuil de 90 % demande **6** axes : c’est ce choix (`K_PC = 6`) qui sert ensuite au K-Means.

PC11 et PC12 sont vides. PC12 vaut 0 parce que `e` est une copie de `slhf`. PC11 est presque vide pour la même raison de redondance (le couple `ro`/`tp` et le trio radiatif n’ajoutent pas une douzième dimension indépendante).

**À retenir.** On ne résume pas le jeu en deux axes sans perdre plus de 40 % de la variance. Deux axes suffisent pour **voir** la structure ; six axes sont le compromis chiffré à 90 % pour le clustering.

---

## 13. Poids des variables (loadings) sur PC1 à PC4

![Loadings](figures/lecture/13_loadings.png)

Chaque case est le poids de la variable dans l’axe. Un poids grand en valeur absolue construit l’axe. Le signe est une orientation : on peut retourner un axe, la physique se lit dans les oppositions.

**PC1 (30 %), l’axe de l’eau.** `tp` +0,44, `str` +0,34, `ro` +0,28, `u10` +0,23 d’un côté ; `slhf` et `e` −0,44 de l’autre. Un PC1 élevé est un mois pluvieux, avec ruissellement, évaporation forte (flux latent très négatif) et un peu plus de vent d’ouest. `t2m` n’y pèse que −0,29 : cet axe n’est pas l’axe de la température.

**PC2 (26 %), l’axe radiatif et thermique.** `ssr` +0,51 et `t2m` +0,32 en haut ; `sshf` −0,49, `str` −0,35, `slhf` et `e` −0,25 en bas. Un PC2 élevé est un mois chaud et ensoleillé, avec un flux sensible très négatif. C’est l’axe qui porte la cible.

**PC3 (12 %), pression et humidité.** `sp` +0,63 et `d2m` +0,48, opposés à `u10` −0,38 et `v10` −0,30. Un PC3 élevé : pression de surface plus forte et air plus proche de la saturation, avec des vents plus faibles. On y retrouve le relief et les masses d’air, que PC1 et PC2 ne voyaient pas.

**PC4 (9 %), le vent méridien.** `v10` +0,65 et `d2m` +0,45, opposés à `ro` −0,32. Axe secondaire, surtout la composante nord-sud et le point de rosée.

`slhf` et `e` ont des poids identiques sur les quatre axes. `sp` et `v10`, presque absents de PC1 et PC2, existent dans PC3 et PC4 : les enlever appauvrirait le résumé à 4 axes, pas le dessin 2D.

**À retenir.** PC1 = épisode d’eau. PC2 = chaleur et soleil. La température à prédire vit sur PC2. Les événements rares de pluie vivent sur PC1 et dominent visuellement le plan, alors qu’ils ne sont pas le signal de la cible.

---

## 14. Projection des observations dans le plan PC1–PC2

![PCA colorée par classe et par mois](figures/lecture/14_pca_2d.png)

20 000 points. PC1 en abscisse (30,4 %), PC2 en ordonnée (26,3 %).

La forme est la même sur les deux panneaux : un noyau dense en forme de coin, centré vers PC1 ≈ 0 et PC2 entre −4 et +3, puis une traîne qui s’étire vers la droite jusqu’à PC1 ≈ 20–25 et vers le haut jusqu’à PC2 ≈ 10. La traîne est l’axe eau de la figure 13 : quelques mois × points de grille avec de fortes précipitations.

**Couleur = classe de `t2m_next` (à gauche).**

- High (rouge) occupe le haut du noyau (PC2 positif) et s’arrête assez tôt vers la droite.
- Low (bleu) occupe le bas du noyau (PC2 négatif) et une partie de la traîne.
- Medium (vert) est partout : il recouvre le rouge, le bleu, et il est majoritaire dans la traîne.

Le dégradé suit PC2, avec un large recouvrement. On ne peut pas découper les trois classes par une droite dans ce plan. C’est cohérent avec les boîtes de `t2m` qui se chevauchent, et avec le fait que PC1 (la direction la plus visible) n’est pas la direction de la température.

**Couleur = mois courant (à droite, échelle HSV).**

Le noyau est organisé verticalement par la saison. Le bas (PC2 négatif) est rouge-orange : mois 1, 2 et 12, l’hiver. Le haut est cyan-vert : mois 6 à 8, l’été. Les intersaisons se mélangent au centre. La traîne de droite, elle, porte toutes les couleurs : un épisode pluvieux extrême n’appartient pas à un seul mois.

**À retenir.** Le plan se lit en deux questions indépendantes. « Fait-il chaud ? » se répond en haut ou en bas (PC2, et donc la saison). « Est-ce un épisode d’eau extrême ? » se répond à droite (PC1). La classe de température n’occupe qu’une de ces deux questions, et elle y est floue.

---

## 15. Biplot PC1–PC2

![Biplot](figures/lecture/15_biplot.png)

Les points gris sont les mêmes observations. Les flèches rouges sont les variables, mises à l’échelle pour être lisibles sur le nuage. Une flèche longue pèse fort dans le plan. Deux flèches dans le même sens sont corrélées positivement. Deux flèches opposées sont corrélées négativement. L’angle droit veut dire « peu liées dans ce plan » (pas « indépendantes dans les 12 dimensions »).

- **`ssr`** monte presque verticalement. **`t2m`** monte vers la gauche. **`sshf`** descend verticalement. **`str`** descend vers la droite. Ce quartet est l’axe vertical : soleil et température d’un côté, flux sensible et infrarouge de l’autre.
- **`slhf` et `e`** sont la même flèche, vers le bas-gauche. Elles s’opposent à la fois à la température et à la pluie.
- **`tp`** est la plus longue flèche vers la droite, suivie de **`ro`**, **`u10`**, **`d2m`** et **`v10`**, en éventail dans le quart haut-droit. La traîne grise pointe exactement dans la direction de `tp`. Les points extrêmes à droite sont des cellules très pluvieuses.
- **`sp`** est une flèche courte vers le bas. La pression apporte peu dans ce plan, comme le disaient les loadings (poids −0,05 et −0,16).

Le coin dense gris se trouve du côté opposé à `tp` : l’état ordinaire du pays est un état sans pluie notable. La traîne est l’exception.

**À retenir.** Le biplot relie les trois figures précédentes. La verticale est le cycle chaud / froid. L’horizontale est la pluie. `e` n’a pas de flèche propre. `sp` est le grand absent de ce portrait en deux dimensions.

---

## 16. Choix du nombre de groupes (coude et silhouette)

![Coude et silhouette](figures/lecture/16_coude_silhouette.png)

K-Means est lancé pour k de 2 à 8, sur les 6 premières composantes (celles qui atteignent 90 % de variance), sur un sous-échantillon de 50 000 lignes. À gauche, l’inertie (somme des carrés intra-groupes) : elle baisse quand on ajoute des groupes. À droite, la silhouette moyenne (à quel point un point est plus proche de son groupe que des autres) : plus elle est haute, plus les groupes sont séparés. Une silhouette vers 0,7 est nette ; vers 0,25, les groupes se touchent.

- **Coude.** L’inertie passe d’environ 415 000 (k = 2) à 305 000 (k = 3), puis la pente se calme : 275 000, 250 000, 225 000, 210 000, 195 000. La cassure la plus lisible est entre 2 et 3. Après, chaque groupe supplémentaire ne fait que grignoter.
- **Silhouette.** Maximum à **k = 3**, autour de **0,30**. k = 2 est vers 0,27. k = 4 et 5 redescendent vers 0,23, avec un petit rebond à 5 qui reste sous le maximum. k = 6 à 8 plafonnent vers 0,19–0,20.

0,30 est un maximum relatif, pas une séparation franche. Les groupes existent comme des régimes qui se touchent, pas comme des îlots.

**À retenir.** k = 3 est le choix cohérent avec les deux courbes. Il coïncide avec le nombre de classes de température, ce qui permettra de mesurer s’il retrouve ces classes. La silhouette annonce déjà que non, ou pas nettement.

---

## 17. Les trois groupes dans le plan PCA

![K-Means dans le plan PCA](figures/lecture/17_kmeans_pca.png)

Même plan que la figure 14, couleur = numéro de groupe (k = 3, ajusté sur les 6 composantes, affiché en PC1–PC2). Viridis : 0 en violet, 1 en turquoise, 2 en jaune.

Le nuage est coupé sans trou :

- **Groupe 0, violet**, en bas du noyau (PC2 négatif, PC1 proche de 0). C’est le côté `sshf` / `str` du biplot.
- **Groupe 1, turquoise**, en haut du noyau (PC2 positif). C’est le côté `ssr` / `t2m`.
- **Groupe 2, jaune**, toute la traîne de droite (PC1 élevé) et le raccord avec le noyau. C’est le côté `tp`.

Les frontières sont des contacts, pas des vides. Le jaune commence là où le noyau s’effiloche. Le violet et le turquoise se touchent autour de PC2 = 0. C’est l’image directe d’une silhouette de 0,30.

Part de chaque classe de température **à l’intérieur** du groupe (tableau croisé du notebook, en ligne) :

| Groupe | Low | Medium | High |
|---|---:|---:|---:|
| 0 | 29 % | 61 % | 10 % |
| 1 | 0 % | 27 % | 73 % |
| 2 | 36 % | 57 % | 7 % |

Indice de Rand ajusté entre groupe et classe : **0,294**. L’accord est faible à modéré. Le groupe 1 est le seul qui colle à une classe (High, et aucun Low). Le groupe 0 est un mélange Medium + Low. Le groupe 2 ne correspond à aucune classe.

Le paragraphe de synthèse du notebook inverse les groupes 0 et 1 par rapport à ce tableau et à cette figure (il attribue 73 % de High au groupe 0). La figure, le profil de la section suivante et le tableau imprimé sont d’accord entre eux : **c’est le groupe 1 qui est le régime chaud.**

**À retenir.** K-Means coupe le plan selon la géométrie (bas / haut / traîne), pas selon les trois classes. Il retrouve High dans le groupe du haut, et il isole les épisodes extrêmes dans un groupe à part, que le découpage Low / Medium / High ne sait pas nommer.

---

## 18. Profil moyen de chaque groupe

![Profil des clusters](figures/lecture/18_profil_clusters.png)

Même lecture que la figure 11 : moyenne centrée-réduite. Les colonnes sont les groupes 0, 1 et 2 de la figure précédente.

| Variable | Groupe 0 | Groupe 1 | Groupe 2 |
|---|---:|---:|---:|
| `t2m` | −0,68 | +0,72 | −0,88 |
| `d2m` | −0,37 | +0,16 | +1,24 |
| `sp` | +0,18 | −0,09 | −0,54 |
| `u10` | −0,03 | −0,10 | +0,94 |
| `v10` | −0,26 | +0,18 | +0,40 |
| `slhf` | +0,25 | +0,20 | −3,14 |
| `sshf` | +0,83 | −0,71 | −0,17 |
| `ssr` | −0,90 | +0,77 | +0,17 |
| `str` | +0,73 | −0,77 | +1,01 |
| `e` | +0,25 | +0,20 | −3,14 |
| `ro` | −0,09 | −0,10 | +1,31 |
| `tp` | −0,16 | −0,23 | +2,78 |

- **Groupe 0 — frais, peu ensoleillé.** `t2m` et `ssr` sous la moyenne, `sshf` et `str` au-dessus (flux moins négatifs, moins de déficit infrarouge extrême). Eau proche de la normale. C’est l’hiver et les marges fraîches : 61 % Medium, 29 % Low, 10 % High. La température moyenne du groupe, vers 24 − 0,68×8,8 ≈ 18 °C, tombe dans Medium, ce qui explique qu’il ne soit pas « le groupe Low ».
- **Groupe 1 — chaud et ensoleillé.** `t2m` +0,72 (vers 30 °C), `ssr` +0,77, `sshf` et `str` négatifs. Pluie plutôt sous la moyenne. 73 % High, 27 % Medium, 0 % Low. C’est le seul groupe aligné avec une classe.
- **Groupe 2 — épisode humide extrême.** `tp` à +2,8 écarts-types, `ro` à +1,3, `d2m` à +1,2, `slhf` et `e` à −3,1 (évaporation très forte), `u10` à +0,9 (anomalie de vent d’ouest), pression plus basse. La température y est basse (−0,88), mais la classe reste mixte (36 % Low, 57 % Medium, 7 % High) : ce groupe décrit un régime d’eau, pas un palier de température. Les effectifs de ce groupe sont ceux de la traîne, donc minoritaires ; leurs moyennes sont spectaculaires parce que les queues de `tp`, `ro`, `slhf` et `e` sont extrêmes.

**À retenir.** Les trois groupes sont trois régimes météorologiques : frais, chaud, et épisode pluvieux. L’ARI de 0,29 ne dit pas que le clustering a échoué. Il dit qu’on lui a demandé autre chose que ce que les classes mesurent. Le paragraphe du notebook qui appelle le groupe 0 « chaud » et le groupe 1 « frais » est à corriger : les chiffres de cette heatmap sont l’inverse.

---

## 19. Séries mensuelles (moyenne sur l’Algérie)

![Séries mensuelles](figures/lecture/19_series_mensuelles.png)

Chaque courbe est la moyenne spatiale du mois, de 2015 à septembre 2026. Le bandeau orange couvre janvier 2022 – décembre 2024. Attention aux unités : cette figure est calculée sur `ds_dz` **avant** la conversion en °C. `t2m` et `d2m` sont encore en **Kelvin**.

Ce qui suit le calendrier, bandeau compris :

- **`t2m`.** Oscillation stable entre ~285 K (12 °C, hivers) et ~308 K (35 °C, étés). Les étés 2022–2024 atteignent les mêmes sommets que les autres années. Aucune rupture visible.
- **`d2m`.** Oscillation entre ~268 K (−5 °C) et ~282 K (9 °C), plus irrégulière. Un pic isolé vers 285 K (~12 °C) en 2025, au-dessus du reste de la série. Le bandeau orange ne le déforme pas.
- **`sp`.** Miroir de la température : plus haute en hiver (~96 200 Pa), plus basse en été (~94 800 Pa). Le rythme tient sur toute la période.
- **`u10`.** Oscillation bruitée, le plus souvent négative (composante d’est), de −2,5 à +1,5 m/s. Pas de changement de régime dans le bandeau.
- **`v10`.** Bruit autour de −0,5 m/s, sans cycle annuel net. Conforme au nuage de points sans structure.

Ce qui casse dans le bandeau orange, puis revient :

- **`ssr`.** De 2015 à 2021, l’été culmine vers 1,8×10⁷ et l’hiver vers 1,0×10⁷. De 2022 à 2024, l’été tombe vers 0,6–0,7×10⁷, **sous** les hivers habituels. 2025 et 2026 retrouvent le cycle d’avant. La température, elle, n’a pas bougé. Un effondrement physique du solaire de cette ampleur se verrait sur `t2m`. Il ne s’y voit pas.
- **`str`.** Même fenêtre : la courbe remonte d’environ −1,1×10⁷ vers −0,4×10⁷, puis redescend en 2025. C’est la deuxième bosse de l’histogramme de `str`, et l’une des deux bandes du nuage `ssr`–`str`.
- **`sshf`.** Le cycle annuel reste visible, mais les étés du bandeau sont moins négatifs (vers −1×10⁶ au lieu de −2×10⁶) et la forme se tasse.
- **`slhf` et `e`.** De 2022 à début 2024, les deux courbes se rapprochent de 0 (moins d’évaporation), puis un creux très marqué apparaît en 2025 (vers −1,2×10⁶ pour `slhf` et −5×10⁻⁴ m pour `e`), plus profond que le reste de la série. Les deux courbes restent superposées : la copie `slhf` ≡ `e` vaut aussi dans le temps.
- **`ro` et `tp`.** Pic en 2015, puis un régime modéré jusqu’en 2021. Le bandeau est presque à plat, proche de 0. Reprise en 2025–2026, avec un pic de `tp` vers 6×10⁻⁴ m. Le ruissellement suit la pluie avec un niveau plus bas.

**À retenir.** Le bandeau 2022–2024 est une rupture de série sur les flux (`ssr`, `str`, `sshf`, `slhf`, `e`) et sur l’eau (`tp`, `ro`), pendant que la température, le point de rosée, la pression et le vent continuent leur cycle. C’est la signature d’un problème de traitement (accumulation, facteur, mois incomplets, fusion de fichiers), à contrôler avant d’interpréter une tendance climatique. Tant que ce point n’est pas tranché, les corrélations de `ssr`, `str` et `sshf` avec `t2m` mélangent un signal saisonnier réel et trois années suspectes. La double bosse de `str` et les deux bandes des nuages radiatifs viennent en partie de là.

---

## 20. Zone d’étude

![Carte de la zone](figures/lecture/20_carte_zone.png)

Le polygone bleu est l’Algérie. Le rectangle rouge pointillé est la boîte de téléchargement : latitude 18,9° à 37,1°, longitude −8,7° à 12,0°.

La boîte contient tout le pays et une marge : mer Méditerranée au nord, Atlantique au nord-ouest, et des portions des pays voisins. Elle est nécessaire parce que la requête ERA5 se fait sur un rectangle. Le masque du polygone, appliqué ensuite, retire cette marge. Le sud du rectangle (vers 19–20° N) coupe le Sahara à la frontière sud ; le nord (37° N) passe au-dessus de la côte.

**À retenir.** Toute statistique calculée avant le masque mélange terre algérienne, mer et pays voisins. Les chiffres de l’EDA (808 325 lignes) sont ceux d’après le masque.

---

## 21. Température du premier mois : grille brute et grille masquée

![t2m avant et après masque](figures/lecture/21_carte_t2m.png)

Les deux cartes sont `t2m` du premier pas de temps (janvier 2015), converties en °C.

**À gauche, grille native 0,1°, boîte brute.** L’échelle va d’environ −15 °C à +15 °C, et presque toute la carte est dans le rouge, entre 10 et 15 °C. On distingue la côte nord, le tracé du pays et quelques taches plus claires sur les reliefs. La mer et les pays voisins sont encore dans le champ. Le pas de 0,1° donne un champ lisse. En janvier, la boîte entière est fraîche et peu contrastée : le Sahara n’est pas encore chaud, le littoral non plus.

**À droite, grille 0,2°, masque Algérie.** L’échelle est resserrée, d’environ 2 °C à 16 °C, calculée sur les seules cellules conservées. Le gradient devient lisible :

- le Tell et l’Atlas saharien, au nord, sont en bleu, vers 2–8 °C ;
- les Hauts Plateaux sont dans les tons clairs, vers 8–12 °C ;
- le Sahara central et le sud sont en rouge, vers 14–16 °C, avec un maximum au sud de la carte ;
- une langue plus fraîche suit le Hoggar, au sud-est.

Le pas de 0,2° (facteur 2) pixellise un peu le champ et divise le volume par quatre. Le masque donne au domaine la forme du pays : les cellules hors polygone sont absentes, pas mises à zéro.

**À retenir.** Le contraste nord frais / sud doux dès janvier est la géographie que l’on retrouvera dans toutes les classes : High n’est pas seulement « l’été », c’est aussi « le sud », et Low n’est pas seulement « l’hiver », c’est aussi « le nord et le relief ». La pression de surface basse (queue gauche de `sp`) est le même relief.

---

## 22. Cellules du polygone sans valeur ERA5-Land

![Cellules NaN en frontière](figures/lecture/22_carte_nan.png)

Contour du pays, et en rouge les cellules de la grille native qui tombent dans le polygone mais n’ont pas de valeur de `t2m` au premier mois.

Le décompte imprimé est : **21 257** cellules dans le polygone, dont **12** sans valeur. Les 12 points sont alignés sur la côte méditerranéenne, du centre vers l’est, sur le trait de côte. ERA5-Land est un produit terrestre : les cellules dont le centre tombe côté mer, ou sur un masque terre/mer qui ne coïncide pas exactement avec le shapefile, restent vides. Aucun trou n’apparaît à l’intérieur du pays, ni sur la frontière terrestre.

Sur la grille réduite du premier mois, le notebook compte par ailleurs 9 568 cellules, dont 5 425 valides et 4 143 NaN. Ces 4 143 NaN sont les cellules du rectangle hors de l’Algérie (la marge marine et les pays voisins), pas les 12 cellules côtières. Les 12 manquants côtiers sont négligeables devant 21 257.

**À retenir.** Le masque est propre. La perte de données à l’intérieur du pays se limite à une douzaine de cellules de littoral. Elle ne crée pas de biais régional dans l’EDA.

---

## Synthèse pour la suite du travail

1. **La cible est saisonnière.** `t2m` du mois courant (Spearman 0,87), `ssr` (+0,71), `str` (−0,72) et `sshf` (−0,69) portent presque tout le lien avec `t2m_next`. Le mois, à lui seul, a un V de Cramér de 0,69 avec la classe. Une baseline calendaire est le minimum à battre.
2. **Deux axes, et ils ne disent pas la même chose.** PC2 est la chaleur et le soleil (57 % de la variance avec PC1, 26 % seul). PC1 est l’eau et les événements rares. Les classes se séparent, mal, le long de PC2.
3. **De la redondance mesurée.** `e` est `slhf`. `ro` suit `tp` en rang (0,98) sans être le même en valeur. `ssr`, `sshf` et `str` sont un seul bloc radiatif. La PCA a deux composantes nulles ou presque à cause de cela.
4. **Quatre variables ne se prêtent pas à une lecture gaussienne.** `slhf`, `e`, `ro` et `tp` ont 15 à 16 % d’outliers IQR, un pic en zéro et une queue. Pearson y change de signe ou de magnitude par rapport à Spearman. Leurs boîtes par classe sont illisibles ; leur information est dans les extrêmes, que le groupe K-Means n° 2 isole.
5. **k = 3 trouve des régimes, pas les classes.** Groupe 1 = chaud et ensoleillé (73 % High). Groupe 0 = frais (61 % Medium, 29 % Low). Groupe 2 = épisode pluvieux extrême, sans classe propre. ARI = 0,29, silhouette = 0,30. Le texte du notebook qui nomme le groupe 0 « chaud » est à inverser.
6. **La fenêtre 2022–2024 est à vérifier avant toute conclusion sur les flux.** Température, point de rosée, pression et vent gardent leur cycle. Solaire, infrarouge, flux de chaleur, évaporation, pluie et ruissellement décrochent puis reviennent en 2025. Tant que l’origine (fichiers, accumulation, facteur) n’est pas identifiée, les doubles bandes des nuages radiatifs et la deuxième bosse de `str` restent en partie suspectes.

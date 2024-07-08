import os
from jinja2 import Template
from openai import AzureOpenAI

patent= """DESCRIPTION

TITRE : SYSTEME DE GENERATION D’ONDES SONORES POUR AU MOINS DEUX ZONES
DISTINCTES D’UN MEME ESPACE ET PROCEDE ASSOCIE
DOMAINE TECHNIQUE
L&#39;invention se rapporte au domaine des systèmes de génération d’ondes sonores
permettant de sonoriser une pluralité de zones distinctes d’un même espace.
L’invention vise également un procédé de détermination des filtres associés.
L’invention peut être appliquée à un grand nombre de domaines techniques pour
lesquels il est recherché de sonoriser plusieurs zones distinctes d’un même espace,
comme une salle de cinéma diffusant un film en plusieurs langues simultanément,
un véhicule dans lequel plusieurs passagers écoutent des contenus sonores
différents, une zone de concert en plein air autour de laquelle les riverains sont
protégés des nuisances sonores…

TECHNIQUES ANTÉRIEURES
La création de zones recevant des contenus sonores différents au sein d’un même
espace est une problématique qui suscite beaucoup d’intérêt ces dernières années.
Au sens de l’invention, un « espace » peut correspondre à un espace délimité par
des frontières réelles ou virtuelles, tels qu’un habitacle de voiture ou un quartier
d’une ville. De la même manière, une « zone » est généralement délimitée par des
frontières virtuelles, comme par exemple une bulle sonore autour d’un bâtiment ou
autour de la tête d’un auditeur.
De manière générale, pour contrôler la propagation sonore au sein des différentes
zones de l’espace, il est connu de placer des barrières acoustiques physiques entre
les différentes zones et/ou d’installer des haut-parleurs au plus proche de chaque
zone et tout en limitant la propagation des ondes sonores qu’ils génèrent.
Lorsque ces deux méthodes ne peuvent être implémentées, par exemple car les
différentes zones sont trop proches et/ou que la puissance sonore attendue dans une
zone est trop importante, il est possible d’utiliser des moyens de traitement sonores
permettant de contrôler la propagation des ondes sonores à une zone cible, tout en
limitant la pollution sonore induite sur les autres zones sonorisées différemment.

2

Pour ce faire, tel qu’illustré sur la figure 1, une solution consiste à former au moins
un faisceau sonore directif Os1, Os2 au moyen d’un alignement de haut-parleurs
HP1 disposés dans un espace 1000 donné. Ces derniers sont orientés,
physiquement ou par l’ajout de délais temporels, en direction d’une zone cible à
sonoriser Z1, Z2.
Afin de créer un réseau de haut-parleurs directifs, les haut-parleurs HP1
constitutifs du réseau R1 sont espacés d’une distance inférieure à la moitié du
maximum des longueurs d’ondes générées par les haut-parleurs HP1 de sorte à
obtenir des interférences constructives et à former une onde sonore sensiblement
cylindrique. La formation d’un faisceau sonore directif, également appelée
« beamforming » dans la littérature anglo-saxonne, peut être obtenu à partir d’un
réseau de haut-parleurs alignés, aussi connue sous le nom de « line-array » dans la
littérature anglo-saxonne.
Lorsque plusieurs signaux U1, U2 sont transmises à un même réseau R1, il est
possible diriger, dans l’espace, chaque contenu sonore au sein de faisceaux
distincts Os1, Os2, en adaptant les délais temporels à l’entrée de chaque haut-
parleur constitutif du réseau. Cette technique est appelée « beam steering » dans la
littérature anglo-saxonne. Cependant, pour obtenir une qualité sonore satisfaisante
en basse-fréquences, les haut-parleurs de grave sont généralement volumineux, ce
qui complexifie leur intégration sous forme de réseaux. En outre, la distance entre
les haut-parleurs d’un réseau doit être adaptée en fonction de la gamme de
fréquences générée par ces haut-parleurs. Plus clairement, pour former un réseau
de haut-parleurs directifs, la distance entre des haut-parleurs aigu est plus faible
que la distance entre des haut-parleurs de grave. Ainsi, l’installation d’un réseau de
haut-parleurs de grave dans l’habitacle d’une voiture se révèle quasiment
impossible.
Une autre solution consiste à contrôler la sonorisation de plusieurs zones d’un
même espace en filtrant les signaux transmis aux haut-parleurs pour générer des
interférences destructives. Ces interférences destructives limitent la propagation
des ondes sonores en dehors des zones cibles. Cette méthode est connue sous le

3

terme « Crosstalk cancellation » dans la littérature anglo-saxonne, signifiant
« annulation des diaphonies ».
Pour ce faire, tel qu’illustré sur la figure 2 de l’art antérieur, un haut-parleur HP3,
HP4 peut être associé à chaque zone de sonorisation Z3, Z4 de l’espace 2000. Un
premier haut-parleur HP3 est en charge de sonoriser la première zone cible Z3
tandis qu’un second haut-parleur HP4 est en charge de sonoriser la seconde zone
cible Z4.
Cependant, sans aucun traitement préalable, les haut-parleurs HP3 et HP4
émettent des ondes sonores en direction des l’ensemble des zones Z3, Z4.
Ainsi, le premier haut-parleur HP3 émet une onde acoustique à la fois perçue au
niveau de la zone Z3, et dont la fonction de transfert est notée Os5 et à la fois au
niveau de la zone Z4, dont la fonction de transfert est notée Os6. De même, le
second haut-parleur HP4 émet une onde acoustique au niveau de la zone Z3 dont
la fonction de transfert est notée Os3 et à la fois au niveau de la zone Z4 dont la
fonction de transfert est notée Os4.
La matrice de propagation du son qui relie la pression acoustique induite par les
différentes ondes dans les zones Z3 et Z4 et les signaux U3 et U4 envoyés à
chaque haut-parleur HP3, HP4 peut alors s’écrire sous la forme :
[Math1]

Pour limiter la pollution sonore induite sur les autres zones Z3, Z4 sonorisées
différemment, chaque haut-parleur HP3, HP4 est associé à un filtrage F1, F2
commandant la génération d’ondes sonores « destructives » pour annuler les ondes
sonores indésirables Os6, Os3. Au sens de l’invention, chaque haut-parleur HP3,
HP4 forme classiquement une onde sonore pouvant être virtuellement subdivisée
en une onde sonore attendue dans une zone Z3, Z4 et éventuellement des ondes
sonores indésirables Os6, Os3 et/ou destructives. Une onde sonore « indésirables »
Os6, Os3 correspond à une onde sonore que l’on ne souhaite pas voir parvenir
jusqu’aux zones Z3, Z4. Une onde sonore « destructive » correspond à une onde
sonore configurée pour générer des interférences destructives au niveau d’une zone

4

cible de sorte que les ondes sonores indésirables Os6, Os3 et les ondes sonores
destructives s’annulent, au moins en majeure partie.
Pour ce faire, les filtres F1, F2 reçoivent en entrée les deux signaux U3, U4
représentant les contenus sonores attendus respectivement dans les deux zones Z3,
Z4. En fonction de l’évolution de ces signaux U3, U4 au cours du temps, chaque
filtre F1, F2 détermine le signal S1, S2 à transmettre à son haut-parleur HP3, HP4,
de sorte que ce haut-parleur HP3, HP4 génère des ondes sonores permettant de
sonoriser sa zone cible Z3, Z4 ainsi que des ondes sonores destructives permettant
de limiter, au moins en partie, les ondes sonores Os6, Os3 générées par l’autre
haut-parleur HP3, HP4 et qui sont diffusée en direction de la mauvaise zone Z3,
Z4.
Plus précisément, les filtres F1, F2 sont formés de différentes composantes,
chaque composante étant destinée à filtrer le signal d’entrée U3, U4 correspondant.
A titre d’exemple, les filtres F1, F2 peuvent s’écrire sous forme de matrices lignes,
tel qu’illustré ci-dessous :
[Math2]

Ainsi, les signaux S1 et S2 en entrée des haut-parleurs HP3, HP4, reçoivent les
signaux U3, U4. Les signaux S1 et S2 peuvent alors s’écrire sous la forme
suivante :
[Math3]

Les signaux sonores perçus dans les zones Z3 et Z4 sont exprimés à partir de la
matrice de propagation et du signal en entrée du système tel que :
[Math4]

Afin d’isoler les zones Z3 et Z4 entre elles, le haut-parleur HP3 peut être
configuré pour que le contenu audio F22.U4 dans la zone Z3, correspondant à la

5

fonction de transfert Os3, interfère de façon destructive avec le contenu audio
F12.U4 propagé par le haut-parleur HP3 dans la zone Z3. De même, le contenu
audio F11.U3 émis par le haut-parleur HP3 dans la zone Z4, correspondant à la
fonction de transfert Os6, interfère de façon destructive avec le contenu audio
F21.U3 émis par le haut-parleur HP4 dans la zone Z4, correspondant à la fonction
de transfert Os4. Après filtrage la matrice suivante est obtenue :
[Math5]

Une solution peut être obtenue à partir de l’inversion de matrice suivante :
[Math6]

Il s’ensuit que les ondes sonores perçues dans la première zone cible Z3
correspondent majoritairement à celles du signal U3 et que les ondes sonores
perçues dans la seconde zone cible Z4 correspondent majoritairement à celles du
signal U4.
Cette solution est particulièrement complexe à mettre en place, notamment
lorsqu’il est recherché d’atteindre des haute-fréquences. En effet, du fait du
phénomène de recouvrement spatial, particulièrement présents à haute-fréquences,
il convient d’utiliser un plus grand nombre de haut-parleurs pour générer les haute-
fréquences avec une qualité sonore satisfaisante. Or, puisque chaque haut-parleur
est relié à un filtrage dont le nombre de filtres dépend du nombre de haut-parleurs,
plus le nombre de haut-parleurs augmente, plus le nombre de composantes des
filtres est également conséquent.

6

Ainsi, cette solution requiert une électronique complexe et encombrante, et ce
d’autant plus lorsque le nombre de haut-parleurs et de composantes des filtres
augmente et/ou lorsque que les haut-parleurs commandés par les filtres utilisent
des fréquences importantes, typiquement supérieure à 1 kHz.
Le problème technique que se propose de résoudre l’invention est donc de pouvoir
générer des ondes sonores pour au moins deux zones distinctes d’un même espace
avec une qualité sonore satisfaisante et une robustesse aux déplacements, tout en
limitant l’encombrement du système, c’est-à-dire le nombre de haut-parleurs et la
complexité de l’électronique de commande.

EXPOSE DE L’INVENTION
Pour répondre à ce problème technique, l’invention propose, pour un espace
donné, de générer les basse-fréquences en filtrant les signaux transmis aux haut-
parleurs de grave pour générer des interférences destructives, et de générer les
haute-fréquences grâce à au moins un réseau directif de haut-parleurs aigu pour
lequel un filtre est mutualisé afin de filtrer les signaux transmis au réseau de haut-
parleurs aigu pour générer des interférences destructives.
En effet, l’invention est issue d’une découverte selon laquelle un réseau peut être
modélisé comme un unique haut-parleur directif. Il est donc possible d’associer un
seul filtre pour l’ensemble d’un réseau directif sans pour autant perdre en
directivité.
Ainsi, l’utilisation d’un réseau directif associé à la génération d’ondes destructives
permet de réduire le nombre de composantes des filtres et, par conséquent, la
complexité de l’électronique de commande et la consommation énergétique du
système.
Il s’ensuit que l’électronique de commande est globalement simplifiée et le
système est donc plus facile à intégrer dans des espaces réduits où les contraintes
d’installation sont fortes, comme par exemple l’habitacle d’une voiture.
En d’autres termes, l’invention porte sur un système de génération d’ondes sonores
pour au moins deux zones distinctes d’un même espace ; ledit système comportant
pour chaque zone dudit espace :

7

- au moins un réseau de haut-parleurs aigu comportant au moins trois haut-parleurs
aigus de sorte à former au moins une onde sonore directive ; et
- au moins un haut-parleur de grave.
Le système comporte également des moyens de traitement audio des signaux
transmis aux haut-parleurs ; lesdits moyens de traitement audio commandant au
moins un haut-parleur pour générer des ondes sonores destructives dans au moins
une zone dudit espace et obtenir des contenus sonores distincts dans lesdites au
moins deux zones distinctes dudit espace ; chaque contenu sonore de chaque zone
résultant de la somme des ondes sonores propagées dans ladite zone.
L’invention se caractérise en ce que les moyens de traitement audio commandent
individuellement chaque haut-parleur de grave et mutuellement chaque réseau de
haut-parleurs aigu pour générer les ondes sonores destructives.
Dans un mode de réalisation privilégié, plusieurs zones dudit espace sont
sonorisées par un même réseau de haut-parleurs aigu formant au moins deux ondes
sonores directives.
Autrement formulé, l’ensemble des haut-parleurs aigu du réseau peut être utilisé
pour sonoriser les au moins deux zones à la fois en formant au moins deux
faisceaux directifs distincts. Afin de faire parvenir les bons signaux sonores aux
bonnes zones, des délai temporels sont appliqués à chaque haut-parleur aigu
constitutif du réseau.
De manière surprenante, l’invention permet également d’obtenir une meilleure
robustesse aux déplacements au sein des zones de l’espace.
En pratique, pour calculer les coefficients d’un filtre commandant un haut-parleur
pour générer des interférences destructives dans une zone cible, il est nécessaire
d’estimer au préalable l’ensemble des signaux générés dans cette zone. Pour ce
faire, il convient d’estimer les fonctions de transfert entre les différents haut-
parleurs et les différentes zones pour différentes fréquences. Cette estimation peut
être réalisée en plaçant un microphone dans la zone cible ou en effectuant une
simulation numérique à partir d’un ou plusieurs point(s) de contrôle de cette zone.

8

Au sens de l’invention, un point de contrôle est un point de référence situé dans
une zone, pour lequel la fonction de transfert entre le haut-parleur et le point de
contrôle ainsi que la pression acoustique en ce point sont connues.
A l’issue de cette étape, les différentes fonctions de transfert peuvent être intégrées
dans une matrice, appelée matrice de propagation.
Le filtre associé au haut-parleur destiné transmettre des ondes sonores dans la zone
cible est alors calculé pour annuler les fonctions de transfert des ondes sonores non
désirées dans la zone cible.
En utilisant cette méthode pour un grand nombre de haut-parleurs, le calcul de
l’annulation des fonctions de transfert devient spatialement très localisé, et ce
notamment pour les haute-fréquences. Formulé autrement, dans les zones cible, les
interférences constructives et destructives des ondes acoustiques sont très
localisées autour des points de contrôle.
Il est alors constaté que cette méthode n’est efficace que lorsque l’auditeur est
précisément placé au niveau du point de contrôle de la zone cible.
Cette méthode de calcul des filtres induit une restitution optimale au niveau de l’au
moins un point de contrôle d’une zone cible et des variations importantes du
niveau d’isolation acoustique pour de faibles variations de position spatiales par
rapport à ce point central. Typiquement, un auditeur qui bougerait sa tête de
quelques centimètres par rapport au point de contrôle d’une zone percevrait
d’importantes variations du niveau sonore des signaux indésirés issus des
programmes des autres auditeurs. Cet inconvénient peut rendre l’écoute difficile et
inconfortable pour l’auditeur.
L’invention permet de répondre à ce problème car elle permet que la restitution
sonore soit optimale sur une zone plus élargie que dans l’art antérieur. Ainsi,
l’invention permet d’obtenir une restitution plus homogène dans la zone cible.
Autrement dit, un auditeur qui bougerait sa tête de quelques centimètres par
rapport au point de contrôle d’une zone ne verrait pas varier la qualité du son qu’il
perçoit. Son expérience d’écoute est donc globalement améliorée.

9

Dans un mode de réalisation préférentiel, l’espace comportant au moins quatre
zones, le système comprend au moins quatre ondes sonores directives et au moins
quatre haut-parleurs de grave ; lesdits moyens de traitement audio commandant :
- chaque haut-parleur de grave associé à une zone cible pour générer des ondes
sonores destructives destinées à limiter les ondes sonores générées, dans la zone
cible, par les haut-parleurs de grave associés à d’autre zones ; et
- chaque réseau de haut-parleur aigu associé à une zone cible pour générer des
ondes sonores destructives destinées à limiter les ondes sonores générées, dans la
zone cible, par les réseaux de haut-parleurs aigu associés à d’autre zones.
Bien-entendu, les réseaux de haut-parleurs aigus peuvent être utilisés pour générer
une première onde sonore à destination d’une première zone et une seconde onde
sonore à destination d’une seconde zone.
Ce mode de réalisation permet de reproduire un effet de répartition dans l&#39;espace
des sources sonores.
Au sens de l’invention, les zones peuvent être définies dans un espace
sensiblement en deux dimensions (2D). Ce mode de réalisation permet alors
d’obtenir une restitution sonore stéréophonique pour les auditeurs, c’est-à-dire
qu’ils peuvent localiser dans l’espace 2D les sons qu’ils perçoivent. Pour ce faire,
des contenus audios distincts pour chaque oreille sont envoyés par les haut-
parleurs, ce qui contribue à améliorer l’expérience immersive de l’auditeur.
Au sens de l’invention, les zones peuvent également être définies dans un espace
sensiblement en trois dimensions (3D). Ce mode de réalisation permet alors
d’obtenir une restitution sonore 3D pour les auditeurs, c’est-à-dire qu’ils peuvent
localiser dans l’espace 3D les sons qu’ils perçoivent.
Pour ce faire, des contenus audios distincts pour chaque oreille sont envoyés par
les haut-parleurs afin d’obtenir une reproduction sonore binaurale. Une telle
restitution sonore est celle qui se rapproche le plus de la réalité, elle permet à
l’auditeur de se sentir complètement immergé dans l’espace.
Afin de répartir les signaux entre les haut-parleurs de grave et les réseaux directifs
de haut-parleurs aigus, les moyens de traitement audio comportent
préférentiellement au moins un filtre passe-bas et au moins un filtre passe-haut

10

permettant de scinder le signal transmis aux haut-parleurs en au moins un signal
haute-fréquences transmis aux réseaux de haut-parleurs aigu et au moins un signal
basse-fréquence transmis aux haut-parleurs de grave.
Dans un cas particulier de réalisation, le système peut comporter des haut-parleurs
large bande, capables de reproduire à la fois les sons en haute-fréquences des haut-
parleurs aigu et les sons en basse-fréquence des haut-parleurs de grave.
Il est alors possible d’envoyer simultanément au haut-parleur large bande un signal
lui indiquant de se comporter comme un haut-parleurs aigu constitutif d’un réseau
directif et un signal lui indiquant de se comporter comme un haut-parleur de grave,
sans créer d’interférences entre les deux signaux.
Autrement formulé, le système comprend au moins un haut-parleur large bande
constituant à la fois un haut-parleur de grave et un haut-parleur aigu d’un réseau,
ledit haut-parleur large bande recevant au moins un signal haute-fréquences et au
moins un signal basse-fréquences.
Incorporer des haut-parleurs large bande permet ainsi de limiter le nombre total de
haut-parleurs du système, ce qui facilite l’installation dans des espaces
contraignants.
En pratique, le système comporte, pour chaque zone dudit espace, entre 2 et 6
haut-parleurs de grave et un réseau comportant entre 10 et 20 haut-parleurs aigu.
Dans un mode de réalisation avantageux, le système comporte en outre des moyens
de détection de la position de la tête de l’utilisateur, les moyens de traitement audio
commandant l’au moins un haut-parleur de grave et l’au moins un réseau de haut-
parleurs aigu pour générer les ondes sonores destructives en fonction de la position
de la tête de l’utilisateur.
Ce suivi de la tête de l’utilisateur, également appelée « Head-tracking » dans la
littérature anglo-saxonne permet, en temps réel, d’appliquer un filtre,
préalablement calculé, qui engendrera la meilleure restitution sonore pour
l’utilisateur, en fonction de la position de sa tête. Le suivit de la tête de l’utilisateur
permet donc d’augmenter encore plus la robustesse du système.
Selon un autre aspect, l’invention porte sur un procédé de détermination d’au
moins une matrice de filtrage associée à au moins un haut-parleur de grave et au

11

moins un réseau de haut-parleurs aigu du système tel que décrit précédemment. Le
procédé comporte les étapes suivantes :
- mesure et/ou simulation d’une première matrice de propagation entre les
différents haut-parleurs de grave et les différentes zones;
- mesure et/ou simulation d’une seconde matrice de propagation entre les réseaux
de haut-parleurs aigu et les différentes zones, chaque matrice de propagation
incluant les fonctions de transfert entre chaque haut-parleur de grave ou réseau de
haut-parleurs aigu et chaque zone ;
- détermination d’une première matrice objectif à partir de la première matrice de
propagation en annulant les fonctions de transfert dans les zones destinées à
recevoir les ondes sonores destructives ;
- détermination d’une seconde matrice objectif à partir de la seconde matrice de
propagation en annulant les fonctions de transfert dans les zones destinées à
recevoir les ondes sonores destructives ;
- calcul d’une première matrice de filtrage correspondant au produit de la matrice
inverse de la première matrice de propagation et de la première matrice objectif, et
- calcul d’une seconde matrice de filtrage correspondant au produit de la matrice
inverse de la seconde matrice de propagation et de la seconde matrice objectif.
Afin de limiter la puissance numérique nécessaire au système, il est possible de
réduire le nombre de filtres en calculant une matrice de filtrage commune à partir
des première et seconde matrice de filtrage. Ainsi, la matrice commune comporte à
la fois les informations concernant les réseaux directifs et les haut-parleurs de
grave. Cette étape de calcul est particulièrement utile lorsque le système inclut des
haut-parleurs large bande qui doivent à la fois recevoir un signal filtré destiné au
réseau directif et un signal filtré destiné aux haut-parleurs de grave.
En pratique, la mesure ou la simulation de la première et/ou de la seconde matrice
de propagation peut être réalisée en au moins un point de contrôle par zone.
Un mode d’utilisation consiste à augmenter le nombre de points de contrôle à
l’intérieur d’une zone. La matrice objectif impose alors d’obtenir le signal désiré
au niveau de chaque point de contrôle. Bien que ce système augmente le nombre
de filtres, l’utilisation de plusieurs points de contrôle permet d’homogénéiser

12

l’isolation acoustique dans les zones cibles. Une meilleure robustesse par rapport
aux mouvements de la tête de l’utilisateur est ainsi obtenue. Si le niveau
d’isolation est plus homogène dans la zone, celui-ci diminue avec le nombre de
points de contrôle et ce, d’autant plus, si la zone couverte par les points de contrôle
est grande. Autrement formulé, la mesure ou la simulation de la première et/ou de
la seconde matrice de propagation peut être réalisée en au moins deux points de
contrôle, les fonctions de transfert entre chaque haut-parleur de grave ou réseau de
haut-parleurs aigu et chaque zone sont obtenues en calculant plusieurs filtres pour
chaque point de contrôle situés dans les différentes zones.
En pratique, l’au moins une matrice de filtrage est sélectionnée parmi un ensemble
de matrices de filtrage calculées pour les différents points de contrôle ou ensemble
de points de contrôle, en fonction de la position de la tête de l’utilisateur.

DESCRIPTION DES FIGURES
La manière de réaliser l’invention, ainsi que les avantages qui en découlent,
ressortiront bien de la description des modes de réalisation qui suivent, à l’appui
des figures annexées dans lesquelles :
[Fig 1] La figure 1 est une représentation schématique d’un système de l’art
antérieur configuré pour sonoriser deux zones distinctes d’un espace par un réseau
de haut-parleurs,
[Fig 2] La figure 2 est une représentation schématique d’un système de l’art
antérieur configuré pour sonoriser deux zones distinctes d’un espace par
génération d’ondes destructives,
[Fig 3] La figure 3 est une représentation schématique du système de l’invention
selon un premier mode de réalisation,
[Fig 4] La figure 4 est une représentation schématique du système de l’invention
selon un second mode de réalisation,
[Fig 5] La figure 5 est un organigramme représentant les étapes du procédé de
l’invention selon un mode de réalisation,
[Fig 6] La figure 6 est une représentation schématique de l’étape de mesure et/ou
de simulation d’une première matrice de propagation entre les différents haut-

13

parleurs de grave et les différentes zones du procédé de la figure 5 selon un mode
de réalisation monophonique,
[Fig 7] La figure 7 est une représentation schématique de l’obtention de la
première matrice objectif selon le mode de réalisation de la figure 6, en fonction
des premières matrices de propagation et de filtrage,
[Fig 8] La figure 8 est une représentation schématique de l’obtention de la
première matrice objectif pour une restitution sonore stéréophonique, en fonction
des premières matrices de propagation et de filtrage,
[Fig 9] La figure 9 est une représentation schématique de l’obtention de la
première matrice objectif pour une restitution sonore 3D, en fonction des
premières matrices de propagation et de filtrage,
[Fig 10] La figure 10 est une représentation schématique de l’étape de mesure
et/ou de simulation d’une seconde matrice de propagation entre les différents
réseaux de haut-parleurs aigu et les différentes zones du procédé de la figure 5
selon un mode de réalisation monophonique,
[Fig 11] La figure 11 une représentation schématique de la seconde matrice
objectif selon le mode de réalisation de la figure 8, en fonction des secondes
matrices de propagation et de filtrage,
[Fig 12] La figure 12 est une représentation schématique de l’obtention de la
seconde matrice objectif pour une restitution sonore stéréophonique, en fonction de
la seconde matrice de propagation et de la seconde matrice de filtrage,
[Fig 13] La figure 13 est une représentation schématique de l’obtention de la
seconde matrice objectif pour une restitution sonore 3D, en fonction de la seconde
matrice de propagation et de la seconde matrice de filtrage,
[Fig 14] La figure 14 est une représentation schématique de la première matrice de
filtrage selon le mode de réalisation de la figure 7, et
[Fig 15] La figure 15 est une représentation schématique de la seconde matrice de
filtrage après optimisation du paramètre β, selon le mode de réalisation de la figure
7,
[Fig 16] La figure 16 est une représentation schématique de la fusion des matrices
de filtrage selon deux modes de réalisation distincts ;

14

[Fig 17] La figure 17 est un graphique comparatif de la répartition spatiale de
l&#39;intensité sonore pour une source seule, un réseau avec un filtrage préalable sur
chaque source, un réseau directif et un réseau de haut-parleur avec filtrage
préalable sur chaque faisceau pour une fréquence de 100Hz ;
[Fig 18] La figure 18 est un graphique comparatif de la répartition spatiale de
l’intensité sonore pour une source seule, un réseau avec un filtrage préalable sur
chaque source, un réseau directif et un réseau de haut-parleurs avec filtrage
préalable sur chaque faisceau pour une fréquence de 1000Hz,
[Fig 19] La figure 19 est un graphique comparatif de la répartition spatiale de
l’intensité sonore pour une source seule, un réseau avec un filtrage préalable sur
chaque source, un réseau directif et un réseau de haut-parleurs avec filtrage
préalable sur chaque faisceau pour une fréquence de 2000Hz,
[Fig 20] La figure 20 est un graphique comparatif de l’atténuation acoustique entre
deux utilisateurs en fonction de la fréquence pour un réseau de haut-parleurs seul,
un réseau avec un filtrage préalable sur chaque source et un réseau avec filtrage
mutualisé, et
[Fig 21] La figure 21 est un graphique de l’atténuation acoustique obtenue en
fonction de la fréquence lorsqu’un filtrage préalable est appliqué sur chaque source
d’un réseau de 16 haut-parleurs large bande par zone pour une fréquence inférieure
à la fréquence de coupure et lorsque l’invention est appliquée pour des fréquences
supérieures à la fréquence de coupure.

DESCRIPTION DÉTAILLÉE DES MODES DE RÉALISATION
Tel qu’illustré sur la figure 3, le système 100 de l’invention peut être intégré dans
ou à proximité d’un espace 3000 que l’on souhaite sonoriser. L’espace 3000 peut
présenter des dimensions variables et être délimité ou non par des frontières
physiques. A titre d’exemple, l’espace 3000 peut être l’habitacle d’une voiture, une
salle de cinéma, une salle de concert ou encore un espace de concert en plein air.
Au sein de l’espace 3000, il est possible de définir des zones Z31, Z32 pour
lesquelles il est recherché d’obtenir une sonorisation spécifique.

15

La zone Z31 peut par exemple être une zone dans laquelle il est recherché de
maximiser l’intensité sonore, tandis que dans la zone Z32, il est recherché de
minimiser l’intensité sonore. A titre d’exemple, l’espace 3000 peut inclure une
zone de de concert en plein air et son voisinage proche. La zone Z31 peut
correspondre à l’intérieur de la zone de concert en plein air, cette zone Z31 étant
destinée à être sonorisée par la musique du concert. La zone Z32 peut, quant à elle,
correspondre à l’extérieur de la zone de concert en plein air. Il est alors recherché
de limiter au maximum l’intensité sonore dans la zone Z32 pour ne pas déranger le
voisinage.
Selon un autre exemple, la zone Z31 peut être une zone dans laquelle on souhaite
générer un contenu sonore d’un premier type, tandis que dans la zone Z32, on
souhaite générer un contenu sonore d’un second type. A titre d’exemple, l’espace
3000 peut correspondre à une salle de cinéma, la zone Z31 peut correspondre à une
première rangée de sièges pour lesquels on souhaite diffuser un film dans une
première langue et la zone Z32 peut correspondre à une seconde rangée de sièges
pour lesquels on souhaite diffuser le film dans une seconde langue. En variante,
l’espace 3000 peut comporter plus de deux zones, typiquement entre 3 et 20 zones
distinctes. En particulier, l’espace 3000 peut comporter des « paires de zones »,
c’est-à-dire des zones espacées d’entre 15 et 25cm pour permettre à un utilisateur
de positionner chacune de ses oreilles dans une zones distincte. L’utilisateur peut
alors recevoir un contenu sonore différent dans chaque oreille, ce qui permet de
recréer un effet sonore stéréophonique ou 3D.
Afin de sonoriser ces zones Z31, Z32, le système 100 comporte des haut-
parleurs HPG21, HPG22, HPA21, HPA22 disposés au sein de l’espace 3000. Par
exemple, les haut-parleurs HPG21, HPG22, HPA21, HPA22 peuvent être
disposés à proximité des zones à sonoriser. Typiquement, les haut-
parleurs HPG21, HPG22, HPA21, HPA22 peuvent être intégrés dans le siège de
l’utilisateur ou dans le dossier d’un siège lui faisant face, dans le cas d’une rangée
de sièges. Les haut-parleurs HPG21, HPG22, HPA21, HPA22 peuvent également
être éloignés de la zone à sonoriser, typiquement sur une distance comprise entre
0.5m et 100 m. Les haut-parleurs HPG21, HPG22, HPA21, HPA22 peuvent par

16

exemple être intégrés dans les murs et/ou parois de l’espace 3000 ou montés sur
une barre de son.
Tel qu’illustré sur la figure 3, pour chaque zone Z31, Z32 de l’espace 3000, il est
possible d’associer un haut-parleur de grave HPG21, HPG22 et un réseau R21,
R22 de trois haut-parleurs aigu HPA21, HPA22. En variante, le nombre de haut-
parleurs de grave HPG21, HPG22 peut être compris entre 2 et 10.
De même, le nombre de haut-parleurs aigu HPA21, HPA22 peut-être compris
entre 2 et 30. De manière générale, les réseaux R21, R22 de haut-parleurs aigu
HPA21, HPA22 sont formées d’un ensemble de haut-parleurs aigu HPA21,
HPA22 alignés et séparés d’une distance inférieure à la moitié du maximum des
longueurs d’ondes générées par les haut-parleurs de sorte à obtenir des
interférences constructives et à former une onde sonore sensiblement cylindrique.
Cependant, les réseaux R21, R22 de haut-parleurs aigu HPA21, HPA22 ne sont
pas forcément physiquement séparés. Il est possible de former des sous-réseaux et
de leurs attribuer une fonction différente.
A titre d’exemple, un réseau R21, R22 de haut-parleurs aigu HPA21, HPA22 peut
être constitué de 10 haut-parleurs aigu HPA21, HPA22. Au sein de ce réseau R21,
R22, 5 haut-parleurs aigu HPA21, HPA22 peuvent être attribués à la zone Z31,
tandis que les 5 autres haut-parleurs aigu HPA21, HPA22 sont attribué à la zone
Z32 En variante, les 10 haut-parleurs aigu HPA21, HPA22 peuvent être à la fois
attribués à la zone Z31 et à la zone Z32. Deux ondes sonores directives sont alors
générées, à destination de chaque zone Z31, Z32. Des délais temporels peuvent
être appliqués à chaque haut-parleur aigu HPA21, HPA22 constitutif du réseau
R21, R22 pour faire parvenir le bon signal sonore à la bonne zone Z31, Z32.
Un haut-parleur de grave HPG21, HPG22 émet typiquement dans une plage de
fréquences comprise entre 20 Hz et 2000 Hz et un haut-parleur aigu HPA21,
HPA22, émet typiquement dans une plage de fréquences comprise entre 2000 Hz
et 40 kHz.
En variante, tel qu’illustré sur la figure 4, le système 200 peut comporter des haut-
parleurs large bande HPLB, émettant, dans l’espace 4000, à la fois sur la plage des
basse-fréquences et sur la plage des haute-fréquences, c’est-à-dire, typiquement sur

17

toute la bande passante de l’oreille humaine à savoir entre 20 Hz et 20 kHz. Les
haut-parleurs large bande HPLB peuvent faire partie intégrante d’un réseau R31,
R32 ou encore fonctionner en autonomie.
Tel qu’illustré sur la figure 3, sans aucun traitement préalable, les haut-parleurs
aigu HPA11, HPA12 et les haut-parleurs de grave HPG21, HPG22 ne sont pas
parfaitement directifs et peuvent émettre des ondes sonores en direction des autres
zones Z31, Z32 que celles qu’ils sont en charge de sonoriser. Ainsi, le premier
haut-parleur de grave HPG21 émet à la fois une onde sonore Os32 en direction de
sa zone Z31 et une onde sonore Os36 en direction de la seconde zone Z32 et de
même, le second haut-parleur de grave HPG22 émet à la fois une onde
sonore Os33 en direction de sa zone Z32 et une onde sonore Os37 en direction de
l’autre zone Z31. En outre, les réseaux de haut-parleurs aigu R21, R22 ne sont pas
non plus parfaitement directifs et émettent également des ondes sonores en
direction des deux zones Z31, Z32 à la fois. A titre d’exemple, le réseau de haut-
parleurs aigu R21 émet à la fois une onde sonore Os31 en direction de sa zone Z31
et une onde sonore Os35 en direction de la seconde zone Z32. De même, le réseau
de haut-parleurs aigu R22 émet à la fois une onde sonore Os34 en direction de sa
zone Z32 et une onde sonore Os38 en direction de la zone Z31.
Pour limiter la pollution sonore, chaque haut-parleur de grave HPG21, HPG22 et
chaque réseau R21, R22 de haut-parleurs aigu HPA21, HPA22 est associé à un
filtrage F31-F34 commandant la génération d’ondes sonores destructives Od35-
Od38 pour annuler les ondes sonores indésirables Os35-Os38.
Ainsi, chaque haut-parleur de grave HPG21, HPG22 est associé à un filtre F32,
F33, qui fournit aux haut-parleurs de grave HPG21, HPG22, respectivement les
signaux S32 et S33. En revanche, le filtre F31, F34 est mutualisé pour l’ensemble
des haut-parleurs aigu HPA11, HPA12. Le filtres F31, F34 fournissent ainsi
respectivement un signal S31 et S34 aux réseaux de haut-parleurs HPA21,
HPA22.
Les haut-parleurs HPG21, HPG22, HPA21, HPA22 sont alimentés par deux
signaux électriques U7, U8. De préférence, les signaux U7, U8 sont filtrés par un
filtre passe-bas Pb avec une fréquence de coupure comprise entre 400 Hz et 4kHz

18

et par un filtre passe-haut Ph avec une fréquence de coupure comprise entre 400
Hz et 4kHz afin de distinguer les haut-fréquences des basse-fréquences. Ainsi, les
signaux basse-fréquences U52, U62 sont transmis aux filtres F32, F33 des haut-
parleurs de grave HPG21, HPG22 et les signaux haute-fréquences U51, U61 sont
transmis aux filtres F31, F34 des réseaux R21, R22 de haut-parleurs aigu HPA21,
HPA22.
Il s’ensuit que les contenus sonores obtenus dans la première zone cible Z31
correspondent majoritairement à ceux attendus par le signal U7 par l’association :
- des ondes sonores basse-fréquences Os32 formées par le premier haut-parleur de
grave HPG21 dont le signal S32 est configuré pour également générer des
interférences destructives Od37 pour limiter les ondes sonores Os37 formées par
le second haut-parleur de grave HPG22 ; et
- des ondes sonores haute-fréquences Os31 formées par les haut-parleurs aigu
HPA21 présentant une directivité obtenue par le réseau R21 et générant des
interférences destructives Od38 pour limiter les ondes sonores Os38 formées par
le second réseau R22 de haut-parleurs aigu HPA22.
De la même manière, les contenus sonores obtenus dans la seconde zone cible Z32
correspondent majoritairement à ceux attendus par le signal U8.
Tel qu’illustré sur la figure 4, le système peut comprendre au moins un haut-
parleur large bande HPLB1 en charge de sonoriser la zone Z41 et au moins un
haut-parleur large bande HPLB2, pour sonoriser la zone Z42. De même, le
système peut comprendre au moins un réseau de haut-parleurs aigu R21, R22 pour
sonoriser respectivement les zones Z41 et Z42. Les haut-parleurs large
bande HPLB1 ne sont pas non plus parfaitement directifs et peuvent émettre des
ondes sonores en direction des autres zones Z41, Z42 que celles qu’ils sont en
charge de sonoriser. Ainsi, le haut-parleur large bande HPLB1 émet à la fois une
onde sonore Os42 en direction de sa zone Z41 et une onde sonore Os46 en
direction de la seconde zone Z42. Pour limiter la pollution sonore, chaque haut-
parleur large bande HPLB1, HPLB2 et chaque réseau R21, R22 de haut-parleurs
aigu HPA21, HPA22 est associé à au moins un filtrage F41-F44 commandant la
génération d’ondes sonores destructives Od45-Od48 pour annuler les ondes

19

sonores indésirables Os35-Os38. Par exemple, le haut-parleur large bande HPLB1
peut-être associé à deux filtres F41 et F42 commandant la génération d’ondes
sonores destructives Od47 pour annuler les ondes sonores indésirables Os45-
Os48. Le premier filtre F41 est alimenté par la partie haut-fréquences U71 du
signal électrique U9 et produit un signal S41 à destination du haut-parleur large
bande HPLB1 et du réseau R31. Le second filtre F42 est alimenté par la partie
basse-fréquences U72 du signal électrique U9 et produit un signal S42 à
destination du haut-parleur large bande HPLB1. De même, le haut-parleur large
bande HPLB2 peut-être associé à deux filtres F43 et F44 commandant la
génération d’ondes sonores destructives Od46 pour annuler les ondes sonores
indésirables Os45-Os48. Le premier filtre F44 est alimenté par la partie haut-
fréquences U81 du signal électrique U10 et produit un signal S44 à destination du
haut-parleur large bande HPLB2 et du réseau R32 et le second filtre F43 est
alimenté par la partie basse-fréquences U82 du signal électrique U10 et produit un
signal S43 à destination du haut-parleur large bande HPLB2.
Dans l’exemple de la figure 4, le haut-parleur large bande HPLB1 est utilisé pour
sonoriser la zone Z41 en basse-fréquences et pour annuler les ondes sonores
indésirables Os47 provenant du haut-parleur large bande HPLB2.
En variante, le haut-parleur large bande HPLB1 peut être utilisé pour sonoriser la
zone Z41 en haute-fréquences, par exemple en faisant partie intégrante du réseau
R31, et/ou pour annuler les ondes sonores indésirables Os48 provenant du réseau
de haut-parleurs aigu HPA32. Dans encore une autre variante, le haut-parleur large
bande HPLB1 peut jouer les deux rôles à la fois ou une combinaison de ces rôles.
De même, le haut-parleur large bande HPLB2 est utilisé pour sonoriser la zone
Z42 en basse-fréquences et pour annuler les ondes sonores indésirables Os47
provenant du haut-parleur large bande HPLB1. Ce haut-parleur large bande
HPLB2 est connecté à un second filtre F43 alimenté par la partie basse-
fréquences U82 du signal électrique U10.
En outre, le réseau de haut-parleurs aigu R31 émet à la fois une onde sonore Os41
en direction de sa zone Z41 et une onde sonore Os45 en direction de la seconde
zone Z42. De même, le réseau de haut-parleurs aigu R32 émet à la fois une onde

20

sonore Os44 en direction de sa zone Z42 et une onde sonore Os48 en direction de
la zone Z41.
Afin de configurer les différents filtres, une matrice de filtrage C1, C2, C peut être
mesurée ou simulée. Ce procédé de détermination d’au moins une matrice de
filtrage C1, C2, C est associé à au moins un haut-parleur de grave HPG21,
HPG22, et au moins un réseau de haut-parleurs aigu HPA21, HPA22, HPA31,
HPA32 du système 100.
Tel qu’illustré sur les figures 5 et 6, la première étape du procédé consiste à
mesurer et/ou simuler 101 une première matrice de propagation H1 entre les
différents haut-parleurs de grave HPG41-HPG48 et les différentes zones Z41,
Z42.
Pour ce faire, on mesure ou on simule, la réponse en fréquence entre des points de
contrôle PC1, PC2 et chaque haut-parleur de grave HPG21, HPG22.
Tel qu’illustré sur la figure 6, la mesure peut être obtenue en positionnant un
microphone dans chaque zone Z51, Z52. Les cordonnées des positions des
microphones correspondent aux points de contrôle PC1, PC2. Lorsque les points
de contrôle PC1, PC2 sont définis, les haut-parleurs de grave HPG21, HPG22
sont commandés pour diffuser des ondes sonores dont la fréquence varie sur tout
ou partie de la plage de fréquence que le haut-parleur de grave HPG21, HPG22
peut produire. Typiquement, les haut-parleurs de grave HPG21, HPG22 peuvent
être commandés pour diffuser un signal sinusoïdal glissant sur une plage de
fréquences comprise entre 20Hz et 40000Hz.
En variante, pour simuler la réponse en fréquence des haut-parleurs de grave
HPG21, HPG22, un modèle reproduisant les caractéristiques des haut-parleurs
peut être utilisé. Pour ce faire, la pression générée par le haut-parleur est assimilée
à la pression rayonnée par un monopole acoustique ou un piston. En variante, la
pression rayonnée par le haut-parleur peut être également calculée à l&#39;aide d&#39;un
modèle numérique basée sur la Méthode des Eléments Finis ou sur la Méthode des
Eléments de Frontière.

21

Chaque fonction de transfert H1 M,N entre chaque point de contrôle PC1, PC2 et
chaque haut-parleur de grave HPG21, HPG22 est indexée telle que M est le
numéro du point de contrôle et N, le numéro du haut-parleur.
La matrice de propagation H1 illustrée à la figure 7 est ainsi obtenue. Cette matrice
de propagation H1 présente 2 lignes et 8 colonnes car deux points de contrôle
PC1, PC2 sont présents dans l’espace et 8 haut-parleurs grave HPG41-HPG48
sont considérés.
La seconde étape du procédé, tel qu’illustré sur les figures 5 et 10, consiste à
mesurer et/ou simuler 103 une seconde matrice de propagation H2 entre les
différents réseaux de haut-parleurs aigu HPA41-HPG48 et les différentes zones
Z51, Z52. Une méthode similaire à celle illustrée sur la figure 6 peut être utilisée.
Les réseaux R41, R42 de haut-parleurs aigu HPA41-HPA48 sont alors
commandés pour diffuser des ondes sonores dont la fréquence varie sur tout ou
partie de la plage de fréquence que les haut-parleurs aigu HPA41-HPA48 peuvent
produire. Typiquement, les réseaux R41, R42 de haut-parleurs aigu HPA41-
HPA48 peuvent être commandés pour diffuser un signal sinusoïdal glissant sur
toute la plage des fréquences audibles, c’est-à-dire comprises entre 20Hz et 40kHz.
Chaque fonction de transfert H2 M,N entre chaque point de contrôle PC1, PC2 et
chaque réseau R41, R42 de haut-parleurs aigu HPA41-HPA48 est indexée telle
que M est le numéro du point de contrôle et N, le numéro du réseau R41, R42.
Suivant l’exemple de la figure 10, on obtient la matrice de propagation H2 illustrée
à la figure 11. Cette matrice de propagation H2 présente 2 lignes et 2 colonnes car
deux points de contrôle PC1, PC2 sont présents dans l’espace et 2 réseaux R41,
R42 de haut-parleurs aigu HPA41-HPA48 émettant chacun un faisceau sonore en
direction des deux points de contrôle PC1 et PC2 sont considérés.
Les deux étapes 101, 103 sont indépendantes et réalisées l’une après l’autre.
Les étapes 102 et 104 consistent à déterminer une première et une seconde matrice
objectif M1, M2 à partir des première et seconde matrices de propagation H1, H2
en annulant les fonctions de transfert dans les zones destinées à recevoir les ondes
sonores destructives.

22

Ainsi, dans l’étape 102, il est recherché d’annuler les fonctions de transfert H1 1,N
entre les haut-parleurs de grave HPG41-HPG44 et la zone Z52 ainsi que les
fonctions de transfert H1 2,N entre les haut-parleurs de grave HPG45-HPG48 et la
zone Z51.
Dans le cas où il est recherché d’obtenir un son monophonique dans les zones Z51
et Z52, la matrice M1 obtenue est telle qu’illustrée sur la figure 7. Ainsi, la matrice
M1 obtenue est le produit de la matrice H1 et de la matrice de filtrage C1, cette
dernière comportant 8 lignes et 2 colonnes. La matrice M1 obtenue présente donc
2 lignes et 2 colonnes et seuls les coefficients M1 1,1 et M1 2,2 sont conservés.
Dans le cas où il est recherché d’obtenir une restitution sonore stéréophonique, la
matrices de propagation H1 est établie entre 8 haut-parleurs HPG41-HPG48 et 4
points de contrôle PC1-PC4. La matrice H1 présente donc 4 lignes et 8 colonnes,
tandis que la matrice de filtrage C1 présente 8 lignes et 4 colonnes. Pour obtenir la
matrice M1, il convient de converser 2 réponses par ligne et par colonne. Plusieurs
solutions sont possibles et un exemple de conservation est illustré sur la figure 8.
Dans le cas où il est recherché d’obtenir une restitution sonore 3D, la matrices de
propagation H1 est établie entre 8 haut-parleurs HPG41-HPG48 et 4 points de
contrôle PC1-PC4. La matrice H1 présente donc 4 lignes et 8 colonnes, tandis que
la matrice de filtrage C1 présente 8 lignes et 4 colonnes. Pour obtenir la
matrice M1, il convient de converser 1 réponse par ligne et par colonne. Plusieurs
solutions sont possibles et un exemple de conservation est illustré sur la figure 9.
De la même manière, dans l’étape 104, il est recherché d’annuler les fonctions de
transfert H2 1,N entre les réseaux de haut-parleurs aigu HPA41-HPA44 et la zone
Z52 ainsi que les fonctions de transfert H2 2,N entre les réseaux de haut-parleurs
aigu HPA45-HPA48 et la zone Z51. Dans le cas où il est recherché d’obtenir un
son monophonique, la matrice M2 obtenue est illustrée sur la figure 11. La matrice
M2 est le produit de deux matrices carrées H2, C2, elle est donc également carrée.
Dans le cas où il est recherché d’obtenir une restitution sonore stéréophonique, il
convient de converser 2 réponses par ligne et par colonne. Plusieurs solutions sont
possibles et un exemple de conservation est illustré sur la figure 12. La matrice M2
est le produit de deux matrices carrées H2, C2, elle est donc également carrée.

23

Dans le cas où il est recherché d’obtenir une restitution sonore 3D, la matrice M2
est une matrice diagonale, tel qu’illustré sur la figure 13. La matrice M2 est le
produit de deux matrices carrées H2, C2, elle est donc également carrée.
Les étapes 105 et 106 consistent à calculer une première et une seconde matrice de
filtrage C1, C2 correspondant au produit de la matrice inverse de la matrice de
propagation H1, H2 et de la matrice objectif M1, M2, soit C1 = H2 -1 .M2 et C2 =
H1  - 1 .M2.
Les matrices de filtrage C1, C2 sont calculées de manière à minimiser l’erreur
entre la matrice obtenue après filtrage et la matrice objectif M1, M2. En outre,
dans l’exemple de la figure 7, la matrice H1 n’est pas carrée. Seule une pseudo-
inversion de la matrice H1 peut-alors être effectuée et l’introduction d’un
paramètre d’erreur β est nécessaire. En cherchant à minimiser la valeur du
paramètre β, il est alors possible de converger vers des solutions d’inversion. La
valeur du paramètre β peut être constante ou encore dépendre de la fréquence.
Cependant, ces solutions peuvent avoir pour effet de modifier la réponse en
fréquence des ondes sonores résultantes, se traduisant alors par une coloration
sonore par rapport à son désiré dans les matrices objectifs M1 et M2. Ces solutions
peuvent également réduire la plage dynamique du système, c’est-à-dire la plage de
niveau sonore couverte par le système.
A titre d’exemple, la figure 14 illustre la matrice de filtrage C1 obtenue pour
l’exemple de la figure 9. Cette matrice présente 8 lignes et 2 colonnes. De plus, en
basse-fréquences, typiquement entre 10Hz et 500Hz, pour chaque filtre C1 N,M , on
observe un gain élevé pouvant atteindre 8 dB. La figure 15 illustre l’effet sur le
gain de l’introduction du paramètre β. Ce paramètre introduit des erreurs par
rapport à la matrice objectif M1, M2, mais limite l’effort. La valeur de β est
optimisée pour chaque fréquence. Ainsi, sur la figure 14, la courbe en pointillés
illustre la matrice de filtrage C1 avant régularisation, c’est-à-dire avec β=0, et la
courbe en train plein illustre la matrice de filtrage C1 après régularisation. On
observe ainsi que le gain des filtres, notamment en basse-fréquences et plus faible,
c’est-à-dire proche de 0dB.

24

La méthode utilisée pour calculer la matrice de filtrage C2 est identique à la
méthode décrite précédemment.
Avantageusement, il est possible de calculer, dans l’étape 107, une matrice de
filtrage commune C à partir des première et seconde matrices de filtrage C1, C2.
Pour ce faire, selon un exemple illustré sur la figure 16, un réseau R51 de 13 haut-
parleurs, comportant 9 haut-parleurs aigu HPA51 et 4 haut-parleurs large bande
HPLB peut être utilisé. En variante, le réseau R51 peut ne comporte que des haut-
parleurs large bande HPLB. Le réseau R51 illustré à la figure 16 est commandé
par plusieurs filtres configurés pour transmettre aux haut-parleurs large bande
HPLB la partie grave du son et pour transmettre aux haut-parleurs aigu HPA51, la
partie aigue du son.
Au sein de ce réseau R51, les haut-parleurs aigu HPA51 et les haut-parleurs large
bande HPLB sont regroupés en sous-réseaux afin de calculer des matrices de
filtrage correspondantes. Autrement formulé, pour le sous-réseau de haut-parleurs
aigu HPA51, on calcule une première matrice de filtrage et pour le sous-réseau de
haut-parleurs large bande HPLB1, on calcule une seconde matrice de filtrage.
Pour fusionner ces matrices de filtrage, il existe deux possibilités.
La première solution Mode 1 consiste à utiliser un seuillage. A titre d’exemple, le
seuillage peut être réalisée sur la fréquence de coupure. Par exemple, la valeur de
la fréquence de seuillage peut être identique à la fréquence de coupure choisie pour
les filtres passe-bas et/ou passe-haut permettant de distinguer les haute-fréquences
des basse-fréquences.
Ainsi, si la fréquence commandée au réseau R51 est inférieure à la fréquence de
seuillage alors c’est le coefficient de la première matrice de filtrage qui est choisi.
A l’inverse, si la fréquence commandée au réseau R51 est supérieure à la
fréquence de seuillage alors c’est le coefficient de la seconde matrice de filtrage
qui est choisi.
En variante, la seconde solution Mode 2 consiste à multiplier les deux matrices de
filtrages en ajoutant un filtre passe-bas LPF sur la première matrice de filtrage et
un filtre passe-haut HPF sur la seconde matrice de filtrage.

25

Avec l’une ou l’autres des méthodes décrites précédemment, les matrices de
filtrage C, C1, C2 des filtres peuvent être déterminées lors de l’installation du
système. En outre, une ou plusieurs matrices peut être recalculées au cours du
temps ou plusieurs jeux de matrices de filtrage C, C1, C2 peuvent être
prédéterminés et utilisés en fonction des besoins.
Par exemple, il est possible d’ajouter au système une fonctionnalité de suivit de la
tête d’un utilisateur. Un exemple de réalisation est décrit dans le document US
6243476. A partir de la position de la tête, il est possible de calculer ou d’utiliser
une matrice de filtrage C, C1, C2 spécifique.
L’invention permet de générer des ondes sonores pour au moins deux zones
distinctes d’un même espace avec une qualité sonore satisfaisante et une robustesse
aux déplacements, tout en limitant l’encombrement du système, c’est-à-dire le
nombre de haut-parleurs et la complexité de l’électronique de commande.
Afin de comparer les performances du système de l’invention avec les systèmes
existants, plusieurs simulations ont été réalisées.
Pour ce faire, on définit deux zones Z61 et Z62 d’un espace 5000. Au sein de
chaque zone Z61, Z62, on positionne deux points de contrôle PC1-PC4. On
commande ensuite une source seule SS, un réseau de haut-parleurs AR, un réseau
de haut-parleurs avec filtrage individuel de chaque haut-parleur AR+F et le
système de l’invention AR+I pour diffuser une onde sonore à une fréquence de
100Hz, tel qu’illustré sur la figure 17.
On observe que, dans le cas d’une source seule SS à basse-fréquences, les zones
Z61, Z62 reçoivent une intensité sonore sensiblement homogène comprise entre -5
et 5dB. La directivité est très faible et les zones Z61, Z62 ne sont pas différentiées.
Dans le cas d’un réseau de haut-parleurs AR, les zones Z61, Z62 reçoivent une
intensité sonore similaire à la source seule SS, comprise entre -5 et 5dB. La
directivité est toujours très faible et les zones Z61, Z62 ne sont pas différentiées.
Dans le cas d’un réseau de haut-parleurs avec filtrage individuel de chaque haut-
parleur AR+F, on observe que la zone Z61 présente un niveau sonore proche de -

26

30dB, tandis que la zone Z62 présente un niveau sonore compris entre 0 et 5dB. Il
y a donc différentiation du niveau sonore entre les zones Z61, Z62.
Dans le cas du système de l’invention AR+I, on observe que la zone Z61 présente
également un niveau sonore entre -20dB et -30dB, tandis que la zone Z62 présente
un niveau sonore compris entre 0 et 5dB. Il y a donc également différentiation du
niveau sonore entre les zones Z61, Z62. A 100Hz, les résultats entre l’invention
AR+I et un réseau de haut-parleurs avec filtrage individuel de chaque haut-parleur
AR+F sont comparables.
La figure 18 illustre les mêmes éléments commandés pour diffuser une onde
sonore à une fréquence de 1000Hz.
On observe que, dans le cas d’une source seule SS, les zones Z61, Z62 reçoivent
une intensité sonore sensiblement homogène comprise entre -5 et 5dB. La
directivité est très faible et les zones Z61, Z62 ne sont pas différentiées.
Dans le cas d’un réseau de haut-parleurs AR, on observe que la zone Z61 présente
un niveau sonore entre -10dB et -20dB, tandis que la zone Z62 présente un niveau
sonore compris entre 0 et 5dB. Il y a donc différentiation du niveau sonore entre
les zones Z61, Z62.
Dans le cas d’un réseau de haut-parleurs avec filtrage individuel de chaque haut-
parleur AR+F, on observe que la zone Z61 présente un niveau sonore compris
entre -30dB et -15dB, tandis que la zone Z62 présente un niveau sonore compris
entre -5 et 5dB. Il y a donc bien différentiation du niveau sonore entre les zones
Z61, Z62. Cependant, on observe que les zones Z61 et Z62 comportent des raies
d’intensité. Autrement formulé, l’intensité sonore peut varier brutalement,
typiquement de -5dB à 5dB au sein d’une zone Z62 lors du passage d’une raie à
l’autre. Ainsi, ce système permet une très bonne isolation sonore puisque les points
de contrôle PC1-PC4 sont chacun positionnés dans une raie différente, mais ce
système n’est pas suffisamment robuste si l’utilisateur se déplace au sein des zones
Z61, Z62 par rapport aux points de contrôle PC1-PC4.
Dans le cas du système de l’invention AR+I, on observe que la zone Z61 présente
un niveau sonore proche de -30dB, tandis que la zone Z62 présente un niveau
sonore compris entre 0 et 5dB. Il y a donc bien différentiation du niveau sonore

27

entre les zones Z61, Z62. En outre, l’intensité sonore est sensiblement homogène
sur toute la surface de la zone Z61, Z62, ce qui permet d’obtenir une bonne
robustesse par rapport aux déplacements de l’utilisateur au sein des zones Z61,
Z62 par rapport aux points de contrôle PC1-PC4.
Tel qu’illustré sur la figure 19, les mêmes éléments sont commandés pour diffuser
une onde sonore à une fréquence de 5000 Hz.
On observe que dans le cas d’une source seule SS en haute-fréquences, les zones
Z61, Z62 reçoivent une intensité sonore sensiblement homogène comprise entre -5
et 0dB. La directivité est très faible et les zones Z61, Z62 ne sont pas différentiées.
Dans le cas d’un réseau de haut-parleurs AR, on observe que la zone Z61 présente
un niveau sonore homogène de -30dB, tandis que la zone Z62 présente un niveau
sonore compris entre 0 et 5dB. Il y a donc différentiation du niveau sonore entre
les zones Z61, Z62.
Dans le cas d’un réseau de haut-parleurs avec filtrage individuel de chaque haut-
parleur AR+F, on observe que la zone Z61 présente un niveau sonore compris
entre -30dB et -20dB, tandis que la zone Z62 présente un niveau sonore compris
entre -30 et 5dB. Il y a donc bien différentiation du niveau sonore entre les zones
Z61, Z62. Cependant, on observe que les zones Z61 et Z62 comportent également
des raies d’intensité. Ainsi, l’intensité sonore peut varier brutalement au sein des
zones Z61 et Z62 lors du passage d’une raie à l’autre. Par exemple, au sein de la
zone Z62, si les utilisateurs se déplacent au sein des zones Z61, Z62 par rapport
aux points de contrôle PC1-PC4, l’intensité sonore qu’ils reçoivent peut
brutalement passer de 0dB à -30dB. Ainsi, ce système permet une très bonne
isolation sonore puisque les points de contrôle PC1-PC4 sont chacun positionnés
sur une raie différente, mais ce système n’est pas suffisamment robuste si les
’utilisateurs se déplacent au sein des zones Z61, Z62 par rapport aux points de
contrôle PC1-PC4.
Dans le cas du système de l’invention AR+I, on observe que on observe que la
zone Z61 présente un niveau sonore homogène de -30dB, tandis que la zone Z62
présente un niveau sonore compris entre 0 et 5dB. Il y a donc bien différentiation
du niveau sonore entre les zones Z61, Z62. En outre, l’intensité sonore est

28

sensiblement homogène sur toute la surface de chaque zone Z61, Z62, ce qui
permet d’obtenir une meilleure robustesse par rapport aux déplacements de
l’utilisateur.
Selon un autre exemple, illustré à la figure 20, l’invention permet d’obtenir une
bonne isolation dans les zones, tout en conservant un intensité sonore suffisante.
Ainsi, sur la figure 20, la courbe 170 représente le niveau d’isolation acoustique
simulé entre deux points de contrôles PC1 et PC2 situées dans une première zone,
et les points de contrôle PC3 et PC4 situées dans une seconde zone pour un réseau
de haut-parleur seul AR. Le niveau d’isolation acoustique NIA peut-être calculé à
partir de la différence d’énergie acoustique entre les deux zones, tel que :
[Math7]

L’isolation acoustique NIA est quasiment nulle en basse fréquence car le réseau
n’est pas directif. L’isolation acoustique NIA est plus importante entre 1 kHz et 9
kHz avec un niveau maximum de 60 dB à 6 kHz. Le niveau d’isolation NIA chute
après 9 kHz, en raison de la présence de lobes secondaires dans la directivité du
réseau. Ces lobes secondaires sont dirigés vers la zone Z61, Z62 où il est
recherché de limiter au maximum l’intensité sonore, ce qui tend à diminuer
l’isolation de la zone Z61, Z62.
La courbe 150 représente l’évolution de l’isolation acoustique NIA en fonction de
la fréquence pour un réseau de haut-parleur traité individuellement. L’isolation
acoustique NIA est constante à environ 30 dB entre 0 et 100 Hz, puis un plateau
d’intensité est observé entre 1000 Hz et 20 kHz. Pour ce plateau, l’intensité sonore
est comprise entre 80 et 110 dB à la position pour laquelle les filtres ont été
optimisés. Avec un traitement individuel sur chaque haut-parleur, il est donc
possible d’atteindre une isolation acoustique importante, mais avec une faible
robustesse contre les mouvements de tête en haute-fréquences.
La courbe 160 représente l’évolution de l’isolation acoustique NIA en fonction de
la fréquence pour un système selon l’invention. L’isolation acoustique NIA est
sensiblement constante entre 20 et 30 dB pour des fréquences comprises entre 0 et
100 Hz. Un pic d’intensité est localisé entre 1 kHz et 10 kHz. Pour ce pic,

29

l’isolation acoustique atteint au maximum théorique de 120 dB. On observe
également que le niveau d’isolation chute en haute-fréquence, c’est-à-dire vers
8000 Hz, principalement à cause de l’apparition des lobe secondaires orienté vers
la zone dans laquelle on souhaite minimiser l’intensité sonore. Cependant, avec
l’invention, il est possible d’augmenter le nombre de haut-parleurs constitutifs du
réseau, tout en conservant la longueur totale du réseau avec un minimum de
changements structurels du système puisque le nombre de filtre reste inchangé. La
solution de l’invention permet donc plus de flexibilité et de robustesse tout en
rendant possible le cumul d’une bonne intensité sonore et d’une bonne isolation.
Dans un mode de réalisation illustré à la figure 21, il est possible de privilégier
l’une ou l’autre des méthodes de sonorisation en fonction de la fréquence, ou
encore de combiner plusieurs méthodes. Ainsi, à titre d’exemple, pour un réseau de
haut-parleurs large bande, il est possible de réaliser un filtrage individuel AR+F de
chaque haut-parleur constitutif du réseau ou encore de ne réaliser un filtrage
individuel que sur certains haut-parleurs constitutifs du réseau lorsque la fréquence
est inférieure à la fréquence de coupure Fc du système car ce filtrage produit les
meilleurs résultats sonores. Lorsque la fréquence est supérieure à la fréquence de
coupure Fc, le système de l’invention AR+I est utilisé car il produit de meilleurs
résultats en termes de robustesse contre les mouvements de tête pour les
fréquences élevées. Dans cet exemple, la fréquence de coupure Fc est comprise
entre 1000 et 10000 Hz, et est par exemple égale à 3000 Hz.

30

REVENDICATIONS

1. Système de génération d’ondes sonores pour au moins deux zones
distinctes (Z31, Z32, Z41, Z42, Z51, Z52, Z61, Z62) d’un même espace
(3000, 4000, 5000) ; ledit système comportant pour chaque zone (Z31, Z32,
Z41, Z42, Z51, Z52, Z61, Z62) dudit espace (3000, 4000, 5000) :
- au moins un réseau (R21, R22, R31, R32, R41, R42) de haut-parleurs aigu
(HPA21, HPA22, HPA31, HPA32, HPA41-HPA48, HPA51) comportant au
moins trois haut-parleurs aigu (HPA21, HPA22, HPA31, HPA32, HPA41-
HPA48, HPA51) de sorte à former au moins une onde sonore directive ; et
- au moins un haut-parleur de grave (HPG21, HPG22, HPG41-HPG48) ;
ledit système comportant également des moyens de traitement audio des
signaux transmis aux haut-parleurs; lesdits moyens de traitement audio
commandant au moins un haut-parleur pour générer des ondes sonores
destructives (Od35-Od38, Od45-Od48) dans au moins une zone (Z31, Z32,
Z41, Z42, Z51, Z52, Z61, Z62) dudit espace (3000, 4000, 5000) et obtenir
des contenus sonores distincts dans lesdites au moins deux zones (Z31, Z32,
Z41, Z42, Z51, Z52, Z61, Z62) distinctes dudit espace (3000, 4000, 5000);
chaque contenu sonore de chaque zone (Z31, Z32, Z41, Z42, Z51, Z52,
Z61, Z62) résultant de la somme des ondes sonores propagées dans ladite
zone (Z31, Z32, Z41, Z42, Z51, Z52, Z61, Z62), caractérisé en ce que
lesdits moyens de traitement audio commandent individuellement chaque
haut-parleur de grave (HPG21, HPG22, HPG41-HPG48) et mutuellement
chaque réseau (R21, R22, R31, R32, R41, R42) de haut-parleurs aigu
(HPA21, HPA22, HPA31, HPA32, HPA41-HPA48, HPA51) pour générer
les ondes sonores destructives (Od35-Od38, Od45-Od48), les ondes sonores
destructives (Od35-Od38, Od45-Od48) étant déterminées dans une zone
cible en estimant l’ensemble des signaux générés dans cette zone et les
fonctions de transfert entre les différents haut-parleurs et les différentes
zones pour différentes fréquences.

31

2. Système selon la revendication 1, caractérisé en ce que plusieurs zones
(Z31, Z32, Z41, Z42, Z51, Z52, Z61, Z62) dudit espace (3000, 4000, 5000)
sont sonorisées par un même réseau (R21, R22, R31, R32, R41, R42) de
haut-parleurs aigu (HPA21, HPA22, HPA31, HPA32, HPA41-HPA48,
HPA51) formant au moins deux ondes sonores directives.

3. Système selon la revendication 1 ou 2, caractérisé en ce que, l’espace
(3000, 4000, 5000) comportant au moins quatre zones (Z31, Z32, Z41, Z42,
Z51, Z52, Z61, Z62), le système comprend au moins quatre ondes sonores
directives et au moins quatre haut-parleurs de grave (HPG21, HPG22,
HPG41-HPG48) ; lesdits moyens de traitement audio commandant :
- chaque haut-parleur de grave (HPG21, HPG22, HPG41-HPG48) associé à
une zone (Z31, Z32, Z41, Z42, Z51, Z52, Z61, Z62) cible pour générer des
ondes sonores destructives (Od35-Od38, Od45-Od48) destinées à limiter les
ondes sonores générées (Os35-Os38, Os45-Os48), dans la zone (Z31, Z32,
Z41, Z42, Z51, Z52, Z61, Z62) cible, par les haut-parleurs de grave
(HPG21, HPG22, HPG41-HPG48) associés à d’autre zones (Z31, Z32, Z41,
Z42, Z51, Z52, Z61, Z62) ; et
- chaque réseau (R21, R22, R31, R32, R41, R42) de haut-parleur aigu
(HPA21, HPA22, HPA31, HPA32, HPA41-HPA48, HPA51) associé à une
zone (Z31, Z32, Z41, Z42, Z51, Z52, Z61, Z62) cible pour générer des
ondes sonores destructives (Od35-Od38, Od45-Od48) destinées à limiter les
ondes sonores générées (Os35-Os38, Os45-Os48), dans la zone (Z31, Z32,
Z41, Z42, Z51, Z52, Z61, Z62) cible, par les réseaux (R21, R22, R31, R32,
R41, R42) de haut-parleurs aigu (HPA21, HPA22, HPA31, HPA32,
HPA41-HPA48, HPA51) associés à d’autre zones (Z31, Z32, Z41, Z42,
Z51, Z52, Z61, Z62).

4. Système selon la revendication 1 ou 2, caractérisé en ce que les moyens
de traitement audio comportent au moins un filtre passe-bas (Pb) et au
moins un filtre passe-haut (Ph) permettant de scinder le signal transmis aux

32

haut-parleurs en au moins un signal haute-fréquences transmis aux réseaux
(R21, R22, R31, R32, R41, R42) de haut-parleurs aigu (HPA21, HPA22,
HPA31, HPA32, HPA41-HPA48, HPA51) et au moins un signal basse-
fréquences transmis aux haut-parleurs de grave (HPG21, HPG22, HPG41-
HPG48).

5. Système selon la revendication 3, caractérisé en ce qu’il comprend au
moins un haut-parleur large bande (HPLB, HPLB1, HPLB2) constituant à
la fois un haut-parleur de grave (HPG21, HPG22, HPG41-HPG48) et un
haut-parleur aigu (HPA21, HPA22, HPA31, HPA32, HPA41-HPA48,
HPA51) d’un réseau (R21, R22, R31, R32, R41, R42), ledit haut-parleur
large bande (HPLB, HPLB1, HPLB2) recevant au moins un signal haute-
fréquences et au moins un signal basse-fréquences.

6. Système selon l’une des revendications 1 à 4, caractérisé en ce que le
système comporte, pour chaque zone (Z31, Z32, Z41, Z42, Z51, Z52, Z61,
Z62) dudit espace (3000, 4000, 5000), entre 2 et 6 haut-parleurs de grave
(HPG21, HPG22, HPG41-HPG48) et un réseau (R21, R22, R31, R32, R41,
R42) comportant entre 10 et 20 haut-parleurs aigu (HPA21, HPA22,
HPA31, HPA32, HPA41-HPA48, HPA51).

7. Système selon l’une des revendications 1 à 4, caractérisé en ce que le
système comporte en outre des moyens de détection de la position de la tête
de l’utilisateur, les moyens de traitement audio commandant l’au moins un
haut-parleur de grave (HPG21, HPG22, HPG41-HPG48) et l’au moins un
réseau (R21, R22, R31, R32, R41, R42) de haut-parleurs aigu (HPA21,
HPA22, HPA31, HPA32, HPA41-HPA48, HPA51) pour générer les ondes
sonores destructives (Od35-Od38, Od45-Od48) en fonction de la position
de la tête de l’utilisateur.

33

8. Procédé de détermination d’au moins une matrice de filtrage associée à
au moins un haut-parleur de grave (HPG21, HPG22, HPG41-HPG48) et au
moins un réseau (R21, R22, R31, R32, R41, R42) de haut-parleurs aigu
(HPA21, HPA22, HPA31, HPA32, HPA41-HPA48, HPA51) du système
selon l’une des revendications 1 à 5, ledit procédé comportant les étapes
suivantes :
- mesure et/ou simulation (101) d’une première matrice de propagation (H1)
entre les différents haut-parleurs de grave (HPG21, HPG22, HPG41-
HPG48) et les différentes zones (Z31, Z32, Z41, Z42, Z51, Z52, Z61, Z62) ;
- mesure et/ou simulation (102) d’une seconde matrice de propagation (H2)
entre les réseaux (R21, R22, R31, R32, R41, R42) de haut-parleurs aigu
(HPA21, HPA22, HPA31, HPA32, HPA41-HPA48, HPA51) et les
différentes zones (Z31, Z32, Z41, Z42, Z51, Z52, Z61, Z62), chaque
matrice de propagation (H1-H2) incluant les fonctions de transfert entre
chaque haut-parleur de grave (HPG21, HPG22, HPG41-HPG48) ou
réseau (R21, R22, R31, R32, R41, R42) de haut-parleurs aigu (HPA21,
HPA22, HPA31, HPA32, HPA41-HPA48, HPA51) et chaque zone (Z31,
Z32, Z41, Z42, Z51, Z52, Z61, Z62);
- détermination (103) d’une première matrice objectif (M1) à partir de la
première matrice de propagation (H1) en annulant les fonctions de transfert
dans les zones (Z31, Z32, Z41, Z42, Z51, Z52, Z61, Z62) destinées à
recevoir les ondes sonores destructives (Od35-Od38, Od45-Od48) ;
- détermination (104) d’une seconde matrice objectif (M2) à partir de la
seconde matrice de propagation (H2) en annulant les fonctions de transfert
dans les zones (Z31, Z32, Z41, Z42, Z51, Z52, Z61, Z62) destinées à
recevoir les ondes sonores destructives (Od35-Od38, Od45-Od48) ;
- calcul (105) d’une première matrice de filtrage (C1) correspondant au
produit de la matrice inverse de la première matrice de propagation (H1) et
de la première matrice objectif (M1), et

34

- calcul (106) d’une seconde matrice de filtrage (C2) correspondant au
produit de la matrice inverse de la seconde matrice de propagation (H2) et
de la seconde matrice objectif (M2).

9. Procédé de selon la revendication 7, caractérisé en ce qu’il comporte en
outre une étape de calcul (107) d’une matrice de filtrage commune (C) à
partir des première et seconde matrices de filtrage (C1, C2).

10. Procédé selon l’une des revendications 7 ou 8, caractérisé en ce que la
mesure et/ou simulation (101) de la première et/ou de la seconde matrice de
propagation (H1, H2) étant réalisée en au moins deux point de contrôle, les
fonctions de transfert entre chaque haut-parleur de grave (HPG21, HPG22,
HPG41-HPG48) ou réseau (R21, R22, R31, R32, R41, R42) de haut-
parleurs aigu (HPA21, HPA22, HPA31, HPA32, HPA41-HPA48, HPA51)
et chaque zone (Z31, Z32, Z41, Z42, Z51, Z52, Z61, Z62) sont obtenues en
calculant plusieurs filtres (F31-F34, F41-F44) pour chaque point de contrôle
(PC1-PC4) situés dans les différentes zones (Z31, Z32, Z41, Z42, Z51, Z52,
Z61, Z62).

11. Procédé selon l’une des revendications 7 ou 8, caractérisé en ce que
l’au moins une matrice de filtrage (C1, C2, C) est sélectionnée parmi un
ensemble de matrices de filtrage (C1, C2, C) calculées pour différents
points de contrôle ou ensemble de points de contrôle, en fonction de la
position de la tête de l’utilisateur.

1-

35

ABREGE

L’invention concerne un système de génération d’ondes sonores pour au moins
deux zones (Z31, Z32) distinctes d’un même espace (3000). Le système comporte
pour chaque zone (Z31, Z32) dudit espace (3000) : au moins un réseau (R21, R22)
de haut-parleurs aigu (HPA21, HPA22) formant une onde sonore directive ; et au
moins un haut-parleur de grave (HPG21, HPG22). Le système comporte également
des moyens de traitement audio des signaux transmis aux haut-parleurs (HPG21,
HPG22, HPA21, HPA22) commandant au moins un haut-parleur (HPG21, HPG22,
HPA21, HPA22) pour générer des ondes sonores destructives (Od35-Od38) dans
au moins une zone (Z31, Z32) dudit espace (3000) et obtenir des contenus sonores
distincts dans lesdites au moins deux zones (Z31, Z32) distinctes dudit espace
(3000). Pour ce faire, les moyens de traitement audio commandent
individuellement chaque haut-parleur de grave (HPG21, HPG22) et mutuellement
chaque réseau (R21, R22) de haut-parleurs aigu (HPA21, HPA22) pour générer les
ondes sonores destructives (Od35-Od38).

Figure pour l’abrégé : Fig 3"""

def call_chat_gpt(messages, json_format=False, max_tokens=2000, temperature=1.0, n=1, frequency_penalty=0, presence_penalty=0, top_p=1.0):

    client = AzureOpenAI(
        api_version="2023-03-15-preview",
        azure_endpoint="https://dev-france-hoomano.openai.azure.com/",
        azure_deployment='gpt4-turbo',
        api_key="fc10e0d97eff46b3a448d5914affbf72",
    )

    completion = client.chat.completions.create(
        model='gpt4-turbo',
        messages= messages,
        response_format={"type": "json_object"} if json_format else None,
       max_tokens=max_tokens, temperature=temperature, 
       top_p=top_p,
       n=n, frequency_penalty=frequency_penalty, presence_penalty=presence_penalty
    )
    return completion.choices[0].message.content

with open("./prompt.txt", "r") as f:
    prompt = Template(f.read()).render(patent = patent)

try:
    response = call_chat_gpt([{"role": 'user', 'content': prompt}],
                            max_tokens=2000, temperature=0, top_p=1)
    print(response)


    # 1. split the response by '\n'
    keywords = response.split("\n")
    # remove last one to avoid not complete keyword
    keywords = keywords[:-1]

    # 2. for each keyword, split by '=>'; first part is French, second part is English
    # create a dictionary with French as key and English as value
    lexical_field_dict = {}
    for keyword in keywords:
        if "=>" in keyword:
            source_language_keyword, target_language_keyword = keyword.split("=>")
            lexical_field_dict[source_language_keyword.strip().lower()] = target_language_keyword.strip().lower()
    #print(lexical_field_dict)
    print(len(lexical_field_dict))
    # 3. For each keyword, check if it appears at least 4 times in the original text
    # if it does, add it to the final dict
    final_dict = {}
    for source_language_keyword, target_language_keyword in lexical_field_dict.items():
        if patent.lower().count(source_language_keyword) >= 4:
            final_dict[source_language_keyword] = target_language_keyword
    print(len(final_dict))
    print(final_dict)

    # prepare a string with keyword1 => keyword1trad \n keyword2 => keyword2trad
    response = ""
    for source_language_keyword, target_language_keyword in final_dict.items():
        response += f"{source_language_keyword} => {target_language_keyword}\n"
    response = response.strip()

    # create a markdown table with the final dict
    table = "| French | English |\n| --- | --- |\n"
    for source_language_keyword, target_language_keyword in final_dict.items():
        table += f"| {source_language_keyword} | {target_language_keyword} |\n"

    print(table)

except Exception as e:
    print(f"🔴 error with response: {response}")
        
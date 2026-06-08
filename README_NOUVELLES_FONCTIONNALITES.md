# 🎯 Nouvelles Fonctionnalités - Flot Maximal

## 1. Affichage Direct du Flot Maximal ⚡
**Bouton : "🎯 Flot maximal direct"**

Au lieu de parcourir toutes les étapes, vous pouvez maintenant voir directement le résultat final du flot maximal en cliquant sur ce bouton. Il vous amène à la dernière étape de Ford-Fulkerson où le flot est maximal.

---

## 2. Zoom et Dézoom 🔍
**Contrôle : Molette de la souris**

- **Molette vers le haut** : Zoom avant
- **Molette vers le bas** : Zoom arrière
- **Limite** : 0.5x à 3.0x (fixée pour éviter de perdre les détails ou de trop zoomer)

Le zoom se fait au niveau du graphe matplotlib, permettant de voir les détails ou la vue d'ensemble selon vos besoins.

---

## 3. Déplacement du Graphe (Pan) 🖱️
**Contrôle : Clic gauche maintenu + déplacement**

1. Maintenez le **clic gauche** sur le graphe
2. Déplacez la souris pour **panoramiser** le graphe
3. Relâchez le bouton pour arrêter

Cela permet de naviguer dans le graphe sans zoomer, utile si certains nœuds ou arcs tombent en dehors du cadre visible.

**Combination pratique** : Zoomez pour voir un détail, puis deplacerez pour explorer d'autres parties du graphe.

---

## 4. Comprendre Pourquoi Certains Éléments Ne S'Affichent Pas 🤔

### Pourquoi des nœuds ne s'affichent pas ?
- **Raison** : Le layout NetworkX (spring_layout avec seed=42) positionne les nœuds de manière force-directed. Certains nœuds peuvent tomber légèrement en dehors de la zone d'affichage (-1.3 à 1.3).
- **Solution** :
  1. Utilisez la **molette pour zoomer**
  2. Utilisez **clic gauche maintenu pour panoramiser**
  3. Relancez la résolution (qui recalcule les positions)

### Pourquoi des arcs ne s'affichent pas ?
- **Raison** : Un arc nécessite que ses deux nœuds d'extrémité aient des coordonnées calculées. Si un nœud manque, l'arc ne peut pas être dessiné.
- **Code** : La fonction `_dessiner_arc()` vérifie :
  ```python
  if i not in positions or j not in positions:
      return  # Arc ignoré silencieusement
  ```
- **Solution** : Même que ci-dessus (zoom et pan, ou relancer)

### Pourquoi les étiquettes Ford-Fulkerson ne s'affichent pas ?
- **Raison** : Les étiquettes s'affichent seulement sur les nœuds ayant été marqués pendant l'étiquetage BFS. Un nœud non atteint n'a pas d'étiquette.
- **Exemple** : Si le puits n'est jamais atteint, il n'aura pas d'étiquette, ce qui signifie que le flot est déjà maximal.

---

## 5. Structure du Code - Où Chercher ?

### Zoom & Pan
- **Fichier** : [interface.py](interface.py)
- **Méthodes** :
  - `_on_scroll()` : Gère l'événement scroll (molette)
  - `_on_press()` : Début du drag (clic gauche)
  - `_on_release()` : Fin du drag
  - `_on_motion()` : Déplacement en temps réel
  - `_update_graph_view()` : Applique zoom et pan aux axes matplotlib

### Flot Maximal Direct
- **Fichier** : [interface.py](interface.py)
- **Méthode** : `_afficher_flot_maximal_direct()`
- **Bouton** : Créé dans `_construire_panneau_gauche()`

### Affichage du Graphe
- **Fichier** : [graphe.py](graphe.py)
- **Fonction** : `dessiner_graphe()`
- **Note** : Vérifie les limites d'affichage et applique les limites des axes

---

## 6. Limitations Connues et Conseils

1. **Layout non optimal pour les grands graphes** : Si vous avez plus de 20 nœuds, le layout force-directed peut produire des chevauchements. Essayez de relancer plusieurs fois.

2. **Positions fixes** : Une fois calculées (avec seed=42), les positions restent identiques pour une même entrée. C'est intentionnel (reproductibilité).

3. **Molette non détectée** : Sur certains systèmes, l'événement scroll peut ne pas être détecté. Essayez un clic droit + déplacement (dépend du système).

4. **Pan très rapide** : Ajustez la sensibilité en modifiant les variables `self.zoom_level` et `self.pan_x / pan_y` dans `interface.py`.

---

## 7. Exemple d'Utilisation

1. Lancez l'app : `python main.py`
2. Cliquez **"Exemple"** pour charger un réseau pré-rempli
3. Cliquez **"Résoudre"** pour lancer les algorithmes
4. Cliquez **"🎯 Flot maximal direct"** pour voir directement le résultat
5. Utilisez la **molette** pour zoomer
6. Maintenez **clic gauche** et déplacez pour explorer
7. Utilisez **"◀ Préc." et "Suiv. ▶"** pour revoir les étapes si souhaité

---

**Bon calcul ! 🚀**

---

## 8. Changements récents (à jour)

- Suppression du **mode création** graphique dans l'interface : l'édition et la création interactive via le panneau de création ont été retirées pour simplifier l'usage.
- **Déplacement d'un sommet par clic droit :** vous pouvez maintenant déplacer un sommet directement dans la zone de visualisation en cliquant droit sur le sommet, déplacer la souris puis relâcher le bouton pour valider sa nouvelle position.
- **Placement ordonné des sommets :** le calcul des positions (`calculer_positions` dans `graphe.py`) place désormais la source à gauche, le puits à droite, et répartit les sommets intermédiaires selon leur distance depuis la source (ordre gauche→droite). Cela facilite la lecture des flux et des chemins.
- **Taille et style des pointes de flèche ajustés :** la forme et l'échelle des pointes d'arc ont été rendues configurables (`head_length`, `head_width`, `mutation_scale`) pour améliorer la lisibilité; modifiez ces paramètres dans `_dessiner_arc()` de `graphe.py` si besoin.

## 9. Où mettre à jour la documentation si besoin

- Interface / interactions : `interface.py`
- Dessin des arcs / layout : `graphe.py`
- Constantes d'apparence (couleurs, tailles) : `constantes.py`

Si tu veux, j'ajoute ici un court exemple montrant comment changer la taille des pointes (valeurs recommandées). Veux-tu que je l'insère ?

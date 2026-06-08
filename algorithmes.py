"""
algorithmes.py
──────────────
Contient la classe FlotMaximal qui implémente les deux algorithmes
de résolution décrits dans la documentation :

  1. Manuel Bloch  → construction d'un flot complet
  2. Ford-Fulkerson → optimisation vers le flot maximal (étiquetage)

Aucune dépendance vers l'interface graphique : ce fichier peut être
importé et testé de manière totalement indépendante.
"""

import copy


class FlotMaximal:
    """
    Résout le problème de flot maximal sur un réseau de transport.

    Paramètre
    ---------
    capacites : dict  {(i, j): capacité}
        Dictionnaire des arcs et de leurs capacités (entiers positifs).

    Attributs publics après construction
    -------------------------------------
    source  : nœud sans prédécesseur (entrée du réseau)
    puits   : nœud sans successeur   (sortie du réseau)
    sommets : ensemble de tous les nœuds
    C       : dictionnaire des capacités (copie interne)
    """

    def __init__(self, capacites: dict):
        self.C       = capacites
        self.sommets = set()
        for (i, j) in capacites:
            self.sommets.add(i)
            self.sommets.add(j)
        self.source = None
        self.puits  = None
        self._detect_source_puits()

    # =========================================================================
    # Détection automatique de la source et du puits
    # =========================================================================

    def _detect_source_puits(self):
        """
        La source est le seul nœud sans prédécesseur (degré entrant = 0).
        Le puits  est le seul nœud sans successeur  (degré sortant = 0).
        """
        pred = {s: set() for s in self.sommets}
        succ = {s: set() for s in self.sommets}
        for (i, j) in self.C:
            succ[i].add(j)
            pred[j].add(i)
        for s in self.sommets:
            if not pred[s]:
                self.source = s
            if not succ[s]:
                self.puits = s

    # =========================================================================
    # ALGORITHME 1 : Manuel Bloch
    # =========================================================================

    def manuel_bloch(self):
        """
        Construit un flot complet selon l'algorithme de Manuel Bloch.

        Principe (fidèle à la documentation) :
        ----------------------------------------
        Initialisation : flux φ(I,J) = 0, résidu ρ(I,J) = C(I,J) pour tout arc.

        Étape courante :
          1. Parmi les arcs praticables (résidu > 0, non bloqués),
             choisir celui de résidu minimal → arc (I0, J0), δ = ρ(I0,J0).
          2. Chercher un chemin simple source → puits passant par (I0, J0).
             • Pas de chemin         → bloquer (I0, J0).
             • Circuit dans le chemin → bloquer l'arc de résidu min du circuit.
             • Chemin élémentaire    → faire passer δ sur tous les arcs du chemin.
          3. Répéter jusqu'à ce qu'il n'y ait plus d'arcs praticables.

        Retourne
        --------
        f      : dict {arc: flux}          — flot complet final
        r      : dict {arc: résidu}        — capacités résiduelles finales
        etapes : list[dict]                — états intermédiaires pour l'animation
        """
        C      = self.C
        f      = {arc: 0      for arc in C}   # flux courant
        r      = {arc: C[arc] for arc in C}   # capacité résiduelle courante
        bloque = set()                         # arcs bloqués
        etapes = []

        # --- État initial ---
        etapes.append({
            "titre":      "Initialisation (Manuel Bloch)",
            "desc":       "Tous les flux sont initialisés à 0.\n"
                          "La capacité résiduelle ρ(I,J) = C(I,J) pour chaque arc.",
            "flot":       copy.deepcopy(f),
            "residu":     copy.deepcopy(r),
            "chemin":     [],
            "bloque":     set(),
            "arc_choisi": None,
        })

        iteration = 0
        while True:
            iteration += 1

            # Arcs praticables : résidu > 0 et non bloqués
            praticables = [(arc, r[arc]) for arc in C
                           if r[arc] > 0 and arc not in bloque]
            if not praticables:
                break   # Plus d'arcs disponibles → fin

            # Choisir l'arc de résidu minimal
            arc_choisi, delta = min(praticables, key=lambda x: x[1])
            i0, j0 = arc_choisi

            # Chercher un chemin passant par cet arc
            chemin = self._chemin_via(arc_choisi, r, bloque)

            # --- Cas 1 : aucun chemin → bloquer l'arc ---
            if chemin is None:
                bloque.add(arc_choisi)
                etapes.append({
                    "titre":      f"Itération {iteration} – Arc bloqué",
                    "desc":       f"Aucun chemin élémentaire passant par {i0}→{j0}.\n"
                                  f"L'arc est bloqué.",
                    "flot":       copy.deepcopy(f),
                    "residu":     copy.deepcopy(r),
                    "chemin":     [],
                    "bloque":     copy.deepcopy(bloque),
                    "arc_choisi": arc_choisi,
                })
                continue

            # --- Cas 2 : circuit dans le chemin → bloquer l'arc de résidu min ---
            circuit = self._detecter_circuit(chemin)
            if circuit:
                arc_min = min([a for a in circuit if a in r], key=lambda a: r[a])
                bloque.add(arc_min)
                etapes.append({
                    "titre":      f"Itération {iteration} – Circuit détecté",
                    "desc":       f"Un circuit a été détecté dans le chemin.\n"
                                  f"L'arc {arc_min[0]}→{arc_min[1]} (résidu min du circuit) est bloqué.",
                    "flot":       copy.deepcopy(f),
                    "residu":     copy.deepcopy(r),
                    "chemin":     chemin,
                    "bloque":     copy.deepcopy(bloque),
                    "arc_choisi": arc_choisi,
                })
                continue

            # --- Cas 3 : chemin élémentaire → faire passer δ ---
            for arc in chemin:
                f[arc] += delta
                r[arc] -= delta

            noeuds_chemin = [str(a[0]) for a in chemin] + [str(chemin[-1][1])]
            etapes.append({
                "titre":      f"Itération {iteration} – Flux δ={delta} sur le chemin",
                "desc":       f"Arc choisi : {i0}→{j0}  (résidu = {delta})\n"
                              f"Chemin : {' → '.join(noeuds_chemin)}\n"
                              f"On fait passer {delta} unités sur chaque arc du chemin.\n"
                              f"Capacité résiduelle de ces arcs diminue de {delta}.",
                "flot":       copy.deepcopy(f),
                "residu":     copy.deepcopy(r),
                "chemin":     chemin,
                "bloque":     copy.deepcopy(bloque),
                "arc_choisi": arc_choisi,
            })

        # --- État final ---
        complet   = self._est_complet(r)
        val_flot  = sum(f.get((self.source, j), 0) for j in self.sommets)
        etapes.append({
            "titre":      "Flot complet obtenu ✓" if complet else "Flot obtenu",
            "desc":       "Tout chemin source→puits contient au moins un arc saturé.\n"
                          f"Valeur du flot complet : {val_flot} unités.\n"
                          "On passe maintenant à Ford-Fulkerson pour l'optimiser.",
            "flot":       copy.deepcopy(f),
            "residu":     copy.deepcopy(r),
            "chemin":     [],
            "bloque":     copy.deepcopy(bloque),
            "arc_choisi": None,
        })
        return f, r, etapes

    # =========================================================================
    # ALGORITHME 2 : Ford-Fulkerson (étiquetage)
    # =========================================================================

    def ford_fulkerson(self, f_init: dict, r_init: dict):
        """
        Améliore le flot complet vers le flot maximal par étiquetage.

        Principe (fidèle à la documentation) :
        ----------------------------------------
        ÉTAPE 1 – Étiquetage :
          • Marquer la source (+).
          • Marquer J si l'arc (I→J) est non saturé et I déjà marqué  (sens +).
          • Marquer K si l'arc (K→L) transporte un flux > 0 et L déjà marqué (sens −).

        ÉTAPE 2 – Amélioration :
          • Si le puits est marqué : trouver une chaîne améliorante,
            calculer δ = min des résidus (sens +) ou flux (sens −),
            augmenter / diminuer les flux en conséquence.
          • Recommencer jusqu'à ce que le puits ne soit plus marquable.

        Paramètres
        ----------
        f_init : flot complet issu de Manuel Bloch
        r_init : capacités résiduelles associées

        Retourne
        --------
        f_max  : dict {arc: flux}   — flot maximal
        etapes : list[dict]         — états intermédiaires pour l'animation
        """
        f      = copy.deepcopy(f_init)
        r      = copy.deepcopy(r_init)
        etapes = []

        etapes.append({
            "titre":      "Début Ford-Fulkerson",
            "desc":       "On repart du flot complet obtenu par Manuel Bloch.\n"
                          "On va étiqueter les sommets pour trouver des chaînes améliorantes\n"
                          "et augmenter le flot à chaque itération.",
            "flot":       copy.deepcopy(f),
            "residu":     copy.deepcopy(r),
            "etiquettes": {},
            "chemin":     [],
            "delta":      0,
        })

        iteration = 0
        while True:
            iteration += 1

            # --- Étape 1 : étiquetage ---
            etiquettes, chemin_ameliorant = self._etiqueter(f, r)
            puits_atteint = (self.puits in etiquettes)

            etapes.append({
                "titre":      f"Itération {iteration} – Étiquetage",
                "desc":       f"Sommets marqués : {sorted(etiquettes.keys())}\n"
                              + ("✓ Puits atteint → une chaîne améliorante existe !"
                                 if puits_atteint
                                 else "✗ Puits non atteint → le flot est maximal."),
                "flot":       copy.deepcopy(f),
                "residu":     copy.deepcopy(r),
                "etiquettes": copy.deepcopy(etiquettes),
                "chemin":     chemin_ameliorant if puits_atteint else [],
                "delta":      0,
            })

            if not puits_atteint:
                break   # Flot maximal atteint

            # --- Étape 2 : amélioration ---
            delta = self._calculer_delta(chemin_ameliorant, f, r)
            self._augmenter_flot(chemin_ameliorant, delta, f, r)

            etapes.append({
                "titre":      f"Itération {iteration} – Augmentation  δ = {delta}",
                "desc":       f"Chaîne améliorante : {self._chemin_str(chemin_ameliorant)}\n"
                              f"δ = {delta} (minimum des résidus/flux sur la chaîne)\n"
                              f"On augmente (+) ou diminue (−) le flux de {delta} sur chaque arc.",
                "flot":       copy.deepcopy(f),
                "residu":     copy.deepcopy(r),
                "etiquettes": copy.deepcopy(etiquettes),
                "chemin":     chemin_ameliorant,
                "delta":      delta,
            })

        # --- État final ---
        val = sum(f.get((self.source, j), 0) for j in self.sommets)
        etapes.append({
            "titre":      f"🏆 Flot maximal = {val} unités",
            "desc":       f"Le puits n'est plus atteignable depuis la source.\n"
                          f"Par le théorème flot-max / coupe-min, le flot maximal est {val}.",
            "flot":       copy.deepcopy(f),
            "residu":     copy.deepcopy(r),
            "etiquettes": {},
            "chemin":     [],
            "delta":      0,
        })
        return f, etapes

    # =========================================================================
    # Méthodes internes – parcours de graphe
    # =========================================================================

    def _chemin_via(self, arc_cible, r, bloque):
        """
        Trouve un chemin simple source → puits passant par arc_cible.
        Retourne la liste des arcs du chemin, ou None si impossible.
        """
        i0, j0 = arc_cible
        if r.get(arc_cible, 0) <= 0:
            return None
        chemin1 = self._dfs(self.source, i0, r, bloque, set())
        if chemin1 is None and self.source != i0:
            return None
        chemin2 = self._dfs(j0, self.puits, r, bloque, set())
        if chemin2 is None and j0 != self.puits:
            return None
        debut = chemin1 if chemin1 else []
        fin   = chemin2 if chemin2 else []
        return debut + [arc_cible] + fin

    def _dfs(self, start, end, r, bloque, visites):
        """
        Recherche en profondeur (DFS) d'un chemin de start à end
        en suivant uniquement les arcs de résidu > 0 et non bloqués.
        """
        if start == end:
            return []
        visites = visites | {start}
        for (i, j) in self.C:
            if i == start and j not in visites \
               and r.get((i, j), 0) > 0 and (i, j) not in bloque:
                sous = self._dfs(j, end, r, bloque, visites)
                if sous is not None:
                    return [(i, j)] + sous
        return None

    def _detecter_circuit(self, chemin):
        """
        Détecte si le chemin contient un circuit (sommet visité deux fois).
        Retourne la sous-liste formant le circuit, ou None.
        """
        vus = []
        for (i, j) in chemin:
            if i in vus:
                return chemin[vus.index(i):]
            vus.append(i)
        return None

    def _est_complet(self, r):
        """
        Vérifie si le flot est complet : tout chemin source→puits
        contient au moins un arc saturé (résidu = 0).
        Revient à tester si le puits est inaccessible depuis la source
        en ne suivant que les arcs de résidu > 0.
        """
        def dfs(u, visited):
            if u == self.puits:
                return True
            visited.add(u)
            for (i, j) in self.C:
                if i == u and j not in visited and r.get((i, j), 0) > 0:
                    if dfs(j, visited):
                        return True
            return False
        return not dfs(self.source, set())

    # =========================================================================
    # Méthodes internes – Ford-Fulkerson
    # =========================================================================

    def _etiqueter(self, f, r):
        """
        Étiquetage BFS (largeur) selon Ford-Fulkerson.

        Règles d'étiquetage :
          • Arc direct  (I→J) non saturé  → marquer J avec (+I)
          • Arc inverse (K→L) à flux > 0  → marquer K avec (−L)

        Retourne (etiquettes, chemin_ameliorant).
        """
        etiquettes = {self.source: (None, "+", float("inf"))}
        pred       = {}
        file       = [self.source]

        while file:
            u = file.pop(0)
            # Arcs directs non saturés
            for (i, j) in self.C:
                if i == u and j not in etiquettes and r.get((i, j), 0) > 0:
                    etiquettes[j] = (u, "+", r[(i, j)])
                    pred[j]       = (u, "+", (i, j))
                    file.append(j)
            # Arcs inverses avec flux > 0
            for (k, l) in self.C:
                if l == u and k not in etiquettes and f.get((k, l), 0) > 0:
                    etiquettes[k] = (u, "-", f[(k, l)])
                    pred[k]       = (u, "-", (k, l))
                    file.append(k)

        # Reconstruction du chemin améliorant
        chemin = []
        if self.puits in pred:
            noeud = self.puits
            while noeud in pred:
                parent, sens, arc = pred[noeud]
                chemin.append((arc, sens))
                noeud = parent
            chemin.reverse()
        return etiquettes, chemin

    def suggestions_amelioration(self, f: dict, r: dict, max_suggestions: int = 3) -> list[str]:
        """Propose des arcs à augmenter de capacité sans modifier le graphe."""
        if self.source is None or self.puits is None:
            return []

        # Recherche des sommets atteignables dans le graphe résiduel.
        atteignables = {self.source}
        pile = [self.source]
        while pile:
            u = pile.pop()
            for (i, j) in self.C:
                if i == u and j not in atteignables and r.get((i, j), 0) > 0:
                    atteignables.add(j)
                    pile.append(j)
                if j == u and i not in atteignables and f.get((i, j), 0) > 0:
                    atteignables.add(i)
                    pile.append(i)

        suggestions = []
        for (i, j), cap in self.C.items():
            if i in atteignables and j not in atteignables and f.get((i, j), 0) >= cap:
                suggestions.append((i, j, cap))

        if not suggestions:
            return []

        lignes = []
        for i, j, cap in suggestions[:max_suggestions]:
            lignes.append(
                f"Augmenter la capacité de {i}→{j} de 1 unité (capacité actuelle {cap}) pourrait permettre un gain de flot maximal de +1 unité."
            )
        if len(suggestions) > max_suggestions:
            lignes.append(
                f"Et {len(suggestions) - max_suggestions} autre(s) arc(s) saturé(s) du min-cut pourraient aussi être analysé(s)."
            )
        return lignes

    def _calculer_delta(self, chemin, f, r):
        """
        Calcule δ = min des capacités résiduelles (sens +) ou flux (sens −)
        sur la chaîne améliorante.
        """
        delta = float("inf")
        for (arc, sens) in chemin:
            val   = r.get(arc, 0) if sens == "+" else f.get(arc, 0)
            delta = min(delta, val)
        return delta if delta != float("inf") else 0

    def _augmenter_flot(self, chemin, delta, f, r):
        """
        Met à jour flux et résidus le long de la chaîne améliorante :
          • Sens + : φ(arc) += δ,  ρ(arc) −= δ
          • Sens − : φ(arc) −= δ,  ρ(arc) += δ
        """
        for (arc, sens) in chemin:
            if sens == "+":
                f[arc] = f.get(arc, 0) + delta
                r[arc] = r.get(arc, 0) - delta
            else:
                f[arc] = f.get(arc, 0) - delta
                r[arc] = r.get(arc, 0) + delta

    def _chemin_str(self, chemin):
        """Retourne une représentation lisible d'un chemin améliorant."""
        if not chemin:
            return ""
        noeuds = [str(chemin[0][0][0])]
        for (arc, sens) in chemin:
            noeuds.append(("+" if sens == "+" else "−") + str(arc[1]))
        return " → ".join(noeuds)
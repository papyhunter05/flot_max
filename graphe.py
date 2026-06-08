"""
graphe.py
─────────
Tout ce qui concerne le dessin du réseau de transport dans matplotlib.

Responsabilités :
  • Calculer les positions des nœuds (layout NetworkX)
  • Dessiner les arcs avec leur flux/capacité et leur couleur selon l'état
  • Dessiner les nœuds avec leur couleur selon leur rôle
  • Afficher les étiquettes de Ford-Fulkerson au-dessus des nœuds

NOTE : Pourquoi certains éléments n'apparaissent pas ?
──────────────────────────────────────────────────────
1. NŒUDS MANQUANTS : Si un nœud apparaît dans les arcs mais pas sur le graphe,
   c'est probablement qu'il est tombé en dehors du layout (spring_layout avec seed=42).
   Solution : relancer la résolution ou utiliser un layout différent.

2. ARCS MANQUANTS : Si un arc n'est pas dessiné, c'est parce qu'un de ses nœuds
   n'a pas de coordonnées (x,y) calculées. La fonction _dessiner_arc() vérifie
   if i not in positions or j not in positions: return
   et ignore silencieusement cet arc.

3. ÉTIQUETTES FORD-FULKERSON : Elles s'affichent seulement quand un nœud a été
   marqué pendant l'étiquetage (nœud in etiquettes). Les nœuds non atteints
   ne reçoivent pas d'étiquette.

4. ZOOM ET PAN : Utilisez la molette pour zoomer et le clic gauche maintenu
   pour déplacer le graphe et voir les éléments en dehors de la vue.
"""

import math
import matplotlib.pyplot as plt
import networkx as nx

from constantes import (
    BG, CARD, BORDER,
    ACCENT, ACCENT2,
    GREEN, RED, ORANGE, YELLOW,
    TEXT,
)


# ─── Calcul du layout ────────────────────────────────────────────────────────

def calculer_positions(sommets, arcs) -> dict:
    """
    Calcule les coordonnées (x, y) de chaque nœud avec un ordre horizontal.

    Le nœud source est placé à gauche, le puits à droite, et les sommets
    intermédiaires sont organisés par distance depuis la source.

    Paramètres
    ----------
    sommets : ensemble / liste de nœuds
    arcs    : liste de couples (i, j) ou dictionnaire {(i,j): capacité}

    Retourne
    --------
    dict {nœud: (x, y)}
    """
    G = nx.DiGraph()
    G.add_nodes_from(sommets)
    for arc in arcs:
        G.add_edge(arc[0], arc[1])

    sources = [n for n in G.nodes if G.in_degree(n) == 0]
    puits = [n for n in G.nodes if G.out_degree(n) == 0]
    source = sources[0] if sources else None
    sink = puits[0] if puits else None

    if source is None or sink is None:
        try:
            return nx.spring_layout(G, seed=42, k=2.5)
        except Exception:
            return nx.shell_layout(G)

    distances = {}
    for n in G.nodes:
        try:
            distances[n] = nx.shortest_path_length(G, source, n)
        except nx.NetworkXNoPath:
            distances[n] = None

    reachable = [d for d in distances.values() if d is not None]
    max_layer = max(reachable) if reachable else 1
    max_layer = max(max_layer, 1)

    layers = {}
    for node, dist in distances.items():
        layer = dist if dist is not None else max_layer + 1
        layers.setdefault(layer, []).append(node)

    positions = {}
    for layer, nodes in sorted(layers.items()):
        if layer == max_layer + 1:
            x = 0.5
        elif max_layer > 0:
            x = 0.05 + 0.9 * layer / max_layer
        else:
            x = 0.5

        nodes = sorted(nodes, key=lambda n: (G.out_degree(n) - G.in_degree(n), str(n)))
        count = len(nodes)
        for idx, node in enumerate(nodes):
            if count == 1:
                y = 0.0
            else:
                y = 0.8 - idx * 1.6 / (count - 1)
            positions[node] = (x, y)

    if source in positions:
        positions[source] = (0.0, positions[source][1])
    if sink in positions:
        positions[sink] = (1.0, positions[sink][1])

    return positions


# ─── Dessin principal ────────────────────────────────────────────────────────

def dessiner_graphe(ax, solver, positions: dict, etape: dict):
    """
    Redessine entièrement le graphe dans l'axe matplotlib `ax`.

    Paramètres
    ----------
    ax        : matplotlib Axes
    solver    : instance de FlotMaximal (pour accéder à C, source, puits, sommets)
    positions : dict {nœud: (x, y)}
    etape     : dict décrivant l'état courant (flot, résidu, chemin, étiquettes…)
    
    Problèmes d'affichage ?
    ──────────────────────
    Si certains nœuds ou arcs ne s'affichent pas, c'est parce que le layout
    (calculer_positions) n'a pas pu les positionner. Consultez la console ou
    utilisez le zoom/pan (molette + clic gauche maintenu) pour explorer.
    """
    ax.clear()
    ax.set_facecolor(BG)
    ax.axis("off")
    ax.set_xlim(-1.3, 1.3)
    ax.set_ylim(-1.3, 1.3)

    if solver is None or not positions:
        return

    C      = solver.C
    f      = etape["flot"]
    chemin = etape.get("chemin", [])
    bloque = etape.get("bloque", set())
    etiq   = etape.get("etiquettes", {})

    # Construire l'ensemble des arcs qui appartiennent au chemin courant
    arcs_chemin = _arcs_dans_chemin(chemin)

    # ── Dessiner les arcs ────────────────────────────────────────────────────
    for arc in C:
        en_chemin   = arc in arcs_chemin
        est_bloque  = arc in bloque
        est_sature  = (f.get(arc, 0) >= C[arc])

        if en_chemin:
            couleur = ORANGE
            gras    = True
        elif est_bloque:
            couleur = YELLOW
            gras    = False
        elif est_sature:
            couleur = RED
            gras    = False
        else:
            couleur = GREEN
            gras    = False

        _dessiner_arc(ax, arc, positions, couleur, f.get(arc, 0), C[arc], gras)

    # ── Dessiner les nœuds ───────────────────────────────────────────────────
    for noeud in solver.sommets:
        if noeud not in positions:
            continue
        x, y = positions[noeud]

        est_source = (noeud == solver.source)
        est_puits  = (noeud == solver.puits)
        est_etiq   = (noeud in etiq)

        if est_source:
            fond, contour, txt = ACCENT,  ACCENT,  BG
        elif est_puits:
            fond, contour, txt = ACCENT2, ACCENT2, BG
        elif est_etiq:
            fond, contour, txt = ACCENT2, ACCENT2, BG
        else:
            fond, contour, txt = CARD,   BORDER,  TEXT

        cercle = plt.Circle((x, y), 0.06, color=fond,
                             linewidth=2, ec=contour, zorder=5)
        ax.add_patch(cercle)
        ax.text(x, y, str(noeud), color=txt,
                fontsize=10, fontweight="bold",
                ha="center", va="center", zorder=6)

        # Étiquette Ford-Fulkerson : (+source) ou (−précédent)
        if noeud in etiq and etiq[noeud][0] is not None:
            sens, pred = etiq[noeud][1], etiq[noeud][0]
            ax.text(x, y + 0.12, f"({sens}{pred})",
                    color=ACCENT2, fontsize=7,
                    ha="center", zorder=7)

    plt.tight_layout()


# ─── Fonctions internes ───────────────────────────────────────────────────────

def _arcs_dans_chemin(chemin) -> set:
    """
    Extrait les arcs présents dans le chemin courant.

    Le chemin peut être :
      • une liste de tuples (i, j)              → Manuel Bloch
      • une liste de ((i, j), sens)             → Ford-Fulkerson
    """
    arcs = set()
    for element in chemin:
        if isinstance(element, tuple) and len(element) == 2:
            if isinstance(element[0], tuple):
                # Format FF : ((i,j), sens)
                arcs.add(element[0])
            else:
                # Format Bloch : (i, j)
                arcs.add(element)
    return arcs


def _dessiner_arc(ax, arc, positions, couleur, flux, cap, gras=False):
    """
    Dessine un arc orienté avec son label flux/capacité.

    Utilise un léger décalage perpendiculaire pour éviter le chevauchement
    entre un arc (i→j) et son éventuel arc inverse (j→i).
    
    NOTE : Si un nœud n'est pas dans positions (rejeté lors du layout),
    l'arc ne s'affichera pas. C'est normal et prévoyable.
    """
    i, j = arc
    if i not in positions or j not in positions:
        # Arc ignoré : un de ses nœuds n'a pas de position calculée
        return

    xi, yi = positions[i]
    xj, yj = positions[j]
    lw      = 2.5 if gras else 1.5

    # Vecteur perpendiculaire (pour décaler arc direct / inverse)
    dx, dy   = xj - xi, yj - yi
    dist     = math.sqrt(dx * dx + dy * dy) or 1
    px, py   = -dy / dist, dx / dist
    dec      = 0.018

    xi2, yi2 = xi + px * dec, yi + py * dec
    xj2, yj2 = xj + px * dec, yj + py * dec

    # Flèche
    ax.annotate(
        "",
        xy=(xj2, yj2), xytext=(xi2, yi2),
        arrowprops=dict(
            arrowstyle="-|>,head_length=4,head_width=2",
            color=couleur,
            lw=lw,
            mutation_scale=4,
            shrinkA=10,
            shrinkB=10,
            connectionstyle="arc3,rad=0.1",
        ),
    )

    # Label flux / capacité au milieu de l'arc
    mx = (xi2 + xj2) / 2 + px * 0.05
    my = (yi2 + yj2) / 2 + py * 0.05
    ax.text(
        mx, my, f"{flux}/{cap}",
        color=couleur,
        fontsize=7.5,
        ha="center", va="center",
        fontweight="bold" if gras else "normal",
        bbox=dict(boxstyle="round,pad=0.2",
                  fc="#1e293b", ec="none", alpha=0.85),
        zorder=4,
    )
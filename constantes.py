"""
constantes.py
─────────────
Toutes les couleurs et constantes visuelles de l'application.
Modifier ce fichier pour changer le thème de l'interface.
"""

# ── Couleurs du thème (palette sombre) ───────────────────────────────────────

BG       = "#0f172a"   # Fond principal (bleu très foncé)
PANEL    = "#1e293b"   # Fond des panneaux secondaires
CARD     = "#263348"   # Fond des cartes / champs de saisie
BORDER   = "#334155"   # Couleur des bordures et séparateurs

ACCENT   = "#38bdf8"   # Bleu ciel  → source, titres, bouton résoudre
ACCENT2  = "#818cf8"   # Violet     → puits, sommets étiquetés (Ford-Fulkerson)

GREEN    = "#4ade80"   # Vert  → arcs non saturés
RED      = "#f87171"   # Rouge → arcs saturés
ORANGE   = "#fb923c"   # Orange → chemin / chaîne améliorante en cours
YELLOW   = "#facc15"   # Jaune → arcs bloqués (Manuel Bloch)

TEXT     = "#f1f5f9"   # Texte principal (blanc cassé)
TEXT_DIM = "#94a3b8"   # Texte secondaire (gris bleuté)

# ── Exemple de réseau préchargé ───────────────────────────────────────────────
# Reproduit l'exemple de la documentation (dépôts A,B,C → destinations D,E,F,G)
# avec une super-source S et un super-puits T.

EXEMPLE_ARCS = [
    ("S", "A", 45), ("S", "B", 25), ("S", "C", 30),
    ("A", "D", 10), ("A", "E", 15), ("A", "G", 20),
    ("B", "D", 20), ("B", "E",  5), ("B", "F", 15),
    ("C", "F", 10), ("C", "G", 15),
    ("D", "T", 30), ("E", "T", 10), ("F", "T", 20), ("G", "T", 40),
]

EXEMPLE_SOURCE = "S"
EXEMPLE_PUITS  = "T"
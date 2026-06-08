"""
widgets.py
──────────
Fonctions utilitaires pour créer les widgets tkinter réutilisables
de l'application (boutons, champs de saisie, labels de section…).

Toutes les fonctions retournent le widget créé sans l'empaqueter
(pas de .pack() ou .grid() ici) : c'est à l'appelant de le placer.
"""

import tkinter as tk
from constantes import BG, CARD, BORDER, ACCENT, TEXT, TEXT_DIM


def label_section(parent, texte: str) -> tk.Label:
    """
    Label de titre de section en majuscules, couleur accent.
    Usage : label_section(frame, "Arcs du réseau").pack(anchor="w", pady=(8,2))
    """
    return tk.Label(
        parent,
        text=texte.upper(),
        bg=BG,
        fg=ACCENT,
        font=("Helvetica", 8, "bold"),
    )


def champ_texte(parent, variable: tk.StringVar = None, largeur: int = 8) -> tk.Entry:
    """
    Champ de saisie stylisé (fond foncé, bordure fine qui s'illumine au focus).

    Paramètres
    ----------
    variable : StringVar tkinter à lier au champ (optionnel)
    largeur  : largeur en caractères
    """
    return tk.Entry(
        parent,
        textvariable=variable,
        width=largeur,
        bg=CARD,
        fg=TEXT,
        insertbackground=TEXT,      # curseur visible
        relief="flat",
        font=("Helvetica", 10),
        bd=0,
        highlightthickness=1,
        highlightbackground=BORDER,
        highlightcolor=ACCENT,
    )


def bouton(parent,
           texte: str,
           commande,
           bg: str = CARD,
           fg: str = TEXT,
           police=None) -> tk.Button:
    """
    Bouton plat stylisé avec effet de survol (activebackground).

    Paramètres
    ----------
    texte    : libellé du bouton
    commande : fonction appelée au clic
    bg       : couleur de fond  (défaut : CARD)
    fg       : couleur du texte (défaut : TEXT)
    police   : tuple tkinter font, ex. ("Helvetica", 12, "bold")
    """
    if police is None:
        police = ("Helvetica", 10, "bold")
    return tk.Button(
        parent,
        text=texte,
        command=commande,
        bg=bg,
        fg=fg,
        activebackground=ACCENT,
        activeforeground=BG,
        relief="flat",
        font=police,
        cursor="hand2",
        padx=8,
        pady=4,
        bd=0,
    )


def separateur(parent, pady: int = 10) -> tk.Frame:
    """
    Ligne horizontale fine servant de séparateur visuel.
    Usage : separateur(frame).pack(fill=tk.X, pady=10)
    """
    return tk.Frame(parent, bg=BORDER, height=1)


def ligne_arc(parent, de="", vers="", cap="", callback_suppression=None):
    """
    Crée une ligne de saisie complète pour un arc (De → Vers : Capacité).

    Retourne
    --------
    (row_frame, var_de, var_vers, var_cap)
        row_frame : tk.Frame contenant tous les widgets de la ligne
        var_*     : tk.StringVar liées aux champs
    """
    row = tk.Frame(parent, bg=BG)

    v_de   = tk.StringVar(value=de)
    v_vers = tk.StringVar(value=vers)
    v_cap  = tk.StringVar(value=cap)

    champ_texte(row, v_de,   largeur=6).pack(side=tk.LEFT, padx=2)
    tk.Label(row, text="→", bg=BG, fg=TEXT_DIM).pack(side=tk.LEFT)
    champ_texte(row, v_vers, largeur=6).pack(side=tk.LEFT, padx=2)
    champ_texte(row, v_cap,  largeur=5).pack(side=tk.LEFT, padx=2)
    tk.Label(row, text="  ", bg=BG).pack(side=tk.LEFT)

    # Bouton suppression
    from constantes import RED
    def _suppr():
        row.destroy()
        if callback_suppression:
            callback_suppression((v_de, v_vers, v_cap, row))

    tk.Button(
        row, text="✕",
        command=_suppr,
        bg=BG, fg=RED,
        relief="flat",
        cursor="hand2",
        font=("Helvetica", 9),
    ).pack(side=tk.LEFT)

    return row, v_de, v_vers, v_cap
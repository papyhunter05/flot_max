"""
main.py
───────
Point d'entrée de l'application « Flot Maximal ».

Lancement :
    python main.py

Dépendances Python :
    pip install matplotlib networkx

Structure du projet :
    main.py          ← point d'entrée (ce fichier)
    constantes.py    ← couleurs, thème, données de l'exemple
    algorithmes.py   ← FlotMaximal : Manuel Bloch + Ford-Fulkerson
    graphe.py        ← dessin du réseau (matplotlib / NetworkX)
    widgets.py       ← composants tkinter réutilisables
    interface.py     ← fenêtre principale et logique d'affichage
"""

from interface import Application


if __name__ == "__main__":
    app = Application()
    app.mainloop()
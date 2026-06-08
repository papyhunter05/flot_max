"""
interface.py
────────────
Fenêtre principale de l'application tkinter.

Responsabilités :
  • Construire et afficher tous les éléments de l'interface
  • Gérer la saisie du réseau (arcs, source, puits)
  • Déclencher la résolution (appels aux algorithmes)
  • Naviguer entre les étapes de l'animation
  • Déléguer tout le dessin du graphe au module graphe.py
"""

import tkinter as tk
from tkinter import messagebox
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# Modules du projet
from constantes import (
    BG, PANEL, CARD, BORDER,
    ACCENT, ACCENT2,
    GREEN, RED, ORANGE, YELLOW,
    TEXT, TEXT_DIM,
    EXEMPLE_ARCS, EXEMPLE_SOURCE, EXEMPLE_PUITS,
)
from widgets   import label_section, champ_texte, bouton, separateur, ligne_arc
from graphe    import calculer_positions, dessiner_graphe
from algorithmes import FlotMaximal


class Application(tk.Tk):
    """
    Fenêtre principale.

    Structure :
    ┌─────────────┬──────────────────────────────────────┐
    │  Panneau    │  Zone de visualisation (matplotlib)  │
    │  de saisie  │  + titre de phase + description      │
    │  (gauche)   │  + légende                           │
    └─────────────┴──────────────────────────────────────┘
    """

    def __init__(self):
        super().__init__()
        self.title("Flot Maximal – Manuel Bloch & Ford-Fulkerson")
        self.configure(bg=BG)
        self.state("zoomed")

        # État interne
        self.arcs_entries  = []          # liste de (var_de, var_vers, var_cap, frame)
        self.solver        = None        # instance FlotMaximal courante
        self.positions     = {}          # coordonnées des nœuds
        self.etapes_bloch  = []          # liste d'étapes Manuel Bloch
        self.etapes_ff     = []          # liste d'étapes Ford-Fulkerson
        self.etape_idx     = 0           # index dans la phase courante
        self.phase         = "bloch"     # "bloch" ou "ff"

        # Mode création de graphe interactif (désactivé en interface)
        self.mode_creation = False       # True = mode création, False = mode normal
        self.nœuds_creation = set()      # nœuds créés
        self.arcs_creation = {}          # {(i,j): capacité}
        self.nœud_en_cours = None        # nœud de départ du drag en cours
        self.nœud_a_deplacer = None      # nœud en cours de déplacement
        self.positions_creation = {}     # positions des nœuds créés

        self._construire_interface()
        self._charger_exemple()

    # =========================================================================
    # Construction de l'interface
    # =========================================================================

    def _construire_interface(self):
        """Crée les deux colonnes principales de la fenêtre."""
        # Colonne gauche : saisie
        panneau_gauche = tk.Frame(self, bg=BG, width=340)
        panneau_gauche.pack(side=tk.LEFT, fill=tk.Y)
        panneau_gauche.pack_propagate(False)

        # Colonne droite : visualisation
        panneau_droit = tk.Frame(self, bg=BG)
        panneau_droit.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self._construire_panneau_gauche(panneau_gauche)
        self._construire_panneau_droit(panneau_droit)

    # ── Panneau gauche ────────────────────────────────────────────────────────

    def _construire_panneau_gauche(self, parent):
        # En-tête coloré
        entete = tk.Frame(parent, bg=ACCENT, height=60)
        entete.pack(fill=tk.X)
        entete.pack_propagate(False)
        tk.Label(entete, text="⬡  FLOT MAXIMAL",
                 bg=ACCENT, fg=BG,
                 font=("Helvetica", 14, "bold")).pack(side=tk.LEFT, padx=16, pady=12)

        corps = tk.Frame(parent, bg=BG)
        corps.pack(fill=tk.BOTH, expand=True, padx=12, pady=8)

        separateur(corps).pack(fill=tk.X, pady=8)

        # ── Panneau tableau (arcs manuels) ──
        self.tableau_frame = tk.Frame(corps, bg=BG)
        self._construire_tableau_arcs(self.tableau_frame)
        self.tableau_frame.pack(fill=tk.X)

        # ── Panneau interactif (création graphique) ──
        self.interactif_frame = tk.Frame(corps, bg=BG)

        # ── Source / Puits ──
        label_section(corps, "Réseau de transport").pack(anchor="w", pady=(8, 2))
        self._bloc_source_puits(corps)

        # ── Résultat final ──
        separateur(corps).pack(fill=tk.X, pady=10)
        self.lbl_resultat = tk.Label(corps, text="",
                                     bg=BG, fg=YELLOW,
                                     font=("Helvetica", 12, "bold"),
                                     wraplength=300)
        self.lbl_resultat.pack(fill=tk.X)

    def _construire_tableau_arcs(self, parent):
        """Panneau de saisie manuelle (mode tableau)."""
        label_section(parent, "Arcs  (nœud_i → nœud_j : capacité)").pack(anchor="w", pady=(8, 2))
        self._entetes_table(parent)

        self.arcs_frame = tk.Frame(parent, bg=BG)
        self.arcs_frame.pack(fill=tk.X)

        # Boutons ajouter / exemple
        ligne_btn = tk.Frame(parent, bg=BG)
        ligne_btn.pack(fill=tk.X, pady=6)
        bouton(ligne_btn, "+ Ajouter arc", self._ajouter_arc_vide,
               bg=ACCENT2, fg=BG).pack(side=tk.LEFT)
        bouton(ligne_btn, "Exemple", self._charger_exemple,
               bg=CARD, fg=TEXT_DIM).pack(side=tk.RIGHT)

        # ── Bouton Résoudre ──
        separateur(parent).pack(fill=tk.X, pady=10)
        bouton(parent, "▶  Résoudre", self._resoudre,
               bg=GREEN, fg=BG,
               police=("Helvetica", 12, "bold")).pack(fill=tk.X, ipady=8)

        # ── Navigation étape par étape ──
        separateur(parent).pack(fill=tk.X, pady=10)
        label_section(parent, "Navigation étape par étape").pack(anchor="w", pady=(0, 4))

        nav = tk.Frame(parent, bg=BG)
        nav.pack(fill=tk.X)
        self.btn_prev = bouton(nav, "◀ Préc.", self._etape_precedente)
        self.btn_prev.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 4))
        self.btn_next = bouton(nav, "Suiv. ▶", self._etape_suivante)
        self.btn_next.pack(side=tk.LEFT, expand=True, fill=tk.X)

        # Bouton pour afficher directement le flot maximal
        self.btn_direct = bouton(parent, "🎯 Flot maximal direct", self._afficher_flot_maximal_direct,
                                 bg=ORANGE, fg=BG)
        self.btn_direct.pack(fill=tk.X, ipady=6, pady=6)

        # Compteur
        self.var_compteur = tk.StringVar(value="–")
        tk.Label(parent, textvariable=self.var_compteur,
                 bg=BG, fg=ACCENT,
                 font=("Helvetica", 10, "bold")).pack(pady=(6, 0))

    def _activer_mode(self, mode):
        """Active le mode de visualisation.

        Le mode création est désactivé dans cette version de l'interface.
        """
        self.mode_creation = False
        if hasattr(self, "btn_mode_zoom"):
            self.btn_mode_zoom.config(bg=ACCENT, fg=BG)
        if hasattr(self, "btn_mode_creation"):
            self.btn_mode_creation.config(bg=CARD, fg=TEXT)
        self.interactif_frame.pack_forget()
        self.tableau_frame.pack(fill=tk.X)
        self._reset_vue_graphe()

    def _initialiser_graphe_creation(self):
        """Initialise le canvas pour le mode création interactive."""
        self.ax.clear()
        self.ax.set_facecolor(BG)
        self.ax.axis("off")
        self.ax.set_xlim(-1.3, 1.3)
        self.ax.set_ylim(-1.3, 1.3)
        
        # Message d'aide
        self.ax.text(0, 0, "Cliquez pour ajouter un nœud\n"
                            "Glissez d'un nœud à un autre pour un arc\n"
                            "Ctrl+glissez pour déplacer un nœud",
                    ha="center", va="center",
                    color=TEXT_DIM, fontsize=10, style="italic")
        
        self.canvas.draw()
    def _construire_interactif(self, parent):
        """Panneau de création interactive du graphe."""
        # Instructions
        instr = tk.Frame(parent, bg=PANEL)
        instr.pack(fill=tk.X, padx=12, pady=8)
        tk.Label(instr, text="Cliquez sur le graphe pour ajouter des noeuds\n"
                             "Clic + glissez d'un noeud a un autre pour un arc\n"
                             "Ctrl + clic sur un noeud puis glissez pour le deplacer",
                 bg=PANEL, fg=TEXT_DIM, font=("Helvetica", 9),
                 justify="left").pack(anchor="w", padx=8, pady=6)

        # Boutons d'action
        btn_frame = tk.Frame(parent, bg=BG)
        btn_frame.pack(fill=tk.X, padx=12, pady=4)
        
        bouton(btn_frame, "Effacer tout", self._effacer_graphe_creation,
               bg=RED, fg=BG).pack(side=tk.LEFT, padx=2)
        bouton(btn_frame, "Valider et resoudre", self._valider_graphe_creation,
               bg=GREEN, fg=BG).pack(side=tk.LEFT, padx=2)

        # Affichage du graphe cree
        self.lbl_graph_creation = tk.Label(parent, text="",
                                           bg=BG, fg=TEXT_DIM,
                                           font=("Helvetica", 8),
                                           wraplength=300, justify="left")
        self.lbl_graph_creation.pack(fill=tk.X, padx=12, pady=4)
        self._mettre_a_jour_affichage_creation()
        separateur(parent).pack(fill=tk.X, pady=10)
        self.lbl_resultat = tk.Label(parent, text="",
                                     bg=BG, fg=YELLOW,
                                     font=("Helvetica", 12, "bold"),
                                     wraplength=300)
        self.lbl_resultat.pack(fill=tk.X)        # Instructions
        instr = tk.Frame(parent, bg=PANEL)
        instr.pack(fill=tk.X, padx=12, pady=8)
        tk.Label(instr, text="📌 Cliquez sur le graphe pour ajouter des nœuds\n"
                             "🔗 Clic + glissez d'un nœud à un autre pour un arc\n"
                             "✏️ Ctrl + clic sur un nœud puis glissez pour le déplacer",
                 bg=PANEL, fg=TEXT_DIM, font=("Helvetica", 9),
                 justify="left").pack(anchor="w", padx=8, pady=6)

        # Boutons d'action
        btn_frame = tk.Frame(parent, bg=BG)
        btn_frame.pack(fill=tk.X, padx=12, pady=4)
        
        bouton(btn_frame, "🗑️  Effacer tout", self._effacer_graphe_creation,
               bg=RED, fg=BG).pack(side=tk.LEFT, padx=2)
        bouton(btn_frame, "✓ Valider et résoudre", self._valider_graphe_creation,
               bg=GREEN, fg=BG).pack(side=tk.LEFT, padx=2)

        # Affichage du graphe créé
        self.lbl_graph_creation = tk.Label(parent, text="",
                                           bg=BG, fg=TEXT_DIM,
                                           font=("Helvetica", 8),
                                           wraplength=300, justify="left")
        self.lbl_graph_creation.pack(fill=tk.X, padx=12, pady=4)
        self._mettre_a_jour_affichage_creation()
        separateur(parent).pack(fill=tk.X, pady=10)
        self.lbl_resultat = tk.Label(parent, text="",
                                     bg=BG, fg=YELLOW,
                                     font=("Helvetica", 12, "bold"),
                                     wraplength=300)
        self.lbl_resultat.pack(fill=tk.X)

    def _bloc_source_puits(self, parent):
        """Ligne de saisie Source / Puits."""
        row = tk.Frame(parent, bg=BG)
        row.pack(fill=tk.X, pady=4)

        tk.Label(row, text="Source", bg=BG, fg=TEXT_DIM,
                 font=("Helvetica", 10)).grid(row=0, column=0, sticky="w")
        tk.Label(row, text="Puits",  bg=BG, fg=TEXT_DIM,
                 font=("Helvetica", 10)).grid(row=0, column=2, sticky="w", padx=(20, 0))

        self.var_source = tk.StringVar(value=EXEMPLE_SOURCE)
        self.var_puits  = tk.StringVar(value=EXEMPLE_PUITS)

        champ_texte(row, self.var_source).grid(row=1, column=0, sticky="ew")
        tk.Label(row, text=" → ", bg=BG, fg=TEXT_DIM).grid(row=1, column=1)
        champ_texte(row, self.var_puits).grid(row=1, column=2, sticky="ew")
        row.columnconfigure(0, weight=1)
        row.columnconfigure(2, weight=1)

    def _entetes_table(self, parent):
        """Ligne d'en-têtes pour la table des arcs."""
        hdr = tk.Frame(parent, bg=CARD)
        hdr.pack(fill=tk.X, pady=(0, 2))
        for txt in ["De", "Vers", "Cap.", ""]:
            tk.Label(hdr, text=txt, bg=CARD, fg=ACCENT,
                     font=("Helvetica", 9, "bold")).pack(side=tk.LEFT, padx=4, pady=4)

    # ── Panneau droit ─────────────────────────────────────────────────────────

    def _construire_panneau_droit(self, parent):
        # Titre de la phase courante
        self.lbl_phase = tk.Label(parent,
                                  text="Manuel Bloch – Construction du flot complet",
                                  bg=BG, fg=ACCENT,
                                  font=("Helvetica", 13, "bold"))
        self.lbl_phase.pack(pady=(8, 0))

        # Titre de l'étape courante
        self.lbl_titre_etape = tk.Label(parent, text="",
                                        bg=BG, fg=TEXT,
                                        font=("Helvetica", 11))
        self.lbl_titre_etape.pack()

        # Description de l'étape
        self.lbl_desc = tk.Label(parent, text="",
                                 bg=PANEL, fg=TEXT_DIM,
                                 font=("Helvetica", 9),
                                 wraplength=700, justify="left",
                                 padx=12, pady=8)
        self.lbl_desc.pack(fill=tk.X, padx=16, pady=4)

        # Canvas matplotlib
        self.fig, self.ax = plt.subplots(figsize=(9, 5.5))
        self.fig.patch.set_facecolor(BG)
        self.ax.set_facecolor(BG)
        self.canvas = FigureCanvasTkAgg(self.fig, master=parent)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=16, pady=8)

        # Variables pour le zoom et le pan
        self.zoom_level = 1.0
        self.pan_x = 0.0
        self.pan_y = 0.0
        self.pan_active = False
        self.pan_start = (0, 0)

        # Bindings unifiés pour les événements souris
        self.canvas.mpl_connect('scroll_event', self._on_scroll)
        self.canvas.mpl_connect('button_press_event', self._on_mouse_press)
        self.canvas.mpl_connect('button_release_event', self._on_mouse_release)
        self.canvas.mpl_connect('motion_notify_event', self._on_mouse_motion)

        # Légende des couleurs
        self._construire_legende(parent)

    def _on_mouse_press(self, event):
        """Handler unifié pour le clic souris (gauche = 1, droit = 3)."""
        if event.inaxes != self.ax:
            return
        if event.xdata is None or event.ydata is None:
            return

        if self.mode_creation:
            # ── Mode création interactive ──
            if event.button == 1:  # Clic gauche
                nœud_proche = self._chercher_nœud_proche(event.xdata, event.ydata)
                if nœud_proche:
                    if event.state & 0x0004:  # Ctrl appuyé = déplacer
                        self.nœud_a_deplacer = nœud_proche
                    else:
                        # Début de drag pour créer un arc
                        self.nœud_en_cours = nœud_proche
                else:
                    # Clic sur espace vide → ajouter un nœud
                    self._ajouter_nœud_dialog(event.xdata, event.ydata)
            elif event.button == 3:  # Clic droit = supprimer
                nœud_proche = self._chercher_nœud_proche(event.xdata, event.ydata)
                if nœud_proche:
                    self._supprimer_nœud_creation(nœud_proche)
        else:
            # ── Mode normal : pan / déplacer un nœud ──
            if event.button == 1:
                self.pan_active = True
                self.pan_start = (event.xdata, event.ydata)
            elif event.button == 3:
                nœud_proche = self._chercher_nœud_proche(
                    event.xdata, event.ydata, positions=self.positions
                )
                if nœud_proche:
                    self.nœud_a_deplacer = nœud_proche

    def _on_mouse_release(self, event):
        """Handler unifié pour le relâchement de souris."""
        if self.mode_creation:
            # Mode création : fin de déplacement de nœud
            if self.nœud_a_deplacer is not None:
                if event.xdata is not None and event.ydata is not None:
                    self.positions_creation[self.nœud_a_deplacer] = (event.xdata, event.ydata)
                    self._redessiner_graphe_creation()
                self.nœud_a_deplacer = None
            
            # Fin de création d'arc
            if self.nœud_en_cours is not None:
                if event.xdata is not None and event.ydata is not None:
                    nœud_fin = self._chercher_nœud_proche(event.xdata, event.ydata)
                    if nœud_fin and nœud_fin != self.nœud_en_cours:
                        self._ajouter_arc_dialog(self.nœud_en_cours, nœud_fin)
                self.nœud_en_cours = None
                self._redessiner_graphe_creation()
        else:
            # Mode normal : fin de pan / fin du déplacement de nœud
            if self.nœud_a_deplacer is not None:
                self.nœud_a_deplacer = None
            elif event.button == 1:
                self.pan_active = False

    def _on_mouse_motion(self, event):
        """Handler unifié pour le mouvement de souris."""
        if self.mode_creation and self.nœud_a_deplacer is not None:
            # Mode création : déplacer le nœud en temps réel
            if event.xdata is not None and event.ydata is not None:
                self.positions_creation[self.nœud_a_deplacer] = (event.xdata, event.ydata)
                self._redessiner_graphe_creation()
        elif not self.mode_creation and self.nœud_a_deplacer is not None:
            # Mode normal : déplacer le nœud avec clic droit
            if event.xdata is not None and event.ydata is not None:
                self.positions[self.nœud_a_deplacer] = (event.xdata, event.ydata)
                self._afficher_etape()
        elif not self.mode_creation and self.pan_active and event.xdata is not None:
            # Mode normal : pan du graphe
            dx = event.xdata - self.pan_start[0]
            dy = event.ydata - self.pan_start[1]
            self.pan_x -= dx
            self.pan_y -= dy
            self._update_graph_view()

    def _update_graph_view(self):
        """Applique le zoom et le pan au graphe."""
        range_val = 1.3 / self.zoom_level
        self.ax.set_xlim(self.pan_x - range_val, self.pan_x + range_val)
        self.ax.set_ylim(self.pan_y - range_val, self.pan_y + range_val)
        self.canvas.draw_idle()

    def _construire_legende(self, parent):
        """Barre de légende en bas du graphe."""
        frame = tk.Frame(parent, bg=BG)
        frame.pack(pady=4)
        legendes = [
            (GREEN,   "Arc non saturé"),
            (RED,     "Arc saturé"),
            (ORANGE,  "Chemin / Chaîne améliorante"),
            (ACCENT2, "Sommet étiqueté (FF)"),
            (YELLOW,  "Arc bloqué (Bloch)"),
        ]
        for couleur, libelle in legendes:
            f = tk.Frame(frame, bg=BG)
            f.pack(side=tk.LEFT, padx=8)
            tk.Label(f, text="■", bg=BG, fg=couleur,
                     font=("Helvetica", 12)).pack(side=tk.LEFT)
            tk.Label(f, text=libelle, bg=BG, fg=TEXT_DIM,
                     font=("Helvetica", 9)).pack(side=tk.LEFT, padx=2)

    # =========================================================================
    # Gestion des arcs (saisie)
    # =========================================================================

    def _ajouter_arc_vide(self):
        """Ajoute une ligne de saisie vide."""
        self._ajouter_arc()

    def _ajouter_arc(self, de="", vers="", cap=""):
        """Ajoute une ligne de saisie pré-remplie."""
        def _suppr(entry):
            if entry in self.arcs_entries:
                self.arcs_entries.remove(entry)

        row, v_de, v_vers, v_cap = ligne_arc(
            self.arcs_frame, de, vers, cap,
            callback_suppression=_suppr
        )
        row.pack(fill=tk.X, pady=2)
        entry = (v_de, v_vers, v_cap, row)
        self.arcs_entries.append(entry)
        # Mettre à jour la référence dans le callback
        # (on recrée le callback avec la bonne entrée)

    def _charger_exemple(self):
        """Charge le réseau d'exemple de la documentation."""
        # Vider les arcs existants
        for (_, _, _, row) in self.arcs_entries:
            row.destroy()
        self.arcs_entries.clear()

        self.var_source.set(EXEMPLE_SOURCE)
        self.var_puits.set(EXEMPLE_PUITS)

        for de, vers, cap in EXEMPLE_ARCS:
            self._ajouter_arc(de, vers, str(cap))

    def _lire_reseau(self) -> dict | None:
        """
        Lit tous les champs de saisie et retourne le dict des capacités.
        Affiche une erreur et retourne None en cas de problème.
        """
        capacites = {}
        for (v_de, v_vers, v_cap, _) in self.arcs_entries:
            de   = v_de.get().strip()
            vers = v_vers.get().strip()
            cap  = v_cap.get().strip()
            if not de or not vers or not cap:
                continue
            try:
                c = int(cap)
                if c < 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror(
                    "Erreur de saisie",
                    f"Capacité invalide pour {de}→{vers} : '{cap}'\n"
                    "Entrez un entier positif."
                )
                return None
            capacites[(de, vers)] = c

        if not capacites:
            messagebox.showerror("Erreur", "Aucun arc saisi.")
            return None
        return capacites

    # =========================================================================
    # Résolution
    # =========================================================================

    def _resoudre(self):
        """Lance les deux algorithmes et prépare l'animation."""
        caps = self._lire_reseau()
        if caps is None:
            return

        self.solver = FlotMaximal(caps)

        if self.solver.source is None or self.solver.puits is None:
            messagebox.showerror(
                "Erreur de détection",
                "Impossible de détecter source/puits automatiquement.\n"
                "Vérifiez que le graphe possède un seul nœud sans prédécesseur "
                "(source) et un seul nœud sans successeur (puits)."
            )
            return

        # Calcul des positions des nœuds
        self.positions = calculer_positions(self.solver.sommets, caps)

        # ① Manuel Bloch → flot complet
        f_bloch, r_bloch, self.etapes_bloch = self.solver.manuel_bloch()

        # ② Ford-Fulkerson → flot maximal
        f_max, self.etapes_ff = self.solver.ford_fulkerson(f_bloch, r_bloch)

        # Afficher la première étape
        self.etape_idx = 0
        self.phase     = "bloch"
        self.lbl_phase.config(
            text="① Manuel Bloch – Construction du flot complet",
            fg=ACCENT
        )
        self._afficher_etape()

        # Résultat final
        val = sum(f_max.get((self.solver.source, j), 0) for j in self.solver.sommets)
        self.lbl_resultat.config(text=f"🏆 Flot maximal = {val} unités")

    # =========================================================================
    # Affichage direct du flot maximal
    # =========================================================================

    def _afficher_flot_maximal_direct(self):
        """Affiche directement le résultat final du flot maximal."""
        if self.solver is None or not self.etapes_ff:
            messagebox.showwarning("Attention", "Veuillez d'abord résoudre le problème.")
            return

        # Aller à la dernière étape (flot maximal)
        self.phase = "ff"
        self.etape_idx = len(self.etapes_ff) - 1
        self.lbl_phase.config(
            text="② Ford-Fulkerson – Flot maximal final ✓",
            fg=ACCENT2
        )
        self._afficher_etape()

    # =========================================================================
    # Navigation entre étapes
    # =========================================================================

    def _etapes_courantes(self) -> list:
        return self.etapes_bloch if self.phase == "bloch" else self.etapes_ff

    def _etape_suivante(self):
        etapes = self._etapes_courantes()
        if self.etape_idx < len(etapes) - 1:
            self.etape_idx += 1
            self._afficher_etape()
        elif self.phase == "bloch" and self.etapes_ff:
            # Passer à la phase Ford-Fulkerson
            self.phase     = "ff"
            self.etape_idx = 0
            self.lbl_phase.config(
                text="② Ford-Fulkerson – Optimisation vers le flot maximal",
                fg=ACCENT2
            )
            self._afficher_etape()

    def _etape_precedente(self):
        if self.etape_idx > 0:
            self.etape_idx -= 1
            self._afficher_etape()
        elif self.phase == "ff" and self.etapes_bloch:
            # Revenir à la dernière étape Manuel Bloch
            self.phase     = "bloch"
            self.etape_idx = len(self.etapes_bloch) - 1
            self.lbl_phase.config(
                text="① Manuel Bloch – Construction du flot complet",
                fg=ACCENT
            )
            self._afficher_etape()

    # =========================================================================
    # Mode création interactive
    # =========================================================================

    def _on_scroll(self, event):
        """Gère le zoom à la molette."""
        if event.inaxes != self.ax:
            return
        # Augmente ou diminue le zoom
        factor = 1.1 if event.button == 'up' else 0.9
        self.zoom_level *= factor
        self.zoom_level = max(0.5, min(3.0, self.zoom_level))  # Limite [0.5, 3.0]
        self._update_graph_view()

    def _ajouter_nœud_dialog(self, x, y):
        """Affiche un dialog pour ajouter un nœud à la position (x, y)."""
        dialog = tk.Toplevel(self)
        dialog.title("Nouveau nœud")
        dialog.geometry("250x120")
        dialog.configure(bg=BG)
        
        # Centrer le dialog
        dialog.transient(self)
        dialog.grab_set()
        
        tk.Label(dialog, text="Nom du nœud :",
                bg=BG, fg=TEXT, font=("Helvetica", 10)).pack(pady=8)
        var_nom = tk.StringVar()
        entry = champ_texte(dialog, var_nom, largeur=20)
        entry.pack(pady=4)
        entry.focus()
        
        def ajouter():
            nom = var_nom.get().strip()
            if nom and nom not in self.nœuds_creation:
                self.nœuds_creation.add(nom)
                self.positions_creation[nom] = (x, y)
                self._mettre_a_jour_affichage_creation()
                self._redessiner_graphe_creation()
                dialog.destroy()
            elif nom in self.nœuds_creation:
                messagebox.showwarning("Doublon", f"Le nœud '{nom}' existe déjà.")
        
        bouton(dialog, "✓ Ajouter", ajouter, bg=GREEN, fg=BG).pack(pady=8)

    def _ajouter_arc_dialog(self, nœud_debut, nœud_fin):
        """Affiche un dialog pour entrer la capacité d'un nouvel arc."""
        dialog = tk.Toplevel(self)
        dialog.title(f"Arc {nœud_debut} → {nœud_fin}")
        dialog.geometry("250x120")
        dialog.configure(bg=BG)
        
        # Centrer le dialog
        dialog.transient(self)
        dialog.grab_set()
        
        tk.Label(dialog, text=f"Capacité de {nœud_debut}→{nœud_fin} :",
                bg=BG, fg=TEXT, font=("Helvetica", 10)).pack(pady=8)
        var_cap = tk.StringVar()
        entry = champ_texte(dialog, var_cap, largeur=20)
        entry.pack(pady=4)
        entry.focus()
        
        def ajouter_arc():
            try:
                cap = int(var_cap.get().strip())
                if cap <= 0:
                    raise ValueError
                self.arcs_creation[(nœud_debut, nœud_fin)] = cap
                self._mettre_a_jour_affichage_creation()
                self._redessiner_graphe_creation()
                dialog.destroy()
            except ValueError:
                messagebox.showerror("Erreur", "Entrez un entier positif.")
        
        bouton(dialog, "✓ Ajouter arc", ajouter_arc, bg=GREEN, fg=BG).pack(pady=8)

    def _chercher_nœud_proche(self, x, y, positions=None, dist=0.1):
        """Cherche le nœud le plus proche de (x, y), dans une distance de dist."""
        if positions is None:
            positions = self.positions_creation
        plus_proche = None
        dist_min = dist
        for nœud, (nx, ny) in positions.items():
            d = ((x - nx) ** 2 + (y - ny) ** 2) ** 0.5
            if d < dist_min:
                plus_proche = nœud
                dist_min = d
        return plus_proche

    def _supprimer_nœud_creation(self, nœud):
        """Supprime un nœud et tous ses arcs associés."""
        self.nœuds_creation.discard(nœud)
        self.positions_creation.pop(nœud, None)
        # Supprimer tous les arcs liés
        arcs_a_supprimer = [(i, j) for (i, j) in self.arcs_creation if i == nœud or j == nœud]
        for arc in arcs_a_supprimer:
            del self.arcs_creation[arc]
        self._mettre_a_jour_affichage_creation()
        self._redessiner_graphe_creation()

    def _mettre_a_jour_affichage_creation(self):
        """Affiche la liste des nœuds et arcs créés."""
        texte = f"Nœuds ({len(self.nœuds_creation)}): {', '.join(sorted(self.nœuds_creation)) or '(aucun)'}\n"
        texte += f"Arcs ({len(self.arcs_creation)}): "
        if self.arcs_creation:
            arcs_str = ", ".join(f"{i}→{j}({c})" for (i, j), c in self.arcs_creation.items())
            texte += arcs_str
        else:
            texte += "(aucun)"
        self.lbl_graph_creation.config(text=texte)

    def _redessiner_graphe_creation(self):
        """Redessine le graphe en mode création."""
        self.ax.clear()
        self.ax.set_facecolor(BG)
        self.ax.axis("off")
        self.ax.set_xlim(-1.3, 1.3)
        self.ax.set_ylim(-1.3, 1.3)

        # Dessiner les arcs
        for (i, j), cap in self.arcs_creation.items():
            if i in self.positions_creation and j in self.positions_creation:
                xi, yi = self.positions_creation[i]
                xj, yj = self.positions_creation[j]
                
                # Flèche
                self.ax.annotate(
                    "",
                    xy=(xj, yj), xytext=(xi, yi),
                    arrowprops=dict(
                        arrowstyle="-|>",
                        color=ORANGE,
                        lw=2,
                        mutation_scale=15,
                        connectionstyle="arc3,rad=0.1",
                    ),
                )
                # Label capacité
                mx, my = (xi + xj) / 2, (yi + yj) / 2
                self.ax.text(mx, my, str(cap),
                            color=ORANGE, fontsize=9, fontweight="bold",
                            ha="center", va="center",
                            bbox=dict(boxstyle="round,pad=0.3",
                                     fc="#1e293b", ec="none", alpha=0.85))

        # Dessiner les nœuds
        for nœud, (x, y) in self.positions_creation.items():
            cercle = plt.Circle((x, y), 0.06, color=ACCENT, linewidth=2,
                               ec=ACCENT, zorder=5)
            self.ax.add_patch(cercle)
            self.ax.text(x, y, str(nœud), color=BG, fontsize=10, fontweight="bold",
                        ha="center", va="center", zorder=6)

        self.canvas.draw()

    def _effacer_graphe_creation(self):
        """Efface tous les nœuds et arcs créés."""
        self.nœuds_creation.clear()
        self.arcs_creation.clear()
        self.positions_creation.clear()
        self._mettre_a_jour_affichage_creation()
        self._redessiner_graphe_creation()

    def _valider_graphe_creation(self):
        """Transfère le graphe créé vers le mode tableau et résout."""
        if not self.nœuds_creation or not self.arcs_creation:
            messagebox.showwarning("Graphe incomplet",
                                 "Créez au moins un nœud et un arc.")
            return

        # Remplir le tableau à partir du graphe créé
        for (_, _, _, row) in self.arcs_entries:
            row.destroy()
        self.arcs_entries.clear()

        for (i, j), cap in self.arcs_creation.items():
            self._ajouter_arc(i, j, str(cap))

        # Basculer en mode tableau
        self.var_mode.set("tableau")
        self._basculer_mode()

        # Résoudre
        self._resoudre()

    def _afficher_etape(self):
        """Met à jour les labels et redessine le graphe pour l'étape courante."""
        etapes = self._etapes_courantes()
        if not etapes:
            return

        etape      = etapes[self.etape_idx]
        total      = len(self.etapes_bloch) + len(self.etapes_ff)
        idx_global = (self.etape_idx if self.phase == "bloch"
                      else len(self.etapes_bloch) + self.etape_idx)

        self.var_compteur.set(f"Étape {idx_global + 1} / {total}")
        self.lbl_titre_etape.config(text=etape["titre"])
        self.lbl_desc.config(text=etape.get("desc", ""))

        # Déléguer le dessin au module graphe.py
        dessiner_graphe(self.ax, self.solver, self.positions, etape)
        self._update_graph_view()
        self.canvas.draw()
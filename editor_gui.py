#!/usr/bin/env python3
"""
Editor visual del portfolio
- Árbol = estructura de la página
- Editar / agregar / eliminar / reordenar
- Icono (emoji o URL) en casi todos los ítems
- Crear grupos de tech stack
- Contacto como lista con iconos
- Ocultar / mostrar secciones
- Reordenar secciones completas
- Borrar Skills (y su rastro) / Certificaciones
- Guardar + opcional push a GitHub
"""

import json
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from pathlib import Path
from copy import deepcopy

BASE = Path(__file__).parent
PROFILE = BASE / "data" / "profile.json"
PROJECTS = BASE / "data" / "projects.json"
CONFIG = BASE / "data" / "editor_config.json"

BG, BG2, FG, ACCENT, MUTED, CARD = (
    "#0f0f1a", "#16122a", "#e8e6f0", "#a78bfa", "#9590a8", "#1a1730"
)

# id HTML → (label, nav label)
SECTION_META = [
    ("sobre-mi", "Acerca de mí", "Acerca"),
    ("experiencia", "Experiencia", "Exp."),
    ("proyectos", "Proyectos", "Proyectos"),
    ("educacion", "Educación", "Edu"),
    ("certs", "Certificaciones", "Certs"),
    ("tecnologias", "Tecnologías", "Tech"),
    ("skills", "Skills", "Skills"),
    ("contacto", "Contacto", "Contacto"),
]
SECTION_IDS = [s[0] for s in SECTION_META]
SECTION_LABEL = {s[0]: s[1] for s in SECTION_META}


def load_json(path, default=None):
    if path.exists():
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return deepcopy(default) if default is not None else {}


def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def ask(parent, title, prompt, initial=""):
    return simpledialog.askstring(title, prompt, initialvalue=initial or "", parent=parent)


def tech_name(t):
    return t.get("name", "") if isinstance(t, dict) else str(t)


def tech_icon(t):
    return t.get("icon", "") if isinstance(t, dict) else ""


def make_tech(name, icon):
    name, icon = (name or "").strip(), (icon or "").strip()
    return {"name": name, "icon": icon} if icon else name


def ensure_sections(profile):
    """Garantiza profile.sections con order + visible."""
    sec = profile.setdefault("sections", {})
    order = sec.get("order")
    if not isinstance(order, list) or not order:
        order = SECTION_IDS[:]
    # completar ids faltantes al final
    for sid in SECTION_IDS:
        if sid not in order:
            order.append(sid)
    # quitar ids desconocidos
    order = [s for s in order if s in SECTION_IDS]
    sec["order"] = order
    vis = sec.setdefault("visible", {})
    for sid in SECTION_IDS:
        if sid not in vis:
            vis[sid] = True
    return sec


class EditDialog(tk.Toplevel):
    """Formulario genérico: lista de (clave, label, valor) + opcional icono."""

    def __init__(self, parent, title, fields, with_icon=False, icon_value=""):
        super().__init__(parent)
        self.title(title)
        self.configure(bg=BG)
        self.result = None
        self.vars = {}
        self.icon_var = tk.StringVar(value=icon_value or "")
        frm = tk.Frame(self, bg=BG, padx=14, pady=12)
        frm.pack(fill="both", expand=True)
        for key, label, val in fields:
            tk.Label(frm, text=label, bg=BG, fg=MUTED, anchor="w").pack(fill="x")
            if key in ("description", "about", "bullets"):
                w = tk.Text(frm, height=5, bg=CARD, fg=FG, insertbackground=FG, wrap="word")
                w.insert("1.0", val or "")
                w.pack(fill="x", pady=(0, 8))
                self.vars[key] = w
            else:
                e = tk.Entry(frm, bg=CARD, fg=FG, insertbackground=FG)
                e.insert(0, val or "")
                e.pack(fill="x", pady=(0, 8))
                self.vars[key] = e
        if with_icon:
            tk.Label(frm, text="Icono (emoji o URL https://...)", bg=BG, fg=MUTED).pack(fill="x")
            e = tk.Entry(frm, textvariable=self.icon_var, bg=CARD, fg=FG, insertbackground=FG)
            e.pack(fill="x", pady=(0, 8))
            tk.Label(
                frm,
                text="Atajo: si:python  ·  si:github/ffffff  ·  URL  ·  emoji",
                bg=BG, fg=MUTED, font=("", 8), wraplength=400, justify="left",
            ).pack(fill="x")
        bf = tk.Frame(frm, bg=BG)
        bf.pack(fill="x", pady=8)
        ttk.Button(bf, text="Cancelar", command=self.destroy).pack(side="right", padx=4)
        ttk.Button(bf, text="OK", command=self._ok).pack(side="right")
        self.transient(parent)
        self.grab_set()
        self.wait_window()

    def _ok(self):
        out = {}
        for k, w in self.vars.items():
            if isinstance(w, tk.Text):
                out[k] = w.get("1.0", "end").strip()
            else:
                out[k] = w.get().strip()
        out["_icon"] = self.icon_var.get().strip()
        self.result = out
        self.destroy()


class PortfolioEditor(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Editor Portfolio — Uncharsacc")
        self.geometry("1060x720")
        self.minsize(900, 560)
        self.configure(bg=BG)
        self.profile = load_json(PROFILE, {})
        self.projects = load_json(PROJECTS, [])
        self.config = load_json(CONFIG, {"github_remote": "", "github_branch": "main", "auto_push": False})
        ensure_sections(self.profile)
        self._map = {}
        self._style()
        self._build()
        self.refresh_tree()

    def _style(self):
        s = ttk.Style(self)
        try:
            s.theme_use("clam")
        except tk.TclError:
            pass
        s.configure("Treeview", background=CARD, foreground=FG, fieldbackground=CARD, rowheight=26)
        s.configure("Treeview.Heading", background=BG2, foreground=ACCENT)
        s.map("Treeview", background=[("selected", "#3d2f6b")], foreground=[("selected", FG)])

    def _build(self):
        top = tk.Frame(self, bg=BG2, pady=8, padx=12)
        top.pack(fill="x")
        tk.Label(top, text="✦ Editor del Portfolio", bg=BG2, fg=ACCENT,
                 font=("Segoe UI", 13, "bold")).pack(side="left")
        right = tk.Frame(top, bg=BG2)
        right.pack(side="right")
        ttk.Button(right, text="⚙️ GitHub", command=self.github_settings).pack(side="left", padx=3)
        ttk.Button(right, text="💾 Guardar", command=self.save_all).pack(side="left", padx=3)
        ttk.Button(right, text="💾 + Push", command=self.save_and_push).pack(side="left", padx=3)
        ttk.Button(right, text="↻ Recargar", command=self.reload).pack(side="left", padx=3)

        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True, padx=8, pady=6)

        left = tk.Frame(body, bg=BG)
        left.pack(side="left", fill="both", expand=True)
        self.tree = ttk.Treeview(left, selectmode="browse", show="tree headings")
        self.tree.heading("#0", text="Estructura de la página", anchor="w")
        self.tree.pack(side="left", fill="both", expand=True)
        sb = ttk.Scrollbar(left, orient="vertical", command=self.tree.yview)
        sb.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.bind("<<TreeviewSelect>>", self.on_select)
        self.tree.bind("<Double-1>", lambda e: self.edit_selected())

        side = tk.Frame(body, bg=BG2, width=310, padx=10, pady=10)
        side.pack(side="right", fill="y")
        side.pack_propagate(False)
        tk.Label(side, text="Acciones", bg=BG2, fg=ACCENT, font=("Segoe UI", 11, "bold")).pack(anchor="w")
        self.info = tk.Label(side, text="Selecciona un ítem", bg=BG2, fg=MUTED,
                             justify="left", wraplength=280, font=("Segoe UI", 9))
        self.info.pack(anchor="w", pady=6)
        for text, cmd in [
            ("✏️  Editar (o doble clic)", self.edit_selected),
            ("➕  Agregar en sección", self.add_in_section),
            ("📁  Nuevo grupo (stack)", self.add_stack_group),
            ("⬆️  Subir", lambda: self.move(-1)),
            ("⬇️  Bajar", lambda: self.move(1)),
            ("👁️  Ocultar / Mostrar sección", self.toggle_section),
            ("🗑️  Eliminar ítem", self.delete_selected),
            ("🧹  Borrar Skills (rastro)", self.wipe_skills),
            ("🧹  Borrar Certificaciones", self.wipe_certs),
        ]:
            ttk.Button(side, text=text, command=cmd).pack(fill="x", pady=2)
        tk.Label(
            side,
            text="\n📑 Secciones: usa Subir/Bajar sobre\n"
                 "un ítem de «Orden de secciones»\n"
                 "u Ocultar/Mostrar.\n\n"
                 "Skills/Certs vacíos se ocultan solos\n"
                 "en la web (main.js).\n\n"
                 "Iconos: emoji, si:python o URL.",
            bg=BG2, fg=MUTED, justify="left", font=("Segoe UI", 8), wraplength=280,
        ).pack(anchor="w", pady=10)

        self.status = tk.Label(self, text="Listo", bg=BG, fg=MUTED, anchor="w", padx=10)
        self.status.pack(fill="x", side="bottom")

    def set_status(self, m):
        self.status.config(text=m)

    # ---- estado del árbol ----
    def _tree_path(self, iid):
        parts = []
        while iid:
            parts.append(self.tree.item(iid, "text"))
            iid = self.tree.parent(iid)
        return tuple(reversed(parts))

    def _open_paths(self):
        paths = set()

        def walk(parent):
            for c in self.tree.get_children(parent):
                if self.tree.item(c, "open"):
                    paths.add(self._tree_path(c))
                walk(c)

        walk("")
        return paths

    def _find_by_path(self, path):
        parent, found = "", None
        for part in path:
            found = next((c for c in self.tree.get_children(parent)
                          if self.tree.item(c, "text") == part), None)
            if found is None:
                return None
            parent = found
        return found

    def refresh_tree(self):
        ensure_sections(self.profile)
        open_before = self._open_paths()
        sel = self.tree.selection()
        sel_path = self._tree_path(sel[0]) if sel else None

        self.tree.delete(*self.tree.get_children())
        self._map.clear()

        def add(parent, text, kind, key=None, open_=False):
            iid = self.tree.insert(parent, "end", text=text, open=open_)
            self._map[iid] = (kind, key)
            return iid

        # --- Secciones (orden + visibilidad) ---
        # No forzar open_=True: si no, al editar/OK se reabre sola y al iniciar ya viene abierta.
        sec = ensure_sections(self.profile)
        so = add("", "📑 Orden de secciones (mover / ocultar)", "section_order")
        for i, sid in enumerate(sec["order"]):
            on = sec["visible"].get(sid, True)
            mark = "👁️" if on else "🚫"
            add(so, f"{mark}  {SECTION_LABEL.get(sid, sid)}  [{sid}]", "section_row", sid)

        h = add("", "🏠 Hero / Datos", "section_personal")
        for k, lab in [("name", "Nombre"), ("shortName", "Iniciales"),
                       ("heroSubtitle", "Subtítulo"), ("about", "About"), ("github", "GitHub URL")]:
            val = (self.profile.get(k) or "")[:55]
            add(h, f"{lab}: {val}", "field", k)

        st = self.profile.get("stats") or {}
        s = add("", "📊 Stats", "section_stats")
        for k in ("years", "yearsLabel", "projects", "projectsLabel", "skills", "skillsLabel"):
            add(s, f"{k}: {st.get(k, '')}", "stat", k)

        m = add("", "🎢 Barra tecnologías", "section_marquee")
        for i, t in enumerate(self.profile.get("techMarquee") or []):
            add(m, t, "marquee_item", i)

        hi = add("", "🃏 Highlights", "section_highlights")
        for i, it in enumerate(self.profile.get("highlights") or []):
            add(hi, f"{it.get('num', '')} — {it.get('label', '')}", "highlight", i)

        si = add("", "◆ Habilidades clave (iconos en About)", "section_skill_icons")
        for i, sk in enumerate(self.profile.get("skillIcons") or []):
            add(si, f"{(sk.get('icon') or '◆')[:20]}  {sk.get('name', '')}", "skill_icon", i)

        sk_list = self.profile.get("skills")
        if sk_list is None:
            sk_list = []
        sk = add("", f"📈 Skills %  ({'vacío → oculta sección' if not sk_list else len(sk_list)} ítems)", "section_skills")
        for i, it in enumerate(sk_list):
            add(sk, f"{it.get('name', '')} — {it.get('level', 0)}%", "skill", i)

        ex = add("", "💼 Experiencia", "section_experience")
        for i, e in enumerate(self.profile.get("experience") or []):
            add(ex, f"{e.get('title', '')} @ {e.get('company', '')}", "experience", i)

        pr = add("", "🚀 Proyectos", "section_projects")
        for i, p in enumerate(self.projects):
            star = "★ " if p.get("featured") else ""
            add(pr, f"{star}{p.get('name', '')}", "project", i)

        ed = add("", "🎓 Educación", "section_education")
        for i, e in enumerate(self.profile.get("education") or []):
            add(ed, e.get("title", ""), "education", i)

        ce = add("", "📜 Certificaciones", "section_certs")
        for i, c in enumerate(self.profile.get("certifications") or []):
            add(ce, f"{c.get('name', '')} — {c.get('org', '')}", "cert", i)

        ts = add("", "🧩 Tech stack", "section_stack")
        for group, items in (self.profile.get("techStack") or {}).items():
            gid = add(ts, f"📁 {group}", "stack_group", group)
            for i, tech in enumerate(items):
                add(gid, ("🖼 " if tech_icon(tech) else "") + tech_name(tech), "stack_item", (group, i))

        co = add("", "📧 Contacto", "section_contact")
        c = self.profile.get("contact") or {}
        items = c.get("items")
        if not items:
            items = []
            if c.get("email"):
                items.append({"label": "Email", "value": c["email"], "url": "mailto:" + c["email"],
                              "icon": c.get("emailIcon") or "✉️"})
            if c.get("phone"):
                items.append({"label": "Teléfono", "value": c["phone"], "url": "tel:" + c["phone"],
                              "icon": c.get("phoneIcon") or "📞"})
            if c.get("location"):
                items.append({"label": "Ubicación", "value": c["location"], "url": "",
                              "icon": c.get("locationIcon") or "📍"})
            if c.get("github"):
                items.append({"label": "GitHub", "value": "@" + c["github"].rstrip("/").split("/")[-1],
                              "url": c["github"], "icon": c.get("githubIcon") or "🐙"})
            if c.get("linkedin"):
                items.append({"label": "LinkedIn", "value": "Perfil", "url": c["linkedin"],
                              "icon": c.get("linkedinIcon") or "in"})
            c["items"] = items
            self.profile["contact"] = c
        for i, it in enumerate(items):
            add(co, f"{it.get('label', '')}: {it.get('value', '')}", "contact_item", i)

        self.set_status("Árbol actualizado")

        for path in open_before:
            nid = self._find_by_path(path)
            if nid:
                self.tree.item(nid, open=True)
        if sel_path:
            nid = self._find_by_path(sel_path)
            if nid:
                cur = self.tree.parent(nid)
                while cur:
                    self.tree.item(cur, open=True)
                    cur = self.tree.parent(cur)
                self.tree.selection_set(nid)
                self.tree.see(nid)

    def on_select(self, _=None):
        sel = self.tree.selection()
        if not sel:
            return
        kind, key = self._map.get(sel[0], (None, None))
        extra = ""
        if kind == "section_row":
            vis = ensure_sections(self.profile)["visible"].get(key, True)
            extra = f"\nVisible: {'sí' if vis else 'no'}\nDoble clic o «Ocultar/Mostrar»"
        self.info.config(text=f"Tipo: {kind}\nClave: {key}{extra}")

    def selected(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Info", "Selecciona un ítem primero")
            return None
        return sel[0], self._map.get(sel[0], (None, None))

    def section_of(self, iid, kind):
        if kind and kind.startswith("section_"):
            return kind
        parent = self.tree.parent(iid)
        while parent:
            pk = self._map.get(parent, (None,))[0]
            if pk and pk.startswith("section_"):
                return pk
            parent = self.tree.parent(parent)
        return None

    # ---- ocultar / mostrar sección ----
    def toggle_section(self):
        got = self.selected()
        if not got:
            return
        iid, (kind, key) = got
        sec = ensure_sections(self.profile)
        sid = None
        if kind == "section_row":
            sid = key
        else:
            # mapear sección del árbol a id HTML
            sec_kind = self.section_of(iid, kind)
            mapping = {
                "section_personal": "sobre-mi",
                "section_experience": "experiencia",
                "section_projects": "proyectos",
                "section_education": "educacion",
                "section_certs": "certs",
                "section_stack": "tecnologias",
                "section_skills": "skills",
                "section_contact": "contacto",
            }
            sid = mapping.get(sec_kind)
        if not sid:
            messagebox.showinfo(
                "Secciones",
                "Selecciona un ítem en «📑 Orden de secciones»\n"
                "o una sección de contenido (Experiencia, Skills…).",
            )
            return
        cur = sec["visible"].get(sid, True)
        sec["visible"][sid] = not cur
        self.refresh_tree()
        self.set_status(
            f"Sección «{SECTION_LABEL.get(sid, sid)}» → "
            f"{'visible' if not cur else 'oculta'} (guarda para aplicar en la web)"
        )

    def wipe_skills(self):
        if not messagebox.askyesno(
            "Borrar Skills",
            "Esto vacía la lista de Skills (%) y oculta la sección en la web.\n"
            "También puedes borrar «Habilidades clave» (iconos) por separado.\n\n¿Continuar?",
        ):
            return
        self.profile["skills"] = []
        sec = ensure_sections(self.profile)
        sec["visible"]["skills"] = False
        self.refresh_tree()
        self.set_status("Skills borrados + sección oculta — pulsa Guardar")

    def wipe_certs(self):
        if not messagebox.askyesno(
            "Borrar Certificaciones",
            "Vacía certificaciones y oculta la sección. ¿Continuar?",
        ):
            return
        self.profile["certifications"] = []
        sec = ensure_sections(self.profile)
        sec["visible"]["certs"] = False
        self.refresh_tree()
        self.set_status("Certificaciones borradas + sección oculta — pulsa Guardar")

    def edit_selected(self):
        got = self.selected()
        if not got:
            return
        iid, (kind, key) = got

        if kind == "section_row":
            self.toggle_section()
            return

        if kind == "field":
            cur = self.profile.get(key, "")
            d = EditDialog(self, key, [(key, key, cur)], with_icon=False)
            if d.result:
                self.profile[key] = d.result[key]

        elif kind == "stat":
            st = self.profile.setdefault("stats", {})
            d = EditDialog(self, "Stat", [(key, key, st.get(key, ""))])
            if d.result:
                st[key] = d.result[key]

        elif kind == "marquee_item":
            arr = self.profile.setdefault("techMarquee", [])
            d = EditDialog(self, "Tech", [("name", "Nombre", arr[key])])
            if d.result:
                arr[key] = d.result["name"]

        elif kind == "highlight":
            arr = self.profile.setdefault("highlights", [])
            it = arr[key]
            d = EditDialog(self, "Highlight",
                           [("num", "Número", it.get("num", "")),
                            ("label", "Label", it.get("label", ""))],
                           with_icon=True, icon_value=it.get("icon", ""))
            if d.result:
                it["num"], it["label"] = d.result["num"], d.result["label"]
                it["icon"] = d.result["_icon"]

        elif kind == "skill_icon":
            arr = self.profile.setdefault("skillIcons", [])
            it = arr[key]
            d = EditDialog(self, "Skill icono",
                           [("name", "Nombre", it.get("name", ""))],
                           with_icon=True, icon_value=it.get("icon", "◆"))
            if d.result:
                it["name"] = d.result["name"]
                it["icon"] = d.result["_icon"] or "◆"

        elif kind == "skill":
            arr = self.profile.setdefault("skills", [])
            if not isinstance(arr, list):
                self.profile["skills"] = arr = []
            it = arr[key]
            d = EditDialog(self, "Skill %",
                           [("name", "Nombre", it.get("name", "")),
                            ("level", "Nivel 0-100 (vacío = sin %)", str(it.get("level", "") or ""))],
                           with_icon=True, icon_value=it.get("icon", ""))
            if d.result:
                it["name"] = d.result["name"]
                lvl = d.result["level"].strip()
                if lvl == "":
                    it.pop("level", None)
                else:
                    try:
                        it["level"] = int(lvl)
                    except ValueError:
                        pass
                it["icon"] = d.result["_icon"]

        elif kind == "experience":
            arr = self.profile.setdefault("experience", [])
            it = arr[key]
            d = EditDialog(
                self, "Experiencia",
                [
                    ("title", "Cargo", it.get("title", "")),
                    ("company", "Empresa", it.get("company", "")),
                    ("period", "Periodo", it.get("period", "")),
                    ("location", "Ubicación", it.get("location", "")),
                    ("description", "Descripción", it.get("description", "")),
                    ("bullets", "Bullets (una línea cada uno)", "\n".join(it.get("bullets") or [])),
                    ("tech", "Tech (coma)", ", ".join(it.get("tech") or [])),
                ],
                with_icon=True, icon_value=it.get("icon", ""),
            )
            if d.result:
                r = d.result
                it.update({k: r[k] for k in ("title", "company", "period", "location", "description")})
                it["bullets"] = [x.strip() for x in r["bullets"].splitlines() if x.strip()]
                it["tech"] = [x.strip() for x in r["tech"].split(",") if x.strip()]
                it["icon"] = r["_icon"]

        elif kind == "project":
            it = self.projects[key]
            d = EditDialog(
                self, "Proyecto",
                [
                    ("name", "Nombre", it.get("name", "")),
                    ("description", "Descripción", it.get("description", "")),
                    ("tech", "Tech (coma)", ", ".join(it.get("tech") or [])),
                    ("github", "GitHub URL", it.get("github") or ""),
                    ("demo", "Demo URL", it.get("demo") or ""),
                    ("image", "Imagen URL", it.get("image") or ""),
                    ("featured", "Destacado (s/n)", "s" if it.get("featured") else "n"),
                ],
                with_icon=True, icon_value=it.get("icon", ""),
            )
            if d.result:
                r = d.result
                it["name"] = r["name"]
                it["description"] = r["description"]
                it["tech"] = [x.strip() for x in r["tech"].split(",") if x.strip()]
                it["github"] = r["github"] or None
                it["demo"] = r["demo"] or None
                it["image"] = r["image"] or None
                it["featured"] = r["featured"].lower() in ("s", "si", "sí", "y", "1")
                it["icon"] = r["_icon"]
                if not it.get("id") or it.get("id") in ("nuevo", "nuevo"):
                    it["id"] = (it["name"] or "proyecto").lower().replace(" ", "-")[:40]

        elif kind == "education":
            arr = self.profile.setdefault("education", [])
            it = arr[key]
            d = EditDialog(
                self, "Educación",
                [
                    ("title", "Título", it.get("title", "")),
                    ("institution", "Institución", it.get("institution", "")),
                    ("period", "Periodo", it.get("period", "")),
                    ("status", "Estado", it.get("status", "")),
                ],
                with_icon=True, icon_value=it.get("icon", ""),
            )
            if d.result:
                for k in ("title", "institution", "period", "status"):
                    it[k] = d.result[k]
                it["icon"] = d.result["_icon"]

        elif kind == "cert":
            arr = self.profile.setdefault("certifications", [])
            it = arr[key]
            d = EditDialog(
                self, "Certificación",
                [("name", "Nombre", it.get("name", "")), ("org", "Organización", it.get("org", ""))],
                with_icon=True, icon_value=it.get("icon", ""),
            )
            if d.result:
                it["name"], it["org"] = d.result["name"], d.result["org"]
                it["icon"] = d.result["_icon"]

        elif kind == "stack_group":
            stack = self.profile.setdefault("techStack", {})
            d = EditDialog(self, f"Grupo: {key}", [("name", "Nombre del grupo", key)])
            if d.result:
                new_name = d.result["name"] or key
                if new_name != key:
                    self.profile["techStack"] = {
                        (new_name if k == key else k): v for k, v in stack.items()
                    }

        elif kind == "stack_item":
            group, idx = key
            arr = self.profile.setdefault("techStack", {}).setdefault(group, [])
            cur = arr[idx]
            d = EditDialog(self, "Tecnología", [("name", "Nombre", tech_name(cur))],
                           with_icon=True, icon_value=tech_icon(cur))
            if d.result:
                arr[idx] = make_tech(d.result["name"], d.result["_icon"])

        elif kind == "contact_item":
            items = self.profile.setdefault("contact", {}).setdefault("items", [])
            it = items[key]
            d = EditDialog(
                self, "Contacto",
                [
                    ("label", "Etiqueta (Email, Tel…)", it.get("label", "")),
                    ("value", "Valor (texto visible)", it.get("value", "")),
                    ("url", "Link (mailto:, https://…)", it.get("url", "")),
                ],
                with_icon=True, icon_value=it.get("icon", ""),
            )
            if d.result:
                it["label"] = d.result["label"]
                it["value"] = d.result["value"]
                it["url"] = d.result["url"]
                it["icon"] = d.result["_icon"]

        elif kind and kind.startswith("section_"):
            messagebox.showinfo("Sección", "Elige un ítem dentro, o usa «Agregar en sección».")
            return
        else:
            messagebox.showinfo("Info", f"Sin editor para: {kind}")
            return

        self.refresh_tree()
        self.set_status("Editado — pulsa Guardar para persistir")

    def add_in_section(self):
        got = self.selected()
        if not got:
            return
        iid, (kind, key) = got
        sec = self.section_of(iid, kind)

        if sec == "section_marquee":
            v = ask(self, "Tech", "Nombre")
            if v:
                self.profile.setdefault("techMarquee", []).append(v)
        elif sec == "section_highlights":
            d = EditDialog(self, "Highlight",
                           [("num", "Número", "1+"), ("label", "Label", "")], with_icon=True)
            if d.result:
                self.profile.setdefault("highlights", []).append(
                    {"num": d.result["num"], "label": d.result["label"], "icon": d.result["_icon"]})
        elif sec == "section_skill_icons":
            d = EditDialog(self, "Skill", [("name", "Nombre", "")], with_icon=True, icon_value="◆")
            if d.result:
                self.profile.setdefault("skillIcons", []).append(
                    {"name": d.result["name"], "icon": d.result["_icon"] or "◆"})
        elif sec == "section_skills":
            d = EditDialog(self, "Skill %",
                           [("name", "Nombre", ""), ("level", "Nivel (vacío = sin %)", "70")], with_icon=True)
            if d.result:
                item = {"name": d.result["name"], "icon": d.result["_icon"]}
                lvl = d.result["level"].strip()
                if lvl:
                    try:
                        item["level"] = int(lvl)
                    except ValueError:
                        pass
                arr = self.profile.get("skills")
                if not isinstance(arr, list):
                    arr = []
                    self.profile["skills"] = arr
                arr.append(item)
                # si agregas skills, muestra la sección
                ensure_sections(self.profile)["visible"]["skills"] = True
        elif sec == "section_experience":
            self.profile.setdefault("experience", []).append(
                {"title": "Nuevo", "company": "", "period": "", "location": "",
                 "description": "", "bullets": [], "tech": [], "icon": ""})
            self.refresh_tree()
            self.set_status("Agregado — selecciónalo y edítalo")
            return
        elif sec == "section_projects":
            self.projects.append(
                {"id": "nuevo", "name": "Nuevo proyecto", "description": "", "tech": [],
                 "github": None, "demo": None, "featured": False, "image": None, "icon": ""})
            self.refresh_tree()
            return
        elif sec == "section_education":
            d = EditDialog(self, "Educación",
                           [("title", "Título", ""), ("institution", "Institución", ""),
                            ("period", "Periodo", ""), ("status", "Estado", "")], with_icon=True)
            if d.result:
                self.profile.setdefault("education", []).append({
                    "title": d.result["title"], "institution": d.result["institution"],
                    "period": d.result["period"], "status": d.result["status"],
                    "icon": d.result["_icon"]})
        elif sec == "section_certs":
            d = EditDialog(self, "Cert",
                           [("name", "Nombre", ""), ("org", "Organización", "")], with_icon=True)
            if d.result:
                self.profile.setdefault("certifications", []).append(
                    {"name": d.result["name"], "org": d.result["org"], "icon": d.result["_icon"]})
                ensure_sections(self.profile)["visible"]["certs"] = True
        elif sec == "section_stack":
            if kind in ("stack_group", "stack_item"):
                group = key if kind == "stack_group" else key[0]
                d = EditDialog(self, f"Nueva tecnología en «{group}»",
                               [("name", "Nombre", "")], with_icon=True)
                if not d.result or not d.result["name"]:
                    return
                self.profile.setdefault("techStack", {}).setdefault(group, []).append(
                    make_tech(d.result["name"], d.result["_icon"]))
            else:
                self.add_stack_group()
                return
        elif sec == "section_contact" or kind == "contact_item":
            d = EditDialog(
                self, "Nuevo contacto",
                [("label", "Etiqueta", "Email"),
                 ("value", "Valor", ""),
                 ("url", "Link", "")],
                with_icon=True, icon_value="✉️",
            )
            if d.result:
                self.profile.setdefault("contact", {}).setdefault("items", []).append({
                    "label": d.result["label"],
                    "value": d.result["value"],
                    "url": d.result["url"],
                    "icon": d.result["_icon"],
                })
        else:
            messagebox.showinfo("Info", "Selecciona una sección (o un ítem dentro) para agregar.")
            return

        self.refresh_tree()
        self.set_status("Agregado")

    def add_stack_group(self):
        name = ask(self, "Nuevo grupo", "Nombre del grupo (ej: Herramientas, DevOps, Cloud)")
        if not name:
            return
        stack = self.profile.setdefault("techStack", {})
        if name in stack:
            messagebox.showinfo("Info", "Ese grupo ya existe")
            return
        techs = ask(self, "Tecnologías", "Lista separada por coma (opcional)") or ""
        stack[name] = [x.strip() for x in techs.split(",") if x.strip()]
        self.refresh_tree()
        self.set_status(f"Grupo «{name}» creado")

    def move(self, delta):
        got = self.selected()
        if not got:
            return
        iid, (kind, key) = got

        # Mover sección completa en el orden de la página
        if kind == "section_row":
            sec = ensure_sections(self.profile)
            order = sec["order"]
            try:
                i = order.index(key)
            except ValueError:
                return
            j = i + delta
            if j < 0 or j >= len(order):
                return
            order[i], order[j] = order[j], order[i]
            self.refresh_tree()
            self.set_status(f"Sección «{SECTION_LABEL.get(key, key)}» movida")
            return

        arr, i = None, None
        if kind == "project":
            arr, i = self.projects, key
        elif kind == "marquee_item":
            arr, i = self.profile.setdefault("techMarquee", []), key
        elif kind == "highlight":
            arr, i = self.profile.setdefault("highlights", []), key
        elif kind == "skill_icon":
            arr, i = self.profile.setdefault("skillIcons", []), key
        elif kind == "skill":
            arr = self.profile.get("skills")
            if not isinstance(arr, list):
                return
            i = key
        elif kind == "experience":
            arr, i = self.profile.setdefault("experience", []), key
        elif kind == "education":
            arr, i = self.profile.setdefault("education", []), key
        elif kind == "cert":
            arr, i = self.profile.setdefault("certifications", []), key
        elif kind == "contact_item":
            arr, i = self.profile.setdefault("contact", {}).setdefault("items", []), key
        elif kind == "stack_item":
            group, i = key
            arr = self.profile.setdefault("techStack", {}).setdefault(group, [])
        else:
            messagebox.showinfo(
                "Info",
                "Este ítem no se reordena así.\n"
                "Para secciones de la página: selecciona en «📑 Orden de secciones».",
            )
            return
        j = i + delta
        if j < 0 or j >= len(arr):
            return
        arr[i], arr[j] = arr[j], arr[i]
        self.refresh_tree()
        self.set_status("Reordenado")

    def delete_selected(self):
        got = self.selected()
        if not got:
            return
        iid, (kind, key) = got
        if kind == "section_row":
            messagebox.showinfo(
                "Secciones",
                "Las secciones de la página no se eliminan del HTML.\n"
                "Usa «Ocultar / Mostrar sección» o los botones 🧹 para Skills/Certs.",
            )
            return
        if not messagebox.askyesno("Confirmar", "¿Eliminar?"):
            return
        try:
            if kind == "project":
                self.projects.pop(key)
            elif kind == "marquee_item":
                self.profile["techMarquee"].pop(key)
            elif kind == "highlight":
                self.profile["highlights"].pop(key)
            elif kind == "skill_icon":
                self.profile["skillIcons"].pop(key)
            elif kind == "skill":
                arr = self.profile.get("skills")
                if isinstance(arr, list):
                    arr.pop(key)
                    if not arr:
                        ensure_sections(self.profile)["visible"]["skills"] = False
            elif kind == "experience":
                self.profile["experience"].pop(key)
            elif kind == "education":
                self.profile["education"].pop(key)
            elif kind == "cert":
                self.profile["certifications"].pop(key)
                if not self.profile.get("certifications"):
                    ensure_sections(self.profile)["visible"]["certs"] = False
            elif kind == "contact_item":
                self.profile["contact"]["items"].pop(key)
            elif kind == "stack_item":
                g, i = key
                self.profile["techStack"][g].pop(i)
            elif kind == "stack_group":
                self.profile.get("techStack", {}).pop(key, None)
            else:
                messagebox.showinfo("Info", "No eliminable")
                return
        except (IndexError, KeyError) as e:
            messagebox.showerror("Error", str(e))
            return
        self.refresh_tree()
        self.set_status("Eliminado")

    def github_settings(self):
        d = EditDialog(
            self, "Config GitHub",
            [
                ("remote", "Remote (origen del repo, vacío = default)",
                 self.config.get("github_remote", "")),
                ("branch", "Branch", self.config.get("github_branch", "main")),
                ("auto", "¿Auto-push al guardar? (s/n)",
                 "s" if self.config.get("auto_push") else "n"),
            ],
        )
        if d.result:
            self.config["github_remote"] = d.result["remote"]
            self.config["github_branch"] = d.result["branch"] or "main"
            self.config["auto_push"] = d.result["auto"].lower() in ("s", "si", "sí", "y", "1")
            save_json(CONFIG, self.config)
            self.set_status("Config GitHub guardada")

    def save_all(self, quiet=False):
        ensure_sections(self.profile)
        # skills null → lista vacía (más predecible para el JS)
        if self.profile.get("skills") is None:
            self.profile["skills"] = []
        c = self.profile.setdefault("contact", {})
        items = c.get("items") or []
        for it in items:
            lab = (it.get("label") or "").lower()
            if "mail" in lab:
                c["email"] = it.get("value", "")
            elif "tel" in lab or "phone" in lab:
                c["phone"] = it.get("value", "")
            elif "ubic" in lab or "loc" in lab:
                c["location"] = it.get("value", "")
            elif "git" in lab:
                c["github"] = it.get("url") or it.get("value", "")
            elif "link" in lab:
                c["linkedin"] = it.get("url") or it.get("value", "")
        save_json(PROFILE, self.profile)
        save_json(PROJECTS, self.projects)
        save_json(CONFIG, self.config)
        self.set_status("💾 Guardado en data/")
        if not quiet:
            messagebox.showinfo(
                "Guardado",
                "JSON actualizados.\n"
                "Si cambiaste orden/visibilidad de secciones, asegúrate de tener el main.js nuevo.\n"
                "Recarga la web (Ctrl+F5).",
            )
        if self.config.get("auto_push"):
            self._git_push()

    def save_and_push(self):
        self.save_all(quiet=True)
        self._git_push()

    def _git_push(self):
        branch = self.config.get("github_branch") or "main"
        remote = self.config.get("github_remote") or "origin"
        try:
            r = subprocess.run(["git", "status"], cwd=BASE, capture_output=True, text=True)
            if r.returncode != 0:
                messagebox.showwarning(
                    "Git",
                    "Esta carpeta no es un repo git.\n"
                    "Ejecuta:\n  git init\n  git remote add origin URL\n"
                    "y vuelve a intentar.",
                )
                return
            subprocess.run(["git", "add", "-A"], cwd=BASE, check=False)
            msg = ask(self, "Commit", "Mensaje del commit", "update portfolio") or "update portfolio"
            subprocess.run(["git", "commit", "-m", msg], cwd=BASE, capture_output=True)
            push = subprocess.run(
                ["git", "push", "-u", remote, branch],
                cwd=BASE, capture_output=True, text=True,
            )
            if push.returncode == 0:
                self.set_status("✅ Push OK → GitHub")
                messagebox.showinfo("Push", "Subido a GitHub.\nSi Pages está activo, en 1–2 min verás los cambios.")
            else:
                messagebox.showerror(
                    "Push falló",
                    push.stderr or push.stdout or "Error desconocido.\n¿Estás logueado? (gh auth login)",
                )
                self.set_status("Push falló")
        except FileNotFoundError:
            messagebox.showerror("Git", "No se encontró git en el sistema.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def reload(self):
        self.profile = load_json(PROFILE, {})
        self.projects = load_json(PROJECTS, [])
        self.config = load_json(CONFIG, self.config)
        ensure_sections(self.profile)
        self.refresh_tree()
        self.set_status("Recargado desde disco")


if __name__ == "__main__":
    PortfolioEditor().mainloop()
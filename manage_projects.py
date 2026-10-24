#!/usr/bin/env python3
"""Editor del portfolio — menú por secciones (agregar / editar / quitar)."""

import json
import sys
from pathlib import Path

BASE = Path(__file__).parent
PROFILE = BASE / "data" / "profile.json"
PROJECTS = BASE / "data" / "projects.json"


def load(path, default=None):
    if not path.exists():
        return default if default is not None else {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"✅ Guardado → {path.relative_to(BASE)}")


def ask(label, current=""):
    cur = f" [{current}]" if current not in ("", None) else ""
    v = input(f"{label}{cur}: ").strip()
    return v if v else current


def menu_list_edit(title, items, fields, make_new):
    """Generic list editor: show, add, edit, remove."""
    while True:
        print(f"\n=== {title} ({len(items)}) ===")
        for i, it in enumerate(items, 1):
            preview = " | ".join(str(it.get(f, ""))[:40] for f in fields[:2])
            print(f"  {i}. {preview}")
        print("  [a] Agregar  [e] Editar  [d] Eliminar  [0] Volver")
        op = input("> ").strip().lower()
        if op == "0" or op == "":
            return items
        if op == "a":
            items.append(make_new())
            print("✅ Agregado")
        elif op == "e" and items:
            try:
                i = int(input("Número: ")) - 1
                if 0 <= i < len(items):
                    for f, lab in fields:
                        items[i][f] = ask(lab, items[i].get(f, ""))
                    print("✅ Editado")
            except ValueError:
                print("Número inválido")
        elif op == "d" and items:
            try:
                i = int(input("Número a eliminar: ")) - 1
                if 0 <= i < len(items):
                    removed = items.pop(i)
                    print(f"✅ Eliminado: {removed.get(fields[0][0], removed)}")
            except ValueError:
                print("Número inválido")


def main():
    while True:
        print("""
╔════════════════════════════════════════╗
║     EDITOR DEL PORTFOLIO               ║
╠════════════════════════════════════════╣
║  1. Datos personales (nombre, about…)  ║
║  2. Stats del hero                     ║
║  3. Barra de tecnologías (marquee)     ║
║  4. Habilidades clave (iconos)         ║
║  5. Skills con % (barras)              ║
║  6. Experiencia                        ║
║  7. Proyectos                          ║
║  8. Educación                          ║
║  9. Certificaciones                    ║
║ 10. Tech stack (categorías)            ║
║ 11. Contacto                           ║
║ 12. Highlights (cards del about)       ║
║  0. Salir                              ║
╚════════════════════════════════════════╝""")
        op = input("Opción: ").strip()
        p = load(PROFILE, {})

        if op == "0":
            break

        elif op == "1":
            print("\n— Datos personales —")
            for key, lab in [
                ("name", "Nombre"),
                ("shortName", "Iniciales nav"),
                ("title", "Título"),
                ("tagline", "Tagline"),
                ("heroSubtitle", "Subtítulo hero"),
                ("about", "Sobre mí"),
                ("github", "GitHub URL"),
            ]:
                p[key] = ask(lab, p.get(key, ""))
            save(PROFILE, p)

        elif op == "2":
            s = p.get("stats", {})
            for key, lab in [
                ("years", "Años (ej 1+)"),
                ("yearsLabel", "Label años"),
                ("projects", "Proyectos (ej 4+)"),
                ("projectsLabel", "Label proyectos"),
                ("skills", "Skills (ej 6+)"),
                ("skillsLabel", "Label skills"),
            ]:
                s[key] = ask(lab, s.get(key, ""))
            p["stats"] = s
            save(PROFILE, p)

        elif op == "3":
            tech = p.get("techMarquee", [])
            print("Actual:", ", ".join(tech))
            val = input("Lista separada por comas (Enter = no cambiar): ").strip()
            if val:
                p["techMarquee"] = [x.strip() for x in val.split(",") if x.strip()]
                save(PROFILE, p)

        elif op == "4":
            icons = p.get("skillIcons", [])
            def new_icon():
                return {"name": ask("Nombre"), "icon": ask("Icono/texto corto", "◆")}
            p["skillIcons"] = menu_list_edit(
                "Habilidades clave (iconos)",
                icons,
                [("name", "Nombre"), ("icon", "Icono")],
                new_icon,
            )
            save(PROFILE, p)

        elif op == "5":
            skills = p.get("skills", [])
            def new_skill():
                name = ask("Nombre skill")
                lvl = ask("Nivel 0-100", "70")
                return {"name": name, "level": int(lvl) if str(lvl).isdigit() else 70}
            # edit level as string then convert
            while True:
                print(f"\n=== Skills % ({len(skills)}) ===")
                for i, s in enumerate(skills, 1):
                    print(f"  {i}. {s.get('name')} — {s.get('level')}%")
                print("  [a] Agregar  [e] Editar  [d] Eliminar  [0] Volver")
                o = input("> ").strip().lower()
                if o == "0" or o == "":
                    break
                if o == "a":
                    skills.append(new_skill())
                elif o == "e" and skills:
                    i = int(input("Número: ")) - 1
                    if 0 <= i < len(skills):
                        skills[i]["name"] = ask("Nombre", skills[i]["name"])
                        lv = ask("Nivel", str(skills[i]["level"]))
                        if str(lv).isdigit():
                            skills[i]["level"] = int(lv)
                elif o == "d" and skills:
                    i = int(input("Número: ")) - 1
                    if 0 <= i < len(skills):
                        skills.pop(i)
            p["skills"] = skills
            save(PROFILE, p)

        elif op == "6":
            exp = p.get("experience", [])
            def new_exp():
                return {
                    "title": ask("Cargo"),
                    "company": ask("Empresa"),
                    "period": ask("Periodo"),
                    "location": ask("Ubicación"),
                    "description": ask("Descripción corta"),
                    "bullets": [b.strip() for b in ask("Bullets (separados por |)").split("|") if b.strip()],
                    "tech": [t.strip() for t in ask("Tech (coma)").split(",") if t.strip()],
                }
            while True:
                print(f"\n=== Experiencia ({len(exp)}) ===")
                for i, e in enumerate(exp, 1):
                    print(f"  {i}. {e.get('title')} @ {e.get('company')}")
                print("  [a] Agregar  [e] Editar  [d] Eliminar  [0] Volver")
                o = input("> ").strip().lower()
                if o in ("0", ""):
                    break
                if o == "a":
                    exp.append(new_exp())
                elif o == "e" and exp:
                    i = int(input("Número: ")) - 1
                    if 0 <= i < len(exp):
                        e = exp[i]
                        for k, lab in [("title", "Cargo"), ("company", "Empresa"), ("period", "Periodo"),
                                       ("location", "Ubicación"), ("description", "Descripción")]:
                            e[k] = ask(lab, e.get(k, ""))
                        b = ask("Bullets |", " | ".join(e.get("bullets") or []))
                        if b:
                            e["bullets"] = [x.strip() for x in b.split("|") if x.strip()]
                        te = ask("Tech coma", ", ".join(e.get("tech") or []))
                        if te:
                            e["tech"] = [x.strip() for x in te.split(",") if x.strip()]
                elif o == "d" and exp:
                    i = int(input("Número: ")) - 1
                    if 0 <= i < len(exp):
                        exp.pop(i)
            p["experience"] = exp
            save(PROFILE, p)

        elif op == "7":
            projects = load(PROJECTS, [])
            def new_proj():
                name = ask("Nombre")
                pid = "".join(c if c.isalnum() or c == "-" else "-" for c in name.lower().replace(" ", "-"))
                return {
                    "id": pid,
                    "name": name,
                    "description": ask("Descripción"),
                    "tech": [t.strip() for t in ask("Tech (coma)").split(",") if t.strip()],
                    "github": ask("GitHub URL"),
                    "demo": ask("Demo URL") or None,
                    "featured": ask("¿Destacado? s/n", "n").lower() in ("s", "si", "sí", "y"),
                }
            while True:
                print(f"\n=== Proyectos ({len(projects)}) ===")
                for i, pr in enumerate(projects, 1):
                    star = "★" if pr.get("featured") else " "
                    print(f" {star} {i}. {pr.get('name')}")
                print("  [a] Agregar  [e] Editar  [d] Eliminar  [0] Volver")
                o = input("> ").strip().lower()
                if o in ("0", ""):
                    break
                if o == "a":
                    projects.append(new_proj())
                elif o == "e" and projects:
                    i = int(input("Número: ")) - 1
                    if 0 <= i < len(projects):
                        pr = projects[i]
                        pr["name"] = ask("Nombre", pr.get("name", ""))
                        pr["description"] = ask("Descripción", pr.get("description", ""))
                        te = ask("Tech", ", ".join(pr.get("tech") or []))
                        if te:
                            pr["tech"] = [x.strip() for x in te.split(",") if x.strip()]
                        pr["github"] = ask("GitHub", pr.get("github", ""))
                        d = ask("Demo", pr.get("demo") or "")
                        pr["demo"] = d or None
                        pr["featured"] = ask("Destacado s/n", "s" if pr.get("featured") else "n").lower() in ("s", "si", "sí", "y")
                elif o == "d" and projects:
                    i = int(input("Número: ")) - 1
                    if 0 <= i < len(projects):
                        projects.pop(i)
            save(PROJECTS, projects)

        elif op == "8":
            edu = p.get("education", [])
            def new_edu():
                return {
                    "title": ask("Título"),
                    "institution": ask("Institución"),
                    "period": ask("Periodo"),
                    "status": ask("Estado (Completado/En curso)"),
                }
            p["education"] = menu_list_edit(
                "Educación", edu,
                [("title", "Título"), ("institution", "Institución"), ("period", "Periodo"), ("status", "Estado")],
                new_edu,
            )
            save(PROFILE, p)

        elif op == "9":
            certs = p.get("certifications", [])
            def new_cert():
                return {"name": ask("Nombre cert"), "org": ask("Organización")}
            p["certifications"] = menu_list_edit(
                "Certificaciones", certs,
                [("name", "Nombre"), ("org", "Organización")],
                new_cert,
            )
            save(PROFILE, p)

        elif op == "10":
            stack = p.get("techStack", {})
            print("\nGrupos actuales:", ", ".join(stack.keys()) or "(vacío)")
            g = ask("Grupo a editar/crear (ej Frontend)")
            if g:
                cur = ", ".join(stack.get(g, []))
                val = ask(f"Tecnologías de {g} (coma)", cur)
                if val:
                    stack[g] = [x.strip() for x in val.split(",") if x.strip()]
                p["techStack"] = stack
                save(PROFILE, p)

        elif op == "11":
            c = p.get("contact", {})
            for key, lab in [
                ("email", "Email"),
                ("phone", "Teléfono"),
                ("location", "Ubicación"),
                ("github", "GitHub URL"),
                ("linkedin", "LinkedIn URL"),
            ]:
                c[key] = ask(lab, c.get(key, ""))
            p["contact"] = c
            save(PROFILE, p)

        elif op == "12":
            highs = p.get("highlights", [])
            def new_h():
                return {"num": ask("Número (ej 2+)"), "label": ask("Label")}
            p["highlights"] = menu_list_edit(
                "Highlights (cards about)", highs,
                [("num", "Número"), ("label", "Label")],
                new_h,
            )
            save(PROFILE, p)

        else:
            print("Opción no válida")

        if op != "0":
            input("\nEnter para seguir...")


if __name__ == "__main__":
    main()
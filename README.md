# Portfolio de Uncharsacc

Portfolio personal con animación de fondo inspirada en la imagen de la mano de Jesús alcanzando a alguien, rayos de luz y atmósfera cálida.

## Cómo usarlo

### 1. Subir a GitHub Pages

1. Crea un repositorio llamado **`uncharsacc.github.io`** (importante que se llame exactamente así).
2. Sube **todo el contenido** de esta carpeta a la raíz del repositorio.
3. Ve a **Settings → Pages** y elige la rama `main` (o `master`).
4. En unos minutos tu portfolio estará en:  
   **https://uncharsacc.github.io**

### 2. Editar tu información personal

Abre el archivo:

```
data/profile.json
```

Ahí puedes cambiar:
- Nombre
- Título
- Tagline
- Texto “Sobre mí”
- Habilidades (nombre + porcentaje)
- Experiencia

Solo edita el JSON y guarda. La página se actualiza sola.

### 3. Agregar / quitar / editar proyectos (fácil)

Hay un script de Python para no tocar el código:

```bash
# Ver proyectos actuales
python manage_projects.py list

# Agregar un proyecto nuevo (te pregunta todo)
python manage_projects.py add

# Eliminar un proyecto
python manage_projects.py remove

# Editar un proyecto existente
python manage_projects.py edit
```

Los proyectos se guardan en `data/projects.json`.  
Cada proyecto puede tener:
- nombre
- descripción
- tecnologías
- link de GitHub
- link de demo (opcional)
- si es destacado o no

### 4. Estructura de archivos

```
uncharsacc-portfolio/
├── index.html
├── css/style.css
├── js/main.js
├── data/
│   ├── profile.json      ← tu info personal
│   └── projects.json     ← tus proyectos
├── manage_projects.py    ← script para gestionar proyectos
└── README.md
```

## Notas

- La animación del fondo es pura (Canvas + JavaScript). No necesita librerías.
- Todo es estático → perfecto para GitHub Pages.
- Puedes ir agregando proyectos de a poco cuando quieras.

¡Que Dios te bendiga en cada proyecto que construyas! 🙌

# Portfolio — Juan Nicolás Cabrera Werner

Portfolio profesional con toggle ES/EN, desplegado con Flask en Railway.

## Estructura

```
portfolio-nicolas/
├── index.html          # Portfolio principal
├── app.py              # Flask server
├── requirements.txt    # Dependencias
├── Procfile            # Comando Railway
└── static/
    ├── css/style.css
    └── js/lang.js
```

## Deploy en Railway

1. Subir esta carpeta como nuevo repositorio en GitHub
2. En Railway → New Project → Deploy from GitHub repo
3. Seleccionar el repo → Railway detecta el Procfile automáticamente
4. En Settings → Generate Domain → copiar URL pública

## Desarrollo local

```bash
pip install -r requirements.txt
python app.py
# Abre http://localhost:5000
```

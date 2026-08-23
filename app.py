import os, json, uuid, shutil
from functools import wraps
from flask import (Flask, render_template, request, redirect,
                   url_for, session, flash, send_from_directory)

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'jncw-portfolio-secret-2026')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'zentra2026')

DATA_FILE     = os.path.join(os.path.dirname(__file__), 'data', 'portfolio.json')
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'static', 'img', 'uploads')
ALLOWED_EXT   = {'png', 'jpg', 'jpeg', 'webp', 'gif'}

os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ── DEFAULT DATA ──────────────────────────────────────────────────────────────

DEFAULT_DATA = {
    "info": {
        "full_name":   "Juan Nicolás Cabrera Werner",
        "role_es":     "Python Developer — Soporte IT",
        "role_en":     "Python Developer — IT Support",
        "location":    "Tucumán, Argentina",
        "year":        "2026",
        "bio_es":      "Desarrollador Python con experiencia real en producción. Creador de Zentra, llevado de app de escritorio a plataforma web con IA integrada. Orientado a Data Science y Machine Learning.",
        "bio_en":      "Python developer with real production experience. Creator of Zentra, taken from desktop app to web platform with integrated AI. Focused on Data Science and Machine Learning.",
        "email":       "nicolascabrerawerner@gmail.com",
        "github":      "https://github.com/NicolasCabreraWerner",
        "phone":       "381-2201696",
        "initials":    "NC",
        "avatar_mode": "initials",
        "photo_file":  ""
    },
    "projects": [
        {
            "id": "zentra",
            "name": "Zentra", "name_en": "Zentra",
            "eyebrow": "Producto propio", "eyebrow_en": "Own product",
            "description": "Sistema de gestión de conocimiento y soporte técnico desarrollado íntegramente de forma autónoma para Núcleo IT. Nació como app de escritorio (Zentra Organizador) y evolucionó a Zentra Support IA, una plataforma web completa con inteligencia artificial integrada, desplegada en la nube con más de 33 versiones documentadas.",
            "desc_en": "Knowledge management and technical support system developed entirely autonomously for Núcleo IT. Started as a desktop app and evolved into Zentra Support AI, a full web platform with integrated AI, deployed in the cloud with over 33 documented versions.",
            "phase1_title": "Zentra Organizador", "phase1_title_en": "Zentra Organizador",
            "phase1_sub": "Desktop", "phase1_sub_en": "Desktop",
            "phase1_tech": "Python · Tkinter · OOP · SQLite",
            "phase2_title": "Zentra Support IA", "phase2_title_en": "Zentra Support AI",
            "phase2_sub": "Plataforma web", "phase2_sub_en": "Web platform",
            "phase2_tech": "Flask · PostgreSQL · OpenAI API · Railway",
            "stats": [
                {"num": "33+", "label": "versiones",  "label_en": "versions"},
                {"num": "26",  "label": "despliegues", "label_en": "deploys"},
                {"num": "10+", "label": "módulos",     "label_en": "modules"},
                {"num": "100%","label": "autónomo",    "label_en": "solo built"}
            ],
            "live": True,
            "images": [
                {"id":"d1","filename":"desktop-1.jpg","caption":"Vista principal — búsqueda, filtros y editor","caption_en":"Main view — search, filters and editor","tab":"desktop","wide":True},
                {"id":"d2","filename":"desktop-2.jpg","caption":"Gestión de adjuntos por registro","caption_en":"Attachment management per record","tab":"desktop","wide":False},
                {"id":"d3","filename":"desktop-3.jpg","caption":"Reproductor de audio · modo claro","caption_en":"Audio player · light mode","tab":"desktop","wide":False},
                {"id":"w1","filename":"web-1.jpg","caption":"Contact Center — herramientas e integraciones","caption_en":"Contact Center — tools and integrations","tab":"web","wide":True},
                {"id":"w2","filename":"web-2.jpg","caption":"AI Assistant con dictado por voz","caption_en":"AI Assistant with voice dictation","tab":"web","wide":False},
                {"id":"w3","filename":"web-3.jpg","caption":"Respuestas rápidas con comandos","caption_en":"Quick replies with commands","tab":"web","wide":False},
                {"id":"w4","filename":"web-4.jpg","caption":"Notas inteligentes con autoguardado","caption_en":"Smart notes with auto-save","tab":"web","wide":False},
                {"id":"w5","filename":"web-5.jpg","caption":"Configuración — paletas y módulos","caption_en":"Settings — palettes and modules","tab":"web","wide":True}
            ]
        }
    ],
    "experience": [
        {"id":"e1","years":"2022 — hoy","company":"Nucleo IT","company_en":"Nucleo IT","role":"Analista Soporte IT · Remoto","role_en":"IT Support Analyst · Remote","detail":"Desarrollo y mantenimiento de Zentra. Instalación de sistemas POS, soporte de periféricos, asistencia a clientes, SQL y Web Scraping.","detail_en":"Development and maintenance of Zentra. POS installation, peripheral support, client assistance, SQL and Web Scraping."},
        {"id":"e2","years":"2021 — hoy","company":"MS Informática","company_en":"MS Informática","role":"Técnico PC · Autónomo","role_en":"PC Technician · Freelance","detail":"Administración Windows, diagnóstico de fallas, redes, armado y mantenimiento de equipos.","detail_en":"Windows administration, fault diagnosis, networking, computer assembly and maintenance."},
        {"id":"e3","years":"2020 — 2022","company":"Sec. MiPyME Tucumán","company_en":"MiPyME Secretary","role":"Pasante Sistemas","role_en":"Systems Intern","detail":"Mantenimiento de equipos, asistencia técnica, Data Entry a bases de datos y planillas Excel.","detail_en":"Equipment maintenance, technical assistance, Data Entry to databases and Excel."},
        {"id":"e4","years":"2017 — 2021","company":"Lego Arquitectura","company_en":"Lego Arquitectura","role":"Técnico Eléctrico","role_en":"Electrical Technician","detail":"Planos eléctricos, instalaciones de baja y media tensión, dirección técnica en obras.","detail_en":"Electrical blueprints, low and medium voltage installations, technical supervision."}
    ],
    "education": [
        {"id":"edu1","year_range":"2017 — 2024","name":"UTN — FRT","degree":"Ingeniería en Sistemas de la Información","degree_en":"Information Systems Engineering"},
        {"id":"edu2","year_range":"2006 — 2011","name":"Inst. Salesiano L. Massa","degree":"Técnico Electrónico","degree_en":"Electronics Technician"}
    ],
    "certifications": [
        {"id":"c1","name":"Programación en Python Inicial","name_en":"Python Programming — Beginner","issuer":"UTN · 66 hs · 2022"},
        {"id":"c2","name":"Learning Data Science: Understanding the Basics","name_en":"Learning Data Science: Understanding the Basics","issuer":"LinkedIn Learning · 2024"},
        {"id":"c3","name":"Principios de Inteligencia Artificial","name_en":"AI Fundamentals","issuer":"Digital House"},
        {"id":"c4","name":"Inglés Intensivo A1 · A1.2","name_en":"Intensive English A1 · A1.2","issuer":"Instituto Rush · 168 hs · 2023–2024"},
        {"id":"c5","name":"Ingeniería de Prompts · Gestión con IA","name_en":"Prompt Engineering · AI Project Management","issuer":"Formación continua"}
    ],
    "skills": [
        {"id":"s1","title":"Python","title_en":"Python","items":"OOP · Flask · FastAPI · Tkinter · Web Scraping · Machine Learning"},
        {"id":"s2","title":"Datos","title_en":"Data","items":"PostgreSQL · MySQL · SQL Server · SQLite · Power BI · Pandas · Jupyter"},
        {"id":"s3","title":"IA & ML","title_en":"IA & ML","items":"OpenAI API · Ing. de Prompts · Data Science · Machine Learning"},
        {"id":"s4","title":"Sistemas","title_en":"Systems","items":"Linux · Windows Admin · Redes TCP/IP · Hardware · VirtualBox"},
        {"id":"s5","title":"Web","title_en":"Web","items":"HTML · CSS · JavaScript · Flask · Railway · Git · VS Code"}
    ],
    "languages": [
        {"id":"l1","lang_name":"Español","level":"Nativo","level_en":"Native"},
        {"id":"l2","lang_name":"Inglés","level":"A1.2 cert. · B1 en curso","level_en":"A1.2 cert. · B1 in progress"},
        {"id":"l3","lang_name":"Alemán","level":"Básico","level_en":"Basic"}
    ]
}

# ── JSON HELPERS ──────────────────────────────────────────────────────────────

def load_data():
    if not os.path.exists(DATA_FILE):
        save_data(DEFAULT_DATA)
        return DEFAULT_DATA
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXT

def img_src(filename):
    """Return correct static path for an image."""
    zentra = ['desktop-1.jpg','desktop-2.jpg','desktop-3.jpg',
              'web-1.jpg','web-2.jpg','web-3.jpg','web-4.jpg','web-5.jpg']
    if filename in zentra:
        return url_for('static', filename='img/zentra/' + filename)
    return url_for('static', filename='img/uploads/' + filename)

app.jinja_env.globals['img_src'] = img_src

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('admin'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated

# ── PUBLIC ────────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    data = load_data()
    return render_template('public/index.html', **data)

# ── ADMIN LOGIN ───────────────────────────────────────────────────────────────

@app.route('/admin', methods=['GET', 'POST'])
def admin_login():
    if session.get('admin'):
        return redirect(url_for('admin_dashboard'))
    error = None
    if request.method == 'POST':
        if request.form.get('password') == ADMIN_PASSWORD:
            session['admin'] = True
            return redirect(url_for('admin_dashboard'))
        error = 'Contraseña incorrecta'
    return render_template('admin/login.html', error=error)

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin', None)
    return redirect(url_for('index'))

# ── ADMIN DASHBOARD ───────────────────────────────────────────────────────────

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    data = load_data()
    return render_template('admin/dashboard.html',
        pcount=len(data['projects']),
        ecount=len(data['experience']),
        ccount=len(data['certifications']),
        icount=sum(len(p['images']) for p in data['projects']))

# ── ADMIN INFO ────────────────────────────────────────────────────────────────

@app.route('/admin/info', methods=['GET', 'POST'])
@login_required
def admin_info():
    data = load_data()
    if request.method == 'POST':
        f = request.form
        data['info'].update({k: f.get(k, '') for k in [
            'full_name','role_es','role_en','location','year',
            'bio_es','bio_en','email','github','phone','initials']})
        if 'photo' in request.files and request.files['photo'].filename:
            file = request.files['photo']
            if allowed_file(file.filename):
                ext = file.filename.rsplit('.', 1)[1].lower()
                fname = f'profile.{ext}'
                file.save(os.path.join('static', 'img', fname))
                data['info']['photo_file'] = fname
                data['info']['avatar_mode'] = 'photo'
        save_data(data)
        flash('✅ Información actualizada', 'success')
        return redirect(url_for('admin_info'))
    return render_template('admin/info.html', info=data['info'])

# ── ADMIN PROJECTS ────────────────────────────────────────────────────────────

@app.route('/admin/projects')
@login_required
def admin_projects():
    data = load_data()
    return render_template('admin/projects.html', projects=data['projects'])

@app.route('/admin/projects/new', methods=['GET', 'POST'])
@login_required
def admin_project_new():
    if request.method == 'POST':
        data = load_data()
        f = request.form
        proj = {
            'id': uuid.uuid4().hex[:8],
            'name': f.get('name',''), 'name_en': f.get('name_en',''),
            'eyebrow': f.get('eyebrow',''), 'eyebrow_en': f.get('eyebrow_en',''),
            'description': f.get('description',''), 'desc_en': f.get('desc_en',''),
            'phase1_title': f.get('phase1_title',''), 'phase1_title_en': f.get('phase1_title_en',''),
            'phase1_sub': f.get('phase1_sub',''), 'phase1_sub_en': f.get('phase1_sub_en',''),
            'phase1_tech': f.get('phase1_tech',''),
            'phase2_title': f.get('phase2_title',''), 'phase2_title_en': f.get('phase2_title_en',''),
            'phase2_sub': f.get('phase2_sub',''), 'phase2_sub_en': f.get('phase2_sub_en',''),
            'phase2_tech': f.get('phase2_tech',''),
            'stats': [
                {'num': f.get(f'stat{i}_num',''), 'label': f.get(f'stat{i}_label',''), 'label_en': f.get(f'stat{i}_label_en','')}
                for i in range(1,5) if f.get(f'stat{i}_num')
            ],
            'live': 'live' in f,
            'images': []
        }
        data['projects'].append(proj)
        save_data(data)
        flash('✅ Proyecto creado', 'success')
        return redirect(url_for('admin_projects'))
    return render_template('admin/project_form.html', project=None)

@app.route('/admin/projects/<pid>/edit', methods=['GET', 'POST'])
@login_required
def admin_project_edit(pid):
    data = load_data()
    proj = next((p for p in data['projects'] if p['id'] == pid), None)
    if not proj:
        flash('Proyecto no encontrado', 'error')
        return redirect(url_for('admin_projects'))
    if request.method == 'POST':
        f = request.form
        proj.update({
            'name': f.get('name',''), 'name_en': f.get('name_en',''),
            'eyebrow': f.get('eyebrow',''), 'eyebrow_en': f.get('eyebrow_en',''),
            'description': f.get('description',''), 'desc_en': f.get('desc_en',''),
            'phase1_title': f.get('phase1_title',''), 'phase1_title_en': f.get('phase1_title_en',''),
            'phase1_sub': f.get('phase1_sub',''), 'phase1_sub_en': f.get('phase1_sub_en',''),
            'phase1_tech': f.get('phase1_tech',''),
            'phase2_title': f.get('phase2_title',''), 'phase2_title_en': f.get('phase2_title_en',''),
            'phase2_sub': f.get('phase2_sub',''), 'phase2_sub_en': f.get('phase2_sub_en',''),
            'phase2_tech': f.get('phase2_tech',''),
            'stats': [
                {'num': f.get(f'stat{i}_num',''), 'label': f.get(f'stat{i}_label',''), 'label_en': f.get(f'stat{i}_label_en','')}
                for i in range(1,5) if f.get(f'stat{i}_num')
            ],
            'live': 'live' in f
        })
        save_data(data)
        flash('✅ Proyecto actualizado', 'success')
        return redirect(url_for('admin_project_edit', pid=pid))
    return render_template('admin/project_form.html', project=proj)

@app.route('/admin/projects/<pid>/delete', methods=['POST'])
@login_required
def admin_project_delete(pid):
    data = load_data()
    data['projects'] = [p for p in data['projects'] if p['id'] != pid]
    save_data(data)
    flash('🗑️ Proyecto eliminado', 'info')
    return redirect(url_for('admin_projects'))

# ── ADMIN IMAGES ──────────────────────────────────────────────────────────────

@app.route('/admin/projects/<pid>/images/upload', methods=['POST'])
@login_required
def admin_image_upload(pid):
    data = load_data()
    proj = next((p for p in data['projects'] if p['id'] == pid), None)
    if not proj:
        return redirect(url_for('admin_projects'))
    tab = request.form.get('tab_group', 'web')
    saved = 0
    for file in request.files.getlist('images'):
        if file and allowed_file(file.filename):
            ext = file.filename.rsplit('.', 1)[1].lower()
            fname = f"{uuid.uuid4().hex}.{ext}"
            file.save(os.path.join(UPLOAD_FOLDER, fname))
            proj['images'].append({'id': uuid.uuid4().hex[:8], 'filename': fname,
                                   'caption': '', 'caption_en': '', 'tab': tab, 'wide': False})
            saved += 1
    save_data(data)
    flash(f'✅ {saved} imagen(es) subida(s)', 'success')
    return redirect(url_for('admin_project_edit', pid=pid))

@app.route('/admin/projects/<pid>/images/<iid>/update', methods=['POST'])
@login_required
def admin_image_update(pid, iid):
    data = load_data()
    proj = next((p for p in data['projects'] if p['id'] == pid), None)
    if proj:
        img = next((i for i in proj['images'] if i['id'] == iid), None)
        if img:
            img.update({'caption': request.form.get('caption',''),
                        'caption_en': request.form.get('caption_en',''),
                        'tab': request.form.get('tab_group','web'),
                        'wide': 'is_wide' in request.form})
        save_data(data)
    flash('✅ Imagen actualizada', 'success')
    return redirect(url_for('admin_project_edit', pid=pid))

@app.route('/admin/projects/<pid>/images/<iid>/delete', methods=['POST'])
@login_required
def admin_image_delete(pid, iid):
    data = load_data()
    proj = next((p for p in data['projects'] if p['id'] == pid), None)
    if proj:
        proj['images'] = [i for i in proj['images'] if i['id'] != iid]
        save_data(data)
    flash('🗑️ Imagen eliminada', 'info')
    return redirect(url_for('admin_project_edit', pid=pid))

# ── ADMIN SIMPLE CRUD (experience, education, certifications, skills, languages)

def _simple_crud(section, template, title_field='name'):
    data = load_data()
    if request.method == 'POST':
        action = request.form.get('action')
        item_id = request.form.get('id')
        if action == 'delete':
            data[section] = [x for x in data[section] if x['id'] != item_id]
        else:
            fields = {k: v for k, v in request.form.items() if k not in ('action','id')}
            if action == 'add':
                fields['id'] = uuid.uuid4().hex[:8]
                data[section].append(fields)
            elif action == 'update':
                item = next((x for x in data[section] if x['id'] == item_id), None)
                if item:
                    item.update(fields)
        save_data(data)
        flash('✅ Guardado', 'success')
        return redirect(request.url)
    return render_template(template, items=data[section])

@app.route('/admin/experience', methods=['GET','POST'])
@login_required
def admin_experience():
    return _simple_crud('experience', 'admin/experience.html')

@app.route('/admin/education', methods=['GET','POST'])
@login_required
def admin_education():
    return _simple_crud('education', 'admin/education.html')

@app.route('/admin/certifications', methods=['GET','POST'])
@login_required
def admin_certifications():
    return _simple_crud('certifications', 'admin/certifications.html')

@app.route('/admin/skills', methods=['GET','POST'])
@login_required
def admin_skills():
    return _simple_crud('skills', 'admin/skills.html')

@app.route('/admin/languages', methods=['GET','POST'])
@login_required
def admin_languages():
    return _simple_crud('languages', 'admin/languages.html')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

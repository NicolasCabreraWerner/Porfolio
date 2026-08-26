import os, json, uuid, base64, zlib
from functools import wraps
from flask import (Flask, render_template, request, redirect,
                   url_for, session, flash, send_from_directory)

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'jncw-portfolio-secret-2026')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'zentra2026')

# Imagenes de Zentra hardcodeadas (no cambian)
ZENTRA_IMGS   = {'desktop-1.jpg','desktop-2.jpg','desktop-3.jpg',
                 'web-1.jpg','web-2.jpg','web-3.jpg','web-4.jpg','web-5.jpg'}
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'static', 'img', 'uploads')
ALLOWED_EXT   = {'png','jpg','jpeg','webp','gif'}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ── RAILWAY API para persistir variables ───────────────────────────────────────
RAILWAY_TOKEN   = os.environ.get('RAILWAY_TOKEN', '')
RAILWAY_PROJECT = os.environ.get('RAILWAY_PROJECT_ID', '')
RAILWAY_SERVICE = os.environ.get('RAILWAY_SERVICE_ID', '')
RAILWAY_ENV     = os.environ.get('RAILWAY_ENVIRONMENT_ID', '')

def push_to_railway(data_json_str):
    """Actualiza PORTFOLIO_DATA en Railway via GraphQL API."""
    if not RAILWAY_TOKEN:
        return False
    import urllib.request
    query = """
    mutation variableUpsert($input: VariableUpsertInput!, $skipDeploys: Boolean) {
      variableUpsert(input: $input, skipDeploys: $skipDeploys)
    }
    """
    payload = json.dumps({
        "query": query,
        "variables": {
            "input": {
                "projectId":     RAILWAY_PROJECT,
                "serviceId":     RAILWAY_SERVICE,
                "environmentId": RAILWAY_ENV,
                "name":  "PORTFOLIO_DATA",
                "value": data_json_str
            },
            "skipDeploys": True
        }
    }).encode()
    req = urllib.request.Request(
        "https://backboard.railway.com/graphql/v2",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {RAILWAY_TOKEN}"
        }
    )
    try:
        with urllib.request.urlopen(req, timeout=8) as r:
            return r.status == 200
    except Exception:
        return False

# ── JSON HELPERS ───────────────────────────────────────────────────────────────

DEFAULT_DATA = {
    "info": {
        "full_name":   "Juan Nicolás Cabrera Werner",
        "role_es":     "Application Support · Technical Support L2/L3 · Python · IA",
        "role_en":     "Application Support · Technical Support L2/L3 · Python · AI",
        "location":    "Tucumán, Argentina",
        "year":        "2026",
        "bio_es":      "Especialista en soporte técnico y aplicaciones con experiencia resolviendo incidentes en sistemas de gestión, SQL, bases de datos, redes, periféricos POS y entornos Windows/Linux. Desarrollo herramientas en Python y soluciones web con IA para acelerar diagnósticos, automatizar tareas y centralizar conocimiento técnico.",
        "bio_en":      "Application and technical support specialist with hands-on experience troubleshooting business systems, SQL, databases, networks, POS peripherals and Windows/Linux environments. I build Python tools and AI-powered web solutions to speed up diagnostics, automate workflows and centralize technical knowledge.",
        "email":       "nicolascabrerawerner@gmail.com",
        "github":      "https://github.com/NicolasCabreraWerner",
        "phone":       "381-2201696",
        "initials":    "NC",
        "avatar_mode": "photo",
        "photo_file":  "profile.png",
        "target_roles_es": "Application Support · Technical Support L2/L3 · Implementation · Solutions · AI Automation",
        "target_roles_en": "Application Support · Technical Support L2/L3 · Implementation · Solutions · AI Automation"
    },
    "projects": [], "experience": [], "education": [],
    "certifications": [], "skills": [], "languages": []
}

DATA_FILE = os.path.join(os.path.dirname(__file__), 'data', 'portfolio.json')

def _seed_from_env_once():
    """Al arrancar el proceso (container nuevo), siembra el archivo local
    con el último estado guardado en Railway. Las variables de entorno de
    Railway NO se actualizan en caliente dentro de un proceso ya corriendo,
    así que esto solo importa en el arranque del contenedor."""
    env_data = os.environ.get('PORTFOLIO_DATA', '')
    if not env_data:
        return
    try:
        json.loads(env_data)  # valida que sea JSON correcto
    except Exception:
        return
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        f.write(env_data)

_seed_from_env_once()

def load_data():
    """SIEMPRE lee del archivo local -> refleja cambios al instante,
    sin depender de que Railway propague la variable de entorno."""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return DEFAULT_DATA

def save_data(data):
    """Escribe el archivo local (efecto inmediato) y además empuja a la
    variable de Railway para sobrevivir al próximo reinicio del contenedor."""
    data_str = json.dumps(data, ensure_ascii=False)
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        f.write(data_str)
    push_to_railway(data_str)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXT

def img_src(filename):
    # Imágenes subidas por el admin: se guardan como data-URI base64 dentro
    # del propio JSON, así sobreviven a reinicios reales del contenedor.
    if filename.startswith('data:image'):
        return filename
    if filename in ZENTRA_IMGS:
        return url_for('static', filename='img/zentra/' + filename)
    return url_for('static', filename='img/uploads/' + filename)

app.jinja_env.globals['img_src'] = img_src
app.jinja_env.filters['img_src'] = img_src

def image_to_data_uri(file_storage, max_w=1200, quality=78):
    """Redimensiona/comprime la imagen subida y la devuelve como data-URI
    base64, para que quede embebida en PORTFOLIO_DATA y sobreviva a
    cualquier reinicio del contenedor (no depende del disco efímero)."""
    try:
        from PIL import Image
        import io
        img = Image.open(file_storage.stream)
        if img.mode in ('RGBA', 'LA', 'P'):
            img = img.convert('RGB')
        w, h = img.size
        if w > max_w:
            img = img.resize((max_w, int(h * max_w / w)), Image.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, 'JPEG', quality=quality, optimize=True)
        b64 = base64.b64encode(buf.getvalue()).decode()
        return f'data:image/jpeg;base64,{b64}'
    except Exception:
        return None

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('admin'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated

# ── PUBLIC ─────────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return render_template('public/index.html', **load_data())

# ── ADMIN LOGIN ─────────────────────────────────────────────────────────────────

@app.route('/admin', methods=['GET','POST'])
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

# ── DASHBOARD ───────────────────────────────────────────────────────────────────

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    data = load_data()
    return render_template('admin/dashboard.html',
        pcount=len(data['projects']),
        ecount=len(data['experience']),
        ccount=len(data['certifications']),
        icount=sum(len(p['images']) for p in data['projects']))

# ── INFO ────────────────────────────────────────────────────────────────────────

@app.route('/admin/info', methods=['GET','POST'])
@login_required
def admin_info():
    data = load_data()
    if request.method == 'POST':
        f = request.form
        data['info'].update({k: f.get(k,'') for k in [
            'full_name','role_es','role_en','location','year',
            'bio_es','bio_en','email','github','phone','initials']})
        if 'photo' in request.files and request.files['photo'].filename:
            file = request.files['photo']
            if allowed_file(file.filename):
                ext = file.filename.rsplit('.',1)[1].lower()
                fname = f'profile.{ext}'
                file.save(os.path.join('static','img',fname))
                data['info']['photo_file']  = fname
                data['info']['avatar_mode'] = 'photo'
        save_data(data)
        flash('✅ Información actualizada','success')
        return redirect(url_for('admin_info'))
    return render_template('admin/info.html', info=data['info'])

# ── PROJECTS ────────────────────────────────────────────────────────────────────

@app.route('/admin/projects')
@login_required
def admin_projects():
    return render_template('admin/projects.html', projects=load_data()['projects'])

@app.route('/admin/projects/new', methods=['GET','POST'])
@login_required
def admin_project_new():
    if request.method == 'POST':
        data = load_data()
        f    = request.form
        proj = {
            'id': uuid.uuid4().hex[:8],
            'name':f.get('name',''),'name_en':f.get('name_en',''),
            'eyebrow':f.get('eyebrow',''),'eyebrow_en':f.get('eyebrow_en',''),
            'description':f.get('description',''),'desc_en':f.get('desc_en',''),
            'phase1_title':f.get('phase1_title',''),'phase1_title_en':f.get('phase1_title_en',''),
            'phase1_sub':f.get('phase1_sub',''),'phase1_sub_en':f.get('phase1_sub_en',''),
            'phase1_tech':f.get('phase1_tech',''),
            'phase2_title':f.get('phase2_title',''),'phase2_title_en':f.get('phase2_title_en',''),
            'phase2_sub':f.get('phase2_sub',''),'phase2_sub_en':f.get('phase2_sub_en',''),
            'phase2_tech':f.get('phase2_tech',''),
            'stats':[{'num':f.get(f'stat{i}_num',''),'label':f.get(f'stat{i}_label',''),'label_en':f.get(f'stat{i}_label_en','')}
                     for i in range(1,5) if f.get(f'stat{i}_num')],
            'live':'live' in f, 'images':[]
        }
        data['projects'].append(proj)
        save_data(data)
        flash('✅ Proyecto creado','success')
        return redirect(url_for('admin_projects'))
    return render_template('admin/project_form.html', project=None)

@app.route('/admin/projects/<pid>/edit', methods=['GET','POST'])
@login_required
def admin_project_edit(pid):
    data = load_data()
    proj = next((p for p in data['projects'] if p['id']==pid), None)
    if not proj:
        flash('Proyecto no encontrado','error')
        return redirect(url_for('admin_projects'))
    if request.method == 'POST':
        f = request.form
        proj.update({
            'name':f.get('name',''),'name_en':f.get('name_en',''),
            'eyebrow':f.get('eyebrow',''),'eyebrow_en':f.get('eyebrow_en',''),
            'description':f.get('description',''),'desc_en':f.get('desc_en',''),
            'phase1_title':f.get('phase1_title',''),'phase1_title_en':f.get('phase1_title_en',''),
            'phase1_sub':f.get('phase1_sub',''),'phase1_sub_en':f.get('phase1_sub_en',''),
            'phase1_tech':f.get('phase1_tech',''),
            'phase2_title':f.get('phase2_title',''),'phase2_title_en':f.get('phase2_title_en',''),
            'phase2_sub':f.get('phase2_sub',''),'phase2_sub_en':f.get('phase2_sub_en',''),
            'phase2_tech':f.get('phase2_tech',''),
            'stats':[{'num':f.get(f'stat{i}_num',''),'label':f.get(f'stat{i}_label',''),'label_en':f.get(f'stat{i}_label_en','')}
                     for i in range(1,5) if f.get(f'stat{i}_num')],
            'live':'live' in f
        })
        save_data(data)
        flash('✅ Proyecto actualizado','success')
        return redirect(url_for('admin_project_edit', pid=pid))
    return render_template('admin/project_form.html', project=proj)

@app.route('/admin/projects/<pid>/delete', methods=['POST'])
@login_required
def admin_project_delete(pid):
    data = load_data()
    data['projects'] = [p for p in data['projects'] if p['id']!=pid]
    save_data(data)
    flash('🗑️ Proyecto eliminado','info')
    return redirect(url_for('admin_projects'))

# ── IMAGES ──────────────────────────────────────────────────────────────────────

@app.route('/admin/projects/<pid>/images/upload', methods=['POST'])
@login_required
def admin_image_upload(pid):
    data = load_data()
    proj = next((p for p in data['projects'] if p['id']==pid), None)
    if not proj: return redirect(url_for('admin_projects'))
    tab   = request.form.get('tab_group','web')
    saved = 0
    for file in request.files.getlist('images'):
        if file and allowed_file(file.filename):
            data_uri = image_to_data_uri(file)
            if data_uri:
                proj['images'].insert(0, {'id':uuid.uuid4().hex[:8],'filename':data_uri,
                                          'caption':'','caption_en':'','tab':tab,'wide':False})
                saved += 1
    save_data(data)
    flash(f'✅ {saved} imagen(es) subida(s)','success')
    return redirect(url_for('admin_project_edit', pid=pid))

@app.route('/admin/projects/<pid>/images/<iid>/update', methods=['POST'])
@login_required
def admin_image_update(pid, iid):
    data = load_data()
    proj = next((p for p in data['projects'] if p['id']==pid), None)
    if proj:
        img = next((i for i in proj['images'] if i['id']==iid), None)
        if img:
            img.update({'caption':request.form.get('caption',''),
                        'caption_en':request.form.get('caption_en',''),
                        'tab':request.form.get('tab_group','web'),
                        'wide':'is_wide' in request.form})
        save_data(data)
    flash('✅ Imagen actualizada','success')
    return redirect(url_for('admin_project_edit', pid=pid))

@app.route('/admin/projects/<pid>/images/<iid>/delete', methods=['POST'])
@login_required
def admin_image_delete(pid, iid):
    data = load_data()
    proj = next((p for p in data['projects'] if p['id']==pid), None)
    if proj:
        proj['images'] = [i for i in proj['images'] if i['id']!=iid]
        save_data(data)
    flash('🗑️ Imagen eliminada','info')
    return redirect(url_for('admin_project_edit', pid=pid))

@app.route('/admin/projects/<pid>/images/<iid>/move', methods=['POST'])
@login_required
def admin_image_move(pid, iid):
    """Mueve una imagen una posición hacia arriba o abajo en la lista."""
    data = load_data()
    proj = next((p for p in data['projects'] if p['id']==pid), None)
    if proj:
        imgs = proj['images']
        idx  = next((i for i, im in enumerate(imgs) if im['id']==iid), None)
        direction = request.form.get('direction')
        if idx is not None:
            if direction == 'up' and idx > 0:
                imgs[idx-1], imgs[idx] = imgs[idx], imgs[idx-1]
            elif direction == 'down' and idx < len(imgs)-1:
                imgs[idx+1], imgs[idx] = imgs[idx], imgs[idx+1]
        save_data(data)
    return redirect(url_for('admin_project_edit', pid=pid))

@app.route('/admin/projects/<pid>/images/<iid>/cover', methods=['POST'])
@login_required
def admin_image_cover(pid, iid):
    """Marca una imagen como portada: la mueve al frente de la lista,
    que es la que se muestra en la tarjeta pública."""
    data = load_data()
    proj = next((p for p in data['projects'] if p['id']==pid), None)
    if proj:
        imgs = proj['images']
        idx  = next((i for i, im in enumerate(imgs) if im['id']==iid), None)
        if idx is not None and idx != 0:
            img = imgs.pop(idx)
            imgs.insert(0, img)
        save_data(data)
    flash('⭐ Portada actualizada','success')
    return redirect(url_for('admin_project_edit', pid=pid))

# ── SIMPLE CRUD ─────────────────────────────────────────────────────────────────

def _simple_crud(section, template):
    data = load_data()
    if request.method == 'POST':
        action  = request.form.get('action')
        item_id = request.form.get('id')
        if action == 'delete':
            data[section] = [x for x in data[section] if x['id'] != item_id]
        else:
            fields = {k:v for k,v in request.form.items() if k not in ('action','id')}
            if action == 'add':
                fields['id'] = uuid.uuid4().hex[:8]
                data[section].append(fields)
            elif action == 'update':
                item = next((x for x in data[section] if x['id']==item_id), None)
                if item: item.update(fields)
        save_data(data)
        flash('✅ Guardado','success')
        return redirect(request.url)
    return render_template(template, items=data[section])

@app.route('/admin/experience',     methods=['GET','POST'])
@login_required
def admin_experience():     return _simple_crud('experience',    'admin/experience.html')

@app.route('/admin/education',      methods=['GET','POST'])
@login_required
def admin_education():      return _simple_crud('education',     'admin/education.html')

@app.route('/admin/certifications', methods=['GET','POST'])
@login_required
def admin_certifications(): return _simple_crud('certifications','admin/certifications.html')

@app.route('/admin/skills',         methods=['GET','POST'])
@login_required
def admin_skills():         return _simple_crud('skills',        'admin/skills.html')

@app.route('/admin/languages',      methods=['GET','POST'])
@login_required
def admin_languages():      return _simple_crud('languages',     'admin/languages.html')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

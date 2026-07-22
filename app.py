import os, json, uuid
from functools import wraps
from flask import (Flask, render_template, request, redirect,
                   url_for, session, flash, send_from_directory)

app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = os.environ.get('SECRET_KEY', 'jncw-2026-secret')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'zentra2026')

DATA_FILE     = os.path.join(os.path.dirname(__file__), 'data', 'portfolio.json')
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'static', 'img', 'uploads')
ZENTRA_IMGS   = {'desktop-1.jpg','desktop-2.jpg','desktop-3.jpg',
                 'web-1.jpg','web-2.jpg','web-3.jpg','web-4.jpg','web-5.jpg'}
ALLOWED_EXT   = {'png','jpg','jpeg','webp','gif'}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def load():
    with open(DATA_FILE, encoding='utf-8') as f:
        return json.load(f)

def save(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def allowed(filename):
    return '.' in filename and filename.rsplit('.',1)[1].lower() in ALLOWED_EXT

def img_url(filename):
    if filename in ZENTRA_IMGS:
        return url_for('static', filename='img/zentra/' + filename)
    return url_for('static', filename='img/uploads/' + filename)

app.jinja_env.globals['img_url'] = img_url

def login_required(f):
    @wraps(f)
    def dec(*a, **kw):
        if not session.get('admin'):
            return redirect(url_for('admin_login'))
        return f(*a, **kw)
    return dec

# PUBLIC
@app.route('/')
def index():
    return render_template('index.html', **load())

# ADMIN LOGIN
@app.route('/admin', methods=['GET','POST'])
def admin_login():
    if session.get('admin'):
        return redirect(url_for('dashboard'))
    err = None
    if request.method == 'POST':
        if request.form.get('password') == ADMIN_PASSWORD:
            session['admin'] = True
            return redirect(url_for('dashboard'))
        err = 'Contraseña incorrecta'
    return render_template('admin/login.html', error=err)

@app.route('/admin/logout')
def admin_logout():
    session.clear()
    return redirect(url_for('index'))

# DASHBOARD
@app.route('/admin/dashboard')
@login_required
def dashboard():
    d = load()
    return render_template('admin/dashboard.html',
        pcount=len(d['projects']), ecount=len(d['experience']),
        ccount=len(d['certifications']),
        icount=sum(len(p['images']) for p in d['projects']))

# INFO PERSONAL
@app.route('/admin/info', methods=['GET','POST'])
@login_required
def admin_info():
    d = load()
    if request.method == 'POST':
        for k in ['full_name','role_es','role_en','location','year',
                  'bio_es','bio_en','email','github','phone','initials']:
            d['info'][k] = request.form.get(k,'')
        photo = request.files.get('photo')
        if photo and photo.filename and allowed(photo.filename):
            ext  = photo.filename.rsplit('.',1)[1].lower()
            name = f'profile.{ext}'
            photo.save(os.path.join('static','img', name))
            d['info']['photo_file']  = name
            d['info']['avatar_mode'] = 'photo'
        save(d)
        flash('✅ Información actualizada','success')
        return redirect(url_for('admin_info'))
    return render_template('admin/info.html', info=d['info'])

# PROYECTOS
@app.route('/admin/projects')
@login_required
def admin_projects():
    return render_template('admin/projects.html', projects=load()['projects'])

@app.route('/admin/projects/new', methods=['GET','POST'])
@login_required
def project_new():
    if request.method == 'POST':
        d = load(); f = request.form
        proj = {k:f.get(k,'') for k in [
            'name','name_en','eyebrow','eyebrow_en','description','desc_en',
            'phase1_title','phase1_title_en','phase1_sub','phase1_sub_en','phase1_tech',
            'phase2_title','phase2_title_en','phase2_sub','phase2_sub_en','phase2_tech']}
        proj['id']    = uuid.uuid4().hex[:8]
        proj['live']  = 'live' in f
        proj['stats'] = [{'num':f.get(f's{i}n',''),'label':f.get(f's{i}l',''),'label_en':f.get(f's{i}le','')} for i in range(1,5) if f.get(f's{i}n')]
        proj['images'] = []
        d['projects'].append(proj)
        save(d); flash('✅ Proyecto creado','success')
        return redirect(url_for('admin_projects'))
    return render_template('admin/project_form.html', p=None)

@app.route('/admin/projects/<pid>', methods=['GET','POST'])
@login_required
def project_edit(pid):
    d = load()
    proj = next((x for x in d['projects'] if x['id']==pid), None)
    if not proj: return redirect(url_for('admin_projects'))
    if request.method == 'POST':
        f = request.form
        for k in ['name','name_en','eyebrow','eyebrow_en','description','desc_en',
                  'phase1_title','phase1_title_en','phase1_sub','phase1_sub_en','phase1_tech',
                  'phase2_title','phase2_title_en','phase2_sub','phase2_sub_en','phase2_tech']:
            proj[k] = f.get(k,'')
        proj['live']  = 'live' in f
        proj['stats'] = [{'num':f.get(f's{i}n',''),'label':f.get(f's{i}l',''),'label_en':f.get(f's{i}le','')} for i in range(1,5) if f.get(f's{i}n')]
        save(d); flash('✅ Proyecto actualizado','success')
        return redirect(url_for('project_edit', pid=pid))
    return render_template('admin/project_form.html', p=proj)

@app.route('/admin/projects/<pid>/delete', methods=['POST'])
@login_required
def project_delete(pid):
    d = load()
    d['projects'] = [x for x in d['projects'] if x['id']!=pid]
    save(d); flash('🗑️ Eliminado','info')
    return redirect(url_for('admin_projects'))

# IMÁGENES
@app.route('/admin/projects/<pid>/images', methods=['POST'])
@login_required
def image_upload(pid):
    d = load()
    proj = next((x for x in d['projects'] if x['id']==pid), None)
    if not proj: return redirect(url_for('admin_projects'))
    tab = request.form.get('tab','web'); n = 0
    for file in request.files.getlist('images'):
        if file and allowed(file.filename):
            ext  = file.filename.rsplit('.',1)[1].lower()
            name = uuid.uuid4().hex + '.' + ext
            file.save(os.path.join(UPLOAD_FOLDER, name))
            proj['images'].append({'id':uuid.uuid4().hex[:6],'filename':name,
                'caption':'','caption_en':'','tab':tab,'wide':False})
            n += 1
    save(d); flash(f'✅ {n} imagen(es) subida(s)','success')
    return redirect(url_for('project_edit', pid=pid))

@app.route('/admin/projects/<pid>/images/<iid>', methods=['POST'])
@login_required
def image_update(pid, iid):
    d = load()
    proj = next((x for x in d['projects'] if x['id']==pid), None)
    if proj:
        if request.form.get('action') == 'delete':
            proj['images'] = [i for i in proj['images'] if i['id']!=iid]
        else:
            img = next((i for i in proj['images'] if i['id']==iid), None)
            if img:
                img['caption']    = request.form.get('caption','')
                img['caption_en'] = request.form.get('caption_en','')
                img['tab']        = request.form.get('tab','web')
                img['wide']       = 'wide' in request.form
        save(d)
    return redirect(url_for('project_edit', pid=pid))

# SECCIONES SIMPLES
def crud(section, template):
    d = load()
    if request.method == 'POST':
        action = request.form.get('action')
        iid    = request.form.get('id','')
        fields = {k:v for k,v in request.form.items() if k not in ('action','id')}
        if   action=='add':    fields['id']=uuid.uuid4().hex[:8]; d[section].append(fields)
        elif action=='update':
            item = next((x for x in d[section] if x.get('id')==iid),None)
            if item: item.update(fields)
        elif action=='delete': d[section]=[x for x in d[section] if x.get('id')!=iid]
        save(d); flash('✅ Guardado','success')
        return redirect(request.url)
    return render_template(template, items=d[section])

@app.route('/admin/experience',     methods=['GET','POST'])
@login_required
def admin_experience():     return crud('experience',    'admin/experience.html')

@app.route('/admin/education',      methods=['GET','POST'])
@login_required
def admin_education():      return crud('education',     'admin/education.html')

@app.route('/admin/certifications', methods=['GET','POST'])
@login_required
def admin_certifications(): return crud('certifications','admin/certifications.html')

@app.route('/admin/skills',         methods=['GET','POST'])
@login_required
def admin_skills():         return crud('skills',        'admin/skills.html')

@app.route('/admin/languages',      methods=['GET','POST'])
@login_required
def admin_languages():      return crud('languages',     'admin/languages.html')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

import os
from flask import Flask, render_template, redirect, url_for, request, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from datetime import datetime
from supabase import create_client, Client

from models import db, Usuario, Romaneio, NotaFiscal
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)

# Cliente Supabase
supabase: Client = create_client(app.config['SUPABASE_URL'], app.config['SUPABASE_KEY'])

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))


# --- ROTAS ---

@app.route('/')
@login_required
def meus_romaneios():
    romaneios = Romaneio.query.filter_by(usuario_id=current_user.id).all()
    return render_template('meus_romaneios.html', romaneios=romaneios)


@app.route('/nota/<int:nota_id>/baixa', methods=['GET', 'POST'])
@login_required
def baixar_nota(nota_id):
    nota = NotaFiscal.query.get_or_404(nota_id)

    if request.method == 'POST':
        status_entrega = request.form.get('status_entrega')
        motivo_recusa = request.form.get('motivo_recusa')
        foto = request.files.get('foto')

        if not foto or foto.filename == '':
            flash('A foto do canhoto é obrigatoria para prosseguir.', 'danger')
            return redirect(request.url)

        if status_entrega == 'PARCIALMENTE_ENTREGUE' and not motivo_recusa.strip():
            flash('Informe o motivo da recusa/ressalva.', 'danger')
            return redirect(request.url)

        # Upload de Imagem para o Supabase Storage
        file_bytes = foto.read()
        filename = f"canhoto_{nota.id}_{int(datetime.utcnow().timestamp())}.jpg"
        bucket_name = app.config['SUPABASE_BUCKET']

        # Envia arquivo para o bucket
        res = supabase.storage.from_(bucket_name).upload(
            path=filename,
            file=file_bytes,
            file_options={"content-type": foto.content_type}
        )

        # Gera a URL pública da imagem enviada
        url_imagem = supabase.storage.from_(bucket_name).get_public_url(filename)

        # Atualização do registro da Nota
        nota.status_entrega = status_entrega
        nota.motivo_recusa = motivo_recusa if status_entrega == 'PARCIALMENTE_ENTREGUE' else None
        nota.url_foto_canhoto = url_imagem
        nota.data_atualizacao = datetime.utcnow()

        db.session.commit()

        # Atualização do Status do Romaneio
        romaneio = nota.romaneio
        notas_pendentes = [n for n in romaneio.notas if n.status_entrega == 'PENDENTE']
        if not notas_pendentes:
            romaneio.status = 'CONCLUIDO'
            db.session.commit()

        flash('Baixa realizada com sucesso!', 'success')
        return redirect(url_for('meus_romaneios'))

    return render_template('baixar_nota.html', nota=nota)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        senha = request.form.get('senha')
        usuario = Usuario.query.filter_by(email=email).first()

        if usuario and usuario.senha == senha:
            login_user(usuario)
            return redirect(url_for('meus_romaneios'))

        flash('E-mail ou senha inválidos.', 'danger')

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)

import os
from flask import Flask, render_template, redirect, url_for, request, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from datetime import datetime
from supabase import create_client, Client

from models import db, Transportadora, Usuario, Romaneio, NotaFiscal
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)

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
    # FILTRO DE SEGURANÇA: Exibe apenas os romaneios da Transportadora do usuário logado
    romaneios = Romaneio.query.filter_by(
        TransportadoraID=current_user.TransportadoraID
    ).all()
    
    return render_template('meus_romaneios.html', romaneios=romaneios)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        telefone = request.form.get('telefone')
        senha = request.form.get('senha')
        
        usuario = Usuario.query.filter_by(Telefone=telefone).first()

        if usuario and usuario.Senha == senha:
            login_user(usuario)
            return redirect(url_for('meus_romaneios'))
        
        flash('Telefone ou senha inválidos.', 'danger')

    return render_template('login.html')


@app.route('/nota/<int:nota_id>/baixa', methods=['GET', 'POST'])
@login_required
def baixar_nota(nota_id):
    nota = NotaFiscal.query.get_or_404(nota_id)

    # Validação de isolamento: Impede baixar notas de outra transportadora
    if nota.romaneio.TransportadoraID != current_user.TransportadoraID:
        flash('Acesso não autorizado para esta nota.', 'danger')
        return redirect(url_for('meus_romaneios'))

    if request.method == 'POST':
        status_entrega = request.form.get('status_entrega')
        motivo_devolucao = request.form.get('motivo_devolucao')
        foto = request.files.get('foto')

        if not foto or foto.filename == '':
            flash('A foto do canhoto é obrigatória para prosseguir.', 'danger')
            return redirect(request.url)

        # Trata o campo de justificativa em caso de não entrega ou entrega parcial
        if status_entrega in ['NAO_ENTREGUE', 'PARCIALMENTE_ENTREGUE'] and not motivo_devolucao.strip():
            flash('Informe o motivo da não entrega / ressalva.', 'danger')
            return redirect(request.url)

        # Upload no Supabase Storage
        file_bytes = foto.read()
        filename = f"canhoto_{nota.idNF}_{int(datetime.utcnow().timestamp())}.jpg"
        bucket_name = app.config['SUPABASE_BUCKET']

        supabase.storage.from_(bucket_name).upload(
            path=filename,
            file=file_bytes,
            file_options={"content-type": foto.content_type}
        )

        url_imagem = supabase.storage.from_(bucket_name).get_public_url(filename)

        # Gravação no Banco
        nota.StatusEntrega = status_entrega
        nota.MotivoDevolucao = motivo_devolucao if status_entrega != 'TOTALMENTE_ENTREGUE' else None
        nota.UrlFotoCanhoto = url_imagem
        nota.DataAtualizacao = datetime.utcnow()

        db.session.commit()

        # Atualiza o Romaneio se todas as notas tiverem baixa registrada
        romaneio = nota.romaneio
        notas_pendentes = [n for n in romaneio.notas if n.StatusEntrega == 'PENDENTE']
        if not notas_pendentes:
            romaneio.Status = 'CONCLUIDO'
            db.session.commit()

        flash('Registro atualizado com sucesso!', 'success')
        return redirect(url_for('meus_romaneios'))

    return render_template('baixar_nota.html', nota=nota)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)

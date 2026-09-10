from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()


class Usuario(UserMixin, db.Model):
    __tablename__ = 'usuarios'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    senha = db.Column(db.String(255), nullable=False)
    perfil = db.Column(db.String(20), default='TERCEIRO')  # 'ADMIN' ou 'TERCEIRO'

    romaneios = db.relationship('Romaneio', backref='usuario', lazy=True)


class Romaneio(db.Model):
    __tablename__ = 'romaneios'

    id = db.Column(db.Integer, primary_key=True)
    codigo_romaneio = db.Column(db.String(50), unique=True, nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    status = db.Column(db.String(30), default='EM_TRANSITO')  # 'EM_TRANSITO', 'CONCLUIDO'
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)

    notas = db.relationship('NotaFiscal', backref='romaneio', lazy=True)


class NotaFiscal(db.Model):
    __tablename__ = 'notas_fiscais'

    id = db.Column(db.Integer, primary_key=True)
    numero_nota = db.Column(db.String(50), nullable=False)
    romaneio_id = db.Column(db.Integer, db.ForeignKey('romaneios.id'), nullable=False)
    status_entrega = db.Column(db.String(30), default='PENDENTE')  # 'PENDENTE', 'TOTALMENTE_ENTREGUE', 'PARCIALMENTE_ENTREGUE'
    motivo_recusa = db.Column(db.Text, nullable=True)
    url_foto_canhoto = db.Column(db.String(255), nullable=True)
    data_atualizacao = db.Column(db.DateTime, nullable=True)

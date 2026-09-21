from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class Transportadora(db.Model):
    __tablename__ = 'transportadora'

    idTransportadora = db.Column(db.Integer, primary_key=True)
    Nome = db.Column(db.String(95), nullable=False)
    CNPJ = db.Column(db.String(14), unique=True, nullable=False)

    usuarios = db.relationship('Usuario', backref='transportadora', lazy=True)
    romaneios = db.relationship('Romaneio', backref='transportadora', lazy=True)


class Usuario(UserMixin, db.Model):
    __tablename__ = 'usuarios'

    idUsuario = db.Column(db.Integer, primary_key=True)
    TransportadoraID = db.Column(db.Integer, db.ForeignKey('transportadora.idTransportadora'), nullable=True)
    Nome = db.Column(db.String(30), nullable=False)
    Telefone = db.Column(db.String(11), nullable=False)
    Senha = db.Column(db.String(255), nullable=False)

    # Função para adaptar com o Flask-Login
    def get_id(self):
        return str(self.idUsuario)


class Romaneio(db.Model):
    __tablename__ = 'romaneios'

    idRomaneio = db.Column(db.Integer, primary_key=True)
    TransportadoraID = db.Column(db.Integer, db.ForeignKey('transportadora.idTransportadora'), nullable=False)
    NumeroRomaneio = db.Column(db.String(50), nullable=False)
    Status = db.Column(db.String(45), default='EM_TRANSITO')
    DataCriacao = db.Column(db.DateTime, default=datetime.utcnow)

    notas = db.relationship('NotaFiscal', backref='romaneio', lazy=True)


class NotaFiscal(db.Model):
    __tablename__ = 'notasfiscais'

    idNF = db.Column(db.Integer, primary_key=True)
    idRomaneio = db.Column(db.Integer, db.ForeignKey('romaneios.idRomaneio'), nullable=False)
    NumeroNF = db.Column(db.String(50), nullable=False)
    ValorNF = db.Column(db.Numeric(10, 2))
    Cliente = db.Column(db.String(95))
    StatusEntrega = db.Column(db.String(30), default='PENDENTE')
    MotivoDevolucao = db.Column(db.Text)
    UrlFotoCanhoto = db.Column(db.String(255))
    DataAtualizacao = db.Column(db.DateTime)

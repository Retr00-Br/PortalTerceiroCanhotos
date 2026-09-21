from app import app
from models import db, Transportadora, Usuario, Romaneio, NotaFiscal

def criar_estrutura_inicial():
    with app.app_context():
        # Garantir que as tabelas existem no PostgreSQL/Supabase
        db.create_all()

        # 1. Cadastrar Transportadora Transmat (evita duplicar por CNPJ)
        transmat = Transportadora.query.filter_by(CNPJ="12345678000199").first()
        if not transmat:
            transmat = Transportadora(
                Nome="Transmat Transportes",
                CNPJ="12345678000199"
            )
            db.session.add(transmat)
            db.session.commit()
            print("Transportadora Transmat cadastrada com sucesso!")

        # 2. Cadastrar Usuário vinculado à Transmat
        usuario_transmat = Usuario.query.filter_by(Telefone="11999998888").first()
        if not usuario_transmat:
            usuario_transmat = Usuario(
                TransportadoraID=transmat.idTransportadora,
                Nome="Motorista Transmat",
                Telefone="11999998888",
                Senha="123456"  # Em produção, utilize hash com werkzeug.security
            )
            db.session.add(usuario_transmat)
            db.session.commit()
            print("Usuário da Transmat criado com sucesso!")

        # 3. Criar Romaneio e Nota Fiscal de Teste para a Transmat
        romaneio = Romaneio.query.filter_by(NumeroRomaneio="ROM-TRANSMAT-01").first()
        if not romaneio:
            romaneio = Romaneio(
                TransportadoraID=transmat.idTransportadora,
                NumeroRomaneio="ROM-TRANSMAT-01",
                Status="EM_TRANSITO"
            )
            db.session.add(romaneio)
            db.session.commit()

            nf = NotaFiscal(
                idRomaneio=romaneio.idRomaneio,
                NumeroNF="NF-5001",
                ValorNF=1250.50,
                Cliente="Cliente Exemplo LTDA",
                StatusEntrega="PENDENTE"
            )
            db.session.add(nf)
            db.session.commit()
            print("Romaneio e Nota Fiscal de teste atribuídos à Transmat!")

if __name__ == '__main__':
    criar_estrutura_inicial()

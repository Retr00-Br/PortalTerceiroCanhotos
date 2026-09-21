import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="Painel Admin - Gestão de Romaneios", layout="wide")

# Conexão com o Supabase via SQLAlchemy
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:SUA_SENHA@db.SEU_PROJETO.supabase.co:5432/postgres")
engine = create_engine(DATABASE_URL)

st.title("📦 Painel de Carga e Gestão de Romaneios")

tabs = st.tabs(["📤 Importar Planilha", "📊 Visualizar Dados", "🚛 Cadastrar Transportadora"])

# --- ABA 1: IMPORTAR PLANILHA EXCEL ---
with tabs[0]:
    st.header("Importação de Relatório de Averbação")
    uploaded_file = st.file_uploader("Selecione a planilha (.xlsx)", type=["xlsx"])

    if uploaded_file:
        xls = pd.ExcelFile(uploaded_file)
        st.success(f"Arquivo carregado com sucesso! Abas encontradas: {len(xls.sheet_names)}")

        if st.button("Processar e Enviar para o Supabase"):
            progress_bar = st.progress(0)
            status_text = st.empty()

            with engine.connect() as conn:
                total_sheets = len(xls.sheet_names)

                for i, sheet_name in enumerate(xls.sheet_names):
                    status_text.text(f"Processando aba: {sheet_name}...")
                    df = pd.read_excel(uploaded_file, sheet_name=sheet_name)

                    romaneio_atual = None

                    for idx, row in df.iterrows():
                        # Pula linhas de cabeçalho repetidas
                        if str(row['Nr. Romaneio']).strip() == 'Nr. Romaneio':
                            continue

                        # Detecta linha de Romaneio
                        if pd.notna(row['Nr. Romaneio']):
                            num_romaneio = str(row['Nr. Romaneio']).split('-')[0].strip()
                            desc_veiculo = str(row['Desc.Veiculo']).strip() if pd.notna(row['Desc.Veiculo']) else ''

                            # Define a transportadora
                            nome_transp = "MATRIZ / PRÓPRIO"
                            if "TERCEIRO -" in desc_veiculo:
                                nome_transp = desc_veiculo.replace("TERCEIRO -", "").strip()

                            # Insere ou busca Transportadora
                            query_transp = text("""
                                INSERT INTO Transportadora (Nome, CNPJ) 
                                VALUES (:nome, '00000000000000') 
                                ON CONFLICT (CNPJ) DO NOTHING;
                                SELECT idTransportadora FROM Transportadora WHERE Nome = :nome LIMIT 1;
                            """)
                            res_transp = conn.execute(query_transp, {"nome": nome_transp}).fetchone()
                            id_transp = res_transp[0] if res_transp else 1

                            # Insere ou busca Romaneio
                            query_rom = text("""
                                INSERT INTO Romaneios (TransportadoraID, NumeroRomaneio, Status)
                                VALUES (:id_transp, :num_rom, 'EM_TRANSITO')
                                ON CONFLICT DO NOTHING;
                                SELECT idRomaneio FROM Romaneios WHERE NumeroRomaneio = :num_rom LIMIT 1;
                            """)
                            res_rom = conn.execute(query_rom,
                                                   {"id_transp": id_transp, "num_rom": num_romaneio}).fetchone()
                            romaneio_atual = res_rom[0] if res_rom else None

                        # Detecta linha de Nota Fiscal
                        elif romaneio_atual and pd.notna(row['Unnamed: 10']):
                            num_nf = str(row['Unnamed: 10']).strip()
                            valor_nf = float(row['Unnamed: 11']) if pd.notna(row['Unnamed: 11']) else 0.0
                            cliente = str(row['Unnamed: 8']).strip() if pd.notna(row['Unnamed: 8']) else ''

                            query_nf = text("""
                                INSERT INTO NotasFiscais (idRomaneio, NumeroNF, ValorNF, Cliente, StatusEntrega)
                                VALUES (:id_rom, :num_nf, :valor, :cliente, 'PENDENTE')
                                ON CONFLICT DO NOTHING;
                            """)
                            conn.execute(query_nf, {
                                "id_rom": romaneio_atual,
                                "num_nf": num_nf,
                                "valor": valor_nf,
                                "cliente": cliente
                            })

                    conn.commit()
                    progress_bar.progress((i + 1) / total_sheets)

            st.success("Importação concluída com sucesso no banco de dados!")

# --- ABA 2: VISUALIZAR DADOS ---
with tabs[1]:
    st.header("Consulta de Romaneios e Notas")
    with engine.connect() as conn:
        df_romaneios = pd.read_sql("""
            SELECT r.idRomaneio, r.NumeroRomaneio, t.Nome as Transportadora, r.Status, r.DataCriacao
            FROM Romaneios r
            JOIN Transportadora t ON r.TransportadoraID = t.idTransportadora
            ORDER BY r.idRomaneio DESC;
        """, conn)
        st.dataframe(df_romaneios, use_container_width=True)

# --- ABA 3: CADASTRAR TRANSPORTADORA ---
with tabs[2]:
    st.header("Nova Transportadora")
    with st.form("form_transp"):
        nome = st.text_input("Nome da Transportadora")
        cnpj = st.text_input("CNPJ")
        submit = st.form_submit_button("Salvar")

        if submit and nome and cnpj:
            with engine.connect() as conn:
                conn.execute(text("INSERT INTO Transportadora (Nome, CNPJ) VALUES (:n, :c)"), {"n": nome, "c": cnpj})
                conn.commit()
            st.success(f"Transportadora {nome} cadastrada!")

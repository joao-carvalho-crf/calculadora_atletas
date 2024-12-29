import streamlit as st
import requests
#import locale

st.set_page_config(
    page_title="Calculadora de Compra e Venda de Atletas",
    page_icon=":soccer:",
    layout="wide",
)

'''# Set the locale for number formatting
import subprocess

# Install the pt_BR locale
subprocess.run(["sudo", "locale-gen", "pt_BR.UTF-8"])
try:
    locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
except locale.Error:
    st.warning("A localização 'pt_BR.UTF-8' não está disponível no sistema. A formatação de números pode não estar correta.")
'''
    
st.title("Calculadora de Compra e Venda de Atletas")

# --- Sidebar for Exchange Rate Selection ---
with st.sidebar:
    st.header("Configurações de Cotação")
    cotacao_opcao = st.selectbox(
        "Selecione a cotação Euro / Real:",
        ["Câmbio atual", "Valor fixo"],
    )
    valor_cotacao_fixa = None
    if cotacao_opcao == "Valor fixo":
        valor_cotacao_fixa = st.number_input("Valor da cotação fixa:", min_value=0.0001, step=0.01)

@st.cache_resource
def obter_cotacao_euro():
    """Obtém a cotação atual do Euro usando a Awesome API."""
    try:
        response = requests.get("https://economia.awesomeapi.com.br/last/EUR-BRL")
        response.raise_for_status()  # Lança uma exceção para status de erro
        data = response.json()
        return float(data['EURBRL']['bid'])
    except requests.exceptions.RequestException as e:
        st.error(f"Erro ao obter a cotação atual do Euro: {e}")
        return None
    except (KeyError, ValueError):
        st.error("Erro ao processar a resposta da API de cotação.")
        return None

def formatar_numero_br(number):
    return "{:,.0f}".format(number).replace(",", ".")

def calcular_valor_liquido(valor_euros_milhoes, perc_repasse, perc_intermediacao, venda_exterior, cotacao):
    valor_euros = valor_euros_milhoes * 1_000_000
    perc_iof = 0.0038 if venda_exterior else 0.0
    valor_liquido = valor_euros * cotacao * (1 - perc_intermediacao/100 - perc_repasse/100 - perc_iof)
    return valor_liquido

def calcular_custo_total(valor_euros_milhoes, perc_intermediacao, compra_exterior, cotacao):
    valor_euros = valor_euros_milhoes * 1_000_000
    perc_iof = 0.0038 if compra_exterior else 0.0
    perc_ir = (1/0.85) * 0.15 if compra_exterior else 0.0
    custo_total = valor_euros * cotacao * (1 + perc_intermediacao/100 + perc_iof + perc_ir)
    return custo_total

# --- Fetch Exchange Rate (only once per run) ---
cotacao_usada = None
if cotacao_opcao == "Câmbio atual":
    cotacao_usada = obter_cotacao_euro()
elif cotacao_opcao == "Valor fixo":
    cotacao_usada = valor_cotacao_fixa

# --- Main Columns for Venda and Compra ---
col_venda, col_compra = st.columns(2)

# --- Seção de Venda ---
with col_venda:
    st.header("Venda")
    valor_euros_venda_milhoes = st.number_input("Valor em milhões de euros (ticket de referência):", min_value=0.0, step=0.1, key="venda_valor_euros")
    perc_repasse_venda = st.number_input("% do repasse para o atleta ou outros clubes:", min_value=0.0, max_value=50.0, step=0.1, key="venda_repasse")
    perc_intermediacao_venda = st.number_input("% de intermediação:", min_value=0.0, max_value=20.0, step=0.1, key="venda_inter")
    venda_exterior = st.checkbox("Venda para o exterior?", key="venda_exterior")

    valor_liquido = None
    if valor_euros_venda_milhoes is not None and perc_repasse_venda is not None and perc_intermediacao_venda is not None and cotacao_usada is not None:
        valor_liquido = calcular_valor_liquido(valor_euros_venda_milhoes, perc_repasse_venda, perc_intermediacao_venda, venda_exterior, cotacao_usada)
        st.success(f"Valor Líquido da Venda: R$ {formatar_numero_br(int(valor_liquido))}")
        if cotacao_opcao == "Câmbio atual" and cotacao_usada:
            st.caption(f"Câmbio utilizado: R$ {cotacao_usada:.4f} por Euro")

# --- Seção de Compra ---
with col_compra:
    st.header("Compra")
    valor_euros_compra_milhoes = st.number_input("Valor em milhões de euros (ticket de referência):", min_value=0.0, step=0.1, key="compra_valor_euros")
    perc_intermediacao_compra = st.number_input("% de intermediação:", min_value=0.0, max_value=20.0, step=0.1, key="compra_inter")
    compra_exterior = st.checkbox("Compra do exterior?", key="compra_exterior")

    custo_total = None
    if valor_euros_compra_milhoes is not None and perc_intermediacao_compra is not None and cotacao_usada is not None:
        custo_total = calcular_custo_total(valor_euros_compra_milhoes, perc_intermediacao_compra, compra_exterior, cotacao_usada)
        st.success(f"Custo Total da Compra: R$ {formatar_numero_br(int(custo_total))}")
        if cotacao_opcao == "Câmbio atual" and cotacao_usada:
            st.caption(f"Câmbio utilizado: R$ {cotacao_usada:.4f} por Euro")

# --- Saldo Líquido ---
st.header("Saldo Líquido")

saldo_liquido = 0
if valor_liquido is not None:
    saldo_liquido += valor_liquido
if custo_total is not None:
    saldo_liquido -= custo_total

st.metric("Saldo Líquido (Venda - Compra)", f"R$ {formatar_numero_br(int(saldo_liquido))}")
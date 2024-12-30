import streamlit as st
import requests

# The error happens because this should be the first streamlit command
st.set_page_config(
    page_title="Calculadora de Compra e Venda de Atletas",
    page_icon=":soccer:",
    layout="wide",
)

st.title("Calculadora de Compra e Venda de Atletas")

# --- Sidebar for Exchange Rate Selection and Display ---
with st.sidebar:
    st.header("Configurações de Cotação")
    cotacao_opcao = st.selectbox(
        "Selecione a cotação Euro / Real:",
        ["Câmbio atual", "Valor fixo"],
    )

    # Fetch and display current exchange rate if "Câmbio atual" is selected
    if cotacao_opcao == "Câmbio atual":
        if 'cotacao_atual' not in st.session_state:
            with st.spinner('Obtendo cotação atual...'):
                try:
                    response = requests.get("https://economia.awesomeapi.com.br/last/EUR-BRL")
                    response.raise_for_status()
                    data = response.json()
                    st.session_state.cotacao_atual = float(data['EURBRL']['bid'])
                except requests.exceptions.RequestException as e:
                    st.error(f"Erro ao obter a cotação atual do Euro: {e}")
                    st.session_state.cotacao_atual = None  # Set to None on error
                except (KeyError, ValueError):
                    st.error("Erro ao processar a resposta da API de cotação.")
                    st.session_state.cotacao_atual = None  # Set to None on error

        if st.session_state.cotacao_atual:
            st.metric(label="Câmbio Atual (EUR/BRL)", value=f"R$ {st.session_state.cotacao_atual:.4f}")

        if st.button("Atualizar Cotação"):
            with st.spinner('Atualizando cotação...'):
                try:
                    response = requests.get("https://economia.awesomeapi.com.br/last/EUR-BRL")
                    response.raise_for_status()
                    data = response.json()
                    st.session_state.cotacao_atual = float(data['EURBRL']['bid'])
                    st.rerun()
                except requests.exceptions.RequestException as e:
                    st.error(f"Erro ao atualizar a cotação do Euro: {e}")
                except (KeyError, ValueError):
                    st.error("Erro ao processar a resposta da API de cotação.")

    valor_cotacao_fixa = None
    if cotacao_opcao == "Valor fixo":
        valor_cotacao_fixa = st.number_input("Valor da cotação fixa:", min_value=0.0001, step=0.0001)

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

# --- Use cached exchange rate if available, otherwise use fixed or None ---
cotacao_usada = None
if cotacao_opcao == "Câmbio atual":
    cotacao_usada = st.session_state.cotacao_atual if 'cotacao_atual' in st.session_state and st.session_state.cotacao_atual is not None else None
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
    elif cotacao_opcao == "Câmbio atual" and cotacao_usada is None:
        st.error("Não foi possível obter a cotação atual. Por favor, verifique sua conexão com a internet ou atualize a cotação.")

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
    elif cotacao_opcao == "Câmbio atual" and cotacao_usada is None:
        st.error("Não foi possível obter a cotação atual. Por favor, verifique sua conexão com a internet ou atualize a cotação.")

# --- Saldo Líquido ---
st.header("Saldo Líquido")

saldo_liquido = 0
if valor_liquido is not None:
    saldo_liquido += valor_liquido
if custo_total is not None:
    saldo_liquido -= custo_total

st.metric("Saldo Líquido (Venda - Compra)", f"R$ {formatar_numero_br(int(saldo_liquido))}")

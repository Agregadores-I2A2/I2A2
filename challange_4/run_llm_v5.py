from huggingface_hub import InferenceClient
import os
import pandas as pd
from io import StringIO

def load_and_clean_data(data_path):
    files_to_load = {
        "admissoes": "ADMISSÃO ABRIL.xlsx",
        "afastamentos": "AFASTAMENTOS.xlsx",
        "aprendizes": "APRENDIZ.xlsx",
        "ativos": "ATIVOS.xlsx",
        "dias_uteis": "Base dias uteis.xlsx",
        "sindicato_valor": "Base sindicato x valor.xlsx",
        "desligados": "DESLIGADOS.xlsx",
        "estagiarios": "ESTÁGIO.xlsx",
        "exterior": "EXTERIOR.xlsx",
        "ferias": "FÉRIAS.xlsx",
    }
    dfs = {}
    for key, filename in files_to_load.items():
        try:
            dfs[key] = pd.read_excel(f"{data_path}/{filename}")
            dfs[key].columns = [str(col).strip() for col in dfs[key].columns]
            if 'MATRICULA' not in dfs[key].columns and 'Cadastro' in dfs[key].columns:
                dfs[key].rename(columns={'Cadastro': 'MATRICULA'}, inplace=True)
        except Exception as e:
            raise Exception(f"Error loading {key}: {e}")
    
    dfs['dias_uteis'].columns = ['SINDICADO', 'DIAS_UTEIS']
    dfs['dias_uteis'] = dfs['dias_uteis'].iloc[1:].reset_index(drop=True)
    dfs['sindicato_valor'].columns = ['ESTADO', 'VALOR']
    dfs['sindicato_valor'].dropna(subset=['ESTADO'], inplace=True)
    return dfs

def filter_and_consolidate(dfs):
    consolidated_df = dfs['ativos'].copy()
    matriculas_to_exclude = pd.concat([
        dfs['aprendizes']['MATRICULA'],
        dfs['estagiarios']['MATRICULA'],
        dfs['afastamentos']['MATRICULA'],
        dfs['exterior']['MATRICULA']
    ]).unique()
    consolidated_df = consolidated_df[~consolidated_df['MATRICULA'].isin(matriculas_to_exclude)]

    def _map_sindicato_to_estado(sindicato_name):
        if "PR" in sindicato_name: return "Paraná"
        if "RS" in sindicato_name: return "Rio Grande do Sul"
        if "SP" in sindicato_name: return "São Paulo"
        if "RJ" in sindicato_name: return "Rio de Janeiro"
        return None
    consolidated_df['ESTADO'] = consolidated_df['Sindicato'].apply(_map_sindicato_to_estado)

    consolidated_df = pd.merge(consolidated_df, dfs['sindicato_valor'], on='ESTADO', how='left')
    consolidated_df = pd.merge(consolidated_df, dfs['dias_uteis'], left_on='Sindicato', right_on='SINDICADO', how='left')
    consolidated_df = pd.merge(consolidated_df, dfs['ferias'][['MATRICULA', 'DIAS DE FÉRIAS']], on='MATRICULA', how='left')
    consolidated_df['DIAS DE FÉRIAS'].fillna(0, inplace=True)
    return consolidated_df

def parse_markdown_to_df(md_content):
    # A simple parser for markdown tables
    lines = md_content.strip().split('\n')
    # Find the line with the separator
    separator_index = -1
    for i, line in enumerate(lines):
        if '---' in line:
            separator_index = i
            break
    if separator_index == -1:
        return pd.DataFrame() # Return empty dataframe if no table found

    header = [h.strip() for h in lines[separator_index - 1].strip('|').split('|')]
    data = []
    for line in lines[separator_index + 1:]:
        row = [r.strip() for r in line.strip('|').split('|')]
        if len(row) == len(header):
            data.append(row)
    return pd.DataFrame(data, columns=header)

def run_llm_batch_processing():
    API_TOKEN = "{SUA_API_KEY_AQUI}"
    MODEL_ID = "mistralai/Mixtral-8x7B-Instruct-v0.1"
    client = InferenceClient(model=MODEL_ID, token=API_TOKEN)
    
    data_path = "/home/adriano/Documentos/Desafio 4/Desafio 4 - Dados"
    dfs = load_and_clean_data(data_path)
    consolidated_df = filter_and_consolidate(dfs)
    
    prompt_df = consolidated_df[['MATRICULA', 'DIAS_UTEIS', 'DIAS DE FÉRIAS', 'VALOR']].copy()
    prompt_df = pd.merge(prompt_df, dfs['admissoes'][['MATRICULA', 'Admissão']], on='MATRICULA', how='left')
    prompt_df = pd.merge(prompt_df, dfs['desligados'][['MATRICULA', 'DATA DEMISSÃO', 'COMUNICADO DE DESLIGAMENTO']], on='MATRICULA', how='left')

    batch_size = 100
    all_results = []

    print(f"Iniciando processamento em lotes de {batch_size} funcionários...")

    for i in range(0, len(prompt_df), batch_size):
        batch_df = prompt_df.iloc[i:i+batch_size]
        
        print(f"--- Processando lote {i//batch_size + 1} de {len(prompt_df)//batch_size + 1} ---")

        prompt = f"""Você é um especialista em RH. Sua tarefa é calcular os dias a pagar e o valor final do VR para a lista de funcionários abaixo.

**Dados para Cálculo:**
{batch_df.to_markdown(index=False)}

**Regras de Negócio:**
1. **Cálculo Base:** Comece com `DIAS_UTEIS` e subtraia `DIAS DE FÉRIAS`.
2. **Admissão:** Se houver uma data em `Admissão`, o pagamento deve ser proporcional aos dias trabalhados em Maio/2025.
3. **Desligamento:** Se `COMUNICADO DE DESLIGAMENTO` for 'OK' e a `DATA DEMISSÃO` for antes do dia 15, os dias a pagar são 0. Se for no dia 15 ou depois, o pagamento é proporcional.

**Sua Tarefa:**
Retorne APENAS uma tabela markdown com o resultado final para este lote, contendo as seguintes colunas:
- MATRICULA
- Dias a Pagar
- Valor Total (calculado como `Dias a Pagar` * `VALOR`)
- Custo Empresa (80% do `Valor Total`)
- Desconto Profissional (20% do `Valor Total`)
"""
        
        try:
            messages = [{"role": "user", "content": prompt}]
            response = client.chat_completion(messages, max_tokens=4096, stream=False)
            batch_result_md = response.choices[0].message.content
            batch_result_df = parse_markdown_to_df(batch_result_md)
            all_results.append(batch_result_df)
            print(f"Lote {i//batch_size + 1} processado com sucesso.")
        except Exception as e:
            print(f"Erro ao processar o lote {i//batch_size + 1}: {e}")

    if all_results:
        final_df = pd.concat(all_results, ignore_index=True)
        final_df['MATRICULA'] = pd.to_numeric(final_df['MATRICULA'])
        final_report_df = pd.merge(consolidated_df, final_df, on='MATRICULA')
        
        print("\n--- Relatório Final Combinado ---\n")
        print(final_report_df.head())
        
        final_report_df.to_excel("VR_FINAL_IA_v5.xlsx", index=False)
        print("\nRelatório final salvo em VR_FINAL_IA_v5.xlsx")
    else:
        print("Nenhum lote foi processado com sucesso. Nenhum relatório foi gerado.")

if __name__ == "__main__":
    run_llm_batch_processing()

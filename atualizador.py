import requests
from bs4 import BeautifulSoup
import json
import re
import os

def extrair_dados_congresso():
    url = "https://www.congressonacional.leg.br/materias/materias-aguardando-sancao"
    
    # Simula um navegador real para evitar bloqueios do servidor do governo
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        materias_extraidas = []
        
        # O site do congresso geralmente usa tabelas ou listas descritivas para as matérias.
        # Caso a estrutura mude, ajuste os seletores CSS abaixo.
        # Este é um seletor heurístico com base em portais legislativos padrão.
        
        linhas_tabela = soup.find_all('tr')
        
        for linha in linhas_tabela:
            colunas = linha.find_all('td')
            if len(colunas) >= 4:
                # Extração básica (Sujeita a ajustes finos dependendo da DOM exata do Senado)
                materia_texto = colunas[0].get_text(strip=True)
                ementa_texto = colunas[1].get_text(strip=True)
                recebimento_texto = colunas[2].get_text(strip=True) # Formato esperado: dd/mm/aaaa
                prazo_texto = colunas[3].get_text(strip=True)       # Formato esperado: dd/mm/aaaa
                
                # Conversão de dd/mm/aaaa para aaaa-mm-dd (Formato que o nosso JS lê)
                try:
                    d, m, y = recebimento_texto.split('/')
                    receb_iso = f"{y}-{m}-{d}"
                    
                    d_p, m_p, y_p = prazo_texto.split('/')
                    prazo_iso = f"{y_p}-{m_p}-{d_p}"
                except:
                    continue # Pula a linha se não for uma data válida
                
                materias_extraidas.append({
                    "materia": materia_texto,
                    "ementa": ementa_texto,
                    "recebimento": receb_iso,
                    "prazo": prazo_iso,
                    "autoria": "Autoria Padrão", # Extraia das colunas se existir, caso contrário deixe fixo ou raspe da página interna
                    "assunto": "Tema Geral"      # Extraia se houver categoria
                })
        
        return materias_extraidas

    except Exception as e:
        print(f"Erro ao extrair dados do Congresso: {e}")
        return []

def atualizar_html(novos_dados):
    caminho_html = 'index.html'
    
    if not os.path.exists(caminho_html):
        print("Arquivo index.html não encontrado no repositório.")
        return

    with open(caminho_html, 'r', encoding='utf-8') as file:
        conteudo_html = file.read()

    # Transforma o dicionário Python em uma String JSON formatada que o Javascript entende
    dados_js_str = "const dados = " + json.dumps(novos_dados, indent=12, ensure_ascii=False) + ";"

    # Procura as tags âncoras dentro do HTML e substitui o bloco do meio
    padrao = r'(// --- DADOS DINAMICOS INICIO ---).*?(// --- DADOS DINAMICOS FIM ---)'
    conteudo_atualizado = re.sub(
        padrao, 
        rf'\1\n        {dados_js_str}\n        \2', 
        conteudo_html, 
        flags=re.DOTALL
    )

    with open(caminho_html, 'w', encoding='utf-8') as file:
        file.write(conteudo_atualizado)
    
    print("Dashboard atualizado com sucesso!")

if __name__ == "__main__":
    dados = extrair_dados_congresso()
    # Somente atualiza se a extração retornou algo para evitar apagar o site por erro de conexão
    if dados and len(dados) > 0:
        atualizar_html(dados)
    else:
        print("Nenhum dado extraído. O HTML não foi modificado.")

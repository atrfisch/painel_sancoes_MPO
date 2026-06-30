import requests
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime

def extrair_dados():
    url = "https://www.congressonacional.leg.br/materias/materias-aguardando-sancao"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=20)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Converte todo o HTML da página em um texto corrido com espaços
        # Isso evita que a extração quebre se o Congresso não usar tabelas ou mudar as tags (<li>, <div>)
        texto_limpo = re.sub(r'\s+', ' ', soup.get_text())
        
        materias = []
        hoje = datetime.now()

        # Regex avançada: Procura e extrai os rótulos exatos em qualquer lugar do texto do site
        padrao = re.compile(
            r"Matéria:\s*(.*?)\s+Ementa:\s*(.*?)\s+Recebimento pela Presidência:\s*(\d{2}/\d{2}/\d{4})\s+Prazo para sanção:\s*(\d{2}/\d{2}/\d{4})",
            re.IGNORECASE
        )
        
        matches = padrao.finditer(texto_limpo)
        
        for match in matches:
            materia_raw = match.group(1).strip()
            ementa = match.group(2).strip()
            recebimento_str = match.group(3).strip()
            prazo_str = match.group(4).strip()
            
            # Limpa o texto da matéria. Ex: "PL 5868/2025 (PL 5868...)" vira "PL 5868/2025"
            materia = materia_raw.split('(')[0].strip()
            
            try:
                recebimento_dt = datetime.strptime(recebimento_str, '%d/%m/%Y')
                prazo_dt = datetime.strptime(prazo_str, '%d/%m/%Y')
                
                # Ignora matérias cujos prazos já encerraram ontem ou antes
                if prazo_dt >= hoje.replace(hour=0, minute=0, second=0, microsecond=0):
                    materias.append({
                        "materia": materia,
                        "ementa": ementa,
                        "recebimento": recebimento_dt.strftime('%Y-%m-%d'),
                        "prazo": prazo_dt.strftime('%Y-%m-%d')
                    })
            except Exception as e:
                print(f"Erro ao analisar data de {materia}: {e}")
                continue
                
        print(f"Extração concluída: {len(materias)} matérias encontradas e tratadas.")
        return materias
        
    except Exception as e:
        print(f"Erro crasso na extração: {e}")
        return []

def atualizar_html(dados):
    if not dados:
        print("Aviso: A extração retornou zero dados. O index.html não será modificado.")
        return

    try:
        with open('index.html', 'r', encoding='utf-8') as f:
            html = f.read()
        
        # Converte a lista em JSON puro
        dados_json = json.dumps(dados, indent=4, ensure_ascii=False)
        
        # Procura exatamente pelas flags HTML e substitui com perfeição todo o bloco
        padrao = r'(<!-- ROBOT_DATA_START -->).*?(<!-- ROBOT_DATA_END -->)'
        novo_html = re.sub(
            padrao, 
            rf'\1\n        <script>\n        const dados = {dados_json};\n        </script>\n        \2', 
            html, 
            flags=re.DOTALL
        )
        
        with open('index.html', 'w', encoding='utf-8') as f:
            f.write(novo_html)
            
        print("Sucesso! index.html foi alimentado com a nova base.")
        
    except FileNotFoundError:
        print("Erro: Não encontrei o index.html na raiz do seu projeto.")
    except Exception as e:
        print(f"Erro ao gravar o arquivo: {e}")

if __name__ == "__main__":
    lista_materias = extrair_dados()
    atualizar_html(lista_materias)

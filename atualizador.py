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
        
        # Pega todo o texto da página garantindo que haverá espaço entre elementos HTML diferentes
        texto = soup.get_text(separator=' ', strip=True)
        # Substitui múltiplos espaços ou quebras de linha por um único espaço
        texto_limpo = re.sub(r'\s+', ' ', texto)
        
        materias = []
        hoje = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

        if 'Matéria:' not in texto_limpo:
            print("Aviso: A estrutura do site não contém a palavra 'Matéria:'.")
            return []
            
        # O split cria uma lista onde cada item começa após a palavra 'Matéria:'
        blocos = texto_limpo.split('Matéria:')[1:] 
        
        for bloco in blocos:
            try:
                # Se faltar algum dos campos obrigatórios, ignora o bloco
                if 'Ementa:' not in bloco or 'Recebimento pela Presidência:' not in bloco or 'Prazo para sanção:' not in bloco:
                    continue
                    
                # Extração cirúrgica cortando as partes exatas do texto
                parte1, resto = bloco.split('Ementa:', 1)
                materia_raw = parte1.strip()
                
                parte2, resto = resto.split('Recebimento pela Presidência:', 1)
                ementa = parte2.strip()
                
                parte3, resto = resto.split('Prazo para sanção:', 1)
                recebimento_str = parte3.strip()
                
                # A data final de sanção é a primeira coisa logo após a âncora
                prazo_str = resto.strip().split()[0]
                
                # Limpa a Matéria (ex: "PL 5868/2025 (PL 5868..." -> "PL 5868/2025")
                materia = materia_raw.split('(')[0].strip()
                if not materia: 
                    materia = materia_raw
                    
                recebimento_dt = datetime.strptime(recebimento_str, '%d/%m/%Y')
                prazo_dt = datetime.strptime(prazo_str, '%d/%m/%Y')
                
                # Regra: Só guarda matérias que ainda não venceram
                if prazo_dt >= hoje:
                    materias.append({
                        "materia": materia,
                        "ementa": ementa,
                        "recebimento": recebimento_dt.strftime('%Y-%m-%d'),
                        "prazo": prazo_dt.strftime('%Y-%m-%d')
                    })
            except Exception as e:
                print(f"Aviso: Erro ao analisar uma matéria específica: {e}")
                continue
                
        print(f"Extração concluída: {len(materias)} matérias válidas e dentro do prazo capturadas com sucesso.")
        return materias
        
    except Exception as e:
        print(f"Erro crítico ao tentar extrair dados do site: {e}")
        return []

def atualizar_html(dados):
    if not dados:
        print("Aviso: Nenhuma matéria foi extraída. O index.html não será alterado para evitar apagar a lista atual.")
        return

    try:
        with open('index.html', 'r', encoding='utf-8') as f:
            html = f.read()
        
        # Converte a lista do Python para formato Javascript puro
        dados_json = json.dumps(dados, indent=4, ensure_ascii=False)
        novo_conteudo = f'<!-- ROBOT_DATA_START -->\n        <script>\n        const dados = {dados_json};\n        </script>\n        <!-- ROBOT_DATA_END -->'
        
        padrao = r'<!-- ROBOT_DATA_START -->.*?<!-- ROBOT_DATA_END -->'
        novo_html = re.sub(padrao, novo_conteudo, html, flags=re.DOTALL)
        
        with open('index.html', 'w', encoding='utf-8') as f:
            f.write(novo_html)
            
        print("Sucesso! Os novos projetos de lei foram injetados no arquivo index.html.")
        
    except Exception as e:
        print(f"Erro ao salvar os dados no HTML: {e}")

if __name__ == "__main__":
    lista_materias = extrair_dados()
    atualizar_html(lista_materias)

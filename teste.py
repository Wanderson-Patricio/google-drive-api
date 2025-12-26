import requests

# Configurações
url = "http://localhost:8000/sua-rota/ID_DA_PASTA_DO_DRIVE"
caminho_arquivo = "documento.pdf"

# Abrindo o arquivo em modo binário
with open(caminho_arquivo, "rb") as f:
    # O dicionário 'files' mapeia o nome do parâmetro no FastAPI 
    # (neste caso, 'file') para o conteúdo
    files = {
        "file": (caminho_arquivo, f, "application/pdf")
    }
    
    # Se o seu verify_credentials exigir um token, adicione aqui:
    headers = {
        "Authorization": "Bearer SEU_TOKEN_AQUI"
    }

    try:
        response = requests.post(url, files=files, headers=headers)
        response.raise_for_status() # Levanta erro se o status for 4xx ou 5xx
        
        print("Upload realizado com sucesso!")
        print(response.json())
    except requests.exceptions.HTTPError as err:
        print(f"Erro no upload: {err}")
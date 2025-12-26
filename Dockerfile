# Usa uma imagem oficial do Python leve como base
FROM python:3.11-slim

# Define variáveis de ambiente para evitar arquivos .pyc e garantir logs em tempo real
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Define o diretório de trabalho dentro do container
WORKDIR /app

# Instala as dependências do sistema necessárias (opcional, dependendo do seu app)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copia apenas o arquivo de dependências primeiro para aproveitar o cache do Docker
COPY requirements.txt .

# Instala as dependências do Python
RUN pip install --no-cache-dir -r requirements.txt

# Copia o restante do código da aplicação
COPY . .

# Expõe a porta que o FastAPI usará
EXPOSE 3000

# Comando para iniciar a aplicação usando Uvicorn
# --host 0.0.0.0 é obrigatório para ser acessível fora do container
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "3000"]
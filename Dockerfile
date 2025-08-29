# Use uma imagem base Python oficial
FROM python:3.9-slim-buster

# Defina o diretório de trabalho dentro do contêiner
WORKDIR /app

# Copie o arquivo de dependências e instale-as
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copie o restante do código da aplicação
COPY . .

# Exponha a porta que a aplicação vai escutar
EXPOSE 5000

# Comando para iniciar a aplicação usando Gunicorn
# 'app:app' significa que a aplicação Flask está na variável 'app' dentro do arquivo 'app.py'
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
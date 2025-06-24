FROM python:3.9-alpine

# Instala dependências do sistema necessárias (como pip )
RUN apk add --no-cache py3-pip

# Define o diretório de trabalho dentro do contêiner
WORKDIR /app

# Copia o arquivo de requisitos e instala as dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o script principal
COPY sms_gamer_ups_monitor.py .

# Copia o script de execução do add-on e o torna executável
COPY run.sh .
RUN chmod +x run.sh

# Define o comando padrão para executar o script run.sh
CMD ["./run.sh"]

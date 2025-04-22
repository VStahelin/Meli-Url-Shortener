# 📌 Objetivo Geral

Cria um serviço encurtador de URL atendendo os seguintes requisitos:

- Dada uma URL longa, retorne uma URL curta.  
- Dada uma URL curta, retorne a URL longa original.  
- Permita obter estatísticas sobre as URLs encurtadas.  
- Consiga lidar com solicitações em grande escala.  
- Dar conta de 50k requisições por segundo (quando em larga escala).  
- 90% das requisições sejam atendidas em menos de 10ms.  
- Criação da URL não pode demorar mais que 1000ms.  
- Permita a deleção das URLs curtas quando necessário.  
- Garanta que, ao acessar uma URL curta válida no navegador, o usuário seja redirecionado para a URL longa.  

---

# 🧠 Topologia da Solução

## Diagrama Geral

Para suportar 50k RPS com baixa latência (<10ms em 90% dos casos), a arquitetura segue os seguintes princípios:

- Um balanceador de carga distribui as requisições entre múltiplos pods do serviço FastAPI.  
- Cada pod pode escalar horizontalmente com base no uso de CPU ou número de requisições por segundo (HPA).  
- A resolução da URL curta ocorre majoritariamente via Redis (cache).  
- Em caso de cache miss, a aplicação consulta o banco de dados PostgreSQL.  
- As respostas são redirecionadas imediatamente após a resolução.  
- Métricas e rastreamentos são enviados para Prometheus e OpenTelemetry Collector.  
- Visualização via Grafana.  

## Componentes Principais

![image](https://github.com/user-attachments/assets/eb6eb5ce-0f2c-408a-9d89-2f6ea4c3184b)

- **Load Balancer**: distribui as requisições de forma balanceada  
- **App Pods (FastAPI)**: processam requisições, escalam via Kubernetes  
- **Redis**: cache quente, capaz de lidar com +100k RPS  
- **PostgreSQL**: persistência principal, uso secundário no redirecionamento  
- **Observabilidade**: Prometheus + OpenTelemetry  
- **Escalabilidade**:
  - Horizontal: mais pods
  - Vertical: múltiplos workers por pod (Uvicorn)

---

# 🧾 Notas Pessoais

- Precisa ser um script de baixa latência e de alta escalabilidade, ou seja, preciso pensar nos seguintes pontos:
- Escalabilidade horizontal para N pods:
  - Kubernetes gerencia facilmente.
  - Exemplo: 70% de uso por mais de X minutos cria um novo pod.
- Escalabilidade vertical caso um pod tenha múltiplos núcleos:
  - Um webserver Gunicorn consegue gerenciar isso facilmente distribuindo workers.
  - Regra base: (2 x núcleos) + 1 workers.
- Race/concurrency na geração da URL:
  - Deve ser controlado por locks, mas não há risco, temos até 1000ms de resposta.
- O número de núcleos e sua eficiência impactam diretamente no dimensionamento e métricas.
  - CPUs mais fracas escalam mais rapidamente horizontalmente.
- A linguagem escolhida é decisiva:
  - Python é mais pesado. Para produção massiva, C ou Go seriam mais indicadas.
- Redis suporta até 100k RPS com apenas uma instância em hardware modesto.

---

# 🚀 Análise de Performance

As análises de performance, incluindo todos os dados coletados e os cenários testados (como diferentes taxas de requisição e configurações de workers), estão documentadas de forma detalhada no link abaixo:

📄 [Google Docs - Análise de Performance](https://docs.google.com/document/d/1eVI0TtzehebV0zNoT8cG2zof1yLMxJCNnUBRXXCVEeg/edit?usp=sharing)

Esse material inclui a metodologia utilizada, gráficos e interpretação dos resultados obtidos.

---

# 🧪 Como Rodar o Projeto

Este projeto já está configurado para execução com Docker. O `.env` está pronto — **nenhuma alteração necessária**.

## Pré-requisitos

- [Docker](https://www.docker.com/)  
- [Docker Compose](https://docs.docker.com/compose/install/)

## Passo a Passo

```bash
git clone https://github.com/VStahelin/Meli-Url-Shortener
cd seu-repositorio
docker compose up --build
```

- Sobe FastAPI, Redis, PostgreSQL e Prometheus.
- Exposto em `http://localhost:8000`

### Métricas Prometheus

Acesse via:
```
http://localhost:8000/metrics
```

---

# 🌐 Rotas da API

### Criar URL encurtada

![image](https://github.com/user-attachments/assets/e78bc759-eaf4-4608-ae7a-faccb79f4b1a)

- **POST /**  
  Corpo:
  ```json
  {
    "url": "https://exemplo.com"
  }
  ```
  Resposta:
  ```json
  {
    "success": true,
    "data": {
      "url": "http://localhost:8000/XXYYZZ"
    }
  }
  ```
  
  Exemplo via `curl`:
  ```bash
  curl -X POST http://localhost:8000/ \
    -H 'Content-Type: application/json' \
    -d '{"url": "https://exemplo.com"}'
  ```

---

### Redirecionar URL

![image](https://github.com/user-attachments/assets/ea49442b-70dc-496b-bda9-025d04ade0fd)

- **GET /{url_id}**  
  Exemplo: `/XXYYZZ`  
  Redireciona para a URL original.

---

### Deletar URL encurtada

![image](https://github.com/user-attachments/assets/a3b23568-751a-4c83-b775-d3561057a330)

- **DELETE /{url_id}**  
  Exemplo: `/XXYYZZ`  
  Resposta:
  ```json
  {
    "success": true,
    "data": {
      "message": "URL deleted successfully"
    }
  }
  ```
  Exemplo via `curl`:
  ```bash
  curl -X DELETE http://localhost:8000/XXYYZZ
  ```

---

### Estatísticas de uso

- **GET /statics/**  
  Resposta:
  ```json
  {
    "success": true,
    "data": [
      {
        "route": "GET /{url_id}",
        "avg_response_time_ms": 1.63,
        "requests_per_second": 0.24,
        "total_requests_last_minute": 14,
        "total_requests": 578,
        "total_response_time_ms": 1013.21
      }
    ]
  }
  ```
  Exemplo via `curl`:
  ```bash
  curl -X GET http://localhost:8000/statics/
  ```

---

# ⚙️ Testes de Performance com Locust

> 💡 **Importante**: É altamente recomendável rodar o Locust **fora do Docker** para evitar que o consumo do container afete os resultados.  
> Para isso, crie um ambiente virtual Python localmente e instale os requisitos com:
>
> ```bash
> python -m venv venv
> source venv/bin/activate
> pip install -r requirements.txt
> ```

Já existe um `locustfile.py` configurado para testar o endpoint `GET /{url_id}`. Basta garantir que URLs válidas estejam criadas na base.

### Comando (modo headless)

```bash
locust -f tests/locustfile.py --headless -u 1000 -r 100 --host http://localhost:8000 --run-time 1m --csv locust_rps1000
```

Parâmetros:
- `-u 1000`: usuários simultâneos
- `-r 100`: novos usuários por segundo
- `--csv`: salva os resultados em arquivos `.csv` para análise posterior

### Output esperado

- `locust_rps1000_stats.csv` e `locust_rps1000_failures.csv`
- Principais análises:
  - Tempo médio de resposta
  - Percentual de requisições abaixo de 10ms


### 🧪 Testando com múltiplos workers (modo distribuído com interface web)

Para simular cargas maiores e aproveitar múltiplos núcleos da máquina, é possível rodar o Locust em modo distribuído — com **1 master**, **interface web** e **N workers** conectados, permitindo escalar o volume de requisições conforme o hardware disponível.

https://docs.locust.io/en/stable/running-distributed.html

#### Passo a passo

**1. Inicie o processo Master (com interface web):**

```bash
locust -f tests/locustfile.py --master
```

O master abrirá a interface web e ficará aguardando os workers se conectarem.

---

**2. Em outros terminais, inicie os Workers:**

```bash
locust -f tests/locustfile.py --worker --master-host=127.0.0.1
```

Você pode abrir quantos workers desejar — **não há limite fixo**, apenas os recursos da sua máquina (CPU/RAM). Isso permite simular cargas bem mais altas com estabilidade.

---

**3. Acesse a interface web:**

Abra o navegador e acesse:

```
http://localhost:8089
```

Na interface, você poderá:
- Definir o número de usuários simultâneos
- Taxa de spawn (usuários/segundo)
- Iniciar/parar o teste
- Acompanhar gráficos ao vivo com:
  - Tempo de resposta
  - Throughput
  - Percentual de falhas
- Exportar os resultados

---

# 🧪 Testes Unitários

> Também se recomenda executar os testes unitários **fora do Docker** para maior controle e legibilidade do output.

### Passo a passo para executar localmente:

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pytest
```

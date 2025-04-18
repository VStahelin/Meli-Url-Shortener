# Objetivo Geral

Cria um serviço encurtador de URL atendendo os seguintes requisitos:

- Dada uma URL longa, retorne uma URL curta.
- Dada uma URL curta, retorne a URL longa original.
- Permita obter estatísticas sobre as URLs encurtadas.
- Consiga lidar com solicitações em grande escala.
- Dar conta de 50k requisições por segundo. (Quando em larga escala)
- 90% das requisições sejam atendidas em menos de 10ms.
- Criação da URL não pode demorar mais que 1000ms.
- Permita a deleção das URLs curtas quando necessário.
- Garanta que, ao acessar uma URL curta válida no navegador, o usuário seja redirecionado para a URL longa.

---

# Primeira etapa - Setup

### Must Have
- FastAPI como framework base.
  - Com worktree por feature/domain.
- Redis para cachear as URLs.
- Postgres para persistir as URLs.
  - Com SQLAlchemy e Alembic.
- Docker para containerizar a aplicação.

### Nice to Have
- Balanceador de carga.
- Observabilidade.
  - Prometheus para métricas.

---

# Segunda etapa - Funcionalidades
- Criar um endpoint para encurtar a URL.
  - Criar uma URL curta a partir de uma URL longa.
  - Retornar a URL curta criada.
- Criar um endpoint para redirecionar a URL curta.
  - Criar um endpoint que redirecione a URL curta para a URL longa.
- Criar um endpoint para obter estatísticas.
  - Criar um endpoint que retorne as estatísticas da URL curta.
- Criar um endpoint para deletar a URL curta.

---

# Terceira etapa - Teste de Performance
- Teste de carga.
  - Usar ferramenta de teste de carga para verificar a performance da aplicação.

---

# Topologia da Solução

Para suportar 50k RPS com baixa latência (<10ms em 90% dos casos), a arquitetura segue os seguintes princípios:

## Diagrama Geral

- Um balanceador de carga distribui as requisições entre múltiplos pods do serviço FastAPI.
- Cada pod pode escalar horizontalmente com base no uso de CPU ou número de requisições por segundo, via HPA (Horizontal Pod Autoscaler).
- A resolução da URL curta ocorre majoritariamente via Redis (cache), reduzindo drasticamente o tempo de resposta.
- Em caso de cache miss, a aplicação consulta o banco de dados PostgreSQL.
- As respostas são redirecionadas imediatamente após a resolução.
- Métricas e rastreamentos são enviados para Prometheus e OpenTelemetry Collector.
- Os dados são visualizados através do Grafana.

## Componentes principais:
![image](https://github.com/user-attachments/assets/eb6eb5ce-0f2c-408a-9d89-2f6ea4c3184b)


- **Load Balancer:** distribui as requisições de forma balanceada.
- **App Pods (FastAPI):** processam requisições, escalam horizontalmente via Kubernetes.
- **Redis:** responde pela maior parte dos acessos (cache quente), com capacidade para lidar com 100k+ RPS.
- **PostgreSQL:** base de persistência, com uso secundário no fluxo de redirecionamento.
- **Observabilidade:** Prometheus e OpenTelemetry monitoram latência, throughput e rastreiam requisições.
- **Escalabilidade:**
  - Horizontal para lidar com volume.
  - Vertical para uso eficiente de núcleos com múltiplos workers Uvicorn.

---

# Progresso

- [x] Setup do projeto (FastAPI, Redis, Postgres, Docker).
- [x] Montar diagrama de topologia (Atual, e escalável).
- [X] Criar fluxograma base.
- [X] Adicionar diagramas
- [x] Criar um endpoint para encurtar a URL.
- [x] Criar um endpoint para redirecionar a URL curta.
- [x] Criar um endpoint para deletar a URL curta.
- [x] Integrar Prometheus.
- [x] Criar um endpoint para métricas do Prometheus.
- [x] Criar um endpoint para obter estatísticas simplificadas.
- [x] Teste simplificado de carga.

---

# Notas

- Precisa ser um script de baixa latência e de alta escalabilidade, ou seja, preciso pensar nos seguintes pontos:
- Escalabilidade horizontal para N pods:
  - Kubernetes gerencia facilmente.
  - Exemplo: 70% de uso por mais de X minutos cria um novo pod.
- Escalabilidade vertical caso um pod tenha múltiplos núcleos:
  - Um webserver Uvicorn consegue gerenciar isso facilmente distribuindo workers.
  - Regra base: (2 x núcleos) + 1 workers.
- Race/concurrency na geração da URL:
  - Deve ser controlado por locks, mas não há risco, temos até 1000ms de resposta.
- O número de núcleos e sua eficiência impactam diretamente no dimensionamento e métricas.
  - CPUs mais fracas escalam mais rapidamente horizontalmente.
- A linguagem escolhida é decisiva:
  - Python é mais pesado. Para produção massiva, C ou Go seriam mais indicadas.
- Redis suporta até 100k RPS com apenas uma instância em hardware modesto.

---

# Analize teste de Performance
### Teste local, um único container/pod docker, 12 workers

| Métrica                | 100 RPS       | 1000 RPS      |
|------------------------|---------------|---------------|
| Tempo médio (avg)      | 3.84 ms       | 12.80 ms      |
| Mediana (p50)          | 3 ms          | 6 ms          |
| Tempo mínimo           | 1.34 ms       | 1.27 ms       |
| Tempo máximo           | 162.87 ms     | 414.38 ms     |
| p75                    | 3 ms          | 10 ms         |
| p80                    | 3 ms          | 12 ms         |
| p90                    | 4 ms          | 22 ms         |
| p95                    | 5 ms          | 53 ms         |
| p98                    | 6 ms          | 110 ms        |
| p99                    | 57 ms         | 150 ms        |
| p99.9                  | 74 ms         | 240 ms        |
| p99.99                 | 160 ms        | 390 ms        |
| p100                   | 160 ms        | 410 ms        |
| Requisições totais     | 5921          | 54323         |


**Minha interpretação:**  
No teste com 1000 RPS, não consegui manter 90% das requisições abaixo de 10 ms, o que já era esperado, porem ficou perto. Mesmo com um código bem otimizado, encontrei limitações naturais de performance do Python para lidar com uma carga tão alta.

Em uma aplicação real, com uma meta tão agressiva (como 50k RPS abaixo de 10 ms), eu definitivamente não usaria Python como escolha principal. Mas fiquei satisfeito com o resultado: o código respondeu bem e mostrou que a arquitetura funciona, mesmo sob estresse.

---


# Como rodar o projeto

Este projeto já está configurado para ser executado em ambiente local utilizando Docker. O arquivo `.env` já contém todas as variáveis necessárias, portanto **nenhuma alteração é requerida** antes da execução.

## Pré-requisitos

Certifique-se de ter os seguintes itens instalados:

- [Docker](https://www.docker.com/)
- [Docker Compose](https://docs.docker.com/compose/install/)

## Passo a passo

1. **Clone o repositório:**

   ```bash
   git clone https://github.com/seu-usuario/seu-repositorio.git
   cd seu-repositorio
   ```

2. **Suba os containers:**

   ```bash
   docker compose up --build
   ```

   Isso irá:
   - Subir o serviço FastAPI (API principal).
   - Subir o banco de dados PostgreSQL.
   - Subir o Redis para cache.
   - Expor a aplicação na porta `8000`.

3. **Acesse a API:**

   A API estará disponível em:
   ```
   http://localhost:8000
   ```

   Você pode testar as rotas diretamente via navegador, Postman ou ferramentas de terminal como `curl`.

4. **Acesse as métricas Prometheus:**

   ```
   http://localhost:8000/metrics
   ```

---

# Rotas da API

#### Criar URL encurtada
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

#### Redirecionar URL
![image](https://github.com/user-attachments/assets/ea49442b-70dc-496b-bda9-025d04ade0fd)

- **GET /{url_id}**  
  Exemplo: `/XXYYZZ`  
  Redireciona para a URL original.

#### Deletar URL encurtada
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

#### Estatísticas de uso
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

# Testes de Performance com Locust

Este projeto possui um arquivo `locustfile.py` já configurado para testar carga no endpoint de redirecionamento (`GET /{url_id}`).
Necessita-se criar algumas urls encurtadas e substituí-las dentro da lista.

### Executar Locust em modo headless

```bash
locust -f tests/locustfile.py --headless -u 1000 -r 100 --host http://localhost:8000 --run-time 1m --csv locust_rps1000
```

**Parâmetros utilizados:**
- `-u 1000`: total de usuários simultâneos
- `-r 100`: número de novos usuários por segundo
- `--run-time 1m`: duração do teste (1 minuto)
- `--csv`: salva resultados em arquivos `.csv` para análise posterior

Os endpoints testados são definidos no array `endpoints` dentro do script, e devem conter URLs válidas que já existam na base para simular redirecionamento real.

### Output esperado
- Os arquivos `locust_rps1000_stats.csv` e `locust_rps1000_failures.csv` conterão estatísticas de tempo de resposta e erros.
- A métrica principal analisada é o tempo médio de resposta e o percentual de requisições abaixo de 10ms.

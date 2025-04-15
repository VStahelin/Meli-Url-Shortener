# Objetivo Geral
Cria um serviço encurtador de URL atendendo os seguintes requisitos:
- Dada uma URL longa, retorne uma URL curta.
- Dada uma URL curta, retorne a URL longa original.
- Permita obter estatísticas sobre as URLs encurtadas.
- Consiga lidar com solicitações em grande escala.
- Dar conta de 50k requisições por segundo. (Quando em larga escala)
- 90% das requisições sejam atendidas em menos de 10ms.
- Criação da url não pode demorar mais que 1000ms.
- Permita a deleção das URLs curtas quando necessário.
- Garanta que, ao acessar uma URL curta válida no navegador, o usuário seja redirecionado para a URL longa.


# Primeira etapa - Setup

### Must Have
- FastAPI como framework base.
  - Com worktree por feature/domain.
- Redis para cachear as URLs.
- Postgres para persistir as URLs.
  - Com SQLAlchemy e Alembic
- Docker para containerizar a aplicação.

### Nice to have
- Kubernetes para orquestração de containers.
- Balanceador de carga.
- Observabilidade.
  - Prometheus para metricas.
- OpenTelemetry para rastreamento.


# Segunda etapa - Funcionalidades
- Criar um endpoint para encurtar a URL.
  - Criar uma URL curta a partir de uma URL longa.
  - Retornar a URL curta criada.
- Criar um endpoint para redirecionar a URL curta.
  - Criar um endpoint que redirecione a URL curta para a URL longa.
- Criar um endpoint para obter estatísticas.
  - Criar um endpoint que retorne as estatísticas da URL curta.
- Criar um endpoint para deletar a URL curta.

# Terceira etapa - Teste Performance
- Adicionar testes unitários.
  - Testar os endpoints criados.
- Teste de carga.
  - Usar ferramenta de teste de carga para verificar a performance da aplicação.


## Progresso
- [x] Setup do projeto (FastAPI, Redis, Postgres, Docker).
- [ ] Montar diagrama de topologia (Atual, e escalável).
- [ ] Criar fluxograma base.
- [x] Criar um endpoint para encurtar a URL.
- [x] Criar um endpoint para redirecionar a URL curta.
- [x] Criar um endpoint para deletar a URL curta.
- [x] Integrar Prometheus.
- [x] Criar um endpoint para metricas do Prometheus.
- [x] Criar um endpoint para obter estatísticas simplificadas.
- [ ] Teste simplificado de carga.
- [ ] Criar testes unitários.
- [ ] Criar testes de carga.
- [ ] Validação de alta carga.



# Rotas da API

#### Criar URL encurtada
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
- **GET /{url_id}**  
  Exemplo: `/XXYYZZ`  
  Redireciona para a URL original.

#### Deletar URL encurtada
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
  
#### Métricas Prometheus
- **GET /metrics**  
  Retorna métricas no formato Prometheus para scraping externo.


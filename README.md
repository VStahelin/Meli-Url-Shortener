# Objetivo Geral
Cria um serviço encurtador de URL atendendo os seguintes requisitos:
- Dada uma URL longa, retorne uma URL curta.
- Dada uma URL curta, retorne a URL longa original.
- Permita obter estatísticas sobre as URLs encurtadas.
- Consiga lidar com solicitações em grande escala.
- Dar conta de 50k requisições por segundo.
- 90% das requisições sejam atendidas em menos de 10ms.
- Criação da url não pode demorar mais que 1000ms.
- Permita a deleção das URLs curtas quando necessário.
- Garanta que, ao acessar uma URL curta válida no navegador, o usuário seja redirecionado para a URL longa.


# Arquitetura Inicial (Must have)
- FastAPI como framework base.
  - Ja dando suporte nativo a swagger.
  - Com worktree por feature/domain.
- Redis para cachear as URLs.
- Postgres para persistir as URLs.
  - Com SQLAlchemy e Alembic 
- Pytest para testes.
- Docker para containerizar a aplicação.

# Arquitetura Etapa 2
- Aplicar ferramenta de teste para verificar a performance da aplicação. (Locust?)
- Aplicar um balanceador de carga.
  - Seja com docker ou KS8

# Arquitetura Final (Nice to have)
- Aplicar uma ferramenta de observabilidade

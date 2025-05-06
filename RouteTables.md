# Tabelas e Rotas - Detec-O

Este documento resume as tabelas de banco de dados necessárias para a aplicação e as principais alterações e implementações realizadas recentemente.

## Tabelas de Banco de Dados Requeridas (Baseado em `api/models.py`)

As seguintes tabelas são definidas pelos modelos SQLAlchemy e precisam existir no banco de dados PostgreSQL de produção:

1.  **`users`**:
    *   **Classe SQLAlchemy:** `User`
    *   **Propósito:** Armazena informações dos usuários do sistema (ID, username, email, senha hash, nome completo, status, etc.).

2.  **`cameras`**:
    *   **Classe SQLAlchemy:** `Camera`
    *   **Propósito:** Armazena detalhes das câmeras conectadas (ID, nome, dono, URL RTSP, localização, configurações de detecção/IA, etc.).

3.  **`detection_events`**:
    *   **Classe SQLAlchemy:** `DetectionEvent`
    *   **Propósito:** Armazena os eventos de detecção (ID, ID da câmera, tipo, confiança, timestamp, caminho do vídeo, status de feedback, notas de feedback, usuário do feedback, timestamp do feedback).

4.  **`event_snapshots`**:
    *   **Classe SQLAlchemy:** `EventSnapshot`
    *   **Propósito:** Armazena os caminhos para os arquivos de imagem (snapshots) associados a cada evento de detecção, com timestamp exato.

**Observação:** O arquivo `POSTGRESQL.md` pode estar desatualizado. As tabelas listadas acima são as definidas no código atual (`api/models.py`). Recomenda-se o uso de **Alembic** para gerenciamento do schema em produção.

## Resumo das Alterações e Implementações Recentes

*   **Análise Inicial:** Revisão do `README.md` e `POSTGRESQL.md` para compreensão do projeto.
*   **Funcionalidade de Feedback de Eventos:**
    *   Implementado o endpoint `POST /api/events/{event_id}/feedback` no backend.
    *   Adicionados campos de feedback (`feedback_status`, `feedback_notes`, `feedback_user_id`, `feedback_timestamp`) ao modelo e tabela `detection_events`.
    *   Corrigidas as chamadas no frontend (`FeedbackControl.jsx`, `EventsPage.jsx`) para enviar os dados corretos (nomes de campo, valores, prefixo `/api`) e exibir o feedback salvo de forma persistente.
    *   Aplicados comandos `ALTER TABLE` manualmente via pgAdmin para adicionar as novas colunas ao banco de dados (alternativa à migração com Alembic).
*   **Filtros da `EventsPage`:**
    *   Implementada a lógica de filtragem no backend (`GET /api/events/`) para os parâmetros `min_confidence` e `feedback_status`.
    *   Corrigidos os nomes dos parâmetros de data (`start_date`, `end_date`) e feedback (`feedback_status`) enviados pelo frontend.
    *   Garantida a passagem dos parâmetros de paginação (`skip`, `limit`).
*   **Melhorias no `DashboardPage`:**
    *   **KPIs e Eventos Recentes:** Corrigida a busca inicial de dados que falhava devido a redirecionamentos 307/erros 401 (URLs sem barra final), ajustando as chamadas API para usar `/api/cameras/` e `/api/events/`. A seção "Eventos Recentes" agora exibe dados reais.
    *   **Gráfico "Eventos ao Longo do Tempo":** Implementado o endpoint `GET /api/events/stats/timeseries` no backend e a lógica no frontend para buscar e exibir a contagem real de eventos por dia, substituindo os dados simulados. O filtro de período (24h, 7d, 30d) agora atualiza o gráfico. O período padrão foi alterado para 30 dias.
    *   **Gráfico "Distribuição por Hora":** Implementado o endpoint `GET /api/events/stats/hourly` no backend e a lógica no frontend para exibir a contagem real de eventos por hora do dia, substituindo os dados simulados.
    *   **Gráfico de Pizza (Severidade):** Removidos os labels das fatias e adicionada uma lista detalhada abaixo do gráfico para melhor legibilidade, exibindo nome, contagem e cor para cada nível de severidade.
    *   **Estilização de Gráficos:** Melhorada a aparência dos gráficos na aba "Eventos" (cores, tooltips, largura do eixo Y).
    *   **Aba "Zonas":** Removida a aba "Zonas" e seus dados/componentes associados, pois dependiam de dados simulados e a lógica de associação evento-zona não está implementada.
*   **Remoção de Logs:** Logs de `console.log` adicionados para depuração foram removidos/comentados. 
# Declaração da Tecnologia Utilizada

## IBM Bob — Copiloto de Engenharia Central

O **IBM Bob** foi utilizado como assistente de desenvolvimento ao longo de **todo o ciclo de vida do projeto** — da concepção à entrega. Abaixo estão os usos específicos e verificáveis:

### 1. Arquitetura e design do sistema
Bob analisou a estrutura inicial do projeto (dois projetos misturados no mesmo repositório, com `knowledge_base/` dentro de `knowledge_base/`) e propôs e executou a reorganização completa — movendo arquivos para as pastas corretas, eliminando duplicatas e criando uma estrutura limpa e deployável.

### 2. Desenvolvimento do frontend (app.py)
O arquivo `app.py` (interface Streamlit) foi integralmente criado pelo IBM Bob, incluindo:
- Conexão com o SDK do IBM watsonx Orchestrate via `execute_agent_interaction_with_fallback`
- Sistema de renderização enriquecida da resposta do agente (parser de markdown → HTML visual com cards de status, critérios com ✅/❌, cards de contatos lado a lado, expander de e-mails)
- Suporte dual a credenciais: `st.secrets` (Streamlit Cloud) e `.env` (local)
- Botões de ação rápida, sidebar com dados da knowledge base, exibição de reasoning trace

### 3. Depuração e resolução de problemas
Bob diagnosticou e corrigiu múltiplos problemas em tempo real:
- Identificou que o CLI `orchestrate` estava instalado em `AppData\Roaming` (não `AppData\Local`) e adicionou o caminho ao PATH do sistema
- Identificou que a URL da instância deveria ser `api.eu-de.watson-orchestrate.cloud.ibm.com` (não `api.eu-de.watson-orchestrate.ibm.com`) via DNS lookup
- Identificou que o agente retorna markdown com hífens não-quebrantes (`‑` U+2011) e corrigiu os regex de extração de contatos
- Corrigiu o bug de `**` literais aparecendo na interface ao perceber que o agente usa markdown onde o código esperava texto puro

### 4. Segurança e boas práticas
- Criou o `.gitignore` via git para proteger o `.env` do versionamento
- Criou o `.env.example` como template documentado
- Configurou o `requirements.txt` com versões fixas para deploy reproduzível

### 5. Servidor MCP para uso como frontend conversacional
Bob projetou e implementou o servidor MCP em `mcp/server.py`, expondo as 4 ferramentas de conformidade ao IBM Bob via protocolo MCP (stdio):
- `listar_empresas` — descobre as empresas disponíveis na knowledge base
- `obter_empresa` — recupera dados completos por ID ou nome
- `verificar_conformidade` — aplica os 3 critérios automaticamente, buscando o histórico da KB internamente
- `enviar_solicitacao_aprovacao` — gera os e-mails formais de aprovação

O servidor foi registrado em `.bob/mcp.json` para que o IBM Bob possa atuar como **frontend conversacional direto** — sem necessidade da interface Streamlit — demonstrando o agente de conformidade puramente via chat com o Bob.

### 6. Documentação
Bob redigiu e atualizou o `README.md` com estrutura de projeto, instruções de deploy, seção de interface web com 5 passos detalhados, diagrama de arquitetura Mermaid e seção de testes.

---

## IBM watsonx Orchestrate

O **IBM watsonx Orchestrate** é o motor central da solução:

- **Agente nativo** `agente_conformidade_VF` configurado via YAML com instruções detalhadas de fluxo obrigatório (verificar → enviar se necessário)
- **Knowledge Base RAG** `compras_conformidade_kb` com `empresas_corporativas.json` contendo histórico mensal de 8 empresas (Mai–Out/2026), valores, fornecedores, localizações e contatos aprovadores
- **2 ferramentas Python** registradas no WXO:
  - `verificar_conformidade_transacao`: aplica os 3 critérios e retorna divergências
  - `enviar_solicitacao_aprovacao_conformidade`: gera e-mails formais para os 2 aprovadores
- **SDK Python** (`ibm-watsonx-orchestrate`) usado no frontend para comunicação via threads e runs

## IBM Granite

O LLM utilizado pelo agente no IBM watsonx Orchestrate é **IBM Granite**, configurado no `agente_conformidade_VF.yaml`. O modelo é responsável por interpretar as consultas em linguagem natural, orquestrar as chamadas às ferramentas na ordem correta e formatar a resposta final no template estruturado definido nas instruções do agente.

## Ferramentas Open Source

| Ferramenta | Uso |
|---|---|
| **Python 3.14** | Implementação das tools e lógica de conformidade |
| **Streamlit 1.67** | Interface web conversacional |
| **mcp[cli] 2.x** | Protocolo MCP para integração direta com IBM Bob |
| **python-dotenv** | Gerenciamento de credenciais local |
| **Git** | Controle de versão |

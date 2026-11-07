# MCP Server — Agente de Conformidade VF

Servidor MCP Python que expõe as ferramentas de verificação de conformidade de compras ao **IBM Bob** via protocolo MCP (stdio).

## Ferramentas disponíveis

| Ferramenta | Descrição |
|---|---|
| `listar_empresas` | Lista as 8 empresas cadastradas com IDs, localizações e histórico |
| `obter_empresa` | Retorna dados completos de uma empresa pelo ID ou nome |
| `verificar_conformidade` | Verifica se uma transação tem não-conformidades contra o histórico |
| `enviar_solicitacao_aprovacao` | Gera e-mails formais de aprovação para os 2 contatos responsáveis |

## Fluxo de uso no IBM Bob

```
1. listar_empresas()                     → descobre IDs das empresas
2. verificar_conformidade(empresa_id, …) → analisa a transação
3. Se requer_aprovacao=true →
   enviar_solicitacao_aprovacao(…)       → gera os e-mails de aprovação
```

Os dados dos aprovadores já vêm no campo `contatos_aprovadores` do resultado de `verificar_conformidade()` — sem necessidade de busca adicional.

## Instalação

```bash
pip install "mcp[cli]>=1.9.2"
```

## Teste local

```bash
cd Agente-de-IA-IBM
python mcp/server.py
```

O servidor aguarda mensagens JSON via stdin (protocolo MCP). Para testar interativamente use o `mcp dev`:

```bash
mcp dev mcp/server.py
```

## Registro no IBM Bob

Adicione em `.bob/mcp.json` (workspace) ou no arquivo MCP global do Bob:

```json
{
  "mcpServers": {
    "conformidade-vf": {
      "command": "python",
      "args": ["C:/caminho/absoluto/para/Agente-de-IA-IBM/mcp/server.py"]
    }
  }
}
```

> **Windows:** use barras normais `/` ou barras duplas `\\` no caminho.  
> **Pré-requisito:** o pacote `mcp[cli]` deve estar instalado no Python do PATH.

## Exemplos de conversa com o Bob

```
Você: Quais empresas estão cadastradas?

Bob: [usa listar_empresas] → Alpha Tech (EMP-001), Beta Logística (EMP-002)...

Você: Verifique a conformidade da Alpha Tech para Novembro/2026:
      valor R$ 10.000, fornecedor "Fornecedor X", localização "Manaus, AM"

Bob: [usa verificar_conformidade] → 3 divergências encontradas!
     - Valor 114% acima da média
     - Fornecedor desconhecido
     - Localização não registrada
     Deseja que eu gere a solicitação de aprovação?

Você: Sim

Bob: [usa enviar_solicitacao_aprovacao] → e-mails para Carla Menezes e Roberto Siqueira gerados.
```

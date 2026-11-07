#!/usr/bin/env python3
"""
MCP Server — Agente de Conformidade VF
Expõe as ferramentas de conformidade de compras ao IBM Bob via protocolo MCP (stdio).

Ferramentas disponíveis:
  - listar_empresas              : lista todas as empresas com seus IDs e histórico resumido
  - obter_empresa                : retorna dados completos de uma empresa pelo ID ou nome
  - verificar_conformidade       : verifica se uma transação tem não-conformidades
  - enviar_solicitacao_aprovacao : gera e-mails formais de aprovação para os aprovadores
"""

import json
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Resolve o caminho da knowledge base (relativo ao repo, não ao cwd)
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent
KB_PATH = ROOT / "knowledge_base" / "docs" / "empresas_corporativas.json"

from mcp.server.mcpserver import MCPServer

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------
LIMIAR_INCOERENCIA = 15.0  # %


# ---------------------------------------------------------------------------
# Carrega a knowledge base em memória (uma vez ao iniciar)
# ---------------------------------------------------------------------------
def _carregar_kb() -> dict:
    with open(KB_PATH, encoding="utf-8") as f:
        return json.load(f)


KB = _carregar_kb()

# ---------------------------------------------------------------------------
# Servidor MCP
# ---------------------------------------------------------------------------
server = MCPServer(
    name="conformidade-vf",
    description="Agente de Conformidade de Compras VF — verifica transações corporativas contra histórico e gera solicitações de aprovação.",
)


# ---------------------------------------------------------------------------
# Tool 1: listar_empresas
# ---------------------------------------------------------------------------
@server.tool()
def listar_empresas() -> str:
    """Lista todas as empresas cadastradas na base de conhecimento com seus IDs,
    nomes, cidades de operação e quantidade de meses no histórico.
    Use esta ferramenta primeiro para descobrir quais empresas estão disponíveis."""
    empresas = KB.get("empresas", [])
    resultado = []
    for emp in empresas:
        historico = emp.get("historico_mensal", [])
        localizacoes = list({m["localizacao"] for m in historico if "localizacao" in m})
        resultado.append({
            "id": emp["id"],
            "nome": emp["nome"],
            "meses_historico": len(historico),
            "localizacoes": localizacoes,
            "contatos": [c["nome"] for c in emp.get("contatos", [])],
        })
    return json.dumps(resultado, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------------
# Tool 2: obter_empresa
# ---------------------------------------------------------------------------
@server.tool()
def obter_empresa(empresa_id: str = "", empresa_nome: str = "") -> str:
    """Retorna os dados completos de uma empresa: histórico mensal de compras,
    fornecedores por mês, localizações e contatos aprovadores.

    Forneça 'empresa_id' (ex: 'EMP-001') OU 'empresa_nome' (ex: 'Alpha Tech').
    A busca por nome é case-insensitive e por substring.
    """
    empresas = KB.get("empresas", [])
    encontrada = None

    if empresa_id:
        for emp in empresas:
            if emp["id"].strip().upper() == empresa_id.strip().upper():
                encontrada = emp
                break

    if not encontrada and empresa_nome:
        nome_lower = empresa_nome.strip().lower()
        for emp in empresas:
            if nome_lower in emp["nome"].lower():
                encontrada = emp
                break

    if not encontrada:
        return json.dumps({
            "erro": "Empresa não encontrada. Use listar_empresas() para ver as disponíveis.",
            "empresa_id_buscado": empresa_id,
            "empresa_nome_buscado": empresa_nome,
        }, ensure_ascii=False, indent=2)

    return json.dumps(encontrada, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------------
# Tool 3: verificar_conformidade
# ---------------------------------------------------------------------------
@server.tool()
def verificar_conformidade(
    empresa_id: str,
    pedido_id: str,
    valor_total_atual: float,
    fornecedores_atuais: list[str],
    localizacao_atual: str,
) -> str:
    """Verifica se uma transação de compras tem não-conformidades comparando com
    o histórico da empresa na base de conhecimento.

    Critérios verificados automaticamente:
      1. Valor total > 15% acima da média histórica dos demais meses
      2. Fornecedor(es) não presentes no histórico de compras
      3. Localização não registrada no histórico

    Retorna 'requer_aprovacao: true' com a lista de divergências se qualquer
    critério for violado. Os dados históricos são buscados automaticamente
    a partir do empresa_id — não é necessário informá-los manualmente.
    O resultado inclui o campo 'contatos_aprovadores' pronto para uso em
    enviar_solicitacao_aprovacao().

    Args:
        empresa_id: ID da empresa (ex: 'EMP-001'). Use listar_empresas() para descobrir.
        pedido_id: Código ou referência do pedido / mês sendo analisado (ex: 'Novembro/2026').
        valor_total_atual: Valor total da transação em reais.
        fornecedores_atuais: Lista de nomes dos fornecedores da transação atual.
        localizacao_atual: Localização informada na transação (ex: 'São Paulo, SP').
    """
    # Busca empresa na KB
    empresa = None
    for emp in KB.get("empresas", []):
        if emp["id"].strip().upper() == empresa_id.strip().upper():
            empresa = emp
            break

    if not empresa:
        return json.dumps({
            "erro": f"Empresa '{empresa_id}' não encontrada. Use listar_empresas() para ver as disponíveis.",
        }, ensure_ascii=False, indent=2)

    historico = empresa.get("historico_mensal", [])
    empresa_nome = empresa["nome"]

    # Média histórica excluindo o mês do pedido (se já existir)
    valores_historicos = [
        m["valor_total"] for m in historico
        if m.get("mes", "").strip().lower() != pedido_id.strip().lower()
    ]
    media_historica = sum(valores_historicos) / len(valores_historicos) if valores_historicos else 0.0

    # Fornecedores e localizações históricas (excluindo o mês atual)
    fornecedores_historicos = list({
        f
        for m in historico
        for f in m.get("fornecedores", [])
        if m.get("mes", "").strip().lower() != pedido_id.strip().lower()
    })
    localizacoes_historicas = list({
        m["localizacao"]
        for m in historico
        if "localizacao" in m and m.get("mes", "").strip().lower() != pedido_id.strip().lower()
    })

    # --- Critério 1: Valor atípico ---
    divergencias = []
    variacao_percentual = 0.0
    valor_atipico = False
    if media_historica > 0:
        variacao_percentual = ((valor_total_atual - media_historica) / media_historica) * 100
        if variacao_percentual > LIMIAR_INCOERENCIA:
            valor_atipico = True
            divergencias.append(
                f"Valor total R${valor_total_atual:,.2f} está {variacao_percentual:.1f}% acima "
                f"da média histórica R${media_historica:,.2f} (limite: {LIMIAR_INCOERENCIA:.0f}%)"
            )

    # --- Critério 2: Fornecedores novos ---
    historicos_lower = {f.strip().lower() for f in fornecedores_historicos}
    fornecedores_novos: list[str] = []
    if historicos_lower:
        fornecedores_novos = [
            f for f in fornecedores_atuais
            if f.strip().lower() not in historicos_lower
        ]
    fornecedor_novo = len(fornecedores_novos) > 0
    if fornecedor_novo:
        divergencias.append(
            f"Fornecedor(es) não encontrado(s) no histórico: {', '.join(fornecedores_novos)}"
        )

    # --- Critério 3: Localização nova ---
    localizacao_ausente = not localizacao_atual or str(localizacao_atual).strip() == ""
    localizacao_nova = False
    if localizacao_ausente:
        divergencias.append("Localização da transação não informada")
        localizacao_nova = True
    else:
        historicos_loc_lower = {loc.strip().lower() for loc in localizacoes_historicas}
        if localizacao_atual.strip().lower() not in historicos_loc_lower:
            localizacao_nova = True
            divergencias.append(
                f"Localização '{localizacao_atual}' não registrada no histórico desta empresa"
            )

    requer_aprovacao = len(divergencias) > 0

    return json.dumps({
        "requer_aprovacao": requer_aprovacao,
        "empresa_nome": empresa_nome,
        "empresa_id": empresa_id,
        "pedido_id": pedido_id,
        "valor_total_atual": valor_total_atual,
        "media_historica_mensal": round(media_historica, 2),
        "variacao_percentual": round(variacao_percentual, 2),
        "fornecedores_atuais": fornecedores_atuais,
        "fornecedores_novos": fornecedores_novos,
        "localizacao_atual": localizacao_atual if not localizacao_ausente else "NÃO INFORMADA",
        "localizacao_nova": localizacao_nova,
        "divergencias": divergencias,
        "tipos_divergencia": {
            "valor_atipico": valor_atipico,
            "fornecedor_novo": fornecedor_novo,
            "localizacao_nova_ou_ausente": localizacao_nova,
        },
        "contatos_aprovadores": empresa.get("contatos", []),
    }, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------------
# Tool 4: enviar_solicitacao_aprovacao
# ---------------------------------------------------------------------------
@server.tool()
def enviar_solicitacao_aprovacao(
    empresa_nome: str,
    pedido_id: str,
    valor_total_atual: float,
    media_historica_mensal: float,
    variacao_percentual: float,
    fornecedores_novos: list[str],
    localizacao_atual: str,
    divergencias: list[str],
    nome_aprovador_1: str,
    email_aprovador_1: str,
    cargo_aprovador_1: str,
    telefone_aprovador_1: str,
    nome_aprovador_2: str,
    email_aprovador_2: str,
    cargo_aprovador_2: str,
    telefone_aprovador_2: str,
) -> str:
    """Gera formalmente a solicitação de aprovação para os 2 contatos responsáveis
    quando divergências são detectadas em uma transação.

    Deve ser chamada apenas quando verificar_conformidade() retornar requer_aprovacao=true.
    Os dados dos aprovadores (nome, email, cargo, telefone) estão disponíveis no campo
    'contatos_aprovadores' do resultado de verificar_conformidade().

    Retorna um relatório completo com os modelos de e-mail prontos para envio imediato.
    """
    divergencias_fmt = (
        "\n".join(f"  • {d}" for d in divergencias)
        if divergencias
        else "  • Divergência identificada"
    )
    assunto = (
        f"[CONFORMIDADE — APROVAÇÃO NECESSÁRIA] "
        f"Divergência detectada — {empresa_nome} / {pedido_id}"
    )

    valor_linha = (
        f"R$ {valor_total_atual:,.2f} (+{variacao_percentual:.1f}% acima da média "
        f"R$ {media_historica_mensal:,.2f})"
        if variacao_percentual > 0
        else f"R$ {valor_total_atual:,.2f}"
    )

    loc_linha = (
        "⚠️ NÃO INFORMADA"
        if not localizacao_atual or localizacao_atual == "NÃO INFORMADA"
        else localizacao_atual
    )

    fornecedores_bloco = ""
    if fornecedores_novos:
        fornecedores_bloco = (
            "\n  Fornecedor(es) NÃO encontrado(s) no histórico:\n"
            + "\n".join(f"    ⚠️ {f}" for f in fornecedores_novos)
        )

    def _email(nome: str, email: str) -> str:
        return (
            f"┌─────────────────────────────────────────────────────────────────┐\n"
            f"  SOLICITAÇÃO DE APROVAÇÃO — {nome.upper()}\n"
            f"  Para: {email}\n"
            f"├─────────────────────────────────────────────────────────────────┤\n"
            f"  Assunto: {assunto}\n\n"
            f"  Prezado(a) {nome},\n\n"
            f"  O sistema de Conformidade de Compras identificou divergências na\n"
            f"  transação abaixo que requerem sua aprovação formal:\n\n"
            f"    • Empresa    : {empresa_nome}\n"
            f"    • Referência : {pedido_id}\n"
            f"    • Valor      : {valor_linha}\n"
            f"    • Localização: {loc_linha}{fornecedores_bloco}\n\n"
            f"  Divergências identificadas:\n"
            f"{divergencias_fmt.replace('  •', '    -')}\n\n"
            f"  Por favor, responda a este e-mail com:\n"
            f"    ✅ APROVADO — informe a justificativa para prosseguir.\n"
            f"    ❌ REJEITADO — a ordem de compra será cancelada automaticamente.\n\n"
            f"  Prazo para resposta: 48 horas a partir do recebimento deste e-mail.\n\n"
            f"  Atenciosamente,\n"
            f"  Sistema de Conformidade de Compras — Agente de Conformidade VF\n"
            f"└─────────────────────────────────────────────────────────────────┘"
        )

    email_1 = _email(nome_aprovador_1, email_aprovador_1)
    email_2 = _email(nome_aprovador_2, email_aprovador_2)

    return (
        f"SOLICITAÇÃO DE APROVAÇÃO ENVIADA\n"
        f"═══════════════════════════════════════════════════════════════\n"
        f"EMPRESA        : {empresa_nome}\n"
        f"PEDIDO/REF.    : {pedido_id}\n"
        f"VALOR ATUAL    : R$ {valor_total_atual:,.2f}\n"
        f"MÉDIA HISTÓRICA: R$ {media_historica_mensal:,.2f}\n"
        f"VARIAÇÃO       : {variacao_percentual:.1f}%\n"
        f"LOCALIZAÇÃO    : {loc_linha}\n\n"
        f"DIVERGÊNCIAS QUE MOTIVARAM O ENVIO:\n"
        f"{divergencias_fmt}\n\n"
        f"CONTATOS ACIONADOS:\n"
        f"- Contato 1: {nome_aprovador_1} ({cargo_aprovador_1})\n"
        f"  E-mail: {email_aprovador_1} | Tel: {telefone_aprovador_1}\n"
        f"  Status: Pendente de Resposta\n\n"
        f"- Contato 2: {nome_aprovador_2} ({cargo_aprovador_2})\n"
        f"  E-mail: {email_aprovador_2} | Tel: {telefone_aprovador_2}\n"
        f"  Status: Pendente de Resposta\n\n"
        f"─────────────────────────────────────────────────────────────────────\n"
        f"MODELOS DE E-MAIL GERADOS PARA ENVIO\n"
        f"─────────────────────────────────────────────────────────────────────\n\n"
        f"{email_1}\n\n"
        f"{email_2}"
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    server.run(transport="stdio")

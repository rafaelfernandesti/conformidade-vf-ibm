from ibm_watsonx_orchestrate.agent_builder.tools import tool
import json

# ---------------------------------------------------------------------------
# Limiar de incoerência formal (> 15% acima da média)
# ---------------------------------------------------------------------------
LIMIAR_INCOERENCIA = 15.0  # %


@tool
def verificar_conformidade_transacao(
    empresa_nome: str,
    empresa_id: str,
    pedido_id: str,
    valor_total_atual: float,
    media_historica_mensal: float,
    fornecedores_atuais_json: str,
    fornecedores_historicos_json: str,
    localizacao_atual: str,
    localizacoes_historicas_json: str,
) -> str:
    """Verifica se uma transação apresenta alguma das seguintes não-conformidades:
    (1) o valor total da transação é maior que 15% acima da média histórica;
    (2) a empresa/fornecedor não está no histórico de compras;
    (3) a localização da empresa não se encontra no histórico.

    Se qualquer uma dessas condições for verdadeira, retorna as divergências
    encontradas, indicando que a solicitação deve ser enviada para aprovação
    dos 2 contatos responsáveis.

    Args:
        empresa_nome (str): Nome da empresa da transação.
        empresa_id (str): ID da empresa (ex: "EMP-001").
        pedido_id (str): Código ou referência do pedido/mês analisado.
        valor_total_atual (float): Valor total da transação atual.
        media_historica_mensal (float): Média histórica dos demais meses da empresa.
        fornecedores_atuais_json (str): JSON com lista de strings dos fornecedores
            da transação atual (ex: '["Fornecedor X", "Fornecedor Y"]').
        fornecedores_historicos_json (str): JSON com lista de strings de todos os
            fornecedores já utilizados anteriormente pela empresa (histórico completo).
        localizacao_atual (str): Localização informada na transação atual.
            Deve ser uma string não vazia; caso contrário é tratada como ausente.
        localizacoes_historicas_json (str): JSON com lista de strings das localizações
            já registradas no histórico da empresa (ex: '["São Paulo, SP"]').

    Returns:
        str: JSON com o resultado da verificação contendo:
             - 'requer_aprovacao' (bool): True se qualquer divergência for encontrada.
             - 'divergencias' (list[str]): Lista de motivos de não-conformidade.
             - 'tipos_divergencia' (dict): Flags individuais de cada critério verificado.
             - 'empresa_nome', 'empresa_id', 'pedido_id': Dados de identificação.
             - 'valor_total_atual', 'media_historica_mensal', 'variacao_percentual'.
             - 'fornecedores_novos' (list[str]): Fornecedores não encontrados no histórico.
             - 'localizacao_nova' (bool): True se a localização não está no histórico.
    """
    divergencias = []
    fornecedores_atuais: list = json.loads(fornecedores_atuais_json)
    fornecedores_historicos: list = json.loads(fornecedores_historicos_json)
    localizacoes_historicas: list = json.loads(localizacoes_historicas_json)

    # --- Critério 1: Valor total > 15% acima da média histórica ---
    variacao_percentual = 0.0
    valor_atipico = False
    if media_historica_mensal > 0:
        variacao_percentual = ((valor_total_atual - media_historica_mensal) / media_historica_mensal) * 100
        if variacao_percentual > LIMIAR_INCOERENCIA:
            valor_atipico = True
            divergencias.append(
                f"Valor total R${valor_total_atual:,.2f} está {variacao_percentual:.1f}% acima "
                f"da média histórica R${media_historica_mensal:,.2f} (limite: {LIMIAR_INCOERENCIA:.0f}%)"
            )

    # --- Critério 2: Fornecedor(es) não encontrado(s) no histórico ---
    # Guard: se o histórico estiver vazio não há base de comparação — nenhum
    # fornecedor é considerado "novo" (comportamento consistente com os agentes
    # de origem: auditar_empresa_v2 / auditar_historico_mensal_empresa_v2).
    historicos_lower = {f.strip().lower() for f in fornecedores_historicos}
    if historicos_lower:
        fornecedores_novos = [
            f for f in fornecedores_atuais
            if f.strip().lower() not in historicos_lower
        ]
    else:
        fornecedores_novos = []
    fornecedor_novo = len(fornecedores_novos) > 0
    if fornecedor_novo:
        divergencias.append(
            f"Fornecedor(es) não encontrado(s) no histórico de compras: "
            f"{', '.join(fornecedores_novos)}"
        )

    # --- Critério 3: Localização não encontrada no histórico ---
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
                f"Localização '{localizacao_atual}' não se encontra no histórico "
                f"de compras desta empresa"
            )

    requer_aprovacao = len(divergencias) > 0

    return json.dumps({
        "requer_aprovacao": requer_aprovacao,
        "empresa_nome": empresa_nome,
        "empresa_id": empresa_id,
        "pedido_id": pedido_id,
        "valor_total_atual": valor_total_atual,
        "media_historica_mensal": round(media_historica_mensal, 2),
        "variacao_percentual": round(variacao_percentual, 2),
        "fornecedores_novos": fornecedores_novos,
        "localizacao_atual": localizacao_atual if not localizacao_ausente else "NÃO INFORMADA",
        "localizacao_nova": localizacao_nova,
        "divergencias": divergencias,
        "tipos_divergencia": {
            "valor_atipico": valor_atipico,
            "fornecedor_novo": fornecedor_novo,
            "localizacao_nova_ou_ausente": localizacao_nova,
        },
    }, ensure_ascii=False, indent=2)


@tool
def enviar_solicitacao_aprovacao_conformidade(
    empresa_nome: str,
    pedido_id: str,
    valor_total_atual: float,
    media_historica_mensal: float,
    variacao_percentual: float,
    fornecedores_novos_json: str,
    localizacao_atual: str,
    divergencias_json: str,
    nome_aprovador_1: str,
    email_aprovador_1: str,
    cargo_aprovador_1: str,
    telefone_aprovador_1: str,
    nome_aprovador_2: str,
    email_aprovador_2: str,
    cargo_aprovador_2: str,
    telefone_aprovador_2: str,
) -> str:
    """Gera e envia formalmente a solicitação de aprovação para os 2 contatos
    responsáveis quando divergências de conformidade são detectadas na transação.

    Deve ser chamada apenas quando 'requer_aprovacao' for True no resultado de
    'verificar_conformidade_transacao'. Os contatos aprovadores devem ser obtidos
    da knowledge base ou RAG da empresa correspondente.

    Args:
        empresa_nome (str): Nome da empresa da transação.
        pedido_id (str): Código ou referência do pedido/mês analisado.
        valor_total_atual (float): Valor total da transação atual.
        media_historica_mensal (float): Média histórica de referência.
        variacao_percentual (float): Variação percentual do valor em relação à média.
        fornecedores_novos_json (str): JSON com lista de fornecedores novos (não históricos).
        localizacao_atual (str): Localização registrada ou "NÃO INFORMADA".
        divergencias_json (str): JSON com lista de strings descrevendo cada divergência.
        nome_aprovador_1 (str): Nome do primeiro contato aprovador.
        email_aprovador_1 (str): E-mail do primeiro contato aprovador.
        cargo_aprovador_1 (str): Cargo/área do primeiro contato aprovador.
        telefone_aprovador_1 (str): Telefone do primeiro contato aprovador.
        nome_aprovador_2 (str): Nome do segundo contato aprovador.
        email_aprovador_2 (str): E-mail do segundo contato aprovador.
        cargo_aprovador_2 (str): Cargo/área do segundo contato aprovador.
        telefone_aprovador_2 (str): Telefone do segundo contato aprovador.

    Returns:
        str: Relatório completo com os modelos de e-mail formatados para envio
             imediato a cada um dos 2 contatos aprovadores.
    """
    divergencias: list = json.loads(divergencias_json)
    fornecedores_novos: list = json.loads(fornecedores_novos_json)

    divergencias_fmt = "\n".join(f"  • {d}" for d in divergencias) if divergencias else "  • Divergência identificada"
    assunto = f"[CONFORMIDADE — APROVAÇÃO NECESSÁRIA] Divergência detectada — {empresa_nome} / {pedido_id}"

    valor_linha = (
        f"R$ {valor_total_atual:,.2f} (+{variacao_percentual:.1f}% acima da média R$ {media_historica_mensal:,.2f})"
        if variacao_percentual > 0
        else f"R$ {valor_total_atual:,.2f}"
    )

    loc_linha = (
        f"⚠️ NÃO INFORMADA"
        if not localizacao_atual or localizacao_atual == "NÃO INFORMADA"
        else localizacao_atual
    )

    fornecedores_bloco = ""
    if fornecedores_novos:
        fornecedores_bloco = (
            f"\n  Fornecedor(es) NÃO encontrado(s) no histórico:\n"
            + "\n".join(f"    ⚠️ {f}" for f in fornecedores_novos)
        )

    def _email(nome: str, email: str, cargo: str) -> str:
        return f"""\
┌─────────────────────────────────────────────────────────────────┐
  SOLICITAÇÃO DE APROVAÇÃO — {nome.upper()}
  Para: {email}
├─────────────────────────────────────────────────────────────────┤
  Assunto: {assunto}

  Prezado(a) {nome},

  O sistema de Conformidade de Compras identificou divergências na
  transação abaixo que requerem sua aprovação formal:

    • Empresa    : {empresa_nome}
    • Referência : {pedido_id}
    • Valor      : {valor_linha}
    • Localização: {loc_linha}{fornecedores_bloco}

  Divergências identificadas:
{divergencias_fmt.replace('  •', '    -')}

  Por favor, responda a este e-mail com:
    ✅ APROVADO — informe a justificativa para prosseguir.
    ❌ REJEITADO — a ordem de compra será cancelada automaticamente.

  Prazo para resposta: 48 horas a partir do recebimento deste e-mail.

  Atenciosamente,
  Sistema de Conformidade de Compras — Agente de Conformidade VF
└─────────────────────────────────────────────────────────────────┘"""

    email_1 = _email(nome_aprovador_1, email_aprovador_1, cargo_aprovador_1)
    email_2 = _email(nome_aprovador_2, email_aprovador_2, cargo_aprovador_2)

    relatorio = f"""
SOLICITAÇÃO DE APROVAÇÃO ENVIADA
═══════════════════════════════════════════════════════════════
EMPRESA        : {empresa_nome}
PEDIDO/REF.    : {pedido_id}
VALOR ATUAL    : R$ {valor_total_atual:,.2f}
MÉDIA HISTÓRICA: R$ {media_historica_mensal:,.2f}
VARIAÇÃO       : {variacao_percentual:.1f}%
LOCALIZAÇÃO    : {loc_linha}

DIVERGÊNCIAS QUE MOTIVARAM O ENVIO:
{divergencias_fmt}

CONTATOS ACIONADOS:
- Contato 1: {nome_aprovador_1} ({cargo_aprovador_1})
  E-mail: {email_aprovador_1} | Tel: {telefone_aprovador_1}
  Status: Pendente de Resposta

- Contato 2: {nome_aprovador_2} ({cargo_aprovador_2})
  E-mail: {email_aprovador_2} | Tel: {telefone_aprovador_2}
  Status: Pendente de Resposta

─────────────────────────────────────────────────────────────────────
MODELOS DE E-MAIL GERADOS PARA ENVIO
─────────────────────────────────────────────────────────────────────

{email_1}

{email_2}
""".strip()

    return relatorio

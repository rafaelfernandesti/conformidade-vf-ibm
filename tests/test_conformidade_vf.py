# -*- coding: utf-8 -*-
"""
Testes completos para as ferramentas do agente_conformidade_VF.

Cobertura:
  verificar_conformidade_transacao
    - TC01  Transação em conformidade total (sem divergências)
    - TC02  Valor > 15% acima da média (único critério disparado)
    - TC03  Valor exatamente em 15% (não deve disparar — limiar é ESTRITAMENTE >)
    - TC04  Valor < 15% (não deve disparar)
    - TC05  Fornecedor novo (único critério disparado)
    - TC06  Localização ausente/vazia (único critério disparado)
    - TC07  Localização nova, não vazia (único critério disparado)
    - TC08  Todos os 3 critérios disparados simultaneamente
    - TC09  Histórico de fornecedores vazio → nenhum fornecedor é "novo"
    - TC10  Histórico de localizações vazio + localização informada → nova
    - TC11  Media histórica = 0 (sem divisão por zero)
    - TC12  JSON malformado no fornecedores_atuais_json → deve lançar JSONDecodeError
    - TC13  JSON malformado no localizacoes_historicas_json → deve lançar JSONDecodeError
    - TC14  Comparação case-insensitive de fornecedores
    - TC15  Comparação case-insensitive de localizações
    - TC16  Valor negativo não dispara critério 1

  enviar_solicitacao_aprovacao_conformidade
    - TE01  Saída contém nome dos 2 aprovadores
    - TE02  Saída contém os 2 e-mails dos aprovadores
    - TE03  Saída contém as divergências listadas
    - TE04  Saída contém o assunto do e-mail com empresa e pedido
    - TE05  Sem variação (variacao_percentual = 0) → sem linha de variação
    - TE06  Com variação > 0 → linha de variação aparece
    - TE07  Com fornecedores novos → bloco de fornecedores aparece no e-mail
    - TE08  Sem fornecedores novos (lista vazia) → bloco não aparece
    - TE09  Localização NÃO INFORMADA → ⚠️ aparece no e-mail
    - TE10  Localização informada → aparece sem ⚠️
    - TE11  JSON malformado em divergencias_json → deve lançar JSONDecodeError
    - TE12  JSON malformado em fornecedores_novos_json → deve lançar JSONDecodeError
    - TE13  Saída contém "Pendente de Resposta" para ambos os contatos
    - TE14  Saída contém os telefones dos 2 aprovadores
"""

import json
import sys
import os
import traceback
import io

# Força stdout/stderr UTF-8 no Windows para suportar caracteres Unicode
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

# ---------------------------------------------------------------------------
# Importa as funções diretamente (sem o decorator @tool do WXO)
# ---------------------------------------------------------------------------
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Patch mínimo do decorator @tool para não exigir o SDK instalado
import types

_fake_mod = types.ModuleType("ibm_watsonx_orchestrate")
_fake_agent = types.ModuleType("ibm_watsonx_orchestrate.agent_builder")
_fake_tools = types.ModuleType("ibm_watsonx_orchestrate.agent_builder.tools")
_fake_tools.tool = lambda f: f  # decorator vira no-op
sys.modules.setdefault("ibm_watsonx_orchestrate", _fake_mod)
sys.modules.setdefault("ibm_watsonx_orchestrate.agent_builder", _fake_agent)
sys.modules.setdefault("ibm_watsonx_orchestrate.agent_builder.tools", _fake_tools)

from tools.conformidade_vf_tools import (  # noqa: E402
    verificar_conformidade_transacao,
    enviar_solicitacao_aprovacao_conformidade,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

CONTATOS = dict(
    nome_aprovador_1="Ana Lima",
    email_aprovador_1="ana.lima@empresa.com",
    cargo_aprovador_1="Financeiro",
    telefone_aprovador_1="(11) 99999-1111",
    nome_aprovador_2="Carlos Souza",
    email_aprovador_2="carlos.souza@empresa.com",
    cargo_aprovador_2="Gerência",
    telefone_aprovador_2="(11) 99999-2222",
)


def _verif(
    valor_atual=10_000.0,
    media=10_000.0,
    fornecedores_atuais=None,
    fornecedores_hist=None,
    localizacao="São Paulo, SP",
    localizacoes_hist=None,
):
    """Wrapper conveniente para verificar_conformidade_transacao."""
    if fornecedores_atuais is None:
        fornecedores_atuais = ["Fornecedor A"]
    if fornecedores_hist is None:
        fornecedores_hist = ["Fornecedor A"]
    if localizacoes_hist is None:
        localizacoes_hist = ["São Paulo, SP"]
    return json.loads(verificar_conformidade_transacao(
        empresa_nome="Empresa Teste",
        empresa_id="EMP-TST",
        pedido_id="OUT/2026",
        valor_total_atual=valor_atual,
        media_historica_mensal=media,
        fornecedores_atuais_json=json.dumps(fornecedores_atuais),
        fornecedores_historicos_json=json.dumps(fornecedores_hist),
        localizacao_atual=localizacao,
        localizacoes_historicas_json=json.dumps(localizacoes_hist),
    ))


def _enviar(
    valor=12_000.0,
    media=10_000.0,
    variacao=20.0,
    fornecedores_novos=None,
    localizacao="São Paulo, SP",
    divergencias=None,
):
    """Wrapper conveniente para enviar_solicitacao_aprovacao_conformidade."""
    if fornecedores_novos is None:
        fornecedores_novos = []
    if divergencias is None:
        divergencias = ["Valor total 20% acima da média"]
    return enviar_solicitacao_aprovacao_conformidade(
        empresa_nome="Empresa Teste",
        pedido_id="OUT/2026",
        valor_total_atual=valor,
        media_historica_mensal=media,
        variacao_percentual=variacao,
        fornecedores_novos_json=json.dumps(fornecedores_novos),
        localizacao_atual=localizacao,
        divergencias_json=json.dumps(divergencias),
        **CONTATOS,
    )


# ---------------------------------------------------------------------------
# Infraestrutura de teste simples
# ---------------------------------------------------------------------------

_RESULTS = []


def run_test(name, fn):
    try:
        fn()
        _RESULTS.append(("PASS", name, None))
        print(f"  ✅ PASS  {name}")
    except AssertionError as exc:
        _RESULTS.append(("FAIL", name, str(exc)))
        print(f"  ❌ FAIL  {name}")
        print(f"          AssertionError: {exc}")
    except Exception as exc:
        _RESULTS.append(("ERROR", name, traceback.format_exc()))
        print(f"  💥 ERROR {name}")
        print(f"          {type(exc).__name__}: {exc}")


# ===========================================================================
# TESTES — verificar_conformidade_transacao
# ===========================================================================

print("\n══════════════════════════════════════════════════════════")
print("  verificar_conformidade_transacao")
print("══════════════════════════════════════════════════════════")


def tc01():
    """TC01 — Transação totalmente em conformidade."""
    r = _verif(valor_atual=10_000.0, media=10_000.0)
    assert r["requer_aprovacao"] is False, f"requer_aprovacao deve ser False, got {r['requer_aprovacao']}"
    assert r["divergencias"] == [], f"divergencias deve ser [], got {r['divergencias']}"
    assert r["tipos_divergencia"]["valor_atipico"] is False
    assert r["tipos_divergencia"]["fornecedor_novo"] is False
    assert r["tipos_divergencia"]["localizacao_nova_ou_ausente"] is False


run_test("TC01 – Conformidade total (sem divergências)", tc01)


def tc02():
    """TC02 — Valor 20% acima da média → dispara."""
    r = _verif(valor_atual=12_000.0, media=10_000.0)
    assert r["requer_aprovacao"] is True
    assert r["tipos_divergencia"]["valor_atipico"] is True
    assert r["variacao_percentual"] == 20.0, f"variacao_percentual esperada 20.0, got {r['variacao_percentual']}"
    assert any("20.0%" in d for d in r["divergencias"]), f"divergência de valor não encontrada: {r['divergencias']}"


run_test("TC02 – Valor 20% acima da média (dispara)", tc02)


def tc03():
    """TC03 — Valor exatamente 15% acima → NÃO deve disparar (limiar é ESTRITO >)."""
    r = _verif(valor_atual=11_500.0, media=10_000.0)
    assert r["tipos_divergencia"]["valor_atipico"] is False, \
        f"15.0% exato não deve disparar, got valor_atipico={r['tipos_divergencia']['valor_atipico']}"
    # 15.0% exato: sem divergência de valor
    valor_divs = [d for d in r["divergencias"] if "acima" in d.lower()]
    assert valor_divs == [], f"Não deve haver divergência de valor em exatamente 15%: {valor_divs}"


run_test("TC03 – Valor exatamente 15% (NÃO dispara — limiar estrito)", tc03)


def tc04():
    """TC04 — Valor 10% acima → não dispara."""
    r = _verif(valor_atual=11_000.0, media=10_000.0)
    assert r["tipos_divergencia"]["valor_atipico"] is False
    assert r["requer_aprovacao"] is False


run_test("TC04 – Valor 10% acima da média (NÃO dispara)", tc04)


def tc05():
    """TC05 — Fornecedor novo → dispara."""
    r = _verif(
        fornecedores_atuais=["Fornecedor Novo"],
        fornecedores_hist=["Fornecedor A", "Fornecedor B"],
    )
    assert r["requer_aprovacao"] is True
    assert r["tipos_divergencia"]["fornecedor_novo"] is True
    assert "Fornecedor Novo" in r["fornecedores_novos"]


run_test("TC05 – Fornecedor novo (dispara)", tc05)


def tc06():
    """TC06 — Localização ausente/vazia → dispara."""
    r = _verif(localizacao="", localizacoes_hist=["São Paulo, SP"])
    assert r["requer_aprovacao"] is True
    assert r["tipos_divergencia"]["localizacao_nova_ou_ausente"] is True
    assert r["localizacao_atual"] == "NÃO INFORMADA"
    assert any("não informada" in d.lower() for d in r["divergencias"])


run_test("TC06 – Localização vazia/ausente (dispara)", tc06)


def tc07():
    """TC07 — Localização informada mas nova → dispara."""
    r = _verif(localizacao="Rio de Janeiro, RJ", localizacoes_hist=["São Paulo, SP"])
    assert r["requer_aprovacao"] is True
    assert r["tipos_divergencia"]["localizacao_nova_ou_ausente"] is True
    assert "Rio de Janeiro, RJ" in r["localizacao_atual"]
    assert any("não se encontra" in d.lower() for d in r["divergencias"])


run_test("TC07 – Localização nova (não vazia, mas não no histórico)", tc07)


def tc08():
    """TC08 — Todos os 3 critérios disparados ao mesmo tempo."""
    r = _verif(
        valor_atual=12_000.0,
        media=10_000.0,
        fornecedores_atuais=["Fornecedor X"],
        fornecedores_hist=["Fornecedor A"],
        localizacao="",
        localizacoes_hist=["São Paulo, SP"],
    )
    assert r["requer_aprovacao"] is True
    assert r["tipos_divergencia"]["valor_atipico"] is True
    assert r["tipos_divergencia"]["fornecedor_novo"] is True
    assert r["tipos_divergencia"]["localizacao_nova_ou_ausente"] is True
    assert len(r["divergencias"]) == 3, f"Esperadas 3 divergências, got {len(r['divergencias'])}: {r['divergencias']}"


run_test("TC08 – Todos os 3 critérios disparados", tc08)


def tc09():
    """TC09 — Histórico de fornecedores vazio → nenhum fornecedor é tratado como novo."""
    r = _verif(
        fornecedores_atuais=["Qualquer Fornecedor"],
        fornecedores_hist=[],
    )
    assert r["tipos_divergencia"]["fornecedor_novo"] is False, \
        f"Com histórico vazio, nenhum fornecedor deve ser 'novo', got {r['tipos_divergencia']}"
    assert r["fornecedores_novos"] == []


run_test("TC09 – Histórico vazio de fornecedores (sem falso positivo)", tc09)


def tc10():
    """TC10 — Histórico de localizações vazio + localização informada → nova."""
    r = _verif(localizacao="Curitiba, PR", localizacoes_hist=[])
    assert r["tipos_divergencia"]["localizacao_nova_ou_ausente"] is True
    assert r["requer_aprovacao"] is True


run_test("TC10 – Histórico vazio de localizações + loc informada (dispara)", tc10)


def tc11():
    """TC11 — Media histórica = 0 → sem divisão por zero, sem falso positivo de valor."""
    r = _verif(valor_atual=10_000.0, media=0.0)
    assert r["variacao_percentual"] == 0.0
    assert r["tipos_divergencia"]["valor_atipico"] is False


run_test("TC11 – Media histórica = 0 (sem divisão por zero)", tc11)


def tc12():
    """TC12 — JSON malformado em fornecedores_atuais_json → JSONDecodeError."""
    try:
        verificar_conformidade_transacao(
            empresa_nome="X", empresa_id="EMP-001", pedido_id="P1",
            valor_total_atual=1000.0, media_historica_mensal=900.0,
            fornecedores_atuais_json="INVALID JSON",
            fornecedores_historicos_json="[]",
            localizacao_atual="SP",
            localizacoes_historicas_json='["SP"]',
        )
        assert False, "Deveria ter lançado JSONDecodeError"
    except json.JSONDecodeError:
        pass  # esperado


run_test("TC12 – JSON malformado em fornecedores_atuais_json (JSONDecodeError)", tc12)


def tc13():
    """TC13 — JSON malformado em localizacoes_historicas_json → JSONDecodeError."""
    try:
        verificar_conformidade_transacao(
            empresa_nome="X", empresa_id="EMP-001", pedido_id="P1",
            valor_total_atual=1000.0, media_historica_mensal=900.0,
            fornecedores_atuais_json='["A"]',
            fornecedores_historicos_json='["A"]',
            localizacao_atual="SP",
            localizacoes_historicas_json="NOT JSON AT ALL",
        )
        assert False, "Deveria ter lançado JSONDecodeError"
    except json.JSONDecodeError:
        pass


run_test("TC13 – JSON malformado em localizacoes_historicas_json (JSONDecodeError)", tc13)


def tc14():
    """TC14 — Comparação de fornecedores é case-insensitive."""
    r = _verif(
        fornecedores_atuais=["AMAZON WEB SERVICES"],
        fornecedores_hist=["amazon web services"],
    )
    assert r["tipos_divergencia"]["fornecedor_novo"] is False, \
        f"Comparação deve ser case-insensitive, got {r['fornecedores_novos']}"
    assert r["fornecedores_novos"] == []


run_test("TC14 – Case-insensitive em fornecedores", tc14)


def tc15():
    """TC15 — Comparação de localizações é case-insensitive."""
    r = _verif(localizacao="SÃO PAULO, SP", localizacoes_hist=["são paulo, sp"])
    assert r["tipos_divergencia"]["localizacao_nova_ou_ausente"] is False, \
        f"Comparação de localização deve ser case-insensitive, got {r['tipos_divergencia']}"


run_test("TC15 – Case-insensitive em localizações", tc15)


def tc16():
    """TC16 — Valor negativo não dispara critério de valor (não > 15% acima da média)."""
    r = _verif(valor_atual=-1_000.0, media=10_000.0)
    assert r["tipos_divergencia"]["valor_atipico"] is False, \
        f"Valor negativo não deve ser > 15% acima da média, got {r['tipos_divergencia']}"


run_test("TC16 – Valor negativo não dispara critério 1", tc16)


# ===========================================================================
# TESTES — enviar_solicitacao_aprovacao_conformidade
# ===========================================================================

print("\n══════════════════════════════════════════════════════════")
print("  enviar_solicitacao_aprovacao_conformidade")
print("══════════════════════════════════════════════════════════")


def te01():
    """TE01 — Saída contém nome dos 2 aprovadores."""
    saida = _enviar()
    assert "Ana Lima" in saida, "Nome aprovador 1 não encontrado na saída"
    assert "Carlos Souza" in saida, "Nome aprovador 2 não encontrado na saída"


run_test("TE01 – Nomes dos 2 aprovadores presentes", te01)


def te02():
    """TE02 — Saída contém e-mails dos 2 aprovadores."""
    saida = _enviar()
    assert "ana.lima@empresa.com" in saida
    assert "carlos.souza@empresa.com" in saida


run_test("TE02 – E-mails dos 2 aprovadores presentes", te02)


def te03():
    """TE03 — Saída contém as divergências listadas."""
    saida = _enviar(divergencias=["Critério A violado", "Critério B violado"])
    assert "Critério A violado" in saida
    assert "Critério B violado" in saida


run_test("TE03 – Divergências listadas na saída", te03)


def te04():
    """TE04 — Assunto do e-mail contém empresa e pedido."""
    saida = _enviar()
    assert "Empresa Teste" in saida
    assert "OUT/2026" in saida


run_test("TE04 – Assunto contém empresa e pedido", te04)


def te05():
    """TE05 — Sem variação (variacao_percentual=0) → linha de variação não aparece."""
    saida = _enviar(variacao=0.0, valor=10_000.0, media=10_000.0)
    # Não deve conter "% acima da média" com variação
    assert "+0.0%" not in saida, f"Com variação 0% não deve aparecer '+0.0%': {saida[:300]}"


run_test("TE05 – Variação zero → sem linha de % na saída", te05)


def te06():
    """TE06 — Com variação > 0 → linha de variação aparece."""
    saida = _enviar(variacao=20.0, valor=12_000.0, media=10_000.0)
    assert "+20.0%" in saida, f"Deve aparecer '+20.0%' na saída: {saida[:400]}"


run_test("TE06 – Variação > 0 → linha de variação presente", te06)


def te07():
    """TE07 — Com fornecedores novos → bloco de fornecedores aparece."""
    saida = _enviar(fornecedores_novos=["Fornecedor X", "Fornecedor Y"])
    assert "Fornecedor X" in saida
    assert "Fornecedor Y" in saida
    assert "NÃO encontrado" in saida


run_test("TE07 – Bloco de fornecedores novos presente na saída", te07)


def te08():
    """TE08 — Sem fornecedores novos (lista vazia) → bloco não aparece."""
    saida = _enviar(fornecedores_novos=[])
    assert "NÃO encontrado" not in saida, \
        f"Com lista vazia, bloco de fornecedores não deve aparecer: {saida[:400]}"


run_test("TE08 – Sem fornecedores novos → bloco não aparece", te08)


def te09():
    """TE09 — Localização 'NÃO INFORMADA' → ⚠️ NÃO INFORMADA aparece."""
    saida = _enviar(localizacao="NÃO INFORMADA")
    assert "NÃO INFORMADA" in saida


run_test("TE09 – Localização NÃO INFORMADA → ⚠️ NÃO INFORMADA na saída", te09)


def te10():
    """TE10 — Localização informada → aparece normalmente."""
    saida = _enviar(localizacao="Belo Horizonte, MG")
    assert "Belo Horizonte, MG" in saida
    # Não deve aparecer ⚠️ NÃO INFORMADA para localização
    lines_with_loc = [l for l in saida.splitlines() if "Localização" in l or "Localizacao" in l]
    for line in lines_with_loc:
        assert "NÃO INFORMADA" not in line, \
            f"Com localização informada, não deve aparecer NÃO INFORMADA: {line}"


run_test("TE10 – Localização informada → aparece sem NÃO INFORMADA", te10)


def te11():
    """TE11 — JSON malformado em divergencias_json → JSONDecodeError."""
    try:
        enviar_solicitacao_aprovacao_conformidade(
            empresa_nome="X", pedido_id="P1",
            valor_total_atual=1000.0, media_historica_mensal=900.0,
            variacao_percentual=11.1,
            fornecedores_novos_json="[]",
            localizacao_atual="SP",
            divergencias_json="NOT VALID JSON",
            **CONTATOS,
        )
        assert False, "Deveria ter lançado JSONDecodeError"
    except json.JSONDecodeError:
        pass


run_test("TE11 – JSON malformado em divergencias_json (JSONDecodeError)", te11)


def te12():
    """TE12 — JSON malformado em fornecedores_novos_json → JSONDecodeError."""
    try:
        enviar_solicitacao_aprovacao_conformidade(
            empresa_nome="X", pedido_id="P1",
            valor_total_atual=1000.0, media_historica_mensal=900.0,
            variacao_percentual=11.1,
            fornecedores_novos_json="BAD JSON",
            localizacao_atual="SP",
            divergencias_json='["divergência"]',
            **CONTATOS,
        )
        assert False, "Deveria ter lançado JSONDecodeError"
    except json.JSONDecodeError:
        pass


run_test("TE12 – JSON malformado em fornecedores_novos_json (JSONDecodeError)", te12)


def te13():
    """TE13 — Saída contém 'Pendente de Resposta' para ambos os contatos."""
    saida = _enviar()
    count = saida.count("Pendente de Resposta")
    assert count == 2, f"Esperado 2× 'Pendente de Resposta', encontrado {count}"


run_test("TE13 – 'Pendente de Resposta' presente 2× na saída", te13)


def te14():
    """TE14 — Saída contém os telefones dos 2 aprovadores."""
    saida = _enviar()
    assert "(11) 99999-1111" in saida
    assert "(11) 99999-2222" in saida


run_test("TE14 – Telefones dos 2 aprovadores presentes", te14)


# ===========================================================================
# Sumário final
# ===========================================================================

print("\n══════════════════════════════════════════════════════════")
total = len(_RESULTS)
passed = sum(1 for r in _RESULTS if r[0] == "PASS")
failed = sum(1 for r in _RESULTS if r[0] == "FAIL")
errors = sum(1 for r in _RESULTS if r[0] == "ERROR")

print(f"  Total : {total}")
print(f"  ✅ Pass : {passed}")
print(f"  ❌ Fail : {failed}")
print(f"  💥 Error: {errors}")

if failed > 0 or errors > 0:
    print("\n  Falhas e erros detalhados:")
    for status, name, detail in _RESULTS:
        if status in ("FAIL", "ERROR"):
            print(f"\n  [{status}] {name}")
            print(f"  {detail}")

print("══════════════════════════════════════════════════════════\n")

# Código de saída não-zero se houver falhas
if failed > 0 or errors > 0:
    sys.exit(1)

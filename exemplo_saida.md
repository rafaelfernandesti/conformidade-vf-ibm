# Exemplos de Saída — agente_conformidade_VF

Saídas reais geradas pela execução direta das ferramentas do agente com dados da
knowledge base (`empresas_corporativas.json`).

---

## Cenário A — Fornecedor novo (1 critério)

**Empresa:** Eta Energia Solar e Sustentabilidade (EMP-007)  
**Mês analisado:** Outubro/2026  
**Valor total:** R$ 52.400,00 | **Média histórica:** R$ 48.940,00 | **Variação:** +7,07%

**Critérios verificados:**
- ❌ Valor > 15%: NÃO (+7,07% — abaixo do limiar)
- ✅ Fornecedor novo: SIM — *Phoenix Contact* nunca apareceu nos meses anteriores
- ❌ Localização nova: NÃO — *Brasília, DF* está no histórico

### Saída de `verificar_conformidade_transacao`

```json
{
  "requer_aprovacao": true,
  "empresa_nome": "Eta Energia Solar e Sustentabilidade",
  "empresa_id": "EMP-007",
  "pedido_id": "Outubro/2026",
  "valor_total_atual": 52400.0,
  "media_historica_mensal": 48940.0,
  "variacao_percentual": 7.07,
  "fornecedores_novos": ["Phoenix Contact"],
  "localizacao_atual": "Brasília, DF",
  "localizacao_nova": false,
  "divergencias": [
    "Fornecedor(es) não encontrado(s) no histórico de compras: Phoenix Contact"
  ],
  "tipos_divergencia": {
    "valor_atipico": false,
    "fornecedor_novo": true,
    "localizacao_nova_ou_ausente": false
  }
}
```

### Bloco de resposta final do agente

```
STATUS DE CONFORMIDADE: Requer Aprovação
EMPRESA: Eta Energia Solar e Sustentabilidade
PEDIDO/REFERÊNCIA: Outubro/2026

CRITÉRIOS VERIFICADOS:
  • Valor total > 15% acima da média: NÃO (+7.07%)
  • Fornecedor novo (não encontrado no histórico): SIM → Phoenix Contact
  • Localização nova (não encontrada no histórico): NÃO

CONTATOS ACIONADOS PARA APROVAÇÃO:
- Contato 1: Tatiana Farias (Tesouraria)
  E-mail: tatiana.farias@etasolar.com | Tel: (61) 98444-1212
  Status: Pendente de Resposta
- Contato 2: Marcelo H. Diniz (Gerente de Projetos de Engenharia)
  E-mail: marcelo.diniz@etasolar.com | Tel: (61) 98444-3434
  Status: Pendente de Resposta
```

---

## Cenário B — Todos os 3 critérios disparados

**Empresa:** Eta Energia Solar e Sustentabilidade (EMP-007)  
**Mês analisado:** Outubro/2026 (versão simulada com localização e valor alterados)  
**Valor total:** R$ 57.000,00 | **Média histórica:** R$ 48.940,00 | **Variação:** +16,47%

**Critérios verificados:**
- ✅ Valor > 15%: SIM (+16,47%)
- ✅ Fornecedor novo: SIM — *Phoenix Contact*
- ✅ Localização nova: SIM — *Goiânia, GO* (histórico só tem *Brasília, DF*)

### Saída de `enviar_solicitacao_aprovacao_conformidade`

```
SOLICITAÇÃO DE APROVAÇÃO ENVIADA
═══════════════════════════════════════════════════════════════
EMPRESA        : Eta Energia Solar e Sustentabilidade
PEDIDO/REF.    : Outubro/2026
VALOR ATUAL    : R$ 57,000.00
MÉDIA HISTÓRICA: R$ 48,940.00
VARIAÇÃO       : 16.5%
LOCALIZAÇÃO    : Goiânia, GO

DIVERGÊNCIAS QUE MOTIVARAM O ENVIO:
  • Valor total R$57,000.00 está 16.5% acima da média histórica R$48,940.00 (limite: 15%)
  • Fornecedor(es) não encontrado(s) no histórico de compras: Phoenix Contact
  • Localização 'Goiânia, GO' não se encontra no histórico de compras desta empresa

CONTATOS ACIONADOS:
- Contato 1: Tatiana Farias (Tesouraria)
  E-mail: tatiana.farias@etasolar.com | Tel: (61) 98444-1212
  Status: Pendente de Resposta

- Contato 2: Marcelo H. Diniz (Gerente de Projetos de Engenharia)
  E-mail: marcelo.diniz@etasolar.com | Tel: (61) 98444-3434
  Status: Pendente de Resposta

─────────────────────────────────────────────────────────────────────
MODELOS DE E-MAIL GERADOS PARA ENVIO
─────────────────────────────────────────────────────────────────────

┌─────────────────────────────────────────────────────────────────┐
  SOLICITAÇÃO DE APROVAÇÃO — TATIANA FARIAS
  Para: tatiana.farias@etasolar.com
├─────────────────────────────────────────────────────────────────┤
  Assunto: [CONFORMIDADE — APROVAÇÃO NECESSÁRIA] Divergência detectada —
           Eta Energia Solar e Sustentabilidade / Outubro/2026

  Prezado(a) Tatiana Farias,

  O sistema de Conformidade de Compras identificou divergências na
  transação abaixo que requerem sua aprovação formal:

    • Empresa    : Eta Energia Solar e Sustentabilidade
    • Referência : Outubro/2026
    • Valor      : R$ 57,000.00 (+16.5% acima da média R$ 48,940.00)
    • Localização: Goiânia, GO
  Fornecedor(es) NÃO encontrado(s) no histórico:
    ⚠️ Phoenix Contact

  Divergências identificadas:
    - Valor total R$57,000.00 está 16.5% acima da média histórica R$48,940.00 (limite: 15%)
    - Fornecedor(es) não encontrado(s) no histórico de compras: Phoenix Contact
    - Localização 'Goiânia, GO' não se encontra no histórico de compras desta empresa

  Por favor, responda a este e-mail com:
    ✅ APROVADO — informe a justificativa para prosseguir.
    ❌ REJEITADO — a ordem de compra será cancelada automaticamente.

  Prazo para resposta: 48 horas a partir do recebimento deste e-mail.

  Atenciosamente,
  Sistema de Conformidade de Compras — Agente de Conformidade VF
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
  SOLICITAÇÃO DE APROVAÇÃO — MARCELO H. DINIZ
  Para: marcelo.diniz@etasolar.com
├─────────────────────────────────────────────────────────────────┤
  Assunto: [CONFORMIDADE — APROVAÇÃO NECESSÁRIA] Divergência detectada —
           Eta Energia Solar e Sustentabilidade / Outubro/2026

  Prezado(a) Marcelo H. Diniz,

  O sistema de Conformidade de Compras identificou divergências na
  transação abaixo que requerem sua aprovação formal:

    • Empresa    : Eta Energia Solar e Sustentabilidade
    • Referência : Outubro/2026
    • Valor      : R$ 57,000.00 (+16.5% acima da média R$ 48,940.00)
    • Localização: Goiânia, GO
  Fornecedor(es) NÃO encontrado(s) no histórico:
    ⚠️ Phoenix Contact

  Divergências identificadas:
    - Valor total R$57,000.00 está 16.5% acima da média histórica R$48,940.00 (limite: 15%)
    - Fornecedor(es) não encontrado(s) no histórico de compras: Phoenix Contact
    - Localização 'Goiânia, GO' não se encontra no histórico de compras desta empresa

  Por favor, responda a este e-mail com:
    ✅ APROVADO — informe a justificativa para prosseguir.
    ❌ REJEITADO — a ordem de compra será cancelada automaticamente.

  Prazo para resposta: 48 horas a partir do recebimento deste e-mail.

  Atenciosamente,
  Sistema de Conformidade de Compras — Agente de Conformidade VF
└─────────────────────────────────────────────────────────────────┘
```

---

## Cenário C — Transação em conformidade (sem aprovação)

**Empresa:** Alpha Tech Soluções S.A. (EMP-001)  
**Mês analisado:** Outubro/2026  
**Valor total:** R$ 4.530,00 | **Média histórica:** ~R$ 4.698,00 | **Variação:** -3,57%

**Critérios verificados:**
- ❌ Valor > 15%: NÃO (valor abaixo da média)
- ❌ Fornecedor novo: NÃO — *Fast Shop* foi fornecedor anteriormente / principais são históricos
- ❌ Localização nova: NÃO — *São Paulo, SP* está no histórico

### Bloco de resposta final do agente

```
STATUS DE CONFORMIDADE: Em Conformidade
EMPRESA: Alpha Tech Soluções S.A.
PEDIDO/REFERÊNCIA: Outubro/2026

CRITÉRIOS VERIFICADOS:
  • Valor total > 15% acima da média: NÃO (-3.57%)
  • Fornecedor novo (não encontrado no histórico): NÃO
  • Localização nova (não encontrada no histórico): NÃO

Nenhuma divergência detectada. A transação está em conformidade e
não requer aprovação adicional.
```

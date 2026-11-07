# Declaração do Problema e da Solução

## O Problema

Gestores administrativos e analistas de compras em empresas de médio porte enfrentam um desafio crítico: identificar manualmente transações suspeitas ou fora do padrão em volumes crescentes de ordens de compra mensais. Em uma empresa com 8 unidades corporativas processando dezenas de pedidos por mês, um analista leva em média **4 a 6 horas por ciclo mensal** apenas para comparar valores, verificar fornecedores e checar localizações contra o histórico — trabalho repetitivo, propenso a erros e de baixo valor agregado.

O custo dessa ineficiência é alto: transações fraudulentas passam despercebidas, fornecedores não homologados entram na cadeia de suprimentos sem aprovação formal, e o processo de dupla aprovação — exigido por políticas internas de compliance — frequentemente atrasa dias por falta de acionamento ágil dos responsáveis.

**Stakeholder principal:** Ana Paula, Analista de Conformidade de Compras, responsável por auditar mensalmente as transações de 8 empresas do grupo e acionar os 2 aprovadores designados por empresa sempre que detectar irregularidades. Hoje ela faz isso manualmente, em planilhas, consultando históricos em sistemas separados.

## A Solução

O **Agente de Conformidade de Compras VF** é um agente de IA nativo do IBM watsonx Orchestrate que automatiza completamente o ciclo de auditoria de compras. A solução verifica 3 critérios de conformidade em cada transação:

1. **Valor atípico:** o valor total do mês é mais de 15% acima da média histórica da empresa
2. **Fornecedor novo:** o fornecedor não aparece no histórico de meses anteriores da empresa
3. **Localização nova ou ausente:** a localização da transação não consta no histórico

Quando qualquer critério é violado, o agente aciona automaticamente os **2 contatos aprovadores** cadastrados para aquela empresa na knowledge base, gerando e-mails formais de solicitação de aprovação com prazo de 48 horas.

A interface de interação é uma aplicação web desenvolvida em **Streamlit**, onde Ana Paula pode fazer perguntas em linguagem natural ("Verifique Outubro/2026 da EMP-007") e receber um relatório visual estruturado com status de conformidade, critérios avaliados, contatos acionados e modelos de e-mail prontos para envio.

## Por que é criativo e único

A solução combina **RAG (Retrieval-Augmented Generation)** com lógica de negócio determinística: o agente não "alucina" regras — ele executa ferramentas Python auditáveis que aplicam os critérios exatos definidos pela política da empresa. Os contatos aprovadores são sempre extraídos da knowledge base, nunca inventados pelo modelo.

O diferencial está na **automação ponta a ponta**: da consulta ao histórico, passando pela detecção da anomalia, até a geração dos e-mails de aprovação — tudo em uma única interação conversacional que antes consumia horas de trabalho manual.

## Impacto mensurável

| Métrica | Antes | Depois |
|---|---|---|
| Tempo de auditoria mensal (8 empresas) | ~5 horas | ~5 minutos |
| Tempo para acionar aprovadores | 1–2 dias (e-mail manual) | Imediato (automático) |
| Risco de transação irregular não detectada | Alto (revisão manual) | Baixo (100% das transações verificadas) |
| Escalabilidade | Linear (mais empresas = mais horas) | Constante (100 empresas = mesmo tempo) |

A solução foi inteiramente concebida, desenvolvida, depurada e documentada com o auxílio do **IBM Bob** — assistente de IA da IBM utilizado como copiloto de engenharia ao longo de todo o ciclo de desenvolvimento.

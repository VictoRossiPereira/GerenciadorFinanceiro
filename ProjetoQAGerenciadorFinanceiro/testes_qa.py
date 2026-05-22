#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Suite de Testes de QA — Gerenciador Financeiro
Execução: python testes_qa.py
"""

import json
import os
import sys
import copy
from datetime import date, timedelta
from io import StringIO
import contextlib

# ─── Importa o sistema ────────────────────────────────────────────────────────
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gerenciador import (
    carregar_dados, salvar_dados, parse_valor, parse_data,
    formatar_moeda, verificar_alertas, ARQUIVO_DADOS
)

# ─── Cores para terminal ──────────────────────────────────────────────────────
class C:
    RESET   = "\033[0m"
    BOLD    = "\033[1m"
    VERDE   = "\033[92m"
    VERMELHO= "\033[91m"
    AMARELO = "\033[93m"
    AZUL    = "\033[94m"
    CIANO   = "\033[96m"
    MAGENTA = "\033[95m"
    CINZA   = "\033[90m"
    BRANCO  = "\033[97m"

def cor(texto, c_): return f"{c_}{texto}{C.RESET}"

# ─── Infraestrutura dos Testes ────────────────────────────────────────────────
ARQUIVO_BACKUP = "dados_financeiros_backup_qa.json"
resultados = {"total": 0, "passou": 0, "falhou": 0, "erros": []}

def setup():
    """Faz backup dos dados reais antes dos testes."""
    if os.path.exists(ARQUIVO_DADOS):
        with open(ARQUIVO_DADOS, "r", encoding="utf-8") as f:
            with open(ARQUIVO_BACKUP, "w", encoding="utf-8") as b:
                b.write(f.read())

def teardown():
    """Restaura os dados reais após os testes."""
    if os.path.exists(ARQUIVO_BACKUP):
        with open(ARQUIVO_BACKUP, "r", encoding="utf-8") as b:
            with open(ARQUIVO_DADOS, "w", encoding="utf-8") as f:
                f.write(b.read())
        os.remove(ARQUIVO_BACKUP)
    elif os.path.exists(ARQUIVO_DADOS):
        os.remove(ARQUIVO_DADOS)

def dados_limpos():
    """Retorna um estado de dados zerado para testes."""
    return {"transacoes": [], "proximo_id": 1}

def criar_transacao(dados, tipo="despesa", descricao="Teste", valor=100.0,
                    categoria="Outros", dias_vencimento=5, status="pendente",
                    data_pagamento=None):
    venc = (date.today() + timedelta(days=dias_vencimento)).isoformat()
    t = {
        "id": dados["proximo_id"],
        "tipo": tipo,
        "descricao": descricao,
        "valor": valor,
        "categoria": categoria,
        "data_vencimento": venc,
        "data_pagamento": data_pagamento,
        "status": status,
        "data_cadastro": date.today().isoformat()
    }
    dados["transacoes"].append(t)
    dados["proximo_id"] += 1
    return t

def assert_eq(obtido, esperado, mensagem=""):
    if obtido != esperado:
        raise AssertionError(
            f"{mensagem}\n       Esperado: {repr(esperado)}\n       Obtido:   {repr(obtido)}"
        )

def assert_true(condicao, mensagem=""):
    if not condicao:
        raise AssertionError(mensagem)

def assert_false(condicao, mensagem=""):
    if condicao:
        raise AssertionError(mensagem)

def executar_teste(id_teste, nome, objetivo, fn):
    """Executa um caso de teste e exibe o resultado."""
    resultados["total"] += 1
    try:
        fn()
        resultados["passou"] += 1
        status = cor("  PASSOU", C.VERDE + C.BOLD)
        print(f"  [{id_teste}] {status}  {nome}")
    except AssertionError as e:
        resultados["falhou"] += 1
        resultados["erros"].append((id_teste, nome, str(e)))
        status = cor("  FALHOU", C.VERMELHO + C.BOLD)
        print(f"  [{id_teste}] {status}  {nome}")
        print(cor(f"       ↳ {e}", C.AMARELO))
    except Exception as e:
        resultados["falhou"] += 1
        resultados["erros"].append((id_teste, nome, f"EXCEÇÃO: {e}"))
        status = cor("  ERRO  ", C.MAGENTA + C.BOLD)
        print(f"  [{id_teste}] {status}  {nome}")
        print(cor(f"       ↳ EXCEÇÃO: {e}", C.VERMELHO))

def secao(titulo):
    print()
    print(cor("  ══════════════════════════════════════════════════════", C.AZUL))
    print(cor(f"  {titulo}", C.BOLD + C.AZUL))
    print(cor("  ══════════════════════════════════════════════════════", C.AZUL))

# ═══════════════════════════════════════════════════════════════════════════════
#  MÓDULO 1 — CONTAS A PAGAR E A RECEBER
# ═══════════════════════════════════════════════════════════════════════════════

def TC01():
    """Cadastro de conta a pagar com dados válidos."""
    dados = dados_limpos()
    t = criar_transacao(dados, tipo="despesa", descricao="Aluguel", valor=1500.0,
                        categoria="Moradia", dias_vencimento=10, status="pendente")
    salvar_dados(dados)
    recarregado = carregar_dados()
    transacoes = [x for x in recarregado["transacoes"] if x["tipo"] == "despesa"]
    assert_eq(len(transacoes), 1, "Deve haver 1 despesa cadastrada")
    assert_eq(transacoes[0]["descricao"], "Aluguel", "Descrição deve ser 'Aluguel'")
    assert_eq(transacoes[0]["valor"], 1500.0, "Valor deve ser 1500.0")
    assert_eq(transacoes[0]["status"], "pendente", "Status deve ser 'pendente'")

def TC02():
    """Cadastro de conta a receber com dados válidos."""
    dados = dados_limpos()
    t = criar_transacao(dados, tipo="receita", descricao="Salário", valor=5000.0,
                        categoria="Salário", dias_vencimento=5, status="pendente")
    salvar_dados(dados)
    recarregado = carregar_dados()
    receitas = [x for x in recarregado["transacoes"] if x["tipo"] == "receita"]
    assert_eq(len(receitas), 1, "Deve haver 1 receita cadastrada")
    assert_eq(receitas[0]["valor"], 5000.0, "Valor deve ser 5000.0")
    assert_eq(receitas[0]["categoria"], "Salário", "Categoria deve ser 'Salário'")

def TC03():
    """Edição de conta a pagar — alteração de valor e status."""
    dados = dados_limpos()
    criar_transacao(dados, tipo="despesa", descricao="Internet", valor=100.0, status="pendente")
    t = dados["transacoes"][0]
    # Simula edição
    t["valor"] = 120.0
    t["status"] = "pago"
    t["data_pagamento"] = date.today().isoformat()
    salvar_dados(dados)
    recarregado = carregar_dados()
    editado = recarregado["transacoes"][0]
    assert_eq(editado["valor"], 120.0, "Valor editado deve ser 120.0")
    assert_eq(editado["status"], "pago", "Status deve ser 'pago' após edição")
    assert_true(editado["data_pagamento"] is not None, "Data de pagamento deve ser preenchida")

def TC04():
    """Categorização correta de despesa."""
    dados = dados_limpos()
    criar_transacao(dados, tipo="despesa", descricao="Supermercado", valor=300.0,
                    categoria="Alimentação", status="pendente")
    categoria = dados["transacoes"][0]["categoria"]
    assert_eq(categoria, "Alimentação", "Categoria deve ser 'Alimentação'")

def TC05():
    """Categorização correta de receita."""
    dados = dados_limpos()
    criar_transacao(dados, tipo="receita", descricao="Projeto X", valor=2000.0,
                    categoria="Freelance", status="pendente")
    categoria = dados["transacoes"][0]["categoria"]
    assert_eq(categoria, "Freelance", "Categoria deve ser 'Freelance'")

def TC06():
    """Valor inválido não deve ser aceito."""
    assert_true(parse_valor("") is None, "String vazia deve retornar None")
    assert_true(parse_valor("abc") is None, "Texto inválido deve retornar None")
    assert_true(parse_valor("-100") is None, "Valor negativo deve retornar None")
    assert_true(parse_valor("0") is None, "Zero deve retornar None")

def TC07():
    """Valor válido deve ser parseado corretamente."""
    assert_eq(parse_valor("1500,00"), 1500.0, "1500,00 deve virar 1500.0")
    assert_eq(parse_valor("1.500,00"), 1500.0, "1.500,00 deve virar 1500.0")
    assert_eq(parse_valor("R$ 250,50"), 250.5, "R$ 250,50 deve virar 250.5")
    assert_eq(parse_valor("100"), 100.0, "100 deve virar 100.0")

def TC08():
    """Data inválida não deve ser aceita."""
    assert_true(parse_data("99/99/9999") is None, "Data inválida deve retornar None")
    assert_true(parse_data("abc") is None, "Texto inválido deve retornar None")
    assert_true(parse_data("") is None, "String vazia deve retornar None")

def TC09():
    """Data válida deve ser parseada corretamente."""
    d = parse_data("15/06/2025")
    assert_true(d is not None, "Data válida deve ser parseada")
    assert_eq(d.day, 15, "Dia deve ser 15")
    assert_eq(d.month, 6, "Mês deve ser 6")
    assert_eq(d.year, 2025, "Ano deve ser 2025")

def TC10():
    """Múltiplas contas a pagar devem ter IDs únicos."""
    dados = dados_limpos()
    criar_transacao(dados, descricao="Conta 1", valor=100.0)
    criar_transacao(dados, descricao="Conta 2", valor=200.0)
    criar_transacao(dados, descricao="Conta 3", valor=300.0)
    ids = [t["id"] for t in dados["transacoes"]]
    assert_eq(len(ids), len(set(ids)), "Todos os IDs devem ser únicos")

# ═══════════════════════════════════════════════════════════════════════════════
#  MÓDULO 2 — ALERTAS E LEMBRETES
# ═══════════════════════════════════════════════════════════════════════════════

def TC11():
    """Alerta disparado para conta vencida."""
    dados = dados_limpos()
    criar_transacao(dados, tipo="despesa", descricao="Conta Vencida",
                    valor=500.0, dias_vencimento=-3, status="pendente")
    salvar_dados(dados)
    alertas = verificar_alertas(dados)
    tipos = [a[0] for a in alertas]
    assert_true("vencido" in tipos, "Deve haver alerta 'vencido' para conta vencida")

def TC12():
    """Alerta disparado para conta que vence hoje."""
    dados = dados_limpos()
    criar_transacao(dados, tipo="despesa", descricao="Vence Hoje",
                    valor=200.0, dias_vencimento=0, status="pendente")
    salvar_dados(dados)
    alertas = verificar_alertas(dados)
    tipos = [a[0] for a in alertas]
    assert_true("hoje" in tipos, "Deve haver alerta 'hoje' para conta que vence hoje")

def TC13():
    """Alerta disparado para conta que vence em até 3 dias."""
    dados = dados_limpos()
    criar_transacao(dados, tipo="despesa", descricao="Vence Em Breve",
                    valor=150.0, dias_vencimento=2, status="pendente")
    alertas = verificar_alertas(dados)
    tipos = [a[0] for a in alertas]
    assert_true("proximo" in tipos, "Deve haver alerta 'proximo' para conta que vence em 2 dias")

def TC14():
    """Sem alerta para conta vencendo em mais de 3 dias."""
    dados = dados_limpos()
    criar_transacao(dados, tipo="despesa", descricao="Longe",
                    valor=100.0, dias_vencimento=10, status="pendente")
    alertas = verificar_alertas(dados)
    assert_eq(len(alertas), 0, "Não deve haver alertas para conta com vencimento distante")

def TC15():
    """Contas pagas não devem gerar alertas."""
    dados = dados_limpos()
    criar_transacao(dados, tipo="despesa", descricao="Já Paga",
                    valor=100.0, dias_vencimento=-5, status="pago",
                    data_pagamento=date.today().isoformat())
    alertas = verificar_alertas(dados)
    assert_eq(len(alertas), 0, "Conta paga não deve gerar alerta mesmo vencida")

def TC16():
    """Múltiplos alertas para múltiplas contas vencidas."""
    dados = dados_limpos()
    criar_transacao(dados, descricao="V1", valor=100.0, dias_vencimento=-1)
    criar_transacao(dados, descricao="V2", valor=200.0, dias_vencimento=-2)
    criar_transacao(dados, descricao="V3", valor=300.0, dias_vencimento=-3)
    alertas = verificar_alertas(dados)
    assert_eq(len(alertas), 3, "Deve haver 3 alertas para 3 contas vencidas")

def TC17():
    """Alerta de receita pendente (conta a receber vencida)."""
    dados = dados_limpos()
    criar_transacao(dados, tipo="receita", descricao="Receber Vencido",
                    valor=1000.0, dias_vencimento=-1, status="pendente")
    alertas = verificar_alertas(dados)
    assert_eq(len(alertas), 1, "Deve haver alerta para receita vencida")
    assert_eq(alertas[0][0], "vencido", "Tipo do alerta deve ser 'vencido'")

def TC18():
    """Após marcar como pago, status deve ser 'pago' e não gerar alerta."""
    dados = dados_limpos()
    criar_transacao(dados, descricao="Pagar Agora", valor=300.0, dias_vencimento=0)
    t = dados["transacoes"][0]
    # Simula pagamento
    t["status"] = "pago"
    t["data_pagamento"] = date.today().isoformat()
    alertas = verificar_alertas(dados)
    assert_eq(len(alertas), 0, "Após pagamento não deve gerar alerta")

# ═══════════════════════════════════════════════════════════════════════════════
#  MÓDULO 3 — RELATÓRIOS
# ═══════════════════════════════════════════════════════════════════════════════

def TC19():
    """Saldo calculado corretamente com receitas e despesas."""
    dados = dados_limpos()
    criar_transacao(dados, tipo="receita", descricao="Salário", valor=5000.0,
                    dias_vencimento=0, status="pago", data_pagamento=date.today().isoformat())
    criar_transacao(dados, tipo="despesa", descricao="Aluguel", valor=2000.0,
                    dias_vencimento=0, status="pago", data_pagamento=date.today().isoformat())
    criar_transacao(dados, tipo="despesa", descricao="Mercado", valor=500.0,
                    dias_vencimento=0, status="pago", data_pagamento=date.today().isoformat())

    receitas_pagas = sum(t["valor"] for t in dados["transacoes"]
                         if t["tipo"] == "receita" and t["status"] == "pago")
    despesas_pagas = sum(t["valor"] for t in dados["transacoes"]
                         if t["tipo"] == "despesa" and t["status"] == "pago")
    saldo = receitas_pagas - despesas_pagas
    assert_eq(receitas_pagas, 5000.0, "Total de receitas deve ser 5000.0")
    assert_eq(despesas_pagas, 2500.0, "Total de despesas deve ser 2500.0")
    assert_eq(saldo, 2500.0, "Saldo deve ser 2500.0")

def TC20():
    """Saldo negativo calculado corretamente."""
    dados = dados_limpos()
    criar_transacao(dados, tipo="receita", valor=1000.0, status="pago",
                    data_pagamento=date.today().isoformat())
    criar_transacao(dados, tipo="despesa", valor=3000.0, status="pago",
                    data_pagamento=date.today().isoformat())

    receitas = sum(t["valor"] for t in dados["transacoes"] if t["tipo"] == "receita" and t["status"] == "pago")
    despesas = sum(t["valor"] for t in dados["transacoes"] if t["tipo"] == "despesa" and t["status"] == "pago")
    saldo = receitas - despesas
    assert_true(saldo < 0, "Saldo deve ser negativo")
    assert_eq(saldo, -2000.0, "Saldo deve ser -2000.0")

def TC21():
    """Transações pendentes não entram no saldo realizado."""
    dados = dados_limpos()
    criar_transacao(dados, tipo="receita", valor=5000.0, status="pago",
                    data_pagamento=date.today().isoformat())
    criar_transacao(dados, tipo="receita", valor=1000.0, status="pendente")  # pendente

    receitas_pagas = sum(t["valor"] for t in dados["transacoes"]
                         if t["tipo"] == "receita" and t["status"] == "pago")
    assert_eq(receitas_pagas, 5000.0, "Saldo realizado deve ignorar pendentes")

def TC22():
    """Relatório deve separar pendentes de pagos corretamente."""
    dados = dados_limpos()
    criar_transacao(dados, tipo="despesa", valor=100.0, status="pago",
                    data_pagamento=date.today().isoformat())
    criar_transacao(dados, tipo="despesa", valor=200.0, status="pendente")
    criar_transacao(dados, tipo="despesa", valor=300.0, status="pago",
                    data_pagamento=date.today().isoformat())

    pagas   = sum(t["valor"] for t in dados["transacoes"] if t["status"] == "pago")
    pend    = sum(t["valor"] for t in dados["transacoes"] if t["status"] == "pendente")
    assert_eq(pagas, 400.0, "Total pago deve ser 400.0")
    assert_eq(pend, 200.0, "Total pendente deve ser 200.0")

def TC23():
    """Categorização correta no relatório."""
    dados = dados_limpos()
    criar_transacao(dados, tipo="despesa", valor=300.0, categoria="Alimentação", status="pago",
                    data_pagamento=date.today().isoformat())
    criar_transacao(dados, tipo="despesa", valor=1500.0, categoria="Moradia", status="pago",
                    data_pagamento=date.today().isoformat())
    criar_transacao(dados, tipo="despesa", valor=100.0, categoria="Alimentação", status="pago",
                    data_pagamento=date.today().isoformat())

    cats = {}
    for t in dados["transacoes"]:
        cats[t["categoria"]] = cats.get(t["categoria"], 0) + t["valor"]

    assert_eq(cats["Alimentação"], 400.0, "Alimentação deve somar 400.0")
    assert_eq(cats["Moradia"], 1500.0, "Moradia deve somar 1500.0")

def TC24():
    """Filtro por tipo funciona corretamente."""
    dados = dados_limpos()
    criar_transacao(dados, tipo="receita", valor=500.0)
    criar_transacao(dados, tipo="despesa", valor=200.0)
    criar_transacao(dados, tipo="receita", valor=300.0)

    apenas_receitas = [t for t in dados["transacoes"] if t["tipo"] == "receita"]
    apenas_despesas = [t for t in dados["transacoes"] if t["tipo"] == "despesa"]
    assert_eq(len(apenas_receitas), 2, "Deve haver 2 receitas")
    assert_eq(len(apenas_despesas), 1, "Deve haver 1 despesa")

def TC25():
    """Formatação de moeda correta."""
    assert_eq(formatar_moeda(1500.0), "R$ 1.500,00", "1500.0 deve formatar como R$ 1.500,00")
    assert_eq(formatar_moeda(0.5), "R$ 0,50", "0.5 deve formatar como R$ 0,50")
    assert_eq(formatar_moeda(1000000.0), "R$ 1.000.000,00", "1M deve formatar corretamente")

def TC26():
    """Relatório com zero transações não quebra."""
    dados = dados_limpos()
    receitas = sum(t["valor"] for t in dados["transacoes"] if t["tipo"] == "receita")
    despesas = sum(t["valor"] for t in dados["transacoes"] if t["tipo"] == "despesa")
    saldo = receitas - despesas
    assert_eq(saldo, 0.0, "Saldo com zero transações deve ser 0.0")

# ═══════════════════════════════════════════════════════════════════════════════
#  MÓDULO 4 — EXCLUSÃO DE REGISTROS
# ═══════════════════════════════════════════════════════════════════════════════

def TC27():
    """Exclusão física remove o registro corretamente."""
    dados = dados_limpos()
    criar_transacao(dados, descricao="Excluir Eu", valor=100.0)
    id_del = dados["transacoes"][0]["id"]
    assert_eq(len(dados["transacoes"]), 1, "Deve haver 1 transação antes de excluir")
    dados["transacoes"] = [t for t in dados["transacoes"] if t["id"] != id_del]
    salvar_dados(dados)
    recarregado = carregar_dados()
    assert_eq(len(recarregado["transacoes"]), 0, "Deve haver 0 transações após excluir")

def TC28():
    """Exclusão impacta saldo corretamente."""
    dados = dados_limpos()
    criar_transacao(dados, tipo="receita", valor=5000.0, status="pago",
                    data_pagamento=date.today().isoformat())
    criar_transacao(dados, tipo="despesa", valor=2000.0, status="pago",
                    data_pagamento=date.today().isoformat())

    saldo_antes = sum(
        t["valor"] if t["tipo"] == "receita" else -t["valor"]
        for t in dados["transacoes"] if t["status"] == "pago"
    )
    assert_eq(saldo_antes, 3000.0, "Saldo antes da exclusão deve ser 3000.0")

    id_despesa = dados["transacoes"][1]["id"]
    dados["transacoes"] = [t for t in dados["transacoes"] if t["id"] != id_despesa]

    saldo_depois = sum(
        t["valor"] if t["tipo"] == "receita" else -t["valor"]
        for t in dados["transacoes"] if t["status"] == "pago"
    )
    assert_eq(saldo_depois, 5000.0, "Saldo após excluir despesa deve ser 5000.0")

def TC29():
    """Excluir ID inexistente não altera os dados."""
    dados = dados_limpos()
    criar_transacao(dados, valor=100.0)
    qtd_antes = len(dados["transacoes"])
    dados["transacoes"] = [t for t in dados["transacoes"] if t["id"] != 9999]
    assert_eq(len(dados["transacoes"]), qtd_antes, "Excluir ID inexistente não deve alterar dados")

def TC30():
    """Exclusão de conta pendente impacta total de pendentes."""
    dados = dados_limpos()
    criar_transacao(dados, tipo="despesa", valor=500.0, status="pendente")
    criar_transacao(dados, tipo="despesa", valor=300.0, status="pendente")

    total_antes = sum(t["valor"] for t in dados["transacoes"] if t["status"] == "pendente")
    assert_eq(total_antes, 800.0, "Total pendente antes deve ser 800.0")

    id_del = dados["transacoes"][0]["id"]
    dados["transacoes"] = [t for t in dados["transacoes"] if t["id"] != id_del]

    total_depois = sum(t["valor"] for t in dados["transacoes"] if t["status"] == "pendente")
    assert_eq(total_depois, 300.0, "Total pendente após exclusão deve ser 300.0")

def TC31():
    """Exclusão de conta com alerta ativo remove o alerta."""
    dados = dados_limpos()
    criar_transacao(dados, descricao="Vencida", valor=100.0, dias_vencimento=-2, status="pendente")
    alertas_antes = verificar_alertas(dados)
    assert_eq(len(alertas_antes), 1, "Deve haver 1 alerta antes da exclusão")

    dados["transacoes"] = []
    alertas_depois = verificar_alertas(dados)
    assert_eq(len(alertas_depois), 0, "Não deve haver alertas após excluir a transação")

def TC32():
    """Exclusão não afeta outros registros."""
    dados = dados_limpos()
    criar_transacao(dados, descricao="Manter 1", valor=100.0)
    criar_transacao(dados, descricao="Excluir", valor=200.0)
    criar_transacao(dados, descricao="Manter 2", valor=300.0)

    id_del = dados["transacoes"][1]["id"]
    dados["transacoes"] = [t for t in dados["transacoes"] if t["id"] != id_del]

    assert_eq(len(dados["transacoes"]), 2, "Devem restar 2 transações")
    descs = [t["descricao"] for t in dados["transacoes"]]
    assert_true("Manter 1" in descs, "Manter 1 deve permanecer")
    assert_true("Manter 2" in descs, "Manter 2 deve permanecer")
    assert_false("Excluir" in descs, "Transação excluída não deve aparecer")

# ═══════════════════════════════════════════════════════════════════════════════
#  MÓDULO 5 — TESTES DE REGRESSÃO
# ═══════════════════════════════════════════════════════════════════════════════

def TC33():
    """Salvar e recarregar dados preserva todos os campos."""
    dados = dados_limpos()
    criar_transacao(dados, tipo="receita", descricao="Persistência", valor=1234.56,
                    categoria="Freelance", status="pago",
                    data_pagamento=date.today().isoformat())
    salvar_dados(dados)
    recarregado = carregar_dados()
    t = recarregado["transacoes"][0]
    assert_eq(t["tipo"], "receita")
    assert_eq(t["descricao"], "Persistência")
    assert_eq(t["valor"], 1234.56)
    assert_eq(t["categoria"], "Freelance")
    assert_eq(t["status"], "pago")
    assert_true(t["data_pagamento"] is not None)

def TC34():
    """IDs sequenciais são preservados após salvar/recarregar."""
    dados = dados_limpos()
    criar_transacao(dados, valor=100.0)
    criar_transacao(dados, valor=200.0)
    salvar_dados(dados)
    recarregado = carregar_dados()
    assert_eq(recarregado["proximo_id"], 3, "proximo_id deve ser 3 após 2 inserções")

def TC35():
    """Dados vazios inicializam corretamente."""
    if os.path.exists(ARQUIVO_DADOS):
        os.remove(ARQUIVO_DADOS)
    dados = carregar_dados()
    assert_eq(dados["transacoes"], [], "Transações devem estar vazias")
    assert_eq(dados["proximo_id"], 1, "Próximo ID deve ser 1")

def TC36():
    """Edição não cria duplicatas."""
    dados = dados_limpos()
    criar_transacao(dados, descricao="Original", valor=100.0)
    dados["transacoes"][0]["descricao"] = "Editado"
    dados["transacoes"][0]["valor"] = 150.0
    salvar_dados(dados)
    recarregado = carregar_dados()
    assert_eq(len(recarregado["transacoes"]), 1, "Não deve criar duplicata na edição")
    assert_eq(recarregado["transacoes"][0]["descricao"], "Editado")

def TC37():
    """Alertas recalculados corretamente após edição de data de vencimento."""
    dados = dados_limpos()
    criar_transacao(dados, descricao="Editar Data", valor=100.0, dias_vencimento=-5)
    alertas_antes = verificar_alertas(dados)
    assert_eq(len(alertas_antes), 1, "Deve haver alerta para conta vencida")

    # Edita para longe no futuro
    dados["transacoes"][0]["data_vencimento"] = (date.today() + timedelta(days=30)).isoformat()
    alertas_depois = verificar_alertas(dados)
    assert_eq(len(alertas_depois), 0, "Após editar para futuro, não deve haver alertas")

def TC38():
    """Relatório correto após múltiplas operações (inclusão, edição, exclusão)."""
    dados = dados_limpos()
    criar_transacao(dados, tipo="receita", valor=3000.0, status="pago",
                    data_pagamento=date.today().isoformat())
    criar_transacao(dados, tipo="despesa", valor=1000.0, status="pago",
                    data_pagamento=date.today().isoformat())
    criar_transacao(dados, tipo="despesa", valor=500.0, status="pendente")

    # Edita receita
    dados["transacoes"][0]["valor"] = 4000.0
    # Exclui a despesa pendente
    dados["transacoes"] = [t for t in dados["transacoes"] if t["id"] != 3]

    receitas = sum(t["valor"] for t in dados["transacoes"] if t["tipo"] == "receita" and t["status"] == "pago")
    despesas = sum(t["valor"] for t in dados["transacoes"] if t["tipo"] == "despesa" and t["status"] == "pago")
    saldo = receitas - despesas
    assert_eq(receitas, 4000.0, "Receitas devem ser 4000.0 após edição")
    assert_eq(despesas, 1000.0, "Despesas devem ser 1000.0")
    assert_eq(saldo, 3000.0, "Saldo deve ser 3000.0")

# ═══════════════════════════════════════════════════════════════════════════════
#  MÓDULO 6 — USABILIDADE E DADOS CORRETOS
# ═══════════════════════════════════════════════════════════════════════════════

def TC39():
    """Formatos de data aceitos pelo parser."""
    assert_true(parse_data("31/12/2025") is not None, "dd/mm/aaaa deve funcionar")
    assert_true(parse_data("31/12/25") is not None, "dd/mm/aa deve funcionar")
    assert_true(parse_data("2025-12-31") is not None, "aaaa-mm-dd deve funcionar")

def TC40():
    """Transações de tipos diferentes não se misturam nos filtros."""
    dados = dados_limpos()
    criar_transacao(dados, tipo="receita", descricao="R1", valor=100.0)
    criar_transacao(dados, tipo="despesa", descricao="D1", valor=200.0)
    criar_transacao(dados, tipo="receita", descricao="R2", valor=300.0)

    receitas = [t for t in dados["transacoes"] if t["tipo"] == "receita"]
    despesas = [t for t in dados["transacoes"] if t["tipo"] == "despesa"]

    assert_eq(len(receitas), 2, "Deve haver 2 receitas")
    assert_eq(len(despesas), 1, "Deve haver 1 despesa")
    for r in receitas:
        assert_eq(r["tipo"], "receita", "Filtro de receitas só deve retornar receitas")

# ═══════════════════════════════════════════════════════════════════════════════
#  RUNNER PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════════════

CASOS_DE_TESTE = [
    # MÓDULO 1 — Contas a Pagar e Receber
    ("TC01", "Cadastro de conta a pagar com dados válidos",
     "Verificar se uma despesa é cadastrada com todos os campos corretos", TC01),
    ("TC02", "Cadastro de conta a receber com dados válidos",
     "Verificar se uma receita é cadastrada com todos os campos corretos", TC02),
    ("TC03", "Edição de conta a pagar — valor e status",
     "Verificar se a edição atualiza valor e status corretamente", TC03),
    ("TC04", "Categoria de despesa registrada corretamente",
     "Verificar que a categoria da despesa é salva conforme selecionado", TC04),
    ("TC05", "Categoria de receita registrada corretamente",
     "Verificar que a categoria da receita é salva conforme selecionado", TC05),
    ("TC06", "Rejeição de valores inválidos",
     "Verificar que valores inválidos (texto, negativo, zero) são rejeitados", TC06),
    ("TC07", "Parsing de valores monetários válidos",
     "Verificar que formatos válidos de valor são parseados corretamente", TC07),
    ("TC08", "Rejeição de datas inválidas",
     "Verificar que datas inválidas são rejeitadas pelo parser", TC08),
    ("TC09", "Parsing de data válida",
     "Verificar que data no formato dd/mm/aaaa é parseada corretamente", TC09),
    ("TC10", "IDs únicos para múltiplas transações",
     "Verificar que cada transação recebe um ID único", TC10),

    # MÓDULO 2 — Alertas e Lembretes
    ("TC11", "Alerta para conta vencida",
     "Verificar se conta vencida gera alerta do tipo 'vencido'", TC11),
    ("TC12", "Alerta para conta que vence hoje",
     "Verificar se conta com vencimento hoje gera alerta 'hoje'", TC12),
    ("TC13", "Alerta para conta vencendo em até 3 dias",
     "Verificar se conta próxima do vencimento gera alerta 'proximo'", TC13),
    ("TC14", "Sem alerta para vencimento distante",
     "Verificar que conta com vencimento em mais de 3 dias não gera alerta", TC14),
    ("TC15", "Conta paga não gera alerta",
     "Verificar que transação com status 'pago' não gera alerta", TC15),
    ("TC16", "Múltiplos alertas para múltiplas contas vencidas",
     "Verificar contagem correta de alertas para várias contas vencidas", TC16),
    ("TC17", "Alerta para receita vencida (a receber)",
     "Verificar que receita pendente vencida também gera alerta", TC17),
    ("TC18", "Sem alerta após marcar como pago",
     "Verificar que pagamento remove necessidade de alerta", TC18),

    # MÓDULO 3 — Relatórios
    ("TC19", "Saldo calculado corretamente (positivo)",
     "Verificar cálculo de saldo com receitas maiores que despesas", TC19),
    ("TC20", "Saldo negativo calculado corretamente",
     "Verificar cálculo de saldo com despesas maiores que receitas", TC20),
    ("TC21", "Pendentes excluídos do saldo realizado",
     "Verificar que transações pendentes não entram no saldo atual", TC21),
    ("TC22", "Separação correta entre pagas e pendentes no relatório",
     "Verificar que os totais de pago e pendente são calculados separadamente", TC22),
    ("TC23", "Categorização correta no relatório",
     "Verificar que somas por categoria estão corretas no relatório", TC23),
    ("TC24", "Filtro por tipo retorna dados corretos",
     "Verificar que o filtro por receita/despesa funciona corretamente", TC24),
    ("TC25", "Formatação de moeda brasileira correta",
     "Verificar que os valores são formatados no padrão R$ 1.500,00", TC25),
    ("TC26", "Relatório com zero transações não gera erro",
     "Verificar comportamento do sistema sem nenhuma transação cadastrada", TC26),

    # MÓDULO 4 — Exclusão
    ("TC27", "Exclusão física remove o registro",
     "Verificar que a exclusão remove definitivamente a transação", TC27),
    ("TC28", "Exclusão impacta o saldo corretamente",
     "Verificar que o saldo é recalculado após exclusão", TC28),
    ("TC29", "Excluir ID inexistente não altera dados",
     "Verificar que exclusão de ID inválido é segura", TC29),
    ("TC30", "Exclusão de pendente reduz total de pendentes",
     "Verificar que total de pendentes é atualizado após exclusão", TC30),
    ("TC31", "Exclusão de conta vencida remove o alerta",
     "Verificar que alertas desaparecem após excluir a transação", TC31),
    ("TC32", "Exclusão não afeta outros registros",
     "Verificar que apenas o registro alvo é excluído", TC32),

    # MÓDULO 5 — Regressão
    ("TC33", "Persistência preserva todos os campos",
     "Verificar que salvar e carregar mantém a integridade dos dados", TC33),
    ("TC34", "proximo_id incrementa corretamente",
     "Verificar que o contador de ID é atualizado após inserções", TC34),
    ("TC35", "Inicialização com dados vazios funciona",
     "Verificar que o sistema inicia corretamente sem arquivo de dados", TC35),
    ("TC36", "Edição não cria duplicatas",
     "Verificar que editar uma transação não duplica o registro", TC36),
    ("TC37", "Alertas recalculados após edição de vencimento",
     "Verificar que alertas refletem a nova data de vencimento", TC37),
    ("TC38", "Relatório correto após múltiplas operações",
     "Verificar integridade do relatório após inclusão, edição e exclusão", TC38),

    # MÓDULO 6 — Usabilidade
    ("TC39", "Múltiplos formatos de data aceitos",
     "Verificar que dd/mm/aaaa, dd/mm/aa e aaaa-mm-dd são aceitos", TC39),
    ("TC40", "Filtro por tipo não mistura receitas e despesas",
     "Verificar que receitas e despesas não se misturam nos relatórios", TC40),
]

def main():
    print(cor("""
  ╔══════════════════════════════════════════════════════╗
  ║       🧪  SUITE DE TESTES DE QA  🧪                 ║
  ║          Gerenciador Financeiro                      ║
  ╚══════════════════════════════════════════════════════╝""", C.CIANO + C.BOLD))

    setup()

    modulos = [
        ("MÓDULO 1 — Contas a Pagar e Receber", ["TC01","TC02","TC03","TC04","TC05","TC06","TC07","TC08","TC09","TC10"]),
        ("MÓDULO 2 — Alertas e Lembretes",      ["TC11","TC12","TC13","TC14","TC15","TC16","TC17","TC18"]),
        ("MÓDULO 3 — Relatórios",               ["TC19","TC20","TC21","TC22","TC23","TC24","TC25","TC26"]),
        ("MÓDULO 4 — Exclusão de Registros",    ["TC27","TC28","TC29","TC30","TC31","TC32"]),
        ("MÓDULO 5 — Testes de Regressão",      ["TC33","TC34","TC35","TC36","TC37","TC38"]),
        ("MÓDULO 6 — Usabilidade e Dados",      ["TC39","TC40"]),
    ]

    for nome_modulo, ids in modulos:
        secao(nome_modulo)
        for tc_id, tc_nome, tc_obj, tc_fn in CASOS_DE_TESTE:
            if tc_id in ids:
                executar_teste(tc_id, tc_nome, tc_obj, tc_fn)

    teardown()

    # ── Sumário ────────────────────────────────────────────────────────────────
    print()
    print(cor("  ══════════════════════════════════════════════════════", C.BOLD))
    print(cor("  RESULTADO FINAL", C.BOLD + C.BRANCO))
    print(cor("  ══════════════════════════════════════════════════════", C.BOLD))
    print(f"  Total de testes: {cor(str(resultados['total']), C.BOLD)}")
    print(f"  {cor('Passaram', C.VERDE)}: {cor(str(resultados['passou']), C.VERDE + C.BOLD)}")
    print(f"  {cor('Falharam', C.VERMELHO)}: {cor(str(resultados['falhou']), C.VERMELHO + C.BOLD)}")

    taxa = (resultados["passou"] / resultados["total"] * 100) if resultados["total"] > 0 else 0
    cor_taxa = C.VERDE if taxa == 100 else (C.AMARELO if taxa >= 80 else C.VERMELHO)
    print(f"  Taxa de sucesso: {cor(f'{taxa:.1f}%', cor_taxa + C.BOLD)}")

    if resultados["erros"]:
        print(cor("\n  FALHAS DETALHADAS:", C.VERMELHO + C.BOLD))
        for tc_id, nome, msg in resultados["erros"]:
            print(cor(f"\n  [{tc_id}] {nome}", C.VERMELHO))
            for linha_msg in msg.split("\n"):
                print(cor(f"  {linha_msg}", C.AMARELO))

    if resultados["falhou"] == 0:
        print(cor("\n  ✅  Todos os testes passaram com sucesso!", C.VERDE + C.BOLD))
    print()

if __name__ == "__main__":
    main()

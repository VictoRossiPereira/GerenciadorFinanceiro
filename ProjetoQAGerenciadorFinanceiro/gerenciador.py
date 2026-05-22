#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gerenciador Financeiro - Sistema de controle de receitas e despesas
"""

import json
import os
import sys
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional

# ─────────────────────────────────────────────
#  CORES PARA TERMINAL
# ─────────────────────────────────────────────
class Cor:
    RESET   = "\033[0m"
    BOLD    = "\033[1m"
    VERDE   = "\033[92m"
    VERMELHO= "\033[91m"
    AMARELO = "\033[93m"
    AZUL    = "\033[94m"
    CIANO   = "\033[96m"
    MAGENTA = "\033[95m"
    BRANCO  = "\033[97m"
    CINZA   = "\033[90m"

def c(texto, cor):
    return f"{cor}{texto}{Cor.RESET}"

# ─────────────────────────────────────────────
#  BANCO DE DADOS (JSON)
# ─────────────────────────────────────────────
ARQUIVO_DADOS = "dados_financeiros.json"

def carregar_dados() -> Dict:
    if os.path.exists(ARQUIVO_DADOS):
        with open(ARQUIVO_DADOS, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"transacoes": [], "proximo_id": 1}

def salvar_dados(dados: Dict):
    with open(ARQUIVO_DADOS, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)

# ─────────────────────────────────────────────
#  UTILITÁRIOS
# ─────────────────────────────────────────────
CATEGORIAS_RECEITA = [
    "Salário", "Freelance", "Investimentos", "Aluguel Recebido",
    "Vendas", "Bonificação", "Outros"
]
CATEGORIAS_DESPESA = [
    "Alimentação", "Moradia", "Transporte", "Saúde", "Educação",
    "Lazer", "Vestuário", "Serviços", "Impostos", "Outros"
]

def limpar_tela():
    os.system("cls" if os.name == "nt" else "clear")

def pausar():
    input(c("\n  Pressione ENTER para continuar...", Cor.CINZA))

def linha(char="─", largura=60, cor=Cor.CINZA):
    print(c(char * largura, cor))

def titulo(texto, cor=Cor.CIANO):
    print()
    linha("═", 60, cor)
    print(c(f"  {texto}", Cor.BOLD + cor))
    linha("═", 60, cor)

def cabecalho():
    limpar_tela()
    print(c("""
  ╔══════════════════════════════════════════════════════╗
  ║          💰  GERENCIADOR FINANCEIRO  💰              ║
  ╚══════════════════════════════════════════════════════╝""", Cor.VERDE + Cor.BOLD))

def formatar_moeda(valor: float) -> str:
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def formatar_data(data_str: str) -> str:
    try:
        d = datetime.strptime(data_str, "%Y-%m-%d")
        return d.strftime("%d/%m/%Y")
    except:
        return data_str

def parse_data(data_str: str) -> Optional[date]:
    for fmt in ["%d/%m/%Y", "%d/%m/%y", "%Y-%m-%d"]:
        try:
            return datetime.strptime(data_str, fmt).date()
        except:
            continue
    return None

def parse_valor(s: str) -> Optional[float]:
    s = s.strip().replace("R$", "").replace(" ", "").replace(".", "").replace(",", ".")
    try:
        v = float(s)
        return v if v > 0 else None
    except:
        return None

def input_validado(prompt, validador, msg_erro, obrigatorio=True):
    while True:
        val = input(prompt).strip()
        if not obrigatorio and val == "":
            return None
        resultado = validador(val)
        if resultado is not None:
            return resultado
        print(c(f"  ⚠  {msg_erro}", Cor.AMARELO))

def escolher_categoria(tipo: str) -> str:
    cats = CATEGORIAS_RECEITA if tipo == "receita" else CATEGORIAS_DESPESA
    print(c("\n  Categorias disponíveis:", Cor.AZUL))
    for i, cat in enumerate(cats, 1):
        print(f"  {c(str(i), Cor.BOLD)}. {cat}")
    while True:
        esc = input(c("  Escolha a categoria (número): ", Cor.BRANCO)).strip()
        try:
            idx = int(esc) - 1
            if 0 <= idx < len(cats):
                return cats[idx]
        except:
            pass
        print(c("  ⚠  Opção inválida.", Cor.AMARELO))

# ─────────────────────────────────────────────
#  CRUD DE TRANSAÇÕES
# ─────────────────────────────────────────────
def cadastrar_transacao(dados: Dict, tipo: str):
    titulo(f"Nova {'Receita' if tipo == 'receita' else 'Despesa'} / Conta a {'Receber' if tipo == 'receita' else 'Pagar'}")

    descricao = input(c("  Descrição: ", Cor.BRANCO)).strip()
    if not descricao:
        print(c("  ⚠  Descrição obrigatória.", Cor.AMARELO))
        pausar(); return

    valor = input_validado(
        c("  Valor (R$): ", Cor.BRANCO),
        parse_valor,
        "Valor inválido. Use formato: 1500,00"
    )

    categoria = escolher_categoria(tipo)

    data_str = input(c("  Data de vencimento (dd/mm/aaaa) [hoje]: ", Cor.BRANCO)).strip()
    if not data_str:
        data_venc = date.today()
    else:
        data_venc = parse_data(data_str)
        if not data_venc:
            print(c("  ⚠  Data inválida.", Cor.AMARELO)); pausar(); return

    print(c("\n  Status:", Cor.AZUL))
    print(f"  {c('1', Cor.BOLD)}. Pendente")
    print(f"  {c('2', Cor.BOLD)}. Pago/Recebido")
    status_esc = input(c("  Escolha: ", Cor.BRANCO)).strip()
    status = "pago" if status_esc == "2" else "pendente"

    data_pagamento = None
    if status == "pago":
        dp_str = input(c("  Data de pagamento (dd/mm/aaaa) [hoje]: ", Cor.BRANCO)).strip()
        if not dp_str:
            data_pagamento = date.today().isoformat()
        else:
            dp = parse_data(dp_str)
            data_pagamento = dp.isoformat() if dp else date.today().isoformat()

    transacao = {
        "id": dados["proximo_id"],
        "tipo": tipo,
        "descricao": descricao,
        "valor": valor,
        "categoria": categoria,
        "data_vencimento": data_venc.isoformat(),
        "data_pagamento": data_pagamento,
        "status": status,
        "data_cadastro": datetime.now().isoformat()
    }

    dados["transacoes"].append(transacao)
    dados["proximo_id"] += 1
    salvar_dados(dados)

    print(c(f"\n  ✅  {'Receita' if tipo == 'receita' else 'Despesa'} cadastrada com sucesso! (ID: {transacao['id']})", Cor.VERDE))
    pausar()

def listar_transacoes(dados: Dict, tipo: Optional[str] = None, status: Optional[str] = None):
    transacoes = dados["transacoes"]
    if tipo:
        transacoes = [t for t in transacoes if t["tipo"] == tipo]
    if status:
        transacoes = [t for t in transacoes if t["status"] == status]

    if not transacoes:
        print(c("\n  Nenhuma transação encontrada.", Cor.AMARELO))
        return []

    transacoes_ord = sorted(transacoes, key=lambda x: x["data_vencimento"])

    print(c(f"\n  {'ID':<5} {'Tipo':<10} {'Descrição':<22} {'Categoria':<15} {'Vencimento':<12} {'Valor':>13} {'Status':<12}", Cor.CINZA))
    linha()
    for t in transacoes_ord:
        cor_tipo = Cor.VERDE if t["tipo"] == "receita" else Cor.VERMELHO
        cor_status = Cor.VERDE if t["status"] == "pago" else Cor.AMARELO
        sinal = "+" if t["tipo"] == "receita" else "-"
        print(
            f"  {c(str(t['id']), Cor.BOLD):<14}"
            f"{c(t['tipo'].capitalize(), cor_tipo):<19}"
            f"{t['descricao'][:21]:<22}"
            f"{t['categoria'][:14]:<15}"
            f"{formatar_data(t['data_vencimento']):<12}"
            f"{c(f'{sinal} ' + formatar_moeda(t['valor']), cor_tipo):>22}"
            f"  {c(t['status'].capitalize(), cor_status)}"
        )
    linha()
    return transacoes_ord

def editar_transacao(dados: Dict):
    titulo("Editar Transação")
    listar_transacoes(dados)
    if not dados["transacoes"]:
        pausar(); return

    try:
        id_edit = int(input(c("\n  ID da transação a editar: ", Cor.BRANCO)).strip())
    except:
        print(c("  ⚠  ID inválido.", Cor.AMARELO)); pausar(); return

    transacao = next((t for t in dados["transacoes"] if t["id"] == id_edit), None)
    if not transacao:
        print(c("  ⚠  Transação não encontrada.", Cor.AMARELO)); pausar(); return

    print(c(f"\n  Editando: {transacao['descricao']} | {formatar_moeda(transacao['valor'])} | {transacao['status']}", Cor.CIANO))
    print(c("  (Pressione ENTER para manter o valor atual)", Cor.CINZA))

    nova_desc = input(c(f"  Descrição [{transacao['descricao']}]: ", Cor.BRANCO)).strip()
    if nova_desc:
        transacao["descricao"] = nova_desc

    novo_valor_str = input(c(f"  Valor [{formatar_moeda(transacao['valor'])}]: ", Cor.BRANCO)).strip()
    if novo_valor_str:
        novo_valor = parse_valor(novo_valor_str)
        if novo_valor:
            transacao["valor"] = novo_valor
        else:
            print(c("  ⚠  Valor inválido, mantido o anterior.", Cor.AMARELO))

    nova_cat = input(c(f"  Alterar categoria? (s/n): ", Cor.BRANCO)).strip().lower()
    if nova_cat == "s":
        transacao["categoria"] = escolher_categoria(transacao["tipo"])

    nova_data_str = input(c(f"  Data de vencimento [{formatar_data(transacao['data_vencimento'])}]: ", Cor.BRANCO)).strip()
    if nova_data_str:
        nd = parse_data(nova_data_str)
        if nd:
            transacao["data_vencimento"] = nd.isoformat()
        else:
            print(c("  ⚠  Data inválida, mantida a anterior.", Cor.AMARELO))

    print(c("\n  Status: 1. Pendente  2. Pago/Recebido", Cor.AZUL))
    novo_status = input(c(f"  Escolha [{transacao['status']}]: ", Cor.BRANCO)).strip()
    if novo_status == "1":
        transacao["status"] = "pendente"
        transacao["data_pagamento"] = None
    elif novo_status == "2":
        transacao["status"] = "pago"
        dp_str = input(c("  Data de pagamento (dd/mm/aaaa) [hoje]: ", Cor.BRANCO)).strip()
        if dp_str:
            dp = parse_data(dp_str)
            transacao["data_pagamento"] = dp.isoformat() if dp else date.today().isoformat()
        else:
            transacao["data_pagamento"] = date.today().isoformat()

    salvar_dados(dados)
    print(c("\n  ✅  Transação atualizada com sucesso!", Cor.VERDE))
    pausar()

def excluir_transacao(dados: Dict):
    titulo("Excluir Transação")
    listar_transacoes(dados)
    if not dados["transacoes"]:
        pausar(); return

    try:
        id_del = int(input(c("\n  ID da transação a excluir: ", Cor.BRANCO)).strip())
    except:
        print(c("  ⚠  ID inválido.", Cor.AMARELO)); pausar(); return

    transacao = next((t for t in dados["transacoes"] if t["id"] == id_del), None)
    if not transacao:
        print(c("  ⚠  Transação não encontrada.", Cor.AMARELO)); pausar(); return

    print(c(f"\n  Transação selecionada:", Cor.AMARELO))
    print(f"  ID: {transacao['id']} | {transacao['descricao']} | {formatar_moeda(transacao['valor'])} | {transacao['status']}")
    confirmacao = input(c("\n  ⚠  Confirma a exclusão? Esta ação é permanente. (sim/não): ", Cor.VERMELHO)).strip().lower()

    if confirmacao in ["sim", "s"]:
        dados["transacoes"] = [t for t in dados["transacoes"] if t["id"] != id_del]
        salvar_dados(dados)
        print(c("  ✅  Transação excluída com sucesso!", Cor.VERDE))
    else:
        print(c("  Exclusão cancelada.", Cor.CINZA))
    pausar()

# ─────────────────────────────────────────────
#  ALERTAS E LEMBRETES
# ─────────────────────────────────────────────
def verificar_alertas(dados: Dict, exibir_sempre=False):
    hoje = date.today()
    alertas = []

    for t in dados["transacoes"]:
        if t["status"] == "pago":
            continue
        venc = date.fromisoformat(t["data_vencimento"])
        dias = (venc - hoje).days
        tipo_label = "Receita" if t["tipo"] == "receita" else "Despesa"

        if dias < 0:
            alertas.append(("vencido", t, abs(dias), tipo_label))
        elif dias == 0:
            alertas.append(("hoje", t, 0, tipo_label))
        elif dias <= 3:
            alertas.append(("proximo", t, dias, tipo_label))

    if alertas or exibir_sempre:
        titulo("🔔 Alertas e Lembretes", Cor.AMARELO)
        if not alertas:
            print(c("  ✅  Nenhum alerta pendente!", Cor.VERDE))
        for tipo_alerta, t, dias, tipo_label in alertas:
            if tipo_alerta == "vencido":
                icone = "🚨"
                msg = f"VENCIDA há {dias} dia(s)"
                cor = Cor.VERMELHO
            elif tipo_alerta == "hoje":
                icone = "⚠️ "
                msg = "Vence HOJE"
                cor = Cor.AMARELO
            else:
                icone = "📅"
                msg = f"Vence em {dias} dia(s)"
                cor = Cor.CIANO

            print(f"\n  {icone} {c(msg, cor + Cor.BOLD)}")
            print(f"     {tipo_label}: {t['descricao']}")
            print(f"     Valor: {formatar_moeda(t['valor'])} | Categoria: {t['categoria']}")
            print(f"     Vencimento: {formatar_data(t['data_vencimento'])}")

    return alertas

# ─────────────────────────────────────────────
#  RELATÓRIOS
# ─────────────────────────────────────────────
def relatorio_fluxo_caixa(dados: Dict):
    titulo("📊 Relatório de Fluxo de Caixa")

    print(c("\n  Filtrar por período:", Cor.AZUL))
    print(f"  {c('1', Cor.BOLD)}. Mês atual")
    print(f"  {c('2', Cor.BOLD)}. Últimos 30 dias")
    print(f"  {c('3', Cor.BOLD)}. Últimos 90 dias")
    print(f"  {c('4', Cor.BOLD)}. Período personalizado")
    print(f"  {c('5', Cor.BOLD)}. Todos os registros")

    esc = input(c("\n  Escolha: ", Cor.BRANCO)).strip()
    hoje = date.today()

    if esc == "1":
        inicio = date(hoje.year, hoje.month, 1)
        fim = hoje
        periodo = f"{inicio.strftime('%m/%Y')}"
    elif esc == "2":
        inicio = hoje - timedelta(days=30)
        fim = hoje
        periodo = "Últimos 30 dias"
    elif esc == "3":
        inicio = hoje - timedelta(days=90)
        fim = hoje
        periodo = "Últimos 90 dias"
    elif esc == "4":
        ini_str = input(c("  Data início (dd/mm/aaaa): ", Cor.BRANCO)).strip()
        fim_str = input(c("  Data fim (dd/mm/aaaa): ", Cor.BRANCO)).strip()
        inicio = parse_data(ini_str)
        fim = parse_data(fim_str)
        if not inicio or not fim:
            print(c("  ⚠  Datas inválidas.", Cor.AMARELO)); pausar(); return
        if inicio > fim:
            print(c("  ⚠  Data início maior que data fim.", Cor.AMARELO)); pausar(); return
        periodo = f"{formatar_data(inicio.isoformat())} a {formatar_data(fim.isoformat())}"
    else:
        inicio = date(2000, 1, 1)
        fim = date(2099, 12, 31)
        periodo = "Todos os registros"

    print(c("\n  Filtrar por status:", Cor.AZUL))
    print(f"  {c('1', Cor.BOLD)}. Todos")
    print(f"  {c('2', Cor.BOLD)}. Apenas pagos/recebidos")
    print(f"  {c('3', Cor.BOLD)}. Apenas pendentes")
    status_esc = input(c("  Escolha: ", Cor.BRANCO)).strip()
    filtro_status = None if status_esc != "2" and status_esc != "3" else ("pago" if status_esc == "2" else "pendente")

    transacoes = dados["transacoes"]
    filtradas = []
    for t in transacoes:
        venc = date.fromisoformat(t["data_vencimento"])
        if inicio <= venc <= fim:
            if filtro_status is None or t["status"] == filtro_status:
                filtradas.append(t)

    if not filtradas:
        print(c("\n  Nenhuma transação no período selecionado.", Cor.AMARELO))
        pausar(); return

    receitas_pagas = sum(t["valor"] for t in filtradas if t["tipo"] == "receita" and t["status"] == "pago")
    despesas_pagas = sum(t["valor"] for t in filtradas if t["tipo"] == "despesa" and t["status"] == "pago")
    receitas_pend  = sum(t["valor"] for t in filtradas if t["tipo"] == "receita" and t["status"] == "pendente")
    despesas_pend  = sum(t["valor"] for t in filtradas if t["tipo"] == "despesa" and t["status"] == "pendente")
    saldo_real     = receitas_pagas - despesas_pagas
    saldo_previsto = (receitas_pagas + receitas_pend) - (despesas_pagas + despesas_pend)

    print(c(f"\n  Período: {periodo}", Cor.BOLD))
    linha()

    print(c("\n  RECEITAS:", Cor.VERDE + Cor.BOLD))
    print(f"    Recebidas:  {c(formatar_moeda(receitas_pagas), Cor.VERDE)}")
    print(f"    A receber:  {c(formatar_moeda(receitas_pend), Cor.CIANO)}")

    print(c("\n  DESPESAS:", Cor.VERMELHO + Cor.BOLD))
    print(f"    Pagas:      {c(formatar_moeda(despesas_pagas), Cor.VERMELHO)}")
    print(f"    A pagar:    {c(formatar_moeda(despesas_pend), Cor.AMARELO)}")

    linha()
    cor_saldo = Cor.VERDE if saldo_real >= 0 else Cor.VERMELHO
    cor_prev  = Cor.VERDE if saldo_previsto >= 0 else Cor.VERMELHO
    print(f"  {c('Saldo Atual (realizado):', Cor.BOLD)} {c(formatar_moeda(saldo_real), cor_saldo)}")
    print(f"  {c('Saldo Previsto (c/ pendentes):', Cor.BOLD)} {c(formatar_moeda(saldo_previsto), cor_prev)}")
    linha()

    # Detalhamento por categoria
    print(c("\n  DETALHAMENTO POR CATEGORIA:", Cor.AZUL + Cor.BOLD))
    cats_receita: Dict[str, float] = {}
    cats_despesa: Dict[str, float] = {}
    for t in filtradas:
        if t["tipo"] == "receita":
            cats_receita[t["categoria"]] = cats_receita.get(t["categoria"], 0) + t["valor"]
        else:
            cats_despesa[t["categoria"]] = cats_despesa.get(t["categoria"], 0) + t["valor"]

    if cats_receita:
        print(c("\n  Receitas:", Cor.VERDE))
        for cat, val in sorted(cats_receita.items(), key=lambda x: -x[1]):
            print(f"    {cat:<20} {c(formatar_moeda(val), Cor.VERDE)}")
    if cats_despesa:
        print(c("\n  Despesas:", Cor.VERMELHO))
        for cat, val in sorted(cats_despesa.items(), key=lambda x: -x[1]):
            print(f"    {cat:<20} {c(formatar_moeda(val), Cor.VERMELHO)}")

    pausar()

def relatorio_contas(dados: Dict, tipo: str):
    label = "a Receber" if tipo == "receita" else "a Pagar"
    titulo(f"📋 Contas {label}")

    pendentes = [t for t in dados["transacoes"] if t["tipo"] == tipo and t["status"] == "pendente"]
    pagas     = [t for t in dados["transacoes"] if t["tipo"] == tipo and t["status"] == "pago"]

    hoje = date.today()

    print(c(f"\n  PENDENTES ({len(pendentes)}):", Cor.AMARELO + Cor.BOLD))
    if pendentes:
        total_pend = 0
        for t in sorted(pendentes, key=lambda x: x["data_vencimento"]):
            venc = date.fromisoformat(t["data_vencimento"])
            dias = (venc - hoje).days
            if dias < 0:
                status_venc = c(f"  ⚠ Vencida há {abs(dias)}d", Cor.VERMELHO)
            elif dias == 0:
                status_venc = c("  ⚠ Vence hoje", Cor.AMARELO)
            else:
                status_venc = c(f"  📅 {dias}d", Cor.CIANO)
            print(f"  [{t['id']}] {t['descricao'][:25]:<26} {formatar_moeda(t['valor']):>12}  {formatar_data(t['data_vencimento'])} {status_venc}")
            total_pend += t["valor"]
        linha()
        print(f"  Total pendente: {c(formatar_moeda(total_pend), Cor.AMARELO)}")
    else:
        print(c("    Nenhuma.", Cor.CINZA))

    print(c(f"\n  CONCLUÍDAS ({len(pagas)}):", Cor.VERDE + Cor.BOLD))
    if pagas:
        total_pago = 0
        for t in sorted(pagas, key=lambda x: x.get("data_pagamento") or x["data_vencimento"], reverse=True)[:10]:
            dp = formatar_data(t["data_pagamento"]) if t["data_pagamento"] else "—"
            print(f"  [{t['id']}] {t['descricao'][:25]:<26} {formatar_moeda(t['valor']):>12}  Pago em: {dp}")
            total_pago += t["valor"]
        if len(pagas) > 10:
            print(c(f"  ... e mais {len(pagas)-10} registro(s).", Cor.CINZA))
        linha()
        print(f"  Total pago: {c(formatar_moeda(total_pago), Cor.VERDE)}")
    else:
        print(c("    Nenhuma.", Cor.CINZA))

    pausar()

# ─────────────────────────────────────────────
#  MENUS
# ─────────────────────────────────────────────
def menu_receitas(dados: Dict):
    while True:
        cabecalho()
        titulo("💚 Receitas / Contas a Receber", Cor.VERDE)
        print(f"  {c('1', Cor.BOLD)}. Cadastrar nova receita")
        print(f"  {c('2', Cor.BOLD)}. Ver todas as receitas")
        print(f"  {c('3', Cor.BOLD)}. Contas a receber (pendentes)")
        print(f"  {c('4', Cor.BOLD)}. Editar receita")
        print(f"  {c('5', Cor.BOLD)}. Excluir receita")
        print(f"  {c('0', Cor.BOLD)}. Voltar")

        esc = input(c("\n  Escolha: ", Cor.BRANCO)).strip()
        cabecalho()
        if esc == "1":
            cadastrar_transacao(dados, "receita")
        elif esc == "2":
            titulo("Todas as Receitas", Cor.VERDE)
            listar_transacoes(dados, tipo="receita")
            pausar()
        elif esc == "3":
            relatorio_contas(dados, "receita")
        elif esc == "4":
            editar_transacao(dados)
        elif esc == "5":
            excluir_transacao(dados)
        elif esc == "0":
            break

def menu_despesas(dados: Dict):
    while True:
        cabecalho()
        titulo("❤️  Despesas / Contas a Pagar", Cor.VERMELHO)
        print(f"  {c('1', Cor.BOLD)}. Cadastrar nova despesa")
        print(f"  {c('2', Cor.BOLD)}. Ver todas as despesas")
        print(f"  {c('3', Cor.BOLD)}. Contas a pagar (pendentes)")
        print(f"  {c('4', Cor.BOLD)}. Editar despesa")
        print(f"  {c('5', Cor.BOLD)}. Excluir despesa")
        print(f"  {c('0', Cor.BOLD)}. Voltar")

        esc = input(c("\n  Escolha: ", Cor.BRANCO)).strip()
        cabecalho()
        if esc == "1":
            cadastrar_transacao(dados, "despesa")
        elif esc == "2":
            titulo("Todas as Despesas", Cor.VERMELHO)
            listar_transacoes(dados, tipo="despesa")
            pausar()
        elif esc == "3":
            relatorio_contas(dados, "despesa")
        elif esc == "4":
            editar_transacao(dados)
        elif esc == "5":
            excluir_transacao(dados)
        elif esc == "0":
            break

def menu_relatorios(dados: Dict):
    while True:
        cabecalho()
        titulo("📊 Relatórios", Cor.MAGENTA)
        print(f"  {c('1', Cor.BOLD)}. Fluxo de Caixa")
        print(f"  {c('2', Cor.BOLD)}. Contas a Receber")
        print(f"  {c('3', Cor.BOLD)}. Contas a Pagar")
        print(f"  {c('4', Cor.BOLD)}. Todas as transações")
        print(f"  {c('0', Cor.BOLD)}. Voltar")

        esc = input(c("\n  Escolha: ", Cor.BRANCO)).strip()
        cabecalho()
        if esc == "1":
            relatorio_fluxo_caixa(dados)
        elif esc == "2":
            relatorio_contas(dados, "receita")
        elif esc == "3":
            relatorio_contas(dados, "despesa")
        elif esc == "4":
            titulo("Todas as Transações")
            listar_transacoes(dados)
            pausar()
        elif esc == "0":
            break

def painel_resumo(dados: Dict):
    hoje = date.today()
    mes_inicio = date(hoje.year, hoje.month, 1)
    transacoes = dados["transacoes"]

    rec_mes  = sum(t["valor"] for t in transacoes if t["tipo"] == "receita" and t["status"] == "pago"
                   and date.fromisoformat(t["data_vencimento"]) >= mes_inicio)
    desp_mes = sum(t["valor"] for t in transacoes if t["tipo"] == "despesa" and t["status"] == "pago"
                   and date.fromisoformat(t["data_vencimento"]) >= mes_inicio)
    a_receber = sum(t["valor"] for t in transacoes if t["tipo"] == "receita" and t["status"] == "pendente")
    a_pagar   = sum(t["valor"] for t in transacoes if t["tipo"] == "despesa" and t["status"] == "pendente")
    saldo     = rec_mes - desp_mes

    print(c(f"\n  📅 {hoje.strftime('%d/%m/%Y')} — Resumo do Mês", Cor.CINZA))
    linha("─", 55)
    print(f"  Receitas recebidas:  {c(formatar_moeda(rec_mes), Cor.VERDE)}")
    print(f"  Despesas pagas:      {c(formatar_moeda(desp_mes), Cor.VERMELHO)}")
    cor_s = Cor.VERDE if saldo >= 0 else Cor.VERMELHO
    print(f"  Saldo do mês:        {c(formatar_moeda(saldo), cor_s + Cor.BOLD)}")
    linha("─", 55)
    print(f"  A receber:           {c(formatar_moeda(a_receber), Cor.CIANO)}")
    print(f"  A pagar:             {c(formatar_moeda(a_pagar), Cor.AMARELO)}")
    linha("─", 55)

    # Mini-alertas no painel
    alertas = verificar_alertas(dados)
    if alertas:
        venc = sum(1 for a in alertas if a[0] == "vencido")
        hoje_al = sum(1 for a in alertas if a[0] == "hoje")
        prox = sum(1 for a in alertas if a[0] == "proximo")
        partes = []
        if venc:   partes.append(c(f"🚨 {venc} vencida(s)", Cor.VERMELHO))
        if hoje_al: partes.append(c(f"⚠️  {hoje_al} vence hoje", Cor.AMARELO))
        if prox:   partes.append(c(f"📅 {prox} próxima(s)", Cor.CIANO))
        print("  Alertas: " + " | ".join(partes))
        linha("─", 55)

def menu_principal():
    while True:
        dados = carregar_dados()
        cabecalho()
        painel_resumo(dados)

        print(c("\n  MENU PRINCIPAL", Cor.BOLD + Cor.BRANCO))
        print(f"  {c('1', Cor.BOLD)}. 💚 Receitas / Contas a Receber")
        print(f"  {c('2', Cor.BOLD)}. ❤️  Despesas / Contas a Pagar")
        print(f"  {c('3', Cor.BOLD)}. 📊 Relatórios")
        print(f"  {c('4', Cor.BOLD)}. 🔔 Ver Alertas e Lembretes")
        print(f"  {c('0', Cor.BOLD)}. 🚪 Sair")
        linha()

        esc = input(c("\n  Escolha: ", Cor.BRANCO)).strip()
        cabecalho()
        if esc == "1":
            menu_receitas(dados)
        elif esc == "2":
            menu_despesas(dados)
        elif esc == "3":
            menu_relatorios(dados)
        elif esc == "4":
            verificar_alertas(dados, exibir_sempre=True)
            pausar()
        elif esc == "0":
            print(c("\n  Até logo! 👋\n", Cor.VERDE + Cor.BOLD))
            sys.exit(0)
        else:
            print(c("  ⚠  Opção inválida.", Cor.AMARELO))

# ─────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────
if __name__ == "__main__":
    try:
        menu_principal()
    except KeyboardInterrupt:
        print(c("\n\n  Saindo... Até logo! 👋\n", Cor.VERDE))
        sys.exit(0)

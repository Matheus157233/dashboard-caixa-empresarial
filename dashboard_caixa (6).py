"""
CaixaViva — Dashboard de Caixa
Streamlit + Google Sheets + Login + Planos (Básico / Profissional / Empresarial)
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import hashlib, time, numpy as np

st.set_page_config(page_title="CaixaViva", page_icon="💰", layout="wide",
                   initial_sidebar_state="expanded")

# ══════════════════════════════════════════════════════════════════════════════
#  CLIENTES  —  adicione/edite aqui
# ══════════════════════════════════════════════════════════════════════════════
def _h(s): return hashlib.sha256(s.encode()).hexdigest()

CLIENTES = {
    "demo_basico": {
        "senha_hash": _h("demo123"), "nome": "Empresa Demo Básico",
        "sheet_url": "https://docs.google.com/spreadsheets/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgVE2upms/export?format=csv&gid=0",
        "cor": "#2563eb", "plano": "basico", "meta_mensal": 0,
    },
    "demo_pro": {
        "senha_hash": _h("demo456"), "nome": "Empresa Demo Pro",
        "sheet_url": "https://docs.google.com/spreadsheets/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgVE2upms/export?format=csv&gid=0",
        "cor": "#16a34a", "plano": "profissional", "meta_mensal": 0,
    },
    "demo_emp": {
        "senha_hash": _h("demo789"), "nome": "Empresa Demo Empresarial",
        "sheet_url": "https://docs.google.com/spreadsheets/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgVE2upms/export?format=csv&gid=0",
        "cor": "#7c3aed", "plano": "empresarial", "meta_mensal": 30000,
        "alerta_saidas_pct": 60,   # alerta se saídas > 60% das entradas
    },
    # "cliente_real": {
    #     "senha_hash": _h("senha_dele"), "nome": "Nome da Empresa",
    #     "sheet_url": "https://docs.google.com/spreadsheets/d/ID/export?format=csv&gid=0",
    #     "cor": "#16a34a", "plano": "basico", "meta_mensal": 0,
    # },
}

PLANOS = {
    "basico":       {"fluxo", "pizza"},
    "profissional": {"fluxo","pizza","barras","mensal","top","tabela","filtro_avancado","lembretes"},
    "empresarial":  {"fluxo","pizza","barras","mensal","top","tabela","filtro_avancado","lembretes",
                     "resumo_hoje","comparativo","alertas","tendencia","dias_positivo","meta"},
}

def tem(cl, r): return r in PLANOS.get(cl.get("plano","basico"), set())

# ══════════════════════════════════════════════════════════════════════════════
#  CSS
# ══════════════════════════════════════════════════════════════════════════════
def inject_css(cor="#2563eb"):
    st.markdown(f"""<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    html,body,[class*="css"]{{font-family:'Inter',sans-serif}}
    .login-wrap{{max-width:420px;margin:80px auto 0;background:#fff;border-radius:20px;padding:48px 40px;box-shadow:0 8px 40px rgba(0,0,0,.10)}}
    .login-logo{{font-size:40px;text-align:center;margin-bottom:8px}}
    .login-title{{font-size:24px;font-weight:700;text-align:center;color:#0f172a}}
    .login-sub{{font-size:14px;color:#64748b;text-align:center;margin-bottom:28px}}
    .kpi{{border-radius:16px;padding:22px 24px;color:#fff;box-shadow:0 4px 20px rgba(0,0,0,.10)}}
    .kpi.green{{background:linear-gradient(135deg,#15803d,#22c55e)}}
    .kpi.red{{background:linear-gradient(135deg,#991b1b,#ef4444)}}
    .kpi.blue{{background:linear-gradient(135deg,#1e40af,{cor})}}
    .kpi.slate{{background:linear-gradient(135deg,#334155,#64748b)}}
    .kpi.purple{{background:linear-gradient(135deg,#4a1580,#7c3aed)}}
    .kpi.orange{{background:linear-gradient(135deg,#92400e,#f59e0b)}}
    .kpi-label{{font-size:11px;font-weight:700;opacity:.75;letter-spacing:1px;text-transform:uppercase}}
    .kpi-value{{font-size:28px;font-weight:700;margin-top:6px;line-height:1}}
    .kpi-sub{{font-size:12px;opacity:.65;margin-top:5px}}
    .sec{{font-size:15px;font-weight:700;color:#0f172a;margin:24px 0 8px;padding-left:12px;border-left:4px solid {cor}}}
    .sec-emp{{font-size:15px;font-weight:700;color:#0f172a;margin:24px 0 8px;padding-left:12px;border-left:4px solid #7c3aed}}
    .live{{display:inline-flex;align-items:center;gap:6px;background:#dcfce7;color:#15803d;border-radius:99px;padding:4px 14px;font-size:12px;font-weight:700}}
    .dot{{width:8px;height:8px;background:#22c55e;border-radius:50%;animation:blink 1.4s infinite}}
    @keyframes blink{{0%,100%{{opacity:1}}50%{{opacity:.2}}}}
    .alerta-card{{background:linear-gradient(135deg,#7f1d1d,#ef4444);color:#fff;border-radius:14px;padding:20px 24px;margin:8px 0}}
    .alerta-titulo{{font-size:13px;font-weight:700;opacity:.8;text-transform:uppercase;letter-spacing:.8px}}
    .alerta-msg{{font-size:17px;font-weight:700;margin-top:6px}}
    .meta-bar-bg{{background:#e2e8f0;border-radius:99px;height:18px;margin-top:10px;overflow:hidden}}
    .meta-bar-fill{{height:18px;border-radius:99px;transition:width .5s;display:flex;align-items:center;justify-content:flex-end;padding-right:8px;font-size:11px;font-weight:700;color:#fff}}
    </style>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  DADOS
# ══════════════════════════════════════════════════════════════════════════════
def load_data(url):
    df = pd.read_csv(url + f"&cb={int(time.time())}")
    df.columns = df.columns.str.strip()
    col_map = {}
    for c in df.columns:
        cl = c.lower()
        if   "data"  in cl:              col_map[c]="data"
        elif "escri" in cl or "desc" in cl: col_map[c]="descricao"
        elif "egori" in cl:              col_map[c]="categoria"
        elif "tipo"  in cl:              col_map[c]="tipo"
        elif "alor"  in cl:              col_map[c]="valor"
    df = df.rename(columns=col_map)
    df["data"]  = pd.to_datetime(df["data"], dayfirst=True, errors="coerce")
    df["valor"] = pd.to_numeric(
        df["valor"].astype(str).str.replace("R$","",regex=False)
        .str.replace(".","",regex=False).str.replace(",",".",regex=False).str.strip(),
        errors="coerce").fillna(0)
    df["tipo"] = df["tipo"].astype(str).str.strip().str.title()
    df = df.dropna(subset=["data"])
    df["mes"] = df["data"].dt.to_period("M").astype(str)
    df["dia"] = df["data"].dt.date
    return df

def fmt(v): return f"R$ {v:,.2f}".replace(",","X").replace(".",",").replace("X",".")
def pct(v,t): return f"{v/t*100:.1f}%" if t else "—"


# ══════════════════════════════════════════════════════════════════════════════
#  LOGIN
# ══════════════════════════════════════════════════════════════════════════════
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.usuario   = ""

inject_css()

if not st.session_state.logged_in:
    st.markdown("""<div class="login-wrap">
        <div class="login-logo">💰</div>
        <div class="login-title">CaixaViva</div>
        <div class="login-sub">Dashboard financeiro em tempo real</div>
    </div>""", unsafe_allow_html=True)
    _, col_c, _ = st.columns([1,1.4,1])
    with col_c:
        st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
        usuario = st.text_input("Usuário", placeholder="seu_usuario")
        senha   = st.text_input("Senha",   placeholder="••••••••", type="password")
        st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
        if st.button("Entrar →", use_container_width=True, type="primary"):
            u = CLIENTES.get(usuario.strip())
            if u and u["senha_hash"] == _h(senha.strip()):
                st.session_state.logged_in = True
                st.session_state.usuario   = usuario.strip()
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos.")
        st.markdown("<p style='text-align:center;color:#94a3b8;font-size:12px;margin-top:20px'>Acesso exclusivo para clientes</p>", unsafe_allow_html=True)
    st.stop()


# ══════════════════════════════════════════════════════════════════════════════
#  DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
cliente = CLIENTES[st.session_state.usuario]
inject_css(cliente["cor"])

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"### 👤 {cliente['nome']}")
    st.markdown('<span class="live"><span class="dot"></span>AO VIVO</span>', unsafe_allow_html=True)
    plano_n = {"basico":"⚡ Básico","profissional":"🚀 Profissional","empresarial":"💎 Empresarial"}
    plano_c = {"basico":"#64748b","profissional":"#2563eb","empresarial":"#7c3aed"}
    p = cliente.get("plano","basico")
    st.markdown(f'<span style="background:{plano_c[p]};color:#fff;border-radius:99px;padding:3px 12px;font-size:11px;font-weight:700">{plano_n[p]}</span>', unsafe_allow_html=True)
    st.divider()

    auto = st.toggle("🔄 Atualização automática", value=True)
    intervalo = st.slider("Intervalo (seg)", 3, 30, 5) if auto else 5
    if not auto and st.button("↺ Atualizar agora", use_container_width=True):
        st.rerun()

    st.divider()
    st.subheader("📅 Período")
    if tem(cliente, "filtro_avancado"):
        opcoes = ["Hoje","Últimos 7 dias","Últimos 30 dias","Últimos 90 dias","Este mês","Mês anterior","Todo o histórico"]
        idx = 2
    else:
        opcoes = ["Últimos 7 dias","Últimos 30 dias"]
        idx = 1
        st.caption("🔒 Filtros avançados no plano Profissional")
    periodo = st.selectbox("", opcoes, index=idx, label_visibility="collapsed")

    hoje = datetime.today().date()
    if   periodo=="Hoje":             ini=hoje
    elif periodo=="Últimos 7 dias":   ini=hoje-timedelta(days=7)
    elif periodo=="Últimos 30 dias":  ini=hoje-timedelta(days=30)
    elif periodo=="Últimos 90 dias":  ini=hoje-timedelta(days=90)
    elif periodo=="Este mês":         ini=hoje.replace(day=1)
    elif periodo=="Mês anterior":
        p2=hoje.replace(day=1); ini=(p2-timedelta(days=1)).replace(day=1); hoje=p2-timedelta(days=1)
    else:                             ini=datetime(2000,1,1).date()

    # Meta mensal — só empresarial edita
    if tem(cliente, "meta"):
        st.divider()
        st.subheader("🎯 Meta mensal")
        meta = st.number_input("Faturamento alvo (R$)", min_value=0, value=int(cliente.get("meta_mensal",0)), step=1000)
        cliente["meta_mensal"] = meta
        alerta_pct = st.slider("⚠️ Alertar se saídas >", 10, 95, int(cliente.get("alerta_saidas_pct",60)), step=5, format="%d%%")
        cliente["alerta_saidas_pct"] = alerta_pct

    st.divider()
    if st.button("🚪 Sair", use_container_width=True):
        st.session_state.logged_in=False; st.session_state.usuario=""; st.rerun()
    st.caption(f"🕐 {datetime.now().strftime('%H:%M:%S')}")


# ── Carrega dados ─────────────────────────────────────────────────────────────
try:
    df_all = load_data(cliente["sheet_url"])
except Exception as e:
    st.error("Erro ao carregar planilha. Verifique o acesso público.")
    st.code(str(e)); st.stop()

with st.expander("🔍 Debug — clique se os dados não aparecerem"):
    st.write(f"**Linhas lidas:** `{len(df_all)}`  |  **Colunas:** `{list(df_all.columns)}`")
    if "tipo" in df_all.columns:
        st.write(f"**Valores em Tipo:** `{df_all['tipo'].unique().tolist()}`")
    st.dataframe(df_all.head(5))

df = df_all[(df_all["dia"]>=ini)&(df_all["dia"]<=hoje)].copy()

st.markdown(f"""# 📊 Dashboard de Caixa
<p style='color:#64748b;font-size:13px;margin-top:-10px'>
{cliente['nome']} &nbsp;|&nbsp; {ini.strftime('%d/%m/%Y')} → {hoje.strftime('%d/%m/%Y')}
&nbsp;|&nbsp; ⏱ {datetime.now().strftime('%H:%M:%S')}
</p>""", unsafe_allow_html=True)

if df.empty:
    st.warning("Nenhum registro no período. Adicione dados na planilha!"); st.stop()


# ── KPIs principais ───────────────────────────────────────────────────────────
entradas = df[df["tipo"]=="Entrada"]["valor"].sum()
saidas   = df[df["tipo"]=="Saída"]["valor"].sum()
saldo    = entradas - saidas
n_reg    = len(df)

c1,c2,c3,c4 = st.columns(4)
c1.markdown(f'<div class="kpi green"><div class="kpi-label">📈 Entradas</div><div class="kpi-value">{fmt(entradas)}</div><div class="kpi-sub">{df[df["tipo"]=="Entrada"].shape[0]} lançamentos</div></div>', unsafe_allow_html=True)
c2.markdown(f'<div class="kpi red"><div class="kpi-label">📉 Saídas</div><div class="kpi-value">{fmt(saidas)}</div><div class="kpi-sub">{df[df["tipo"]=="Saída"].shape[0]} lançamentos</div></div>', unsafe_allow_html=True)
c3.markdown(f'<div class="kpi {"blue" if saldo>=0 else "red"}"><div class="kpi-label">💼 Saldo</div><div class="kpi-value">{fmt(saldo)}</div><div class="kpi-sub">{"✅ Positivo" if saldo>=0 else "⚠️ Negativo"}</div></div>', unsafe_allow_html=True)
c4.markdown(f'<div class="kpi slate"><div class="kpi-label">📋 Registros</div><div class="kpi-value">{n_reg}</div><div class="kpi-sub">no período</div></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  BLOCO EXCLUSIVO EMPRESARIAL — logo após os KPIs
# ══════════════════════════════════════════════════════════════════════════════
if tem(cliente, "resumo_hoje"):
    st.markdown('<div class="sec-emp">💎 Painel Empresarial</div>', unsafe_allow_html=True)

    hoje_date = datetime.today().date()
    df_hoje   = df_all[df_all["dia"]==hoje_date]
    ent_hoje  = df_hoje[df_hoje["tipo"]=="Entrada"]["valor"].sum()
    sai_hoje  = df_hoje[df_hoje["tipo"]=="Saída"]["valor"].sum()
    sal_hoje  = ent_hoje - sai_hoje

    # Mês atual completo para comparativo e meta
    ini_mes   = hoje_date.replace(day=1)
    df_mes    = df_all[(df_all["dia"]>=ini_mes)&(df_all["dia"]<=hoje_date)]
    ent_mes   = df_mes[df_mes["tipo"]=="Entrada"]["valor"].sum()
    sai_mes   = df_mes[df_mes["tipo"]=="Saída"]["valor"].sum()

    # Mês anterior
    ini_ant   = (ini_mes-timedelta(days=1)).replace(day=1)
    fim_ant   = ini_mes-timedelta(days=1)
    df_ant    = df_all[(df_all["dia"]>=ini_ant)&(df_all["dia"]<=fim_ant)]
    ent_ant   = df_ant[df_ant["tipo"]=="Entrada"]["valor"].sum()
    sai_ant   = df_ant[df_ant["tipo"]=="Saída"]["valor"].sum()

    # ── Resumo do dia ─────────────────────────────────────────────────────────
    st.markdown("**📅 Resumo de Hoje**")
    e1,e2,e3 = st.columns(3)
    e1.markdown(f'<div class="kpi green"><div class="kpi-label">📈 Entradas Hoje</div><div class="kpi-value">{fmt(ent_hoje)}</div><div class="kpi-sub">{df_hoje[df_hoje["tipo"]=="Entrada"].shape[0]} lançamentos</div></div>', unsafe_allow_html=True)
    e2.markdown(f'<div class="kpi red"><div class="kpi-label">📉 Saídas Hoje</div><div class="kpi-value">{fmt(sai_hoje)}</div><div class="kpi-sub">{df_hoje[df_hoje["tipo"]=="Saída"].shape[0]} lançamentos</div></div>', unsafe_allow_html=True)
    e3.markdown(f'<div class="kpi {"blue" if sal_hoje>=0 else "red"}"><div class="kpi-label">💼 Saldo Hoje</div><div class="kpi-value">{fmt(sal_hoje)}</div><div class="kpi-sub">{"✅ Dia positivo" if sal_hoje>=0 else "⚠️ Dia negativo"}</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Alertas visuais ───────────────────────────────────────────────────────
    if tem(cliente, "alertas") and ent_mes > 0:
        pct_saidas = sai_mes / ent_mes * 100
        limite     = cliente.get("alerta_saidas_pct", 60)
        if pct_saidas >= limite:
            st.markdown(
                f'<div class="alerta-card">'
                f'<div class="alerta-titulo">⚠️ Alerta de Saídas</div>'
                f'<div class="alerta-msg">Suas saídas este mês estão em {pct_saidas:.1f}% das entradas '
                f'(limite configurado: {limite}%). Atenção ao caixa!</div>'
                f'</div>', unsafe_allow_html=True)

    # ── Comparativo com mês anterior ─────────────────────────────────────────
    if tem(cliente, "comparativo"):
        st.markdown("**📊 Comparativo — Este mês vs Mês anterior**")
        var_ent = ((ent_mes-ent_ant)/ent_ant*100) if ent_ant else 0
        var_sai = ((sai_mes-sai_ant)/sai_ant*100) if sai_ant else 0
        f1,f2 = st.columns(2)
        icon_e = "📈" if var_ent>=0 else "📉"
        icon_s = "📈" if var_sai>=0 else "📉"
        cor_e  = "green" if var_ent>=0 else "red"
        cor_s  = "red"   if var_sai>=0 else "green"
        f1.markdown(f'<div class="kpi {cor_e}"><div class="kpi-label">{icon_e} Entradas vs Mês Anterior</div><div class="kpi-value">{fmt(ent_mes)}</div><div class="kpi-sub">{"+" if var_ent>=0 else ""}{var_ent:.1f}% | anterior: {fmt(ent_ant)}</div></div>', unsafe_allow_html=True)
        f2.markdown(f'<div class="kpi {cor_s}"><div class="kpi-label">{icon_s} Saídas vs Mês Anterior</div><div class="kpi-value">{fmt(sai_mes)}</div><div class="kpi-sub">{"+" if var_sai>=0 else ""}{var_sai:.1f}% | anterior: {fmt(sai_ant)}</div></div>', unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

    # ── Meta mensal ───────────────────────────────────────────────────────────
    if tem(cliente, "meta") and cliente.get("meta_mensal",0) > 0:
        meta      = cliente["meta_mensal"]
        progresso = min(ent_mes/meta*100, 100)
        faltam    = max(meta-ent_mes, 0)
        cor_bar   = "#22c55e" if progresso>=100 else "#f59e0b" if progresso>=60 else "#ef4444"
        st.markdown("**🎯 Meta Mensal de Faturamento**")
        st.markdown(
            f'<div style="background:#f8fafc;border-radius:14px;padding:20px 24px;border:1px solid #e2e8f0">'
            f'<div style="display:flex;justify-content:space-between;margin-bottom:6px">'
            f'<span style="font-weight:700;color:#0f172a">{fmt(ent_mes)} faturados</span>'
            f'<span style="color:#64748b">Meta: {fmt(meta)}</span></div>'
            f'<div class="meta-bar-bg"><div class="meta-bar-fill" style="width:{progresso:.1f}%;background:{cor_bar}">{progresso:.0f}%</div></div>'
            f'<div style="margin-top:8px;font-size:13px;color:#64748b">'
            f'{"✅ Meta atingida!" if progresso>=100 else f"Faltam {fmt(faltam)} para atingir a meta"}'
            f'</div></div>', unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

    # ── Indicador de dias para fechar positivo ────────────────────────────────
    if tem(cliente, "dias_positivo"):
        dias_passados = (hoje_date - ini_mes).days + 1
        dias_mes      = (ini_mes.replace(month=ini_mes.month%12+1,day=1) if ini_mes.month<12
                         else ini_mes.replace(year=ini_mes.year+1,month=1,day=1)) - timedelta(days=1)
        total_dias    = dias_mes.day
        dias_restantes= total_dias - dias_passados
        media_dia_ent = ent_mes/dias_passados if dias_passados else 0
        media_dia_sai = sai_mes/dias_passados if dias_passados else 0
        proj_ent_fim  = media_dia_ent * total_dias
        proj_sai_fim  = media_dia_sai * total_dias
        proj_saldo    = proj_ent_fim - proj_sai_fim

        d1,d2,d3 = st.columns(3)
        d1.markdown(f'<div class="kpi orange"><div class="kpi-label">📆 Dias Restantes</div><div class="kpi-value">{dias_restantes}</div><div class="kpi-sub">de {total_dias} dias no mês</div></div>', unsafe_allow_html=True)
        d2.markdown(f'<div class="kpi purple"><div class="kpi-label">📈 Projeção Entradas</div><div class="kpi-value">{fmt(proj_ent_fim)}</div><div class="kpi-sub">média {fmt(media_dia_ent)}/dia</div></div>', unsafe_allow_html=True)
        d3.markdown(f'<div class="kpi {"blue" if proj_saldo>=0 else "red"}"><div class="kpi-label">💼 Saldo Projetado</div><div class="kpi-value">{fmt(proj_saldo)}</div><div class="kpi-sub">{"✅ Mês positivo" if proj_saldo>=0 else "⚠️ Risco de negativo"}</div></div>', unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

    # ── Gráfico de tendência ──────────────────────────────────────────────────
    if tem(cliente, "tendencia"):
        st.markdown('<div class="sec-emp">📈 Tendência e Previsão do Mês</div>', unsafe_allow_html=True)
        diario_mes = (
            df_mes.groupby(["dia","tipo"])["valor"].sum().reset_index()
            .pivot(index="dia",columns="tipo",values="valor").fillna(0).reset_index()
        )
        if len(diario_mes) >= 3:
            x = np.arange(len(diario_mes))
            fig_tend = go.Figure()
            for tipo, cor_t, fill_t in [("Entrada","#22c55e","rgba(34,197,94,.1)"),("Saída","#ef4444","rgba(239,68,68,.1)")]:
                if tipo in diario_mes.columns:
                    y = diario_mes[tipo].values
                    fig_tend.add_trace(go.Scatter(x=list(diario_mes["dia"]), y=y, name=tipo,
                        line=dict(color=cor_t, width=2), fill="tozeroy", fillcolor=fill_t))
                    # Linha de tendência
                    coef = np.polyfit(x, y, 1)
                    tend = np.poly1d(coef)(x)
                    fig_tend.add_trace(go.Scatter(x=list(diario_mes["dia"]), y=tend,
                        name=f"Tendência {tipo}", line=dict(color=cor_t, width=1.5, dash="dot"),
                        showlegend=True))
            fig_tend.update_layout(height=280, margin=dict(l=0,r=0,t=8,b=0),
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                legend=dict(orientation="h", yanchor="bottom", y=1.02),
                yaxis=dict(tickprefix="R$ ", gridcolor="#f1f5f9"), hovermode="x unified")
            st.plotly_chart(fig_tend, use_container_width=True)
        else:
            st.info("Precisa de pelo menos 3 dias de dados para mostrar a tendência.")

    st.divider()


# ══════════════════════════════════════════════════════════════════════════════
#  HELPER — card de bloqueio
# ══════════════════════════════════════════════════════════════════════════════
def bloqueio(nome, upgrade):
    st.markdown(
        f'<div style="background:#f8fafc;border:2px dashed #e2e8f0;border-radius:12px;'
        f'padding:28px;text-align:center;margin:8px 0">'
        f'<div style="font-size:28px;margin-bottom:8px">🔒</div>'
        f'<div style="font-weight:700;font-size:15px;color:#0f172a;margin-bottom:4px">{nome}</div>'
        f'<div style="font-size:13px;color:#64748b;margin-bottom:16px">Disponível no plano <b>{upgrade}</b></div>'
        f'<a href="https://wa.me/5511941563832?text=Quero%20fazer%20upgrade%20do%20meu%20plano" '
        f'target="_blank" style="background:#16a34a;color:#fff;padding:8px 20px;border-radius:8px;'
        f'font-weight:700;font-size:13px;text-decoration:none">⬆️ Fazer upgrade</a></div>',
        unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  GRÁFICOS PADRÃO
# ══════════════════════════════════════════════════════════════════════════════

# ── Fluxo diário ─────────────────────────────────────────────────────────────
st.markdown('<div class="sec">📅 Fluxo de Caixa Diário</div>', unsafe_allow_html=True)
if tem(cliente, "fluxo"):
    diario = (df.groupby(["dia","tipo"])["valor"].sum().reset_index()
              .pivot(index="dia",columns="tipo",values="valor").fillna(0).reset_index())
    fig_f = go.Figure()
    for tipo,cor_t,fill_t in [("Entrada","#22c55e","rgba(34,197,94,.13)"),("Saída","#ef4444","rgba(239,68,68,.13)")]:
        if tipo in diario.columns:
            fig_f.add_trace(go.Scatter(x=diario["dia"],y=diario[tipo],name=tipo,
                line=dict(color=cor_t,width=2.5),fill="tozeroy",fillcolor=fill_t,
                hovertemplate=f"<b>{tipo}</b><br>%{{x}}<br>R$ %{{y:,.2f}}<extra></extra>"))
    fig_f.update_layout(height=270,margin=dict(l=0,r=0,t=8,b=0),
        plot_bgcolor="rgba(0,0,0,0)",paper_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="h",yanchor="bottom",y=1.02),
        yaxis=dict(tickprefix="R$ ",gridcolor="#f1f5f9"),hovermode="x unified")
    st.plotly_chart(fig_f, use_container_width=True)
else:
    bloqueio("Fluxo de Caixa Diário","Básico")

# ── Pizzas ────────────────────────────────────────────────────────────────────
st.markdown('<div class="sec">🍕 Composição por Categoria</div>', unsafe_allow_html=True)
if tem(cliente, "pizza"):
    pp1,pp2 = st.columns(2)
    def pizza(df_b,tipo,cores,col):
        d=df_b[df_b["tipo"]==tipo].groupby("categoria")["valor"].sum().reset_index()
        if d.empty: col.info(f"Sem registros de {tipo}."); return
        fig=px.pie(d,values="valor",names="categoria",color_discrete_sequence=cores,hole=0.44,
                   title=f"{'📈' if tipo=='Entrada' else '📉'} {tipo}s")
        fig.update_traces(textposition="inside",textinfo="percent+label",
                          hovertemplate="<b>%{label}</b><br>R$ %{value:,.2f}<br>%{percent}<extra></extra>")
        fig.update_layout(height=320,margin=dict(l=0,r=0,t=36,b=0),showlegend=False,paper_bgcolor="rgba(0,0,0,0)")
        col.plotly_chart(fig,use_container_width=True)
    pizza(df,"Entrada",px.colors.sequential.Greens_r,pp1)
    pizza(df,"Saída",  px.colors.sequential.Reds_r,  pp2)
else:
    bloqueio("Gráficos de Pizza por Categoria","Básico")

# ── Barras ────────────────────────────────────────────────────────────────────
st.markdown('<div class="sec">📊 Entradas vs Saídas por Categoria</div>', unsafe_allow_html=True)
if tem(cliente, "barras"):
    comp=df.groupby(["categoria","tipo"])["valor"].sum().reset_index()
    if not comp.empty:
        fig_b=px.bar(comp,x="categoria",y="valor",color="tipo",barmode="group",
            color_discrete_map={"Entrada":"#22c55e","Saída":"#ef4444"},text_auto=".2s",
            labels={"valor":"","categoria":"","tipo":""})
        fig_b.update_traces(textposition="outside",hovertemplate="<b>%{x}</b><br>R$ %{y:,.2f}<extra></extra>")
        fig_b.update_layout(height=290,margin=dict(l=0,r=0,t=8,b=0),
            plot_bgcolor="rgba(0,0,0,0)",paper_bgcolor="rgba(0,0,0,0)",
            legend=dict(orientation="h",yanchor="bottom",y=1.02),
            yaxis=dict(tickprefix="R$ ",gridcolor="#f1f5f9"))
        st.plotly_chart(fig_b,use_container_width=True)
else:
    bloqueio("Comparativo por Categoria","Profissional")

# ── Mensal ────────────────────────────────────────────────────────────────────
st.markdown('<div class="sec">📆 Resumo Mensal + Saldo</div>', unsafe_allow_html=True)
if tem(cliente, "mensal"):
    piv=(df_all.groupby(["mes","tipo"])["valor"].sum().reset_index()
         .pivot(index="mes",columns="tipo",values="valor").fillna(0).reset_index())
    piv["Saldo"]=piv.get("Entrada",0)-piv.get("Saída",0)
    piv=piv.sort_values("mes")
    fig_m=make_subplots(specs=[[{"secondary_y":True}]])
    for tipo,cor_t in [("Entrada","#22c55e"),("Saída","#ef4444")]:
        if tipo in piv.columns:
            fig_m.add_trace(go.Bar(x=piv["mes"],y=piv[tipo],name=tipo,
                marker_color=cor_t,opacity=.85),secondary_y=False)
    fig_m.add_trace(go.Scatter(x=piv["mes"],y=piv["Saldo"],name="Saldo",
        line=dict(color=cliente["cor"],width=3,dash="dot"),mode="lines+markers+text",
        text=[fmt(v) for v in piv["Saldo"]],textposition="top center",
        textfont=dict(size=10,color=cliente["cor"])),secondary_y=True)
    fig_m.update_layout(barmode="group",height=310,margin=dict(l=0,r=0,t=8,b=0),
        plot_bgcolor="rgba(0,0,0,0)",paper_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="h",yanchor="bottom",y=1.02))
    fig_m.update_yaxes(tickprefix="R$ ",gridcolor="#f1f5f9",secondary_y=False)
    fig_m.update_yaxes(tickprefix="R$ ",showgrid=False,secondary_y=True)
    st.plotly_chart(fig_m,use_container_width=True)
else:
    bloqueio("Resumo Mensal + Saldo","Profissional")

# ── Top categorias ────────────────────────────────────────────────────────────
st.markdown('<div class="sec">🏆 Top Categorias</div>', unsafe_allow_html=True)
if tem(cliente, "top"):
    ta,tb=st.columns(2)
    for col_w,tipo,cor_t in [(ta,"Entrada","#22c55e"),(tb,"Saída","#ef4444")]:
        top=(df[df["tipo"]==tipo].groupby("categoria")["valor"]
             .sum().sort_values(ascending=True).tail(6).reset_index())
        if top.empty: col_w.info(f"Sem dados de {tipo}"); continue
        fig_h=px.bar(top,x="valor",y="categoria",orientation="h",
                     color_discrete_sequence=[cor_t],labels={"valor":"","categoria":""})
        fig_h.update_traces(text=[fmt(v) for v in top["valor"]],textposition="outside")
        fig_h.update_layout(height=240,margin=dict(l=0,r=80,t=8,b=0),
            plot_bgcolor="rgba(0,0,0,0)",paper_bgcolor="rgba(0,0,0,0)",
            showlegend=False,xaxis=dict(tickprefix="R$ ",gridcolor="#f1f5f9"))
        col_w.plotly_chart(fig_h,use_container_width=True)
else:
    bloqueio("Top Categorias","Profissional")

# ── Tabela ────────────────────────────────────────────────────────────────────
st.markdown('<div class="sec">🕐 Últimos Lançamentos</div>', unsafe_allow_html=True)
cols_show=[c for c in ["data","descricao","categoria","tipo","valor"] if c in df.columns]
if tem(cliente, "tabela"):
    show=df[cols_show].copy().sort_values("data",ascending=False).head(15).reset_index(drop=True)
    show["data"]=show["data"].dt.strftime("%d/%m/%Y")
    show["tipo"]=show["tipo"].apply(lambda x:"✅ Entrada" if x=="Entrada" else "🔴 Saída")
    if "valor" in show.columns: show["valor"]=show["valor"].apply(fmt)
    st.dataframe(show,use_container_width=True,height=310)
    with st.expander("🗂️ Ver todos os registros"):
        all_s=df[cols_show].copy().sort_values("data",ascending=False).reset_index(drop=True)
        all_s["data"]=all_s["data"].dt.strftime("%d/%m/%Y")
        all_s["tipo"]=all_s["tipo"].apply(lambda x:"✅ Entrada" if x=="Entrada" else "🔴 Saída")
        if "valor" in all_s.columns: all_s["valor"]=all_s["valor"].apply(fmt)
        st.dataframe(all_s,use_container_width=True,height=400)
else:
    bloqueio("Tabela de Registros","Profissional")


# ══════════════════════════════════════════════════════════════════════════════
#  LEMBRETES DE PAGAMENTOS — Profissional e Empresarial
# ══════════════════════════════════════════════════════════════════════════════
if tem(cliente, "lembretes"):
    st.markdown('<div class="sec">🔔 Lembretes de Pagamentos</div>', unsafe_allow_html=True)

    if "pagamentos" not in st.session_state:
        st.session_state.pagamentos = []

    hoje_dt = datetime.today().date()

    # ── Alertas ativos ────────────────────────────────────────────────────────
    alertas = [p for p in st.session_state.pagamentos
               if 0 <= (p["vencimento"] - hoje_dt).days <= 3]

    if alertas:
        for a in alertas:
            dias = (a["vencimento"] - hoje_dt).days
            if dias == 0:
                msg, cor = "⚠️ VENCE HOJE", "#991b1b"
            elif dias == 1:
                msg, cor = "⚠️ Vence amanhã", "#92400e"
            else:
                msg, cor = f"🔔 Vence em {dias} dias", "#1e40af"
            st.markdown(
                f'<div style="background:{cor};color:#fff;border-radius:12px;'
                f'padding:16px 20px;margin:6px 0;display:flex;justify-content:space-between;align-items:center">'
                f'<div><div style="font-size:11px;font-weight:700;opacity:.8;text-transform:uppercase">{msg}</div>'
                f'<div style="font-size:17px;font-weight:700;margin-top:4px">{a["descricao"]}</div></div>'
                f'<div style="font-size:20px;font-weight:800">{fmt(a["valor"])}</div>'
                f'</div>', unsafe_allow_html=True)

    # ── Formulário novo pagamento ─────────────────────────────────────────────
    with st.expander("➕ Cadastrar novo pagamento futuro"):
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            desc_pag  = st.text_input("Descrição", placeholder="Ex: Aluguel, Fornecedor...")
        with col_b:
            valor_pag = st.number_input("Valor (R$)", min_value=0.0, step=50.0, format="%.2f")
        with col_c:
            data_pag  = st.date_input("Data de vencimento", min_value=hoje_dt)

        if st.button("💾 Salvar lembrete", use_container_width=True, type="primary"):
            if desc_pag and valor_pag > 0:
                st.session_state.pagamentos.append({
                    "descricao":  desc_pag,
                    "valor":      valor_pag,
                    "vencimento": data_pag,
                })
                st.success(f"✅ Lembrete salvo! Você será avisado 3 dias antes de {data_pag.strftime('%d/%m/%Y')}.")
                st.rerun()
            else:
                st.warning("Preencha a descrição e o valor.")

    # ── Lista de pagamentos ───────────────────────────────────────────────────
    if st.session_state.pagamentos:
        st.markdown("**📋 Pagamentos cadastrados**")
        for i, p in enumerate(sorted(st.session_state.pagamentos, key=lambda x: x["vencimento"])):
            dias = (p["vencimento"] - hoje_dt).days
            if   dias < 0:  status, cor_s = "✅ Vencido", "#64748b"
            elif dias == 0: status, cor_s = "🔴 Vence hoje", "#ef4444"
            elif dias <= 3: status, cor_s = f"⚠️ {dias}d restantes", "#f59e0b"
            else:           status, cor_s = f"🟢 {dias}d restantes", "#22c55e"

            ci, cj, ck, cl = st.columns([3,2,2,1])
            ci.write(f"**{p['descricao']}**")
            cj.write(p["vencimento"].strftime("%d/%m/%Y"))
            ck.write(fmt(p["valor"]))
            cl.markdown(f'<span style="color:{cor_s};font-weight:700;font-size:13px">{status}</span>', unsafe_allow_html=True)
            if cl.button("🗑️", key=f"del_{i}", help="Remover"):
                st.session_state.pagamentos.pop(i); st.rerun()
    else:
        st.info("Nenhum pagamento cadastrado. Use o formulário acima para adicionar.")
else:
    bloqueio("Lembretes de Pagamentos", "Profissional")


# ══════════════════════════════════════════════════════════════════════════════
#  AUTO-REFRESH
# ══════════════════════════════════════════════════════════════════════════════
if auto:
    time.sleep(intervalo)
    st.rerun()

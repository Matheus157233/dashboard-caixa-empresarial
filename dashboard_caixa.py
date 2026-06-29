import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta, date
import hashlib, time, numpy as np, json, base64, requests

st.set_page_config(page_title="CaixaViva", page_icon="💰", layout="wide",
                   initial_sidebar_state="expanded")

# ══════════════════════════════════════════════════════════════════════════════
#  GITHUB JSON — lembretes salvos em lembretes.json no repositório
#  Configure em: Streamlit Cloud → Secrets:
#  GITHUB_TOKEN = "ghp_xxxxxxxxxxxx"
#  GITHUB_REPO  = "seu-usuario/seu-repo"
# ══════════════════════════════════════════════════════════════════════════════
ARQUIVO = "lembretes.json"

def _headers():
    return {"Authorization": f"token {st.secrets['GITHUB_TOKEN']}",
            "Accept": "application/vnd.github.v3+json"}

def _api_url():
    return f"https://api.github.com/repos/{st.secrets['GITHUB_REPO']}/contents/{ARQUIVO}"

def _ler_github() -> tuple:
    r = requests.get(_api_url(), headers=_headers())
    if r.status_code == 404: return {}, ""
    r.raise_for_status()
    j = r.json()
    conteudo = base64.b64decode(j["content"]).decode("utf-8")
    return (json.loads(conteudo) if conteudo.strip() else {}), j["sha"]

def _salvar_github(dados: dict, sha: str):
    conteudo = base64.b64encode(json.dumps(dados, ensure_ascii=False, indent=2).encode()).decode()
    body = {"message": "Atualiza lembretes", "content": conteudo}
    if sha: body["sha"] = sha
    requests.put(_api_url(), headers=_headers(), json=body).raise_for_status()

def carregar_lembretes(usuario: str) -> list:
    try:
        dados, _ = _ler_github()
        return [{**l, "vencimento": date.fromisoformat(l["vencimento"])}
                for l in dados.get(usuario, [])]
    except Exception:
        return []

def salvar_lembrete(usuario: str, descricao: str, valor: float, vencimento: date) -> bool:
    try:
        dados, sha = _ler_github()
        if usuario not in dados: dados[usuario] = []
        dados[usuario].append({"id": int(time.time()*1000), "descricao": descricao,
                                "valor": valor, "vencimento": vencimento.isoformat()})
        _salvar_github(dados, sha); return True
    except Exception as e:
        st.error(f"Erro ao salvar: {e}"); return False

def deletar_lembrete(lembrete_id: int, usuario: str) -> bool:
    try:
        dados, sha = _ler_github()
        if usuario in dados:
            dados[usuario] = [l for l in dados[usuario] if l["id"] != lembrete_id]
        _salvar_github(dados, sha); return True
    except Exception as e:
        st.error(f"Erro ao deletar: {e}"); return False

# ══════════════════════════════════════════════════════════════════════════════
#  CLIENTES  —  adicione/edite aqui
# ══════════════════════════════════════════════════════════════════════════════
def _h(s): return hashlib.sha256(s.encode()).hexdigest()

CLIENTES = {
    "demo_emp": {
        "senha_hash": _h("demo789"), "nome": "Empresa Demo Empresarial",
        "sheet_url": "https://docs.google.com/spreadsheets/d/1C9nreFqzailyyoilLe1OqJ-21uW5p_8UP6lMSaUn1-s/export?format=csv&gid=0",
        "cor": "#7c3aed", "plano": "empresarial", "meta_mensal": 30000,
        "alerta_saidas_pct": 60,
        "filiais": {
            "Matriz": "https://docs.google.com/spreadsheets/d/1C9nreFqzailyyoilLe1OqJ-21uW5p_8UP6lMSaUn1-s/export?format=csv&gid=0",
            "Filial 1": {},
        },
    },
    # ── Exemplo cliente com filiais ───────────────────────────────────────────
    # "rede_silva": {
    #     "senha_hash": _h("senha123"),
    #     "nome": "Rede Silva",
    #     "sheet_url": "URL_DA_MATRIZ",        ← planilha principal (dashboard normal)
    #     "cor": "#7c3aed", "plano": "empresarial", "meta_mensal": 50000,
    #     "alerta_saidas_pct": 60,
    #     "filiais": {                          ← cada filial tem sua planilha
    #         "Matriz — Centro":    "URL_MATRIZ",
    #         "Filial — Moema":     "URL_MOEMA",
    #         "Filial — Pinheiros": "URL_PINHEIROS",
    #     },
    # },
}

PLANOS = {
    "basico":       {"fluxo", "pizza"},
    "profissional": {"fluxo","pizza","barras","mensal","top","tabela","filtro_avancado","lembretes"},
    "empresarial":  {"fluxo","pizza","barras","mensal","top","tabela","filtro_avancado","lembretes",
                     "resumo_hoje","comparativo","alertas","tendencia","dias_positivo","meta",
                     "pdf","ticket_medio","resumo_semanal","cores_categoria",
                     "inadimplencia","ponto_equilibrio","filiais","previsao"},
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
#  NOVAS FUNCIONALIDADES EMPRESARIAIS
# ══════════════════════════════════════════════════════════════════════════════

# ── Resumo semanal ────────────────────────────────────────────────────────────
if tem(cliente, "resumo_semanal"):
    st.markdown('<div class="sec-emp">📅 Resumo Semanal</div>', unsafe_allow_html=True)
    ini_sem  = hoje - timedelta(days=hoje.weekday())
    ini_ant_sem = ini_sem - timedelta(days=7)
    fim_ant_sem = ini_sem - timedelta(days=1)
    df_sem   = df_all[(df_all["dia"]>=ini_sem)&(df_all["dia"]<=hoje)]
    df_sem_ant = df_all[(df_all["dia"]>=ini_ant_sem)&(df_all["dia"]<=fim_ant_sem)]
    ent_sem  = df_sem[df_sem["tipo"]=="Entrada"]["valor"].sum()
    sai_sem  = df_sem[df_sem["tipo"]=="Saída"]["valor"].sum()
    ent_sem_ant = df_sem_ant[df_sem_ant["tipo"]=="Entrada"]["valor"].sum()
    var_sem  = ((ent_sem-ent_sem_ant)/ent_sem_ant*100) if ent_sem_ant else 0
    s1,s2,s3 = st.columns(3)
    s1.markdown(f'<div class="kpi green"><div class="kpi-label">📈 Entradas esta semana</div><div class="kpi-value">{fmt(ent_sem)}</div><div class="kpi-sub">{"+" if var_sem>=0 else ""}{var_sem:.1f}% vs semana anterior</div></div>', unsafe_allow_html=True)
    s2.markdown(f'<div class="kpi red"><div class="kpi-label">📉 Saídas esta semana</div><div class="kpi-value">{fmt(sai_sem)}</div><div class="kpi-sub">{df_sem[df_sem["tipo"]=="Saída"].shape[0]} lançamentos</div></div>', unsafe_allow_html=True)
    s3.markdown(f'<div class="kpi blue"><div class="kpi-label">💼 Saldo da semana</div><div class="kpi-value">{fmt(ent_sem-sai_sem)}</div><div class="kpi-sub">{"✅ Semana positiva" if ent_sem>=sai_sem else "⚠️ Semana negativa"}</div></div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
else:
    bloqueio("Resumo Semanal", "Empresarial")

# ── Ticket médio por dia ──────────────────────────────────────────────────────
if tem(cliente, "ticket_medio"):
    st.markdown('<div class="sec-emp">🎫 Ticket Médio por Dia</div>', unsafe_allow_html=True)
    ticket = (df[df["tipo"]=="Entrada"].groupby("dia")
              .agg(total=("valor","sum"), qtd=("valor","count"))
              .reset_index())
    ticket["ticket_medio"] = ticket["total"] / ticket["qtd"]
    if not ticket.empty:
        fig_tick = go.Figure()
        fig_tick.add_trace(go.Bar(x=ticket["dia"], y=ticket["total"],
            name="Total entradas", marker_color="#22c55e", opacity=.6))
        fig_tick.add_trace(go.Scatter(x=ticket["dia"], y=ticket["ticket_medio"],
            name="Ticket médio", line=dict(color="#f59e0b", width=2.5),
            mode="lines+markers", yaxis="y2",
            hovertemplate="<b>Ticket médio</b><br>%{x}<br>R$ %{y:,.2f}<extra></extra>"))
        fig_tick.update_layout(height=280, margin=dict(l=0,r=0,t=8,b=0),
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            legend=dict(orientation="h", yanchor="bottom", y=1.02),
            yaxis=dict(tickprefix="R$ ", gridcolor="#f1f5f9"),
            yaxis2=dict(tickprefix="R$ ", overlaying="y", side="right", showgrid=False))
        st.plotly_chart(fig_tick, use_container_width=True)
        media_geral = ticket["ticket_medio"].mean()
        st.caption(f"Ticket médio do período: **{fmt(media_geral)}**")
else:
    bloqueio("Ticket Médio por Dia", "Empresarial")

# ── Ponto de equilíbrio ───────────────────────────────────────────────────────
if tem(cliente, "ponto_equilibrio"):
    st.markdown('<div class="sec-emp">⚖️ Ponto de Equilíbrio</div>', unsafe_allow_html=True)
    ini_mes_pe  = hoje.replace(day=1)
    df_mes_pe   = df_all[(df_all["dia"]>=ini_mes_pe)&(df_all["dia"]<=hoje)]
    saidas_fixas = df_mes_pe[df_mes_pe["tipo"]=="Saída"]["valor"].sum()
    entradas_pe  = df_mes_pe[df_mes_pe["tipo"]=="Entrada"]["valor"].sum()
    dias_passados_pe = (hoje - ini_mes_pe).days + 1
    pe1, pe2, pe3 = st.columns(3)
    pe1.markdown(f'<div class="kpi red"><div class="kpi-label">📉 Total Saídas do Mês</div><div class="kpi-value">{fmt(saidas_fixas)}</div><div class="kpi-sub">valor a cobrir</div></div>', unsafe_allow_html=True)
    pe2.markdown(f'<div class="kpi green"><div class="kpi-label">📈 Entradas do Mês</div><div class="kpi-value">{fmt(entradas_pe)}</div><div class="kpi-sub">{"✅ Equilibrio atingido!" if entradas_pe>=saidas_fixas else f"Faltam {fmt(saidas_fixas-entradas_pe)}"}</div></div>', unsafe_allow_html=True)
    cobertura = min(entradas_pe/saidas_fixas*100, 100) if saidas_fixas else 100
    pe3.markdown(f'<div class="kpi {"blue" if cobertura>=100 else "orange"}"><div class="kpi-label">📊 Cobertura</div><div class="kpi-value">{cobertura:.0f}%</div><div class="kpi-sub">das saídas cobertas</div></div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
else:
    bloqueio("Ponto de Equilíbrio", "Empresarial")

# ── Previsão de fluxo de caixa ────────────────────────────────────────────────
if tem(cliente, "previsao"):
    st.markdown('<div class="sec-emp">🔮 Previsão de Fluxo de Caixa — Próximos 30 dias</div>', unsafe_allow_html=True)
    if len(df_all) >= 7:
        media_ent_dia = df_all[df_all["tipo"]=="Entrada"]["valor"].sum() / max(len(df_all["dia"].unique()), 1)
        media_sai_dia = df_all[df_all["tipo"]=="Saída"]["valor"].sum()   / max(len(df_all["dia"].unique()), 1)
        datas_prev = [hoje + timedelta(days=i) for i in range(1, 31)]
        ent_prev   = [media_ent_dia * (1 + np.random.uniform(-0.15, 0.15)) for _ in range(30)]
        sai_prev   = [media_sai_dia * (1 + np.random.uniform(-0.10, 0.10)) for _ in range(30)]
        sal_prev   = [sum(ent_prev[:i+1]) - sum(sai_prev[:i+1]) for i in range(30)]
        fig_prev = go.Figure()
        fig_prev.add_trace(go.Scatter(x=datas_prev, y=ent_prev, name="Entradas previstas",
            line=dict(color="#22c55e", width=2, dash="dot"), fill="tozeroy",
            fillcolor="rgba(34,197,94,.08)"))
        fig_prev.add_trace(go.Scatter(x=datas_prev, y=sai_prev, name="Saídas previstas",
            line=dict(color="#ef4444", width=2, dash="dot"), fill="tozeroy",
            fillcolor="rgba(239,68,68,.08)"))
        fig_prev.add_trace(go.Scatter(x=datas_prev, y=sal_prev, name="Saldo acumulado",
            line=dict(color=cliente["cor"], width=3), yaxis="y2"))
        fig_prev.update_layout(height=280, margin=dict(l=0,r=0,t=8,b=0),
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            legend=dict(orientation="h", yanchor="bottom", y=1.02),
            yaxis=dict(tickprefix="R$ ", gridcolor="#f1f5f9"),
            yaxis2=dict(tickprefix="R$ ", overlaying="y", side="right", showgrid=False),
            hovermode="x unified")
        st.plotly_chart(fig_prev, use_container_width=True)
        st.caption("⚠️ Previsão baseada na média histórica. Valores aproximados.")
    else:
        st.info("Precisa de pelo menos 7 dias de dados para gerar a previsão.")
else:
    bloqueio("Previsão de Fluxo de Caixa", "Empresarial")

# ── Inadimplência ─────────────────────────────────────────────────────────────
if tem(cliente, "inadimplencia"):
    st.markdown('<div class="sec-emp">⚠️ Controle de Inadimplência</div>', unsafe_allow_html=True)
    if "inadimplentes" not in st.session_state:
        st.session_state.inadimplentes = []
    total_inad = sum(i["valor"] for i in st.session_state.inadimplentes)
    i1, i2 = st.columns(2)
    i1.markdown(f'<div class="kpi red"><div class="kpi-label">⚠️ Total em Aberto</div><div class="kpi-value">{fmt(total_inad)}</div><div class="kpi-sub">{len(st.session_state.inadimplentes)} entradas não recebidas</div></div>', unsafe_allow_html=True)
    i2.markdown(f'<div class="kpi slate"><div class="kpi-label">📊 % do Faturamento</div><div class="kpi-value">{(total_inad/entradas*100):.1f}%</div><div class="kpi-sub">em risco no período</div></div>' if entradas > 0 else '<div class="kpi slate"><div class="kpi-label">📊 % do Faturamento</div><div class="kpi-value">0%</div></div>', unsafe_allow_html=True)
    with st.expander("➕ Adicionar entrada não recebida"):
        ia, ib, ic = st.columns(3)
        with ia: desc_i = st.text_input("Cliente/Descrição", placeholder="Ex: João Silva", key="inad_desc")
        with ib: val_i  = st.number_input("Valor (R$)", min_value=0.0, step=50.0, key="inad_val")
        with ic: data_i = st.date_input("Vencimento", key="inad_data")
        if st.button("➕ Adicionar", key="add_inad", use_container_width=True):
            if desc_i and val_i > 0:
                st.session_state.inadimplentes.append({"desc": desc_i, "valor": val_i, "data": data_i})
                st.rerun()
    if st.session_state.inadimplentes:
        for idx, item in enumerate(st.session_state.inadimplentes):
            ca, cb, cc, cd = st.columns([3,2,2,1])
            ca.write(f"**{item['desc']}**")
            cb.write(item["data"].strftime("%d/%m/%Y"))
            cc.write(fmt(item["valor"]))
            if cd.button("✅", key=f"rec_{idx}", help="Marcar como recebido"):
                st.session_state.inadimplentes.pop(idx); st.rerun()
else:
    bloqueio("Controle de Inadimplência", "Empresarial")

# ── Comparativo entre filiais ─────────────────────────────────────────────────
if tem(cliente, "filiais"):
    filiais = cliente.get("filiais", {})
    if filiais:
        st.markdown('<div class="sec-emp">🏢 Comparativo entre Filiais</div>', unsafe_allow_html=True)
        st.caption("Visão consolidada de todas as unidades no período selecionado.")

        # Carrega dados de cada filial
        dados_filiais = {}
        for nome_filial, url_filial in filiais.items():
            try:
                df_fil = load_data(url_filial)
                df_fil = df_fil[(df_fil["dia"]>=ini)&(df_fil["dia"]<=hoje)]
                dados_filiais[nome_filial] = {
                    "entradas": df_fil[df_fil["tipo"]=="Entrada"]["valor"].sum(),
                    "saidas":   df_fil[df_fil["tipo"]=="Saída"]["valor"].sum(),
                    "saldo":    df_fil[df_fil["tipo"]=="Entrada"]["valor"].sum() - df_fil[df_fil["tipo"]=="Saída"]["valor"].sum(),
                    "registros": len(df_fil),
                }
            except Exception:
                dados_filiais[nome_filial] = {"entradas":0,"saidas":0,"saldo":0,"registros":0}

        # KPIs por filial
        cols_fil = st.columns(len(dados_filiais))
        for col_f, (nome_f, dados_f) in zip(cols_fil, dados_filiais.items()):
            cor_saldo = "green" if dados_f["saldo"] >= 0 else "red"
            col_f.markdown(
                f'<div class="kpi {cor_saldo}" style="margin-bottom:8px">'
                f'<div class="kpi-label">🏢 {nome_f}</div>'
                f'<div class="kpi-value">{fmt(dados_f["saldo"])}</div>'
                f'<div class="kpi-sub">↑ {fmt(dados_f["entradas"])} &nbsp;|&nbsp; ↓ {fmt(dados_f["saidas"])}</div>'
                f'</div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Gráfico comparativo
        nomes  = list(dados_filiais.keys())
        ents   = [dados_filiais[n]["entradas"] for n in nomes]
        sais   = [dados_filiais[n]["saidas"]   for n in nomes]
        saldos = [dados_filiais[n]["saldo"]    for n in nomes]

        fig_fil = go.Figure()
        fig_fil.add_trace(go.Bar(name="Entradas", x=nomes, y=ents,
            marker_color="#22c55e", text=[fmt(v) for v in ents], textposition="outside"))
        fig_fil.add_trace(go.Bar(name="Saídas", x=nomes, y=sais,
            marker_color="#ef4444", text=[fmt(v) for v in sais], textposition="outside"))
        fig_fil.add_trace(go.Scatter(name="Saldo", x=nomes, y=saldos,
            mode="markers+text", marker=dict(size=14, color=cliente["cor"]),
            text=[fmt(v) for v in saldos], textposition="top center",
            textfont=dict(size=11, color=cliente["cor"]), yaxis="y2"))
        fig_fil.update_layout(
            barmode="group", height=320, margin=dict(l=0,r=0,t=8,b=0),
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            legend=dict(orientation="h", yanchor="bottom", y=1.02),
            yaxis=dict(tickprefix="R$ ", gridcolor="#f1f5f9"),
            yaxis2=dict(tickprefix="R$ ", overlaying="y", side="right", showgrid=False),
        )
        st.plotly_chart(fig_fil, use_container_width=True)

        # Tabela resumo
        df_resumo = pd.DataFrame([
            {"Filial": n, "Entradas": fmt(d["entradas"]),
             "Saídas": fmt(d["saidas"]), "Saldo": fmt(d["saldo"]),
             "Registros": d["registros"]}
            for n, d in dados_filiais.items()
        ])
        st.dataframe(df_resumo, use_container_width=True, hide_index=True)

        # Melhor filial
        melhor = max(dados_filiais, key=lambda n: dados_filiais[n]["saldo"])
        st.success(f"🏆 Melhor filial no período: **{melhor}** com saldo de {fmt(dados_filiais[melhor]['saldo'])}")
    else:
        st.info("Nenhuma filial cadastrada. Adicione as planilhas das filiais no campo `filiais` do cliente no código.")
else:
    bloqueio("Comparativo entre Filiais", "Empresarial")

# ── Exportar PDF ──────────────────────────────────────────────────────────────
if tem(cliente, "pdf"):
    st.markdown('<div class="sec-emp">📄 Exportar Relatório</div>', unsafe_allow_html=True)
    if st.button("📥 Gerar relatório em PDF", use_container_width=True, type="primary"):
        try:
            from fpdf import FPDF
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Helvetica", "B", 20)
            pdf.cell(0, 12, "Relatório de Caixa", ln=True, align="C")
            pdf.set_font("Helvetica", "", 11)
            pdf.cell(0, 8, f"{cliente['nome']}", ln=True, align="C")
            pdf.cell(0, 8, f"Período: {ini.strftime('%d/%m/%Y')} a {hoje.strftime('%d/%m/%Y')}", ln=True, align="C")
            pdf.ln(8)
            pdf.set_font("Helvetica", "B", 13)
            pdf.cell(0, 10, "Resumo Financeiro", ln=True)
            pdf.set_font("Helvetica", "", 11)
            pdf.cell(0, 8, f"Total Entradas:  R$ {entradas:,.2f}", ln=True)
            pdf.cell(0, 8, f"Total Saidas:    R$ {saidas:,.2f}", ln=True)
            pdf.cell(0, 8, f"Saldo do Periodo: R$ {saldo:,.2f}", ln=True)
            pdf.cell(0, 8, f"Total de Registros: {n_reg}", ln=True)
            pdf.ln(6)
            pdf.set_font("Helvetica", "B", 13)
            pdf.cell(0, 10, "Entradas por Categoria", ln=True)
            pdf.set_font("Helvetica", "", 11)
            for cat, val in df[df["tipo"]=="Entrada"].groupby("categoria")["valor"].sum().items():
                pdf.cell(0, 8, f"  {cat}: R$ {val:,.2f}", ln=True)
            pdf.ln(4)
            pdf.set_font("Helvetica", "B", 13)
            pdf.cell(0, 10, "Saidas por Categoria", ln=True)
            pdf.set_font("Helvetica", "", 11)
            for cat, val in df[df["tipo"]=="Saída"].groupby("categoria")["valor"].sum().items():
                pdf.cell(0, 8, f"  {cat}: R$ {val:,.2f}", ln=True)
            pdf_bytes = pdf.output()
            st.download_button("⬇️ Baixar PDF", data=bytes(pdf_bytes),
                file_name=f"relatorio_{hoje.strftime('%Y%m%d')}.pdf",
                mime="application/pdf", use_container_width=True)
        except Exception:
            st.info("Para ativar o PDF, adicione `fpdf2` no `requirements.txt`.")
else:
    bloqueio("Exportar Relatório em PDF", "Empresarial")


# ══════════════════════════════════════════════════════════════════════════════
#  LEMBRETES DE PAGAMENTOS — Profissional e Empresarial
# ══════════════════════════════════════════════════════════════════════════════
if tem(cliente, "lembretes"):
    st.markdown('<div class="sec">🔔 Lembretes de Pagamentos</div>', unsafe_allow_html=True)

    hoje_dt   = datetime.today().date()
    usuario   = st.session_state.usuario
    lembretes = carregar_lembretes(usuario)

    # ── Alertas ativos ────────────────────────────────────────────────────────
    alertas = [p for p in lembretes if 0 <= (p["vencimento"] - hoje_dt).days <= 3]
    if alertas:
        for a in alertas:
            dias = (a["vencimento"] - hoje_dt).days
            if   dias == 0: msg, cor = "⚠️ VENCE HOJE",          "#991b1b"
            elif dias == 1: msg, cor = "⚠️ Vence amanhã",        "#92400e"
            else:           msg, cor = f"🔔 Vence em {dias} dias","#1e40af"
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
                if salvar_lembrete(usuario, desc_pag, valor_pag, data_pag):
                    st.success(f"✅ Salvo! Alerta 3 dias antes de {data_pag.strftime('%d/%m/%Y')}.")
                    st.rerun()
            else:
                st.warning("Preencha a descrição e o valor.")

    # ── Lista de pagamentos ───────────────────────────────────────────────────
    if lembretes:
        st.markdown("**📋 Pagamentos cadastrados**")
        for p in sorted(lembretes, key=lambda x: x["vencimento"]):
            dias = (p["vencimento"] - hoje_dt).days
            if   dias < 0:  status, cor_s = "✅ Vencido",              "#64748b"
            elif dias == 0: status, cor_s = "🔴 Vence hoje",           "#ef4444"
            elif dias <= 3: status, cor_s = f"⚠️ {dias}d restantes",   "#f59e0b"
            else:           status, cor_s = f"🟢 {dias}d restantes",   "#22c55e"

            ci, cj, ck, cl = st.columns([3,2,2,1])
            ci.write(f"**{p['descricao']}**")
            cj.write(p["vencimento"].strftime("%d/%m/%Y"))
            ck.write(fmt(p["valor"]))
            cl.markdown(f'<span style="color:{cor_s};font-weight:700;font-size:13px">{status}</span>', unsafe_allow_html=True)
            if cl.button("🗑️", key=f"del_{p['id']}", help="Remover"):
                if deletar_lembrete(p["id"], usuario): st.rerun()
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

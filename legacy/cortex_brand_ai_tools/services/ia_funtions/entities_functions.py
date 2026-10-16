from __future__ import annotations
import re
from typing import Dict, List, Tuple, Iterable, Set, Literal
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

import spacy
from collections import Counter, defaultdict

# Carrega o pipeline de português (inclui tagger, parser, NER)
nlp = spacy.load("pt_core_news_lg")


def extrair_entidades(texto: str):
    
      doc = nlp(texto)
      entidades = [(ent.text, ent.label_) for ent in doc.ents]

      

      # conta quantas vezes cada (termo, categoria) aparece
      contador = Counter(entidades)

      # organiza por categoria e ordena do maior para menor
      resultado = defaultdict(list)
      for (termo, categoria), qtd in contador.items():
         resultado[categoria].append((termo, qtd))

      # ordena os termos de cada categoria por contagem (maior -> menor)
      for categoria in resultado:
         resultado[categoria] = sorted(resultado[categoria], key=lambda x: x[1], reverse=True)

      # converte para dict normal
      resultado = dict(resultado)

      return resultado




# =========================
# Config
# =========================
# Requer: pip install langchain langchain-openai pydantic>=2
# Defina a env var: OPENAI_API_KEY

# Apelidos notórios que podem ficar como nome único
KNOWN_NICKNAMES: Set[str] = {
    "lula", "pelé", "xuxa", "neymar", "madonna", "rihanna", "anitta",
    "gil", "caetano", "pabllo", "sabina", "shakira", "bolsonaro", "dilma",
    "temer", "cazuza"  # ajuste à vontade
}

# Palavras-gatilho que indicam órgão/ente público/ONG/universidade
INSTITUTION_HINTS = re.compile(
    r"\b("
    r"minist(é|e)rio|secretaria|prefeitura|governo|c(â|a)mara|senado|"
    r"assembleia|tribunal|universidade|faculdade|instituto|fundação|"
    r"federação|confederação|associa(ç|c)ão|organiza(ç|c)ão|"
    r"onu|unicef|unesco|oms|opas|oab|ibge|sus|banco central|"
    r"cde|ocde|mercosul|oea|anvisa|ibama|inep|mpf|tse|stf"
    r")\b",
    flags=re.I
)

# =========================
# Utilidades
# =========================
def _take_strings(seq: Iterable[Tuple[str, int]]) -> List[str]:
    """Aceita lista de tuplas (texto, count) ou lista de strings; devolve só strings."""
    out = []
    for x in seq:
        if isinstance(x, tuple) and len(x) >= 1:
            out.append(str(x[0]).strip())
        else:
            out.append(str(x).strip())
    return out

def _titlecase_preservando_siglas(s: str) -> str:
    """Titlecase suave: preserva siglas (2–6 letras maiúsculas), mantém 'da', 'do' etc. minúsculas."""
    if s.isupper() and 2 <= len(s) <= 6:  # sigla simples
        return s
    # titlecase básico e correções
    pequenas = {"da","de","do","das","dos","e","a","o","as","os","em"}
    palavras = re.split(r"(\s+|-|/)", s.strip())
    def norm(p: str) -> str:
        if re.fullmatch(r"[A-Z]{2,6}", p):  # siglas tipo ONU, USP
            return p
        pt = p.lower()
        return pt if pt in pequenas else (pt[:1].upper() + pt[1:])
    return "".join(norm(p) if p.strip() else p for p in palavras)

def _is_full_person_name(name: str) -> bool:
    tokens = [t for t in re.split(r"\s+", name.strip()) if t]
    # duas ou mais palavras (com letras), evitando lixo tipo "Podemos-PA"
    return len([t for t in tokens if re.search(r"[A-Za-zÀ-ÖØ-öø-ÿ]", t)]) >= 2

def _is_allowed_nickname(name: str) -> bool:
    return name.strip().lower() in KNOWN_NICKNAMES

def _looks_like_institution(name: str) -> bool:
    return bool(INSTITUTION_HINTS.search(name))

def _dedup_preservando_ordem(items: Iterable[str]) -> List[str]:
    seen = set()
    out = []
    for it in items:
        key = it.casefold()
        if key not in seen:
            out.append(it)
            seen.add(key)
    return out

# =========================
# Saída estruturada do classificador LLM
# =========================
class ClassifiedOrgs(BaseModel):
    Empresas: List[str] = Field(default_factory=list, description="Lista de empresas/companhias/marcas.")
    Instituicoes: List[str] = Field(default_factory=list, description="Lista de órgãos públicos, ONGs, universidades, organismos multilaterais.")
    Ignorar: List[str] = Field(default_factory=list, description="Itens que não são organizações relevantes.")

# =========================
# Prompt de classificação (LLM)
# =========================
_CLASSIFIER_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "Você é um classificad@r de entidades. Separe nomes fornecidos em "
            "Empresas (companhias privadas, marcas, grupos empresariais) "
            "ou Instituições (órgãos públicos, universidades, ONGs, organismos multilaterais). "
            "Se não for organização relevante, coloque em Ignorar. "
            "Mantenha o nome como veio (apenas normalize capitalização). Não invente nomes.",
        ),
        (
            "human",
            "Classifique os itens abaixo:\n\n{itens}\n\n"
            "Responda na estrutura JSON pedida (Empresas, Instituicoes, Ignorar)."
        ),
    ]
)

def _classificar_organizacoes_via_llm(
    candidatos: List[str],
    llm: ChatOpenAI,
) -> ClassifiedOrgs:
    if not candidatos:
        return ClassifiedOrgs()
    # Normaliza capitalização antes de enviar
    itens_norm = [_titlecase_preservando_siglas(x) for x in candidatos]
    chain = _CLASSIFIER_PROMPT | llm.with_structured_output(ClassifiedOrgs)
    return chain.invoke({"itens": "\n".join(f"- {x}" for x in itens_norm)})

# =========================
# Função principal
# =========================
def organizar_entidades(
    entidades: Dict[str, Iterable],
    *,
    model: str = "gpt-4o-mini",
    temperature: float = 0.0,
    use_llm: bool = True,
    llm: ChatOpenAI | None = None,
) -> Dict[str, List[str]]:
    """
    Converte a saída de NER em:
      {
        "Pessoas": [...],
        "Instituições": [...],
        "Empresas": [...]
      }

    Regras:
    - Pessoas: nomes completos (>=2 palavras). Nomes de 1 palavra só entram se forem apelidos notórios (KNOWN_NICKNAMES).
    - ORG/MISC: separados em Empresas vs Instituições via heurística + LLM (opcional).
    - Deduplicação case-insensitive, preservando a primeira ocorrência.
    """
    # ===== 1) Coletar candidatos =====
    per_raw = _take_strings(entidades.get("PER", []))
    org_raw = _take_strings(entidades.get("ORG", []))
    misc_raw = _take_strings(entidades.get("MISC", []))

    # ===== 2) Pessoas =====
    pessoas = []
    for p in per_raw:
        p_clean = re.sub(r"\s+", " ", p).strip()
        p_clean = _titlecase_preservando_siglas(p_clean)
        if _is_full_person_name(p_clean) or _is_allowed_nickname(p_clean):
            pessoas.append(p_clean)
    pessoas = _dedup_preservando_ordem(pessoas)

    # ===== 3) Organizações: heurística rápida =====
    # ORG vai para fila de classificação; MISC que parecem órgãos também.
    org_candidatos = list(org_raw)

    misc_org_like = [m for m in misc_raw if _looks_like_institution(m)]
    # Também empurra MISC em CAIXA-ALTA curta (provável sigla)
    misc_org_like += [m for m in misc_raw if re.fullmatch(r"[A-ZÁ-ÚÇ]{2,10}(\-[A-Z0-9]{1,6})?", m)]

    org_candidatos += misc_org_like
    # Normalização leve antes da decisão
    org_candidatos = [_titlecase_preservando_siglas(re.sub(r"\s+", " ", o).strip()) for o in org_candidatos]
    org_candidatos = _dedup_preservando_ordem([o for o in org_candidatos if o])

    empresas, instituicoes = [], []

    # Heurística inicial: se bater INSTITUTION_HINTS -> Instituição
    for o in org_candidatos:
        if _looks_like_institution(o):
            instituicoes.append(o)
        else:
            empresas.append(o)

    # ===== 4) Refinar com LLM (opcional) =====
    if use_llm and (empresas or instituicoes):
        if llm is None:
            llm = ChatOpenAI(model=model, temperature=temperature)
        # Vamos pedir ao LLM reclassificar o conjunto total, para corrigir a heurística
        # (empresas+instituições) -> classificação final
        classificados = _classificar_organizacoes_via_llm(empresas + instituicoes, llm=llm)
        empresas = _dedup_preservando_ordem(classificados.Empresas)
        instituicoes = _dedup_preservando_ordem(classificados.Instituicoes)

    # ===== 5) Saída
    return {
        "Pessoas": pessoas,
        "Instituições": instituicoes,
        "Empresas": empresas,
    }
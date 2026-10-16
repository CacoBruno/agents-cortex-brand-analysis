
from __future__ import annotations
from typing import Dict, List, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

from pydantic import BaseModel, Field  # ✅ Pydantic v2
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate


# ====== Esquema de saída (Pydantic v2) ======
class SaidaResumoTema(BaseModel):
    resumo: str = Field(..., description="Resumo em exatamente 3 linhas (separe com quebras de linha).")
    tema: str = Field(..., description="Tema curto (máx. 6 palavras).")


# ====== Prompt base ======
prompt = ChatPromptTemplate.from_messages(
    [
        ("system",
         "Você é um assistente de comunicação que resume, em português, conjuntos de textos "
         "de forma fiel, concisa e neutra."),
        ("human",
         "Tarefa:\n"
         "1) Produzir um resumo em 3 linhas (use exatamente 2 quebras de linha \\n).\n"
         "2) Criar um tema curto, máximo 6 palavras, sem ponto final.\n"
         "Regras:\n"
         "- Linguagem clara e factual; evite floreios.\n"
         "- Preserve números/datas/citações relevantes.\n\n"
         "# TEXTOS\n{corpus}")
    ]
)


# ====== Helpers ======
def _make_llm(model: str = "gpt-4o-mini", temperature: float = 0.2) -> ChatOpenAI:
    return ChatOpenAI(model=model, temperature=temperature)

def _split_in_chunks(texts: List[str], max_chars: int = 20000) -> List[str]:
    """
    Divide a lista de textos em blocos concatenados, limitando o tamanho do bloco.
    Útil para listas muito longas (map-reduce).
    """
    blocks, current = [], ""
    for t in texts:
        t = (t or "").strip()
        if not t:
            continue
        if len(current) + len(t) + 1 > max_chars:
            if current:
                blocks.append(current)
            current = t
        else:
            current = (current + "\n" + t) if current else t
    if current:
        blocks.append(current)
    return blocks or [""]  # garante ao menos 1 bloco

def _normalize_resumo(resumo: str) -> str:
    linhas = [l.strip() for l in resumo.splitlines() if l.strip()]
    if len(linhas) < 3:
        linhas = (linhas + [""] * 3)[:3]
    elif len(linhas) > 3:
        linhas = [linhas[0], linhas[1], " ".join(linhas[2:])]
    return "\n".join(linhas)

def _shorten_tema(tema: str, max_palavras: int = 6) -> str:
    palavras = tema.strip().split()
    return " ".join(palavras[:max_palavras])


# ====== Núcleo por ID ======
def _processar_um_id(pair: Tuple[str, List[str]], llm: ChatOpenAI) -> Tuple[str, Dict[str, str]]:
    """
    Processa um único ID -> lista de textos e retorna (id, {"resumo":..., "tema":...}).
    Usa map-reduce quando houver múltiplos blocos.
    """
    id_, textos = pair
    chunks = _split_in_chunks(textos)

    # Runnable com saída estruturada (Pydantic v2)
    structured = llm.with_structured_output(SaidaResumoTema)

    # Cadeia final (prompt -> llm estruturado)
    chain = prompt | structured

    # Se houver vários blocos: obter resumos parciais e consolidar
    if len(chunks) > 1:
        parciais = []
        for ch in chunks:
            parcial: SaidaResumoTema = chain.invoke({"corpus": ch})
            parciais.append(_normalize_resumo(parcial.resumo))
        # Consolida resumos parciais como corpus único
        corpus_final = "\n".join(parciais)
    else:
        corpus_final = chunks[0]

    saida: SaidaResumoTema = chain.invoke({"corpus": corpus_final})

    return id_, {
        "resumo": _normalize_resumo(saida.resumo),
        "tema": _shorten_tema(saida.tema, 6)
    }


# ====== Função principal ======
def resumir_e_tematizar_dict(
    dados: Dict[str, List[str]],
    *,
    model: str = "gpt-4o-mini",
    temperature: float = 0.2,
    max_workers: int = 6
) -> Dict[str, Dict[str, str]]:
    """
    Entrada: {id: [lista_de_textos]}
    Saída:   {id: {"resumo": <3 linhas>, "tema": <string curta>}}
    """
    llm = _make_llm(model=model, temperature=temperature)
    resultados: Dict[str, Dict[str, str]] = {}

    # Paraleliza por ID
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futs = {ex.submit(_processar_um_id, item, llm): item[0] for item in dados.items()}
        for fut in as_completed(futs):
            id_ = futs[fut]
            try:
                k, v = fut.result()
                resultados[k] = v
            except Exception as e:
                resultados[id_] = {
                    "resumo": "Não foi possível gerar o resumo para este ID.",
                    "tema": f"Erro de processamento ({type(e).__name__})"
                }
    return resultados


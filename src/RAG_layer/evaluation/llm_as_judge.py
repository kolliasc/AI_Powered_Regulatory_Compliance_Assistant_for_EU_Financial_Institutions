# import json
# import os
# import time
# from dataclasses import dataclass
# from typing import Any, Dict, List, Optional, Tuple

# import pandas as pd
# from pydantic import BaseModel, Field

# from langchain_core.messages import SystemMessage, HumanMessage

# from src.RAG_layer.evaluation.lib.llm_factory import LlmFactory

# # =========================
# # Configuration / Models
# # =========================

 

# sut_llm = LlmFactory(False).get_llm()  # (System Under Test), the "candidate" whose performance, accuracy, or safety you want to measure.

# judge_llm = LlmFactory(False).get_llm()

# SUT_SYSTEM = """You are a helpful assistant.
# If context is provided, use it as the primary source of truth.
# If you don't know, say you don't know.
# Be concise.
# """

# JUDGE_SYSTEM = """You are a strict automated evaluator for LLM outputs.

# You will receive:
# - question
# - context (may be empty)
# - model_answer

# Your job:
# 1) Relevance: does the answer address the question?
# 2) Faithfulness: if context is provided, does the answer ONLY contain claims supported by the context?
#    - If context is empty, mark faithfulness as "N/A" and score as null.
# 3) Provide clear reasons. Be conservative.

# Return a JSON object that matches the given schema exactly.
# Do not add extra keys.
# """

# class JudgeResult(BaseModel):
#     relevance_score: int = Field(..., ge=0, le=5, description="0-5 relevance score")
#     relevance_reason: str
#     faithfulness_score: Optional[int] = Field(
#         None, ge=0, le=5, description="0-5 faithfulness score; null if no context"
#     )
#     faithfulness_reason: str
#     overall_pass: bool = Field(..., description="True if meets threshold criteria")

# @dataclass
# class EvalCase:
#     id: str
#     question: str
#     context: str
#     expected: str = ""

# # =========================
# # IO helpers
# # =========================

# def load_jsonl(path: str) -> List[EvalCase]:
#     cases: List[EvalCase] = []
#     with open(path, "r", encoding="utf-8") as f:
#         for line in f:
#             obj = json.loads(line)
#             cases.append(
#                 EvalCase(
#                     id=str(obj.get("id")),
#                     question=str(obj.get("question", "")),
#                     context=str(obj.get("context", "")),
#                     expected=str(obj.get("expected", "")),
#                 )
#             )
#     return cases


# def save_json(path: str, data: Any) -> None:
#     with open(path, "w", encoding="utf-8") as f:
#         json.dump(data, f, ensure_ascii=False, indent=2)


# # =========================
# # SUT inference
# # =========================

# def run_sut(case: EvalCase) -> str:
#     # Put context explicitly; keep prompt stable
#     user_content = f"""Question:
# {case.question}

# Context:
# {case.context if case.context else "(none)"}

# Answer the question."""
#     messages = [
#         SystemMessage(content=SUT_SYSTEM), # added as system prompt so that LLM knows the rules, also if there are multiple invocations of the LLM, we need to add system message everytime (or every now and then) to remind it of the rules
#         HumanMessage(content=user_content),
#     ]
#     return sut_llm.invoke(messages).content.strip()

# # =========================
# # Judge (LLM evaluation)
# # =========================

# def judge_answer(case: EvalCase, model_answer: str) -> JudgeResult:
#     # Ask judge to produce *structured* output.
#     # We’ll request JSON and then parse with Pydantic for strictness.

#     thresholds = {
#         "relevance_min": 4,
#         "faithfulness_min": 4,
#     }

#     judge_user = f"""Evaluate this model output.

# question:
# {case.question}

# context:
# {case.context if case.context else "(none)"}

# model_answer:
# {model_answer}

# Evaluation rules:
# - relevance_score: 0..5
# - relevance_reason: Short justification as for the given relevance score
# - faithfulness_score: 0..5 if context is non-empty, else null
# - faithfulness_reason: Short justification as for the given faithfulness score
# - overall_pass: has the following criteria:
#   - relevance_score >= {thresholds["relevance_min"]}
#   - if context non-empty: faithfulness_score >= {thresholds["faithfulness_min"]}
#   - if context empty: ignore faithfulness for pass/fail

# Return ONLY valid JSON matching schema.
# do not add extra commentary or keys.
# do not use fencepost formatting. Return raw JSON.
# """
# # fencepost formatting refers to trailling commas, the name: If you want to build a fence 100 meters long with a post every 10 meters, how many posts do you need? The answer is 11
#     messages = [
#         SystemMessage(content=JUDGE_SYSTEM),
#         HumanMessage(content=judge_user),
#     ]

#     raw = judge_llm.invoke(messages).content.strip()
#     print(f"\nJudge raw output for case {case.id}:\n{raw}\n")  # Debugging aid
#     # Defensive JSON parse: some models may wrap in ```json ... ```
#     raw_clean = raw
#     if raw_clean.startswith("```"):
#         raw_clean = raw_clean.strip("`")
#         raw_clean = raw_clean.replace("json", "", 1).strip()

#     faithfulness_required = bool(case.context.strip())
#     try:
#         parsed = json.loads(raw_clean)
#     except Exception as e:
#         # Hard failure: return a structured "failed judge" result
#         return JudgeResult(
#             relevance_score=0,
#             relevance_reason=f"Judge output was not valid JSON. Error: {e}. Raw: {raw[:500]}",
#             faithfulness_score=None if not faithfulness_required else 0,
#             faithfulness_reason="Invalid judge JSON output.",
#             overall_pass=False,
#         )

#     # Normalize faithfulness for empty context, check prompt - we do not ask it to do the following:
#     if not faithfulness_required:
#         parsed["faithfulness_score"] = None
#         if not parsed.get("faithfulness_reason"):
#             parsed["faithfulness_reason"] = "N/A (no context provided)."

#     # Validate schema strictly
#     try:
#         print(parsed)
#         return JudgeResult(**parsed)
#     except Exception as e:
#         return JudgeResult(
#             relevance_score=0,
#             relevance_reason=f"Judge JSON failed schema validation: {e}. Parsed: {parsed}",
#             faithfulness_score=None if not faithfulness_required else 0,
#             faithfulness_reason="Schema validation failed.",
#             overall_pass=False,
#         )

# # =========================
# # Pipeline runner
# # =========================

# def run_pipeline(dataset_path: str) -> Tuple[pd.DataFrame, Dict[str, Any]]:
#     cases = load_jsonl(dataset_path)
#     rows: List[Dict[str, Any]] = []

#     t0 = time.time()

#     for case in cases:
#         answer = run_sut(case)
#         jr = judge_answer(case, answer)

#         rows.append({
#             "id": case.id,
#             "question": case.question,
#             "context_present": bool(case.context.strip()),
#             "expected": case.expected,
#             "model_answer": answer,

#             "relevance_score": jr.relevance_score,
#             "relevance_reason": jr.relevance_reason,

#             "faithfulness_score": jr.faithfulness_score,
#             "faithfulness_reason": jr.faithfulness_reason,

#             "overall_pass": jr.overall_pass,
#         })

#     df = pd.DataFrame(rows)

#     # Aggregations
#     summary = {
#         "sut_model": "gpt-4-turbo",
#         "judge_model": "gpt-4-turbo",
#         "dataset": dataset_path,
#         "num_cases": int(len(df)),
#         "pass_rate": float(df["overall_pass"].mean()) if len(df) else 0.0,
#         "avg_relevance": float(df["relevance_score"].mean()) if len(df) else 0.0,
#         "avg_faithfulness_over_context": float(
#             # collect all context_present rows, drop null values and take the mean
#             df[df["context_present"]]["faithfulness_score"].dropna().mean()
#         ) if len(df[df["context_present"]]) else None,
#         "duration_sec": round(time.time() - t0, 3),
#         # loc = row selection (overall pass) & column selection (id) collect all overall_pass that are false (~ symbol = NOT)
#         "failed_cases": df.loc[~df["overall_pass"], "id"].tolist(),
#     }

#     return df, summary

# dataset_path = "data/eval_dataset.jsonl"
# df, summary = run_pipeline(dataset_path)

# # Save artifacts
# os.makedirs("data/eval_outputs", exist_ok=True)
# df.to_csv("data/eval_outputs/results.csv", index=False) # false removes: By default, Pandas saves the row numbers (0, 1, 2...) as the first column in your CSV.
# save_json("data/eval_outputs/summary.json", summary)
# save_json("data/eval_outputs/results.json", df.to_dict(orient="records")) # records creates a list of dictionaries (json)

# # Console report (short)
# print("\n=== EVALUATION SUMMARY ===")
# for k, v in summary.items():
#     print(f"{k}: {v}")

# print("\nTop failures:")
# # fetch all that did not pass, and only give me the columns id, relevance_score and faithfulness score
# fails = df[~df["overall_pass"]][["id", "relevance_score", "faithfulness_score"]]
# if len(fails):
#     print(fails.to_string(index=False))
# else:
#     print("(none)")

import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
from pydantic import BaseModel, Field
from langchain_core.messages import SystemMessage, HumanMessage

# 1. Εισαγωγή των RAG modules της εφαρμογής σου
from src.RAG_layer.rag_pipeline import RAGPipeline
from src.RAG_layer.retriever import AzureOpenAIChatLLM
#from src.RAG_layer.llm import AzureOpenAIChatLLM
from src.data_ingestion.vector_store import ChromaVectorStore
from src.data_ingestion.embeddings import LocalEmbeddingModel      # Χρησιμοποιεί SentenceTransformer
from src.data_ingestion.context_builder import build_context  # Για το χτίσιμο του context
from src.config.settings import settings                      # Για να πάρουμε τα paths και settings

from src.RAG_layer.evaluation.lib.llm_factory import LlmFactory

# ==========================================
# Configuration / Αρχικοποίηση Πραγματικού RAG
# ==========================================

# Ο Judge (Δικαστής) παραμένει το Llama-3.3-70b στην Groq
judge_llm = LlmFactory(localLlm=False).get_llm()

# Αρχικοποιούμε τον embedder
my_embedder = LocalEmbeddingModel()

# Προσδιορίζουμε το μονοπάτι της ChromaDB (αν το settings δεν έχει Path object, το μετατρέπουμε)
chroma_path = Path(getattr(settings, "PERSIST_PATH", "data/vector_db"))

# Αρχικοποιούμε το Chroma Store περνώντας το Path που ζητάει ο constructor σου
my_vector_store = ChromaVectorStore(persist_path=chroma_path)

print("====================================")
print(f"📊 ΣΥΝΟΛΙΚΑ CHUNKS ΣΤΗ ΒΑΣΗ: {my_vector_store.count()}")
print("====================================")

# Αρχικοποιούμε το Azure OpenAI LLM (με το prompt των Levels 1-5)
my_sut_llm = AzureOpenAIChatLLM()

# Συνδέουμε τα πάντα στο RAG Pipeline σου
real_rag_pipeline = RAGPipeline(
    vector_store=my_vector_store,
    llm=my_sut_llm,
    embedder=my_embedder
)

JUDGE_SYSTEM = """You are a strict automated evaluator for LLM outputs.

You will receive:
- question
- context (may be empty)
- model_answer

Your job:
1) Relevance: does the answer address the question?
2) Faithfulness: if context is provided, does the answer ONLY contain claims supported by the context?
   - If context is empty, mark faithfulness as "N/A" and score as null.
3) Provide clear reasons. Be conservative.

Return a JSON object that matches the given schema exactly.
Do not add extra keys.
"""

class JudgeResult(BaseModel):
    relevance_score: int = Field(..., ge=0, le=5, description="0-5 relevance score")
    relevance_reason: str
    faithfulness_score: Optional[int] = Field(
        None, ge=0, le=5, description="0-5 faithfulness score; null if no context"
    )
    faithfulness_reason: str
    overall_pass: bool = Field(..., description="True if meets threshold criteria")

@dataclass
class EvalCase:
    id: str
    question: str
    context: str
    expected: str = ""

# =========================
# IO helpers
# =========================

def load_jsonl(path: str) -> List[EvalCase]:
    cases: List[EvalCase] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            obj = json.loads(line)
            cases.append(
                EvalCase(
                    id=str(obj.get("id")),
                    question=str(obj.get("question", "")),
                    context=str(obj.get("context", "")),
                    expected=str(obj.get("expected", "")),
                )
            )
    return cases

def save_json(path: str, data: Any) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ==========================================
# SUT inference (Εκτέλεση του δικού σου RAG)
# ==========================================

def run_sut(case: EvalCase) -> dict:
    """
    Στέλνει την ερώτηση στο RAG Pipeline και επιστρέφει 
    την απάντηση μαζί με τα retrieved chunks από τη ChromaDB.
    """
    return real_rag_pipeline.ask(question=case.question)

# =========================
# Judge (LLM evaluation)
# =========================

def judge_answer(case: EvalCase, model_answer: str, actual_context: str) -> JudgeResult:
    thresholds = {
        "relevance_min": 4,
        "faithfulness_min": 4,
    }

    judge_user = f"""Evaluate this model output.

question:
{case.question}

context:
{actual_context if actual_context else "(none)"}

model_answer:
{model_answer}

Evaluation rules:
- relevance_score: 0..5
- relevance_reason: Short justification as for the given relevance score
- faithfulness_score: 0..5 if context is non-empty, else null
- faithfulness_reason: Short justification as for the given faithfulness score
- overall_pass: has the following criteria:
  - relevance_score >= {thresholds["relevance_min"]}
  - if context non-empty: faithfulness_score >= {thresholds["faithfulness_min"]}
  - if context empty: ignore faithfulness for pass/fail

Return ONLY valid JSON matching schema.
do not add extra commentary or keys.
do not use fencepost formatting. Return raw JSON.
"""
    messages = [
        SystemMessage(content=JUDGE_SYSTEM),
        HumanMessage(content=judge_user),
    ]

    raw = judge_llm.invoke(messages).content.strip()
    print(f"\nJudge raw output for case {case.id}:\n{raw}\n")
    
    raw_clean = raw
    if raw_clean.startswith("```"):
        raw_clean = raw_clean.strip("`")
        raw_clean = raw_clean.replace("json", "", 1).strip()

    faithfulness_required = bool(actual_context.strip())
    try:
        parsed = json.loads(raw_clean)
    except Exception as e:
        return JudgeResult(
            relevance_score=0,
            relevance_reason=f"Judge output was not valid JSON. Error: {e}. Raw: {raw[:500]}",
            faithfulness_score=None if not faithfulness_required else 0,
            faithfulness_reason="Invalid judge JSON output.",
            overall_pass=False,
        )

    if not faithfulness_required:
        parsed["faithfulness_score"] = None
        if not parsed.get("faithfulness_reason"):
            parsed["faithfulness_reason"] = "N/A (no context provided)."

    try:
        print(parsed)
        return JudgeResult(**parsed)
    except Exception as e:
        return JudgeResult(
            relevance_score=0,
            relevance_reason=f"Judge JSON failed schema validation: {e}. Parsed: {parsed}",
            faithfulness_score=None if not faithfulness_required else 0,
            faithfulness_reason="Schema validation failed.",
            overall_pass=False,
        )

# =========================
# Pipeline runner
# =========================

def run_pipeline(dataset_path: str) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    cases = load_jsonl(dataset_path)
    rows: List[Dict[str, Any]] = []

    t0 = time.time()

    for case in cases:
        # 1. Εκτέλεση RAG (Chroma Retrieval + Azure OpenAI Generation)
        rag_output = run_sut(case)
        answer = rag_output["answer"]
        
        # 2. Ανακατασκευή του context από τα πραγματικά chunks που επέστρεψε η ChromaDB
        actual_context = build_context(rag_output["sources"])

        # 3. Ο δικαστής αξιολογεί την απάντηση με βάση τα chunks που διάβασε όντως το σύστημα
        jr = judge_answer(case, answer, actual_context)

        rows.append({
            "id": case.id,
            "question": case.question,
            "context_present": bool(actual_context.strip()),
            "expected": case.expected,
            "model_answer": answer,
            "relevance_score": jr.relevance_score,
            "relevance_reason": jr.relevance_reason,
            "faithfulness_score": jr.faithfulness_score,
            "faithfulness_reason": jr.faithfulness_reason,
            "overall_pass": jr.overall_pass,
        })

    df = pd.DataFrame(rows)

    # Δυναμική ανίχνευση ονομάτων μοντέλων
    sut_model_name = "Azure-OpenAI-Chat"
    judge_model_name = getattr(judge_llm, "model_name", "llama-3.3-70b-versatile")

    summary = {
        "sut_model": sut_model_name,
        "judge_model": judge_model_name,
        "dataset": dataset_path,
        "num_cases": int(len(df)),
        "pass_rate": float(df["overall_pass"].mean()) if len(df) else 0.0,
        "avg_relevance": float(df["relevance_score"].mean()) if len(df) else 0.0,
        "avg_faithfulness_over_context": float(
            df[df["context_present"]]["faithfulness_score"].dropna().mean()
        ) if len(df[df["context_present"]]) else None,
        "duration_sec": round(time.time() - t0, 3),
        "failed_cases": df.loc[~df["overall_pass"], "id"].tolist(),
    }

    return df, summary

if __name__ == "__main__":
    dataset_path = "data/eval_dataset.jsonl"
    df, summary = run_pipeline(dataset_path)

    # Αποθήκευση αποτελεσμάτων
    os.makedirs("data/eval_outputs", exist_ok=True)
    df.to_csv("data/eval_outputs/results.csv", index=False)
    save_json("data/eval_outputs/summary.json", summary)
    save_json("data/eval_outputs/results.json", df.to_dict(orient="records"))

    # Εκτύπωση αποτελεσμάτων στην κονσόλα
    print("\n=== EVALUATION SUMMARY ===")
    for k, v in summary.items():
        print(f"{k}: {v}")

    print("\nTop failures:")
    fails = df[~df["overall_pass"]][["id", "relevance_score", "faithfulness_score"]]
    if len(fails):
        print(fails.to_string(index=False))
    else:
        print("(none)")


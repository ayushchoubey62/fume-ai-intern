import ast
import json
import os
from typing import Any, Dict, List

import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel, Field

# Load environment variables
load_dotenv()

groq_api_key = os.getenv("GROQ_API_KEY")
openai_api_key = os.getenv("OPENAI_API_KEY")
selected_model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

if groq_api_key:
    client = OpenAI(api_key=groq_api_key, base_url="https://api.groq.com/openai/v1")
elif openai_api_key:
    client = OpenAI(api_key=openai_api_key)
else:
    client = None


# --- 1. DEFINE STRICT DATA MODELS (PYDANTIC) ---
# These models force the LLM to return only structured fields and preserve evidence grounding.

class SourceType(str):
    """Source type for every extracted field."""


class Metric(BaseModel):
    value: str = Field(description="The extracted value or 'N/A'.")
    evidence: str = Field(description="Exact word-for-word quote from the transcript, or 'None' if unavailable.")
    source_type: str = Field(description="Must be one of: confirmed_fact, client_reported, ai_inference, or missing")


class Metrics(BaseModel):
    nutrition_adherence: Metric
    exercise_steps: Metric
    sleep: Metric
    water_intake: Metric


class RiskFlag(BaseModel):
    flag: str = Field(description="The risk or attention flag identified from the transcript.")
    severity: str = Field(description="Low, Medium, or High")


class ClientIntelligence(BaseModel):
    weekly_summary: str = Field(description="A concise weekly summary in plain language.")
    metrics: Metrics
    symptoms_stress: Metric
    engagement_level: str = Field(description="High, Medium, or Low")
    key_barriers: List[str]
    pending_actions: List[str]
    risk_attention_flags: List[RiskFlag]
    recommended_next_action: str
    supporting_evidence: List[str] = Field(
        default_factory=list,
        description="Exact quotes that support the summary or notable observations. Use [] if none are available.",
    )


# --- 2. BACKEND LOGIC ---

def _safe_literal_eval(value: Any) -> Any:
    if isinstance(value, str):
        stripped = value.strip()
        if stripped.startswith("{") or stripped.startswith("["):
            try:
                return ast.literal_eval(stripped)
            except Exception:
                return value
    return value


def _get_text_value(payload: Any, fallback: str = "N/A") -> str:
    parsed = _safe_literal_eval(payload)
    if isinstance(parsed, dict):
        if "value" in parsed:
            return str(parsed.get("value") or fallback)
        return str(parsed)
    if isinstance(parsed, list):
        return str(parsed[0]) if parsed else fallback
    return str(parsed) if parsed is not None else fallback


def _metric_from_payload(payload: Any, fallback_value: str = "N/A") -> Dict[str, str]:
    parsed = _safe_literal_eval(payload)
    if isinstance(parsed, dict):
        return {
            "value": str(parsed.get("value") or parsed.get("metric") or fallback_value),
            "evidence": str(parsed.get("evidence") or parsed.get("quote") or parsed.get("support") or "None"),
            "source_type": str(parsed.get("source_type") or parsed.get("type") or "missing"),
        }

    return {
        "value": fallback_value,
        "evidence": "None",
        "source_type": "missing",
    }


def _list_from_payload(payload: Any) -> List[str]:
    parsed = _safe_literal_eval(payload)
    if isinstance(parsed, list):
        return [str(item) for item in parsed if item is not None]
    if isinstance(parsed, str):
        return [parsed] if parsed.strip() else []
    if isinstance(parsed, dict):
        value = parsed.get("value")
        if value is not None:
            return [str(value)]

        values = []
        for key in ("items", "values", "barriers", "actions", "flags"):
            if key in parsed:
                values.extend(_list_from_payload(parsed[key]))
        if values:
            return values

        return [str(parsed)]
    return []


def _risk_flags_from_payload(payload: Any) -> List[Dict[str, str]]:
    parsed = _safe_literal_eval(payload)
    if isinstance(parsed, list):
        result = []
        for item in parsed:
            if isinstance(item, dict):
                result.append({
                    "flag": str(item.get("flag") or item.get("name") or item.get("value") or "Unspecified risk"),
                    "severity": str(item.get("severity") or "Medium"),
                })
            elif isinstance(item, str):
                result.append({"flag": item, "severity": "Medium"})
        return result
    if isinstance(parsed, dict):
        return [{"flag": str(parsed.get("flag") or parsed.get("name") or parsed.get("value") or "Unspecified risk"), "severity": str(parsed.get("severity") or "Medium")}]
    return []


def _normalize_response_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    metrics = payload.get("metrics") if isinstance(payload.get("metrics"), dict) else {}
    alt = payload

    normalized_metrics = {
        "nutrition_adherence": _metric_from_payload(
            metrics.get("nutrition_adherence") or metrics.get("nutrition") or alt.get("nutrition_adherence") or alt.get("nutrition"),
            "N/A",
        ),
        "exercise_steps": _metric_from_payload(
            metrics.get("exercise_steps") or metrics.get("steps_taken") or metrics.get("exercise") or alt.get("exercise_steps") or alt.get("steps_taken") or alt.get("exercise"),
            "N/A",
        ),
        "sleep": _metric_from_payload(
            metrics.get("sleep") or alt.get("sleep") or alt.get("sleep_hours"),
            "N/A",
        ),
        "water_intake": _metric_from_payload(
            metrics.get("water_intake") or alt.get("water_intake") or alt.get("hydration"),
            "N/A",
        ),
    }

    symptoms = _metric_from_payload(
        payload.get("symptoms_stress") or payload.get("symptoms") or payload.get("stress")
    )

    normalized_payload = {
        "weekly_summary": str(payload.get("weekly_summary") or payload.get("summary") or "No weekly summary available."),
        "metrics": normalized_metrics,
        "symptoms_stress": symptoms,
        "engagement_level": _get_text_value(payload.get("engagement_level") or payload.get("engagement") or "Low"),
        "key_barriers": _list_from_payload(payload.get("key_barriers") or payload.get("barriers") or []),
        "pending_actions": _list_from_payload(payload.get("pending_actions") or payload.get("actions") or []),
        "risk_attention_flags": _risk_flags_from_payload(payload.get("risk_attention_flags") or payload.get("risk_flags") or []),
        "recommended_next_action": _get_text_value(payload.get("recommended_next_action") or payload.get("next_action") or "Review transcript manually with the coach."),
        "supporting_evidence": _list_from_payload(payload.get("supporting_evidence") or payload.get("evidence") or []),
    }

    return normalized_payload


def analyze_transcript(transcript: str) -> ClientIntelligence:
    if client is None:
        raise RuntimeError("No API key is configured. Add GROQ_API_KEY or OPENAI_API_KEY to your .env file before running the app.")

    prompt = f"""
    You are an AI assistant analyzing a coach-client transcript for a client intelligence workflow.

    Your job is to produce a concise, evidence-grounded weekly client report.

    CRITICAL INSTRUCTIONS:
    1. Use only information explicitly supported by the transcript.
    2. For every metric and every major claim, include an exact word-for-word quote under 'evidence'.
    3. Categorize each extracted metric as one of:
       - confirmed_fact
       - client_reported
       - ai_inference
       - missing
    4. If the transcript does not mention something, set the value to 'N/A' or 'missing' and the source_type to 'missing'.
    5. Do not fabricate numbers, symptoms, steps, hours, or adherence trends.
    6. Be conservative. When something is only implied, label it as 'ai_inference' and keep the evidence minimal.
    7. Keep the summary short, actionable, and easy for a coach to review.
    8. Return valid JSON only.
    9. Use the exact top-level keys: weekly_summary, metrics, symptoms_stress, engagement_level, key_barriers, pending_actions, risk_attention_flags, recommended_next_action, supporting_evidence.
    10. Under metrics, use exactly these nested keys: nutrition_adherence, exercise_steps, sleep, water_intake.

    Transcript:
    {transcript}
    """

    response = client.chat.completions.create(
        model=selected_model,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        temperature=0.2,
    )

    content = response.choices[0].message.content
    if not content:
        raise RuntimeError("The model returned an empty response. Please try again.")

    parsed = json.loads(content)
    normalized = _normalize_response_payload(parsed)
    return ClientIntelligence.model_validate(normalized)


def save_analysis(data: ClientIntelligence) -> None:
    os.makedirs("outputs", exist_ok=True)
    output_path = os.path.join("outputs", "latest_analysis.json")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(data.model_dump_json(indent=2))


# --- 3. STREAMLIT UI ---

st.set_page_config(page_title="FUME Client Intelligence", layout="wide")
st.title("🧠 GenAI Client Intelligence Platform")
st.caption("Prototype for FUME internship assignment: evidence-grounded client analysis with human review.")

if not groq_api_key and not openai_api_key:
    st.error("Missing GROQ_API_KEY / OPENAI_API_KEY. Add a valid API key to your .env file before generating analysis.")

transcript_input = st.text_area("Paste Transcript Here:", height=250)

if st.button("Generate Intelligence", type="primary"):
    if not transcript_input:
        st.warning("Please paste a transcript first.")
    elif not groq_api_key and not openai_api_key:
        st.warning("Please configure GROQ_API_KEY or OPENAI_API_KEY to run the analysis.")
    else:
        with st.spinner("Analyzing conversation..."):
            try:
                data = analyze_transcript(transcript_input)

                st.success("Analysis Complete!")

                st.header("📋 Weekly Summary")
                st.write(data.weekly_summary)

                if data.supporting_evidence:
                    with st.expander("Supporting Evidence"):
                        for item in data.supporting_evidence:
                            st.write(f"- “{item}”")

                st.header("📊 Core Metrics")

                def render_metric(label: str, metric_obj: Metric) -> None:
                    st.subheader(label)
                    st.write(f"**Value:** {metric_obj.value}")

                    source_color = "gray"
                    if metric_obj.source_type == "confirmed_fact":
                        source_color = "green"
                    elif metric_obj.source_type == "client_reported":
                        source_color = "blue"
                    elif metric_obj.source_type == "ai_inference":
                        source_color = "orange"
                    elif metric_obj.source_type == "missing":
                        source_color = "red"

                    st.markdown(f"**Source:** :{source_color}[{metric_obj.source_type}]")
                    st.write(f'*> "{metric_obj.evidence}"*')
                    st.divider()

                col1, col2 = st.columns(2)
                with col1:
                    render_metric("Nutrition Adherence", data.metrics.nutrition_adherence)
                    render_metric("Sleep", data.metrics.sleep)
                with col2:
                    render_metric("Exercise / Steps", data.metrics.exercise_steps)
                    render_metric("Water Intake", data.metrics.water_intake)

                st.header("⚠️ Risks & Barriers")
                st.write(f"**Engagement Level:** {data.engagement_level}")
                st.write("**Symptoms / Stress:**")
                st.write(f"- Value: {data.symptoms_stress.value}")
                st.write(f'- Evidence: "{data.symptoms_stress.evidence}"')
                st.write(f"- Source: {data.symptoms_stress.source_type}")

                st.write("**Key Barriers:**")
                for barrier in data.key_barriers:
                    st.write(f"- {barrier}")

                st.write("**Attention Flags:**")
                for flag in data.risk_attention_flags:
                    st.error(f"{flag.severity} Risk: {flag.flag}")

                st.header("🎯 Next Steps")
                st.write("**Pending Client Actions:**")
                for action in data.pending_actions:
                    st.write(f"- {action}")

                st.info(f"**Coach Recommendation:** {data.recommended_next_action}")

                st.header("Human Review")
                c1, c2, c3 = st.columns(3)
                if c1.button("✅ Approve to Database"):
                    save_analysis(data)
                    st.success("Approved and saved to outputs/latest_analysis.json")
                if c2.button("✏️ Edit Fields"):
                    st.info("Edit mode enabled. Connect this to a downstream review form or admin workflow for production use.")
                if c3.button("❌ Reject Analysis"):
                    st.error("Analysis discarded. Re-run with a corrected transcript or prompt if needed.")

                with st.expander("Structured JSON Output"):
                    st.json(data.model_dump())

            except Exception as e:
                st.error(f"An error occurred: {e}")
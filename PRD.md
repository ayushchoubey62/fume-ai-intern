# Product Requirements Document (PRD)
## GenAI Client Intelligence Mini-Case for FUME

## 1. Document Purpose
This PRD defines the product requirements for a lightweight prototype that analyzes a coach-client conversation and generates structured client intelligence for a coaching workflow. The goal is to help a coach quickly understand a client’s weekly status, track adherence to health behaviors, identify risks, and decide the next best action.

The prototype is intentionally not production-grade. It is designed to demonstrate:
- problem understanding
- evidence grounding
- hallucination awareness
- structured output design
- practical implementation using simple AI tooling

---

## 2. Product Summary
### Product Name
FUME Client Intelligence Assistant

### One-line Summary
A GenAI-powered assistant that converts a client-coach transcript into a structured, evidence-backed weekly client intelligence report with a human-review workflow.

### Problem Statement
Coaches currently need to manually review long transcripts and extract multiple behavioral and health insights such as adherence, symptoms, barriers, pending actions, and risk flags. This is time-consuming, inconsistent, and prone to missing critical signals.

### Opportunity
A simple AI assistant can reduce manual effort by summarizing the conversation, extracting structured metrics, tagging the source of each insight, and surfacing actions for the coach. The output should be trustworthy enough for a coach to review and approve instead of reading the entire transcript.

---

## 3. Goals
### Primary Goals
1. Extract meaningful client intelligence from a transcript.
2. Provide a structured weekly report with supporting evidence.
3. Separate facts from inference and missing information.
4. Help the coach identify action items and attention flags quickly.
5. Provide a review loop for human approval, editing, or rejection.

### Secondary Goals
1. Demonstrate AI product thinking with a low-friction user experience.
2. Show how hallucination risk can be controlled using constrained output and evidence quotes.
3. Highlight a practical MVP implementation path for future productization.

---

## 4. Non-Goals
1. Full clinical advice or diagnosis
2. Real-time analytics dashboard
3. Multi-user collaboration or governance admin panel
4. Production compliance, audit trail, and enterprise security controls
5. Calibration of medical-grade recommendations

---

## 5. Target Users
### Primary User: Coach
A human coach who wants to understand a client’s recent progress and next-best actions without manually reading every conversation.

### Secondary User: Operations / Product Reviewer
A staff member evaluating whether AI outputs are understandable, grounded, and safe for human review.

---

## 6. User Needs
The coach wants to:
- understand the client’s recent habits and current state quickly
- see what is objectively confirmed versus what the client merely reported
- identify barriers and risk signals early
- know what follow-up action is recommended
- review the AI output and override or reject if necessary

---

## 7. Core User Journey
1. A coach uploads or pastes a client-coach transcript.
2. The system analyzes the transcript.
3. The system generates a structured weekly intelligence summary.
4. The coach reviews the summary, evidence, risk flags, and recommended next action.
5. The coach approves, edits, or rejects the output.

---

## 8. Functional Requirements
### FR1: Transcript Input
The system shall accept a transcript as pasted text or uploaded text content.

### FR2: Structured Output Generation
The system shall produce a weekly report containing:
- weekly client summary
- nutrition adherence
- exercise / steps
- sleep
- water intake
- symptoms / stress
- engagement level
- key barriers
- pending actions
- risk / attention flags
- recommended next action for the coach
- supporting evidence

### FR3: Evidence Grounding
Every extracted metric or claim must include supporting textual evidence from the input conversation.

### FR4: Source Classification
Every metric and claim shall be tagged as one of the following:
- confirmed_fact
- client_reported
- ai_inference
- missing

### FR5: Human Review
The system shall provide a review mechanism with the following options:
- Approve
- Edit
- Reject

### FR6: Risk Visibility
The system shall highlight elevated risks such as severe stress, poor adherence, missed follow-up, or concerning symptoms.

### FR7: Prompted Workflow
The system shall use a deterministic analysis workflow and a structured output schema that reduces free-form output ambiguity.

### FR8: Error Handling
If the transcript is empty, poorly formatted, or missing useful content, the system shall return a safe message rather than fabricate information.

---

## 9. Non-Functional Requirements
### NFR1: Trust and Safety
The outputs must avoid unsupported claims and clearly label inference.

### NFR2: Transparency
The system should expose the evidence it used and the confidence level of the interpretation.

### NFR3: Usability
The interface must be simple and lightweight, with clear sections for summary, metrics, and review actions.

### NFR4: Reliability
The system should fail gracefully when AI response generation does not return valid structured data.

---

## 10. Information Architecture
### Main Screen Sections
1. Transcript input box
2. Generate Intelligence button
3. Weekly summary panel
4. Metrics panel
5. Barriers and risk flags panel
6. Pending actions and next-step recommendation panel
7. Human review controls

---

## 11. Proposed Workflow / Prompt Logic
### Step 1: Input Reception
Accept transcript text from the user.

### Step 2: Context Setting
The system instructs the model to behave as a structured analysis assistant for coaching conversations.

### Step 3: Extraction Rules
The model must:
- find explicit values from the transcript
- quote exact evidence
- classify each output as confirmed fact, client-reported, AI inference, or missing
- avoid inventing missing details

### Step 4: Output Normalization
The model returns a structured JSON object using a strict schema.

### Step 5: Human Review
The coach reviews the generated intelligence and approves, edits, or rejects it.

---

## 12. Suggested Prompt Workflow
A simple prompt structure should look like this:

You are an AI assistant helping a coach understand a client’s weekly status from a transcript.

Your task:
1. Read the transcript carefully.
2. Extract the following fields:
   - weekly summary
   - nutrition adherence
   - exercise / steps
   - sleep
   - water intake
   - symptoms / stress
   - engagement level
   - key barriers
   - pending actions
   - risk / attention flags
   - recommended next action
3. For every metric or statement, include evidence from the transcript.
4. Categorize every extracted item using one of the following labels:
   - confirmed_fact
   - client_reported
   - ai_inference
   - missing
5. Do not invent missing information.
6. Keep the output structured and safe for human review.

Transcript:
<user pasted transcript>

---

## 13. Suggested Structured Output Schema
```json
{
  "weekly_summary": "string",
  "metrics": {
    "nutrition_adherence": {
      "value": "string",
      "evidence": "string",
      "source_type": "confirmed_fact | client_reported | ai_inference | missing"
    },
    "exercise_steps": {
      "value": "string",
      "evidence": "string",
      "source_type": "confirmed_fact | client_reported | ai_inference | missing"
    },
    "sleep": {
      "value": "string",
      "evidence": "string",
      "source_type": "confirmed_fact | client_reported | ai_inference | missing"
    },
    "water_intake": {
      "value": "string",
      "evidence": "string",
      "source_type": "confirmed_fact | client_reported | ai_inference | missing"
    }
  },
  "symptoms_stress": {
    "value": "string",
    "evidence": "string",
    "source_type": "confirmed_fact | client_reported | ai_inference | missing"
  },
  "engagement_level": "High | Medium | Low",
  "key_barriers": ["string"],
  "pending_actions": ["string"],
  "risk_attention_flags": [
    {
      "flag": "string",
      "severity": "Low | Medium | High"
    }
  ],
  "recommended_next_action": "string"
}
```

---

## 14. Hallucination Control Strategy
The product should explicitly control hallucination risk through the following design choices:

1. Source-based tagging
   - Every output item is tied to a source type.

2. Evidence quotations
   - The system includes exact phrase quotes from the transcript.

3. Missing-value handling
   - If information is absent, the system should state "N/A" or "missing" rather than infer.

4. Structured schema enforcement
   - JSON output should follow a strict schema so the model does not drift into free-form content.

5. Human review step
   - The coach remains responsible for final acceptance.

---

## 15. Hallucination / Failure Scenarios
### Scenario 1: False Medical Inference
The model infers that the client has anxiety or a health risk even though the transcript only implies stress.

### Scenario 2: Unsupported Numeric Conversion
The model manufactures a daily step count, calorie count, or hydration total that was never explicitly stated.

### Scenario 3: Misattributed Evidence
The model quotes a coach sentence as if it were a client fact, or vice versa.

### Scenario 4: Missing Context Unclear
The transcript is short or incomplete, and the model tries to produce a confident weekly summary anyway.

---

## 16. Success Metrics
### Product Success Signals
- The coach can extract core insights in under 2 minutes.
- Every major metric includes evidence.
- The output uses clear source labels.
- The model avoids unsupported claims in most test cases.
- The review workflow is intuitive enough for manual intervention.

### Quality Metrics
- precision of extracted facts
- rate of unsupported inference
- evidence coverage ratio
- coach approval rate after review

---

## 17. UI / UX Requirements
### UX Principles
- fast
- readable
- evidence-first
- low-friction
- reliable for human review

### UI Features
- transcript input area
- generate analysis button
- indicators for source type
- risk banners
- simple approve / edit / reject actions

---

## 18. Technical Approach (MVP)
### Proposed Stack
- Streamlit for the front end
- OpenAI structured output API for deterministic extraction
- Pydantic schema for response validation
- Python dotenv for environment configuration

### MVP Capability
The MVP should deliver:
- transcript intake
- LLM-based extraction
- structured JSON output
- evidence display
- source classification
- human review actions

---

## 19. Acceptance Criteria
A release candidate is acceptable if:
1. The user can paste a transcript and generate a structured report.
2. The report includes all requested output domains.
3. Each key metric provides supporting evidence.
4. Source labels identify confirmed fact, client-reported information, inference, or missing data.
5. The app presents a human review workflow.
6. The app does not fabricate missing details.

---

## 20. Risks and Mitigations
### Risk: Hallucinated outputs
Mitigation: enforce schema, require evidence, label inference clearly.

### Risk: Misleading confidence
Mitigation: present visible source types rather than absolute certainty.

### Risk: Weak transcript quality
Mitigation: detect missing or ambiguous content and return safe output.

### Risk: User overtrusting AI outputs
Mitigation: include human review and explicit evidence-based display.

---

## 21. Future Enhancements
1. Add transcript upload from PDF or audio transcription.
2. Introduce confidence scores per extracted metric.
3. Add dashboard history for clients and coaches.
4. Integrate follow-up automation or reminders.
5. Add multi-turn chat for coach clarifications.

---

## 22. Final Product Vision
The end-state product is a coach-facing AI intelligence layer that summarizes client conversations, detects meaningful changes in behavior, identifies risk, and recommends next actions with traceable evidence. The product should be trustworthy enough for a human to inspect and approve quickly, rather than blindly trust the model.

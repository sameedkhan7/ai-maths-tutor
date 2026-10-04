# AI Maths Tutor — Known Limitations

## 1. Question Type Detection

Question type detection is currently rule-based.

It uses keywords and simple patterns to detect:

- concept
- numerical
- homework
- follow-up
- student mistake
- explain_again

Complex or ambiguous questions may sometimes be classified incorrectly.

---

## 2. Explanation Style Detection

Explanation styles are controlled by predefined instructions.

Supported styles:

- simple
- real_life
- story
- sports
- daily_life
- exam
- step_by_step
- beginner
- visual_words
- math_only

The model may not follow a style perfectly in every response.

---

## 3. RAG Dependency

The AI module can use RAG context provided by the retrieval system.

Answer quality for document-based questions depends on:

- retrieval quality
- relevance of retrieved chunks
- chunk content
- source information

The AI module does not create or retrieve documents itself.

---

## 4. Chat History

Only a limited amount of recent conversation history is sent to the model.

This prevents unnecessarily large prompts but means very old conversation details may not be available.

---

## 5. Model Output

The Groq model generates responses dynamically.

Because of this, responses may vary between requests.

The prompt instructs the model to avoid LaTeX, but occasional formatting mistakes may still occur.

---

## 6. API Dependency

The tutor depends on the Groq API.

If the API is unavailable, the API key is missing, or a request fails repeatedly, the system returns an error through the `error` field.

---

## 7. Mathematics Scope

The system is designed primarily for mathematics learning.

It is not intended to act as a general-purpose tutor for unrelated subjects.

---

## 8. No Guaranteed Mathematical Perfection

The model can make mathematical or reasoning mistakes.

Important answers should be verified when accuracy is critical.

---

## 9. Current Architecture

The AI module is intentionally kept simple.

It does not currently use:

- LangChain
- autonomous agents
- multiple AI agents
- complex orchestration frameworks

The module directly connects:

Question → Intent → Context → Prompt → Groq → Response
"""
ask_generic.py — T2 Generic AI Arm
Plain Claude without RAG knowledge base.
Used as comparison group (T2) in Kenya MSME research study.
Provides generic AI responses without Kenyan knowledge base.
"""

import anthropic


def ask_generic_claude(api_key: str, question: str, history: list, lang: str) -> str:
    """
    Ask Claude without any RAG context.
    This is the T2 (generic/Western AI) comparison arm.
    No Kenyan knowledge base — just Claude's general training data.
    """
    client = anthropic.Anthropic(api_key=api_key)

    lang_instructions = {
        "kiswahili": "Jibu kwa Kiswahili tu.",
        "english":   "Respond in clear, simple English.",
        "dholuo":    "Respond in Kiswahili.",
        "kikuyu":    "Respond in Kiswahili.",
        "kalenjin":  "Respond in Kiswahili.",
        "kamba":     "Respond in Kiswahili.",
    }

    system = f"""You are a general business advisor helping small business owners.
You provide general business guidance based on your training knowledge.
LANGUAGE: {lang_instructions.get(lang, "Respond in English.")}

You can help with general business topics like registration, taxes, loans, 
and business management. Provide helpful general advice.

Note: You do not have access to specific local regulatory documents.
Provide general guidance and recommend consulting local authorities for 
specific requirements."""

    messages = []
    for turn in history[-3:]:
        messages += [
            {"role": "user",      "content": turn["user"]},
            {"role": "assistant", "content": turn["assistant"]},
        ]
    messages.append({"role": "user", "content": question})

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1200,
        system=system,
        messages=messages,
    )
    return response.content[0].text

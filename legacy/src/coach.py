"""
coach.py — GPT Coach Mode for Kenya MSME Advisor
Inspired by the Bahamas AI Literacy project (Christophe et al., 2026)
Adds AI literacy coaching on top of the RAG advisory system.

Features:
- Prompt quality scoring
- Follow-up question suggestions
- Lean innovation framework guidance
- AI literacy tips
- Business idea validation framework
"""

import anthropic
import streamlit as st


LEAN_INNOVATION_STAGES = [
    "Problem Discovery",
    "Customer Validation", 
    "Solution Design",
    "MVP Testing",
    "Growth & Scale",
]

PROMPT_TIPS = {
    "too_short": "Your question is quite brief. Try adding more context — mention your business type, location, or specific situation for a better answer.",
    "too_vague": "Your question is broad. Try being specific — for example, instead of 'how do I get money?', ask 'how do I apply for the Hustler Fund as a mama mboga in Nairobi?'",
    "good":      "Good question! You gave enough context for a focused answer.",
    "excellent": "Excellent question! Very specific and contextual — you'll get a highly relevant answer.",
}


def score_prompt(question: str) -> dict:
    """Score the quality of a user's prompt and give feedback."""
    words = question.split()
    length = len(words)
    
    # Check for specific keywords that indicate good prompting
    specific_indicators = [
        "nairobi", "mombasa", "kisumu", "nakuru", "county",
        "my business", "i want to", "i need to", "how much",
        "what documents", "step by step", "kra", "nssf", "nhif",
        "hustler fund", "yedf", "sacco", "mpesa", "register",
    ]
    vague_indicators = ["help", "money", "business", "tell me", "what is"]
    
    specificity = sum(1 for w in specific_indicators if w in question.lower())
    vagueness   = sum(1 for w in vague_indicators   if w in question.lower())
    
    if length < 5:
        score, feedback_key = 2, "too_short"
    elif length < 8 and specificity == 0:
        score, feedback_key = 4, "too_vague"
    elif specificity >= 2 or length > 15:
        score, feedback_key = 9, "excellent"
    else:
        score, feedback_key = 7, "good"
    
    return {
        "score":    score,
        "feedback": PROMPT_TIPS[feedback_key],
        "stars":    "⭐" * (score // 2),
    }


def get_coach_insights(api_key: str, question: str, answer: str, lang: str) -> dict:
    """Use Claude to generate coaching insights after answering."""
    client = anthropic.Anthropic(api_key=api_key)
    
    lang_instruction = {
        "kiswahili": "Jibu YOTE kwa Kiswahili tu. Usitumie Kiingereza kabisa.",
        "english":   "Respond entirely in English only.",
        "dholuo":    "Respond in Kiswahili only.",
        "kikuyu":    "Respond in Kiswahili only.",
        "kalenjin":  "Respond in Kiswahili only.",
        "kamba":     "Respond in Kiswahili only.",
    }.get(lang, "Respond entirely in English only.")

    system = f"""You are an AI literacy coach helping Kenyan MSME owners 
get better at using AI advisory tools. Be concise, practical, and encouraging.
LANGUAGE RULE: {lang_instruction}
Never mix languages. Use only one language throughout your entire response."""

    prompt = f"""The user asked: "{question}"
The AI advisor answered with information about Kenyan business regulations.

Generate a JSON response with exactly these fields:
{{
  "follow_up_questions": ["question1", "question2", "question3"],
  "lean_tip": "One sentence connecting this to lean business validation",
  "literacy_tip": "One sentence teaching the user how to ask better AI questions",
  "next_action": "The single most important action step the user should take today"
}}

Keep each item to 1-2 sentences maximum. Be specific to Kenya."""

    try:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=600,
            system=system,
            messages=[{"role": "user", "content": prompt}],
        )
        import json, re
        text = response.content[0].text
        # Extract JSON from response
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            return json.loads(match.group())
    except Exception:
        pass
    
    # Fallback
    return {
        "follow_up_questions": [
            "What are the specific costs involved?",
            "What documents do I need to prepare?",
            "How long does this process take?",
        ],
        "lean_tip": "Validate this step with one real customer before investing time and money.",
        "literacy_tip": "Add your business type and location to get more specific answers.",
        "next_action": "Write down the key steps from this answer and take the first one today.",
    }


def validate_business_idea(api_key: str, idea: str) -> dict:
    """Run a lean innovation validation on a business idea."""
    client = anthropic.Anthropic(api_key=api_key)
    
    prompt = f"""A Kenyan entrepreneur has this business idea: "{idea}"
    
Apply the lean innovation framework and respond in JSON:
{{
  "problem_fit": "Does this solve a real problem? Rate 1-10 and explain in 1 sentence",
  "market_size": "Estimate the Kenyan market size in simple terms",
  "mvp_suggestion": "The simplest way to test this idea in 1 week with under KES 5,000",
  "key_risks": ["risk1", "risk2", "risk3"],
  "regulatory_note": "Key Kenyan regulations or licenses needed",
  "next_step": "The single most important action to take tomorrow"
}}"""

    try:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=800,
            system="You are a lean startup coach specialising in Kenyan MSMEs.",
            messages=[{"role": "user", "content": prompt}],
        )
        import json, re
        text = response.content[0].text
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            return json.loads(match.group())
    except Exception:
        pass
    return {}


def render_coach_panel(api_key: str, question: str, answer: str, lang: str):
    """Render the coach mode panel below an answer."""
    
    # Prompt quality score
    score_data = score_prompt(question)
    
    with st.expander("🎓 AI Coach Insights", expanded=True):
        
        # Prompt quality
        col1, col2 = st.columns([1, 3])
        with col1:
            st.metric("Prompt Quality", f"{score_data['score']}/10")
        with col2:
            st.caption(f"{score_data['stars']} {score_data['feedback']}")
        
        st.divider()
        
        # Get AI coaching insights
        with st.spinner("Coach is thinking..."):
            insights = get_coach_insights(api_key, question, answer, lang)
        
        # Next action
        st.markdown("**🎯 Your Next Action**")
        st.success(insights.get("next_action", ""))
        
        # Follow-up questions
        st.markdown("**💡 Follow-up Questions to Ask**")
        import time as _time
        _ts = str(int(_time.time() * 1000))[-6:]
        for i, q in enumerate(insights.get("follow_up_questions", [])[:3]):
            if st.button(f"❓ {q}", key=f"coach_followup_{i}_{_ts}_{i}",
                        use_container_width=True):
                st.session_state["prefill"] = q
                st.rerun()
        
        # Lean innovation tip
        st.markdown("**🚀 Lean Innovation Tip**")
        st.info(insights.get("lean_tip", ""))
        
        # AI literacy tip
        st.markdown("**🤖 AI Literacy Tip**")
        st.warning(insights.get("literacy_tip", ""))


def render_idea_validator(api_key: str):
    """Render the business idea validator widget."""
    st.markdown("### 💡 Business Idea Validator")
    st.caption("Test your business idea using the Lean Innovation framework")
    
    idea = st.text_area(
        "Describe your business idea",
        placeholder="e.g. I want to sell fresh vegetables door-to-door in Westlands using WhatsApp orders...",
        height=100,
    )
    
    if st.button("🔍 Validate My Idea", type="primary", use_container_width=True):
        if idea.strip():
            with st.spinner("Analysing your idea..."):
                result = validate_business_idea(api_key, idea)
            
            if result:
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**Problem Fit**")
                    st.info(result.get("problem_fit", ""))
                    st.markdown("**Market Size**")
                    st.info(result.get("market_size", ""))
                with col2:
                    st.markdown("**MVP to Test in 1 Week**")
                    st.success(result.get("mvp_suggestion", ""))
                    st.markdown("**Regulatory Note**")
                    st.warning(result.get("regulatory_note", ""))
                
                st.markdown("**⚠️ Key Risks**")
                for risk in result.get("key_risks", []):
                    st.markdown(f"- {risk}")
                
                st.markdown("**🎯 Next Step**")
                st.success(result.get("next_step", ""))
        else:
            st.warning("Please describe your business idea first.")

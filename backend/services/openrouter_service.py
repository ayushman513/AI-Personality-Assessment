import httpx # Use httpx for async requests
import json
import random
import asyncio
import logging
from typing import List, Dict, Optional

from models import Question, Answer, TraitScore
from config import settings, QUESTION_POOL # Import settings and the loaded question pool

logger = logging.getLogger(__name__)

# --- OpenRouter API Interaction ---

# Use a shared client instance for potential connection pooling
_http_client: Optional[httpx.AsyncClient] = None

def get_http_client() -> httpx.AsyncClient:
    """Returns a shared httpx.AsyncClient instance."""
    global _http_client
    if _http_client is None:
        # Configure timeouts (important for production)
        timeout = httpx.Timeout(10.0, read=60.0) # 10s connect, 60s read
        _http_client = httpx.AsyncClient(timeout=timeout)
    return _http_client

async def shutdown_http_client():
    """Closes the shared httpx client."""
    global _http_client
    if _http_client:
        await _http_client.aclose()
        _http_client = None
    logger.info("HTTP client shut down.")


async def call_openrouter_api(prompt: str, model: str) -> Optional[Dict]:
    """
    Makes an asynchronous call to the OpenRouter Chat Completions API.

    Args:
        prompt: The user prompt for the LLM.
        model: The specific OpenRouter model string (e.g., "google/gemini-flash-1.5").

    Returns:
        The parsed JSON response from OpenRouter or None if an error occurs.
    """
    if not settings.OPENROUTER_API_KEY:
        logger.error("OpenRouter API Key is not configured. Cannot make API call.")
        return None

    client = get_http_client()
    headers = {
        "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        # Optional: Add HTTP Referer or other headers if needed by OpenRouter/your setup
        # "HTTP-Referer": "YOUR_SITE_URL",
        # "X-Title": "YOUR_SITE_NAME",
    }
    data = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        # Consider adding other parameters: max_tokens, temperature, response_format (if available for model)
        # "response_format": {"type": "json_object"}, # Use if model supports JSON mode reliably
        "max_tokens": 1024, # Adjust as needed
        "temperature": 0.5, # Lower temp for more deterministic analysis
    }
    api_url = "https://openrouter.ai/api/v1/chat/completions"

    try:
        logger.info(f"Calling OpenRouter API. Model: {model}. Prompt length: {len(prompt)} chars.")
        response = await client.post(api_url, headers=headers, json=data)
        response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
        logger.info(f"OpenRouter API call successful. Status: {response.status_code}")
        return response.json()

    except httpx.TimeoutException as e:
        logger.error(f"OpenRouter API call timed out: {e}")
        return None
    except httpx.RequestError as e:
        # Network-related errors
        logger.error(f"OpenRouter API request error: {e}")
        return None
    except httpx.HTTPStatusError as e:
        # Errors like 4xx, 5xx
        response_text = "<no response body>"
        try:
             # Try to read response body for more context, but guard against errors reading it
             response_text = await e.response.aread()
             response_text = response_text.decode('utf-8', errors='replace')[:500] # Limit length
        except Exception as read_err:
             logger.error(f"Error reading response body during HTTPStatusError handling: {read_err}")

        logger.error(f"OpenRouter API HTTP status error: {e.status_code} - {e.response.reason_phrase}. Response snippet: {response_text}")

        # Specific handling for common errors
        if e.response.status_code == 401: # Unauthorized
             logger.error("Check if OPENROUTER_API_KEY is correct.")
        elif e.response.status_code == 402: # Quota Exceeded?
             logger.error("OpenRouter quota likely exceeded. Check your account.")
        elif e.response.status_code == 400: # Bad Request (often prompt issues or model parameters)
             logger.error("Bad request sent to OpenRouter. Check prompt format and parameters.")

        return None
    except json.JSONDecodeError as e:
        logger.error(f"Failed to decode JSON response from OpenRouter: {e}")
        return None
    except Exception as e:
        logger.exception(f"An unexpected error occurred during OpenRouter call: {e}") # Use exception to log traceback
        return None


# --- Service Functions ---

def get_next_question_from_pool(asked_question_ids: List[str]) -> Optional[Question]:
    """
    Selects the next question from the configured pool, avoiding repetition.
    """
    available_questions = [q for q in QUESTION_POOL if q['id'] not in asked_question_ids]

    if not available_questions:
        logger.info("No more unique questions available in the pool.")
        return None

    # Simple random selection for now. Could add logic to target traits.
    chosen_question_data = random.choice(available_questions)
    logger.info(f"Selected question ID {chosen_question_data['id']} from pool.")

    return Question(
        id=chosen_question_data['id'], # Use the ID from the pool
        text=chosen_question_data['text'],
        targeted_trait=chosen_question_data.get('trait')
    )


async def analyze_responses_for_profile(candidate_id: str, answers: List[Answer], questions: List[Question]) -> Optional[List[TraitScore]]:
    """
    Analyzes responses using the configured Gemini model via OpenRouter to generate Big Five scores.
    """
    logger.info(f"Starting Big Five analysis for candidate {candidate_id} using {settings.OPENROUTER_MODEL_ANALYSIS}.")

    if not answers:
        logger.warning(f"No answers provided for analysis for candidate {candidate_id}.")
        return None
    if not settings.OPENROUTER_API_KEY:
         logger.error("Cannot perform analysis: OpenRouter API Key is missing.")
         return None # Or raise an internal server error

    # --- Construct the Prompt ---
    prompt_lines = [
        "Analyze the following behavioral interview responses to assess the candidate's personality based on the Big Five model (Openness, Conscientiousness, Extraversion, Agreeableness, Neuroticism).",
        "\nFor each of the five traits, provide:",
        "1. A score from 0 to 100, where 0 is extremely low and 100 is extremely high on the trait.",
        "2. A brief insight (1-2 sentences) explaining the reasoning for the score, based *only* on the provided text.",
        "\nOutput the result STRICTLY in the following JSON format:",
        """
[
  {
    "trait": "Openness",
    "score": <integer_score_0_to_100>,
    "insights": "<brief_insight_string>"
  },
  {
    "trait": "Conscientiousness",
    "score": <integer_score_0_to_100>,
    "insights": "<brief_insight_string>"
  },
  {
    "trait": "Extraversion",
    "score": <integer_score_0_to_100>,
    "insights": "<brief_insight_string>"
  },
  {
    "trait": "Agreeableness",
    "score": <integer_score_0_to_100>,
    "insights": "<brief_insight_string>"
  },
  {
    "trait": "Neuroticism",
    "score": <integer_score_0_to_100>,
    "insights": "<brief_insight_string>"
  }
]""",
        "\nCandidate's Responses:",
        "---"
    ]

    # Map question text for easy lookup
    question_texts = {q.id: q.text for q in questions}
    candidate_responses = ""
    for answer in answers:
        question_text = question_texts.get(answer.question_id, "[Question Text Not Found]")
        candidate_responses += f"Question: {question_text}\n"
        candidate_responses += f"Answer: {answer.response}\n"
        candidate_responses += "---\n"

    # Construct the final prompt as a single string with candidate responses inserted
    final_prompt = f"""
                Analyze the following behavioral interview responses to assess the candidate's personality based on the Big Five model (Openness, Conscientiousness, Extraversion, Agreeableness, Neuroticism).

                Persona for Evaluation:

                You are an expert behavioral interviewer and personality assessment specialist with deep knowledge of the Big Five model. Your task is to evaluate candidate responses solely based on the provided text. If a candidate’s answer is minimal, vague, or consists of non-informative content (e.g., a single letter such as “g” or “s”), you should reflect that lack of detail in your scores. Do not default to a score of 50 for every trait when the response does not contain enough information; instead, adjust scores to reflect the low level of engagement and insight provided. Use the following considerations for each trait:

                Openness: Evaluate the candidate’s creativity, curiosity, and willingness to consider new ideas. Minimal responses indicate low openness.

                Conscientiousness: Assess the candidate’s attention to detail, thoroughness, and reliability. A trivial answer suggests a lack of conscientious reflection.

                Extraversion: Consider the candidate’s communication style and engagement. Insufficient responses may indicate low extraversion or a lack of communicative detail.

                Agreeableness: Look for signs of cooperation, warmth, and empathy. Brief or curt responses might reflect lower agreeableness.

                Neuroticism: Determine the candidate’s emotional stability. Limited responses can imply uncertainty about emotional expression, so adjust the score based on the tone and context provided.

                Instructions:

                For each of the five traits, provide:

                A score from 0 to 100, where 0 is extremely low and 100 is extremely high on the trait.

                A brief insight (1-2 sentences) explaining your reasoning for the score, based only on the provided text.

                Output the result STRICTLY in the following JSON format:
                [
                {{
                    "trait": "Openness",
                    "score": <integer_score_0_to_100>,
                    "insights": "<brief_insight_string>"
                }},
                {{
                    "trait": "Conscientiousness",
                    "score": <integer_score_0_to_100>,
                    "insights": "<brief_insight_string>"
                }},
                {{
                    "trait": "Extraversion",
                    "score": <integer_score_0_to_100>,
                    "insights": "<brief_insight_string>"
                }},
                {{
                    "trait": "Agreeableness",
                    "score": <integer_score_0_to_100>,
                    "insights": "<brief_insight_string>"
                }},
                {{
                    "trait": "Neuroticism",
                    "score": <integer_score_0_to_100>,
                    "insights": "<brief_insight_string>"
                }}
                ]

                Candidate's Responses:
                ---
                {candidate_responses}
                Provide only the JSON output.
"""
    # for answer in answers:
    #     question_text = question_texts.get(answer.question_id, "[Question Text Not Found]")
    #     prompt_lines.append(f"Question: {question_text}")
    #     prompt_lines.append(f"Answer: {answer.response}")
    #     prompt_lines.append("---")

    # prompt_lines.append("\nProvide only the JSON output.")
    # final_prompt = "\n".join(prompt_lines)
    print("final_prompt", final_prompt)
    # --- Call OpenRouter API ---
    response_data = await call_openrouter_api(final_prompt, settings.OPENROUTER_MODEL_ANALYSIS)

    if response_data is None or not response_data.get("choices"):
        logger.error(f"Failed to get a valid response from OpenRouter for candidate {candidate_id}.")
        return None

    # --- Parse the Response ---
    try:
        # Extract the content which should be the JSON string
        llm_response_content = response_data["choices"][0]["message"]["content"]

        # Basic cleaning: LLMs sometimes add ```json ... ``` markdown
        if llm_response_content.strip().startswith("```json"):
             llm_response_content = llm_response_content.strip()[7:-3].strip()
        elif llm_response_content.strip().startswith("```"):
             llm_response_content = llm_response_content.strip()[3:-3].strip()


        # Parse the JSON content
        analysis_result = json.loads(llm_response_content)

        # Validate the structure (basic check)
        if not isinstance(analysis_result, list) or len(analysis_result) != 5:
            raise ValueError("LLM response is not a list of 5 traits.")

        trait_scores = []
        required_traits = {"Openness", "Conscientiousness", "Extraversion", "Agreeableness", "Neuroticism"}
        found_traits = set()

        for item in analysis_result:
            if not isinstance(item, dict) or not all(k in item for k in ["trait", "score", "insights"]):
                raise ValueError(f"Invalid item format in LLM response: {item}")

            trait_name = item["trait"]
            if trait_name not in required_traits:
                 logger.warning(f"Unexpected trait '{trait_name}' found in LLM response.")
                 continue # Skip unexpected traits

            try:
                 score = int(item["score"])
                 if not (0 <= score <= 100):
                     raise ValueError("Score out of range (0-100)")
            except (ValueError, TypeError) as e:
                 logger.error(f"Invalid score format for trait '{trait_name}': {item['score']}. Error: {e}")
                 # Decide how to handle: skip trait, assign default, fail analysis? Let's skip.
                 continue


            trait_scores.append(TraitScore(
                trait=trait_name,
                score=score,
                insights=str(item["insights"]) # Ensure insights is string
            ))
            found_traits.add(trait_name)

        # Check if all required traits were found and parsed correctly
        if found_traits != required_traits:
             missing = required_traits - found_traits
             logger.error(f"Analysis incomplete. Missing traits after parsing: {missing}")
             # Decide: return partial results or fail? Let's fail for consistency.
             return None


        logger.info(f"Successfully parsed Big Five analysis for candidate {candidate_id}.")
        return trait_scores

    except json.JSONDecodeError as e:
        logger.error(f"Failed to decode JSON from LLM response for candidate {candidate_id}: {e}. Response content snippet: {llm_response_content[:500]}")
        return None
    except (ValueError, KeyError, TypeError) as e:
        logger.error(f"Error parsing or validating LLM response structure for candidate {candidate_id}: {e}. Response content snippet: {llm_response_content[:500]}")
        return None
    except Exception as e:
        logger.exception(f"Unexpected error processing LLM response for candidate {candidate_id}: {e}") # Log full traceback
        return None


async def generate_profile_summary(trait_scores: List[TraitScore]) -> str:
    """
    Generates a summary based on trait scores.
    (Could also call an LLM for a more narrative summary).
    """
    # Keeping the simple rule-based summary from before for now.
    if not trait_scores:
        return "No profile data available."
    print("trait scores", trait_scores)
    await asyncio.sleep(0.01) # Minimal async yield point
    high_traits = [ts.insights for ts in trait_scores if ts.score >= 70]
    low_traits  = [ts.insights  for ts in trait_scores if ts.score <= 40]
    mid_traits  = [ts.insights  for ts in trait_scores if 40 < ts.score < 70]

    summary_prompt = f"""
        You are a personality assessment expert.

        Using the candidate's trait data below, generate a **concise, well-structured summary** of the candidate's personality. Your summary should highlight the candidate’s **key strengths**, **potential growth areas**, and provide a brief **overall personality snapshot**. Focus on being clear and insightful without overloading with too much detail.

        When referencing the traits, incorporate them naturally into the narrative.

        Candidate's Trait Data:

        High Scoring Traits (score >= 70):  
        {high_traits}

        Mid Range Traits (score between 40 and 70):  
        {mid_traits}

        Low Scoring Traits (score <= 40):  
        {low_traits}

        **Output Requirements:**

        - Respond strictly in **Markdown format**.
        - Use **paragraph breaks** and **bullet points** where helpful to improve readability.
        - Keep the summary **brief and digestible** – aim for clarity, not length.

        """
    print("summary prompt", summary_prompt)
    response_data = await call_openrouter_api(summary_prompt, settings.OPENROUTER_MODEL_ANALYSIS)
    print("response data", response_data)
    # Extract the content which should be the JSON string
    summary = response_data["choices"][0]["message"]["content"]
    print("summary is", summary)
    # summary_parts = []
    # if high_traits:
    #     summary_parts.append(f"Key strengths appear in {', '.join(high_traits)}.")
    # if low_traits:
    #     summary_parts.append(f"Potential development areas include {', '.join(low_traits)}.")
    # if mid_traits and not high_traits and not low_traits:
    #      summary_parts.append("The profile shows generally balanced traits.")
    # elif mid_traits:
    #      summary_parts.append(f"Traits like {', '.join(mid_traits)} are moderately expressed.")

    # summary = " ".join(summary_parts)
    if not summary:
        summary = "Profile analysis generated, showing a mix of trait expressions."

    logger.info(f"Generated summary: {summary}")
    return summary.strip()
import json
from typing import Optional
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from .llm import get_llm, get_vectorstore

def generate_warband_lore(warband_text: str, theme_info: Optional[str] = None) -> dict:
    """
    Generate warband lore with the given warband description and optional theme info.
    Returns a dict with keys "options" containing a list of 3 different lore options.
    """

    # Prompt instructions:
    # We want JSON output containing 3 options. Each option should have:
    # - A set of member names
    # - A general warband description
    # - A warband goal
    # - A one-paragraph micro-story
    # If theme_info is not provided, ask the LLM to provide 3 distinct thematic variations.
    # If theme_info is provided, incorporate it and still produce 3 different variations of final results.

    base_instructions = """
You are a lore creation assistant for the "Trench Crusade" setting. You have access to Trench Crusade lore documents (provided as context) and must produce a JSON output that describes a warband.

User provides a warband description text that might contain unit names, equipment, etc. You must create a thematic lore output for this warband, including:

- Names for all members of the warband (in a style consistent with the theme).
- A general warband description.
- A warband goal (why they are crusading/fighting).
- A one-paragraph micro-story that highlights some unique aspect of their history or a pivotal event.

You must produce 3 variations (options) of the final lore result. Each variation can differ in tone, details, or cultural background based on the instructions.

Your output must be in valid JSON and contain a key "options" which is an array of 3 objects. Each object must have:
{
  "member_names": [ "name1", "name2", ... ],
  "warband_description": "string",
  "warband_goal": "string",
  "micro_story": "string"
}

Ensure any references to the lore match the Trench Crusade setting information from the provided documents.
If no theme info is provided, propose 3 distinct thematic variations.
If theme info is provided, incorporate that theme but still provide 3 stylistically distinct final outputs.
"""

    # Adjust prompt depending on theme_info
    if theme_info:
        theme_part = f"The theme information provided: {theme_info}\nIncorporate this theme into all 3 variations."
    else:
        theme_part = """No specific theme info given. Provide 3 distinct thematic variations that differ significantly in cultural or conceptual flavor."""

    final_prompt = f"{base_instructions}\nWarband Text:\n{warband_text}\n\n{theme_part}\n\nYour final answer must be valid JSON."

    retriever = get_vectorstore().as_retriever(search_type="similarity", search_kwargs={"k":8})
    chain = RetrievalQA.from_chain_type(
        llm=get_llm(),
        chain_type="stuff",
        retriever=retriever
    )

    response = chain.run(final_prompt)

    # Validate that response is JSON
    try:
        data = json.loads(response)
        # Expect data["options"] with 3 items
        if "options" not in data or len(data["options"]) != 3:
            raise ValueError("Output JSON does not have 'options' with 3 elements.")
        return data
    except Exception as e:
        # If invalid JSON or format, handle gracefully
        return {
            "error": "Invalid response format",
            "raw_response": response
        }

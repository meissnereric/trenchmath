import json
from typing import Optional
from langchain_core.prompts import ChatPromptTemplate
from .llm import get_llm, get_vectorstore
from typing import Optional

from pydantic import BaseModel, Field

import json

from langchain import hub
from langchain_core.documents import Document
from langgraph.graph import START, StateGraph
from typing_extensions import List, TypedDict

# Pydantic
class WarbandLore(BaseModel):
    """Joke to tell user."""

    member_names: list[str] = Field(description="Names for all members of the warband (in a style consistent with the theme).")
    warband_description: str = Field(description="A general warband description.")
    warband_goal: str = Field(description="A warband goal (why they are crusading/fighting).")
    micro_story: str = Field(description="A one-paragraph micro-story that highlights some unique aspect of their history or a pivotal event.")

class WarbandLoreOptions(BaseModel):
    options: list[WarbandLore]

# Define state for application
class State(TypedDict):
    warband_text: str
    warband_theme: str
    context: List[Document]
    answer: WarbandLoreOptions


base_instructions = """
You are a lore creation assistant for the "Trench Crusade" setting. You have access to Trench Crusade lore documents (provided as context) and must produce a JSON output that describes a warband.

User provides a warband description text that might contain unit names, equipment, etc. You must create a thematic lore output for this warband, including:

- Names for all members of the warband (in a style consistent with the theme).
- A general warband description.
- A warband goal (why they are crusading/fighting).
- A one-paragraph micro-story that highlights some unique aspect of their history or a pivotal event.

You must produce 3 variations (options) of the final lore result. Each variation can differ in tone, details, or cultural background based on the instructions.

Ensure any references to the lore match the Trench Crusade setting information from the provided documents.
If no theme info is provided, propose 3 distinct thematic variations.
If theme info is provided, incorporate that theme but still provide 3 stylistically distinct final outputs.
"""

prompt_template = ChatPromptTemplate([
    ("system", base_instructions),
    ("human", "Warband theme: {warband_theme} \n Warband text: {warband_text}"),
])

def generate_warband_lore(warband_text: str, theme_info: Optional[str] = None) -> dict:
    structured_model = get_llm().with_structured_output(WarbandLoreOptions, strict=True)
    if theme_info:
        theme_part = f"The theme information provided: {theme_info}\nIncorporate this theme into all 3 variations."
    else:
        theme_part = "No specific theme info given. Provide 3 distinct thematic variations that differ significantly in cultural or conceptual flavor."


    vector_store = get_vectorstore()
    # Define application steps
    def retrieve(state: State):
        retrieved_docs = vector_store.similarity_search(state["warband_text"] + " \n\n " + state["warband_theme"], search_kwargs={"k": 8})
        return {"context": retrieved_docs}


    def generate(state: State):
        docs_content = "\n\n".join(doc.page_content for doc in state["context"])
        messages = prompt_template.invoke({"warband_text": state["warband_text"], "warband_theme": state["warband_theme"], "context": docs_content})
        response = structured_model.invoke(messages)
        return {"answer": response}
    # Compile application and test
    graph_builder = StateGraph(State).add_sequence([retrieve, generate])
    graph_builder.add_edge(START, "retrieve")
    graph = graph_builder.compile()

    context = {'warband_text': warband_text, 'warband_theme': theme_part}
    result = graph.invoke(context)
    response = result.get('answer', "No answer....")
    print(f"Raw Response: {response}")

    # Ensure response is a JSON string
    try:
        if isinstance(response, WarbandLoreOptions):
            response = json.loads(response.json())  # Convert Pydantic object to dict
        elif isinstance(response, str):
            response = json.loads(response)  # Already a string
        else:
            raise ValueError("Unexpected response type.")
        
        # Check format and validate structure
        if "options" not in response or len(response["options"]) != 3:
            raise ValueError("Output JSON does not have 'options' with 3 elements.")
        
        return response
    except Exception as e:
        # Handle parsing errors
        return {
            "error": "Invalid response format",
            "raw_response": str(response),
            "details": str(e)
        }

if __name__ == "__main__":
    response = generate_warband_lore("Black grail knight, corpse guard, puppy of the night")
    print(f"True response: {type(response)}, {list(response.keys())}, \n {response}")
    import pdb;
    pdb.set_trace()
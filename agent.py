# agent.py
import base64
from typing import List, Dict, Any
from langgraph.graph import StateGraph, END
from openai import OpenAI
from config import api_key
from typing import List, Dict, Any, TypedDict
import pandas as pd

client = OpenAI(api_key=api_key)

# --- State ---
class AgentState(TypedDict):
    messages: List[Dict[str, Any]]
    images: List[str]
    result: List[str]    

# --- Node 1: Analyze images ---
def analyze_images(state: AgentState):
    prompt = """
    You are an expert car damage inspector.
    Multiple images of the same car are provided. 
    Carefully examine all images and identify the damaged parts.
    Return only the final unique list of damaged parts.
    Rules:
    - One part per line
    - No numbering, no commas
    - No explanation, no extra text
    """
    
    user_content = [{"type": "text", "text": "Identify all damaged car parts from these images."}]
    for img_b64 in state["images"]:
        user_content.append(
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}}
        )

    response = client.chat.completions.create(
        model="gpt-4.1",
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": user_content},
        ],
    )

    raw_text = response.choices[0].message.content.strip()
    print("Raw GPT response:\n", raw_text)

    # Normalize → unique parts
    parts_set = set()
    for part in raw_text.splitlines():
        part = part.strip().lower()
        if part:
            parts_set.add(part)

    # Update state
    state["messages"].append(
        {"role": "assistant", "content": f"Identified {len(parts_set)} damaged parts."}
    )
    state["result"] = sorted(parts_set)
    return state

# Node price estimation
def estimate_price_inventory(state:AgentState):
    #input : state["result"]
    df = pd.read_csv("")

# Node Days estimation    
def estimate_days(state: AgentState):
    #Load the model
    # 1. No of parts in each category (small, medium , large)
    # 2. severaity
    # 3. availibility
    #
    print("no. of days")
    
    
# --- Build Graph ---
graph = StateGraph(AgentState)
graph.add_node("analyze", analyze_images)
graph.set_entry_point("analyze")
graph.add_edge("analyze", END)

# Compile to runnable agent
app_agent = graph.compile()

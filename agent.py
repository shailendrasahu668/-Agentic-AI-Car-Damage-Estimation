# agent.py
import base64
from typing import List, Dict, Any
from langgraph.graph import StateGraph, END
from openai import OpenAI
from config import api_key
from typing import List, Dict, Any, TypedDict
import pandas as pd
import os

API_KEY = os.getenv("API_KEY")
if not API_KEY:
    raise RuntimeError("API_KEY is missing. Set it as an environment variable.")

client = OpenAI(api_key=API_KEY)

# --- State ---
class AgentState(TypedDict):
    messages: List[Dict[str, Any]]
    images: List[str]
    result: List[str]
    car_model: str                   # from frontend
    part_prices: Dict[str, float]     

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

# --- Node 2: Fetch approximate prices ---
def fetch_prices(state: AgentState) -> AgentState:
    parts = state.get("result", [])
    car_model = state.get("car_model", "generic car")

    if not parts:
        state["part_prices"] = {}
        return state

    prompt = f"""
    You are a car parts pricing assistant.
    The damaged car parts for a {car_model} are: {', '.join(parts)}.
    Estimate a reasonable replacement cost (in INR) for each part.
    Provide output as a JSON object, example:
    {{
        "front bumper": 450,
        "left headlight": 200
    }}
    """

    response = client.chat.completions.create(
        model="gpt-4.1",
        messages=[{"role": "system", "content": prompt}],
        response_format={"type": "json_object"}
    )

    prices = getattr(response.choices[0].message, "parsed", None)
    if not prices:
        import json
        prices = json.loads(response.choices[0].message.content)

    print("💰 Estimated Prices:", prices)

    state["part_prices"] = prices
    state["messages"].append(
        {"role": "assistant", "content": f"Fetched prices for {len(prices)} parts for {car_model}."}
    )
    return state

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
graph.add_node("fetch_prices", fetch_prices)
graph.set_entry_point("analyze")
graph.add_edge("analyze", "fetch_prices")
graph.add_edge("fetch_prices", END)

# Compile to runnable agent
app_agent = graph.compile()

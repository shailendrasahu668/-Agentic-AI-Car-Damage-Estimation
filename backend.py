# backend.py
import base64
from typing import List
from fastapi import FastAPI, UploadFile, File
from agent import app_agent, AgentState

app = FastAPI()

@app.post("/predict/")
async def predict(files: List[UploadFile] = File(...)):
    # Convert all images to base64
    images_b64 = []
    for file in files:
        img_bytes = await file.read()
        img_b64 = base64.b64encode(img_bytes).decode("utf-8")
        images_b64.append(img_b64)

    # Initialize agent state
    state = AgentState(messages=[{"role": "user", "content": "Car damage estimation request"}], images=images_b64)

    # Run agent
    final_state = app_agent.invoke(state)

    return {"unique_damaged_parts": final_state.get("result", [])}

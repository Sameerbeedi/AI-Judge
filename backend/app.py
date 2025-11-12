from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os
from dotenv import load_dotenv
from groq import Groq
import PyPDF2
import docx
import io
from datetime import datetime

# Import the preprocessing module
from argument_preprocessor import preprocessor, ArgumentSequencer

# Load environment variables
load_dotenv()

app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Groq client
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# In-memory storage (replace with database for production)
cases = {}

# Argument sequence tracker
argument_sequences = {}  # case_id -> list of arguments in order

class CaseCreate(BaseModel):
    case_id: str

class ArgumentSubmit(BaseModel):
    case_id: str
    side: str  # "A" or "B"
    text: str
    
class FollowUpArgument(BaseModel):
    case_id: str
    side: str
    argument: str

def extract_text_from_file(file_content: bytes, filename: str) -> str:
    """Extract text from various file formats"""
    try:
        if filename.endswith('.pdf'):
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text()
            return text
        elif filename.endswith('.docx'):
            doc = docx.Document(io.BytesIO(file_content))
            text = "\n".join([para.text for para in doc.paragraphs])
            return text
        elif filename.endswith('.txt'):
            return file_content.decode('utf-8')
        else:
            return file_content.decode('utf-8')
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing file: {str(e)}")

def get_ai_verdict(case_data: dict) -> dict:
    """Get initial verdict from AI Judge"""
    prompt = f"""You are an AI Judge trained on legal precedents and judgments. Analyze this case carefully and provide a detailed verdict.

SIDE A ARGUMENTS:
{case_data['side_a']['text']}

SIDE B ARGUMENTS:
{case_data['side_b']['text']}

Provide your verdict in the following format:
1. VERDICT: [In favor of Side A / Side B / Split Decision]
2. REASONING: [Detailed legal reasoning]
3. KEY POINTS: [List key legal principles applied]
4. COUNTERARGUMENTS CONSIDERED: [What arguments you weighed]

Be thorough, fair, and base your decision on legal principles and evidence presented."""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": "You are an experienced AI Judge with deep knowledge of legal systems, precedents, and judicial reasoning. You provide fair, balanced, and well-reasoned verdicts."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,
        max_tokens=2000
    )
    
    return {
        "verdict": response.choices[0].message.content,
        "timestamp": datetime.now().isoformat()
    }

def process_follow_up(case_data: dict, side: str, argument: str) -> dict:
    """Process follow-up argument and get AI response"""
    # Build conversation history
    history = []
    history.append({
        "role": "system",
        "content": "You are an AI Judge. You've already given a verdict. Now listen to follow-up arguments and reconsider if the new points are compelling. Be open to changing your verdict if new evidence or legal reasoning is presented."
    })
    
    # Add initial case context
    history.append({
        "role": "user",
        "content": f"""INITIAL CASE:
Side A: {case_data['side_a']['text']}
Side B: {case_data['side_b']['text']}

YOUR INITIAL VERDICT:
{case_data['initial_verdict']['verdict']}"""
    })
    
    # Add follow-up history
    for followup in case_data.get('follow_ups', []):
        history.append({
            "role": "user",
            "content": f"Side {followup['side']} argues: {followup['argument']}"
        })
        history.append({
            "role": "assistant",
            "content": followup['response']
        })
    
    # Add current argument
    history.append({
        "role": "user",
        "content": f"Side {side} now argues: {argument}\n\nPlease reconsider your verdict. If this argument changes your perspective, explain why and issue a revised verdict. If not, explain why the original verdict still stands."
    })
    
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=history,
        temperature=0.4,
        max_tokens=1500
    )
    
    return {
        "response": response.choices[0].message.content,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/")
def root():
    return {"message": "AI Judge API is running"}

@app.post("/api/case/create")
def create_case(case: CaseCreate):
    """Create a new case"""
    cases[case.case_id] = {
        "case_id": case.case_id,
        "side_a": {"text": "", "files": [], "points": [], "metadata": {}},
        "side_b": {"text": "", "files": [], "points": [], "metadata": {}},
        "status": "collecting_evidence",
        "follow_ups": [],
        "follow_up_count": 0,
        "created_at": datetime.now().isoformat()
    }
    return {"message": "Case created", "case_id": case.case_id}

@app.post("/api/case/{case_id}/upload/{side}")
async def upload_document(case_id: str, side: str, files: List[UploadFile] = File(...)):
    """Upload and preprocess documents for a side"""
    if case_id not in cases:
        raise HTTPException(status_code=404, detail="Case not found")
    
    if side not in ["A", "B"]:
        raise HTTPException(status_code=400, detail="Side must be 'A' or 'B'")
    
    try:
        # Use preprocessor to handle files
        processed_data = await preprocessor.process_multiple_files(files, side)
        
        side_key = f"side_{side.lower()}"
        
        # Store processed data
        cases[case_id][side_key]["text"] = processed_data['combined_text']
        cases[case_id][side_key]["files"] = processed_data['files']
        cases[case_id][side_key]["points"] = processed_data['all_points']
        cases[case_id][side_key]["metadata"] = processed_data['summary']
        
        # Initialize or update argument sequence
        if case_id not in argument_sequences:
            argument_sequences[case_id] = []
        
        # Add to sequence with order
        argument_sequences[case_id].append({
            'side': side,
            'order': len(argument_sequences[case_id]) + 1,
            'text': processed_data['combined_text'],
            'point_count': len(processed_data['all_points'])
        })
        
        return {
            "message": f"Files uploaded and processed for Side {side}",
            "processed_data": {
                "file_count": processed_data['summary']['file_count'],
                "total_words": processed_data['summary']['total_words'],
                "total_points": processed_data['summary']['total_points'],
                "formats_detected": processed_data['summary']['formats_used'],
                "argument_sequence_position": len(argument_sequences[case_id])
            },
            "files": [{"filename": f['filename'], "points": len(f['points'])} for f in processed_data['files']]
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing files: {str(e)}")


@app.get("/api/case/{case_id}/validate")
def validate_case_arguments(case_id: str):
    """Validate case arguments before proceeding to verdict"""
    if case_id not in cases:
        raise HTTPException(status_code=404, detail="Case not found")
    
    case_data = cases[case_id]
    
    # Validate both sides have arguments
    validation_result = preprocessor.validate_case_arguments(
        case_data['side_a'],
        case_data['side_b']
    )
    
    # Add sequence information
    if case_id in argument_sequences:
        sequence_info = ArgumentSequencer.process_argument_sequence(
            argument_sequences[case_id]
        )
        validation_result['sequence'] = {
            'total_rounds': sequence_info['total_rounds'],
            'is_balanced': sequence_info['is_balanced'],
            'arguments_order': [
                f"Round {i+1}: Side {arg['side']}" 
                for i, arg in enumerate(argument_sequences[case_id])
            ]
        }
    
    return validation_result

@app.post("/api/case/{case_id}/argument/{side}")
def submit_argument(case_id: str, side: str, data: dict):
    """Submit text argument for a side"""
    if case_id not in cases:
        raise HTTPException(status_code=404, detail="Case not found")
    
    if side not in ["A", "B"]:
        raise HTTPException(status_code=400, detail="Side must be 'A' or 'B'")
    
    side_key = f"side_{side.lower()}"
    cases[case_id][side_key]["text"] = data.get("text", "")
    
    return {"message": f"Argument submitted for Side {side}"}

@app.post("/api/case/{case_id}/get-verdict")
def get_verdict(case_id: str):
    """Get AI Judge verdict - returns existing verdict if already decided"""
    if case_id not in cases:
        raise HTTPException(status_code=404, detail="Case not found")
    
    case = cases[case_id]
    
    # Check if verdict already exists
    if case.get('verdict') and case.get('status') == 'decided':
        return {
            "verdict": case['verdict']['text'],
            "timestamp": case['verdict']['timestamp'],
            "cached": True,
            "message": "Returning existing verdict for this case"
        }
    
    # Check if both sides have submitted
    if not case['side_a']['text'] and not case['side_a']['files']:
        raise HTTPException(status_code=400, detail="Side A has not submitted evidence")
    if not case['side_b']['text'] and not case['side_b']['files']:
        raise HTTPException(status_code=400, detail="Side B has not submitted evidence")
    
    # Combine text from files and manual input
    case['side_a']['text'] = case['side_a']['text'] + "\n\n" + "\n\n".join([f['text'] for f in case['side_a']['files']])
    case['side_b']['text'] = case['side_b']['text'] + "\n\n" + "\n\n".join([f['text'] for f in case['side_b']['files']])
    
    # Get verdict
    verdict = get_ai_verdict(case)
    cases[case_id]['initial_verdict'] = verdict
    cases[case_id]['status'] = "verdict_issued"
    
    return verdict

@app.post("/api/case/{case_id}/follow-up")
def submit_follow_up(case_id: str, data: FollowUpArgument):
    """Submit follow-up argument"""
    if case_id not in cases:
        raise HTTPException(status_code=404, detail="Case not found")
    
    case = cases[case_id]
    
    if case['status'] != 'verdict_issued':
        raise HTTPException(status_code=400, detail="Cannot submit follow-up before verdict")
    
    if case['follow_up_count'] >= 5:
        raise HTTPException(status_code=400, detail="Maximum follow-ups (5) reached")
    
    # Process follow-up
    response = process_follow_up(case, data.side, data.argument)
    
    # Store follow-up
    case['follow_ups'].append({
        "side": data.side,
        "argument": data.argument,
        "response": response['response'],
        "timestamp": response['timestamp']
    })
    case['follow_up_count'] += 1
    
    return {
        "response": response,
        "follow_ups_remaining": 5 - case['follow_up_count']
    }

@app.get("/api/case/{case_id}")
def get_case(case_id: str):
    """Get case details"""
    if case_id not in cases:
        raise HTTPException(status_code=404, detail="Case not found")
    
    return cases[case_id]

@app.get("/api/cases")
def list_cases():
    """List all cases"""
    return {"cases": list(cases.keys())}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

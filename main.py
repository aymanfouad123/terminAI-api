"""
TerminAI API - Backend service for the TerminAI CLI tool.

This API securely processes natural language requests from the TerminAI CLI,
generates appropriate terminal commands using the Groq AI service,
and returns them to the CLI without exposing API keys to end users.
"""
import os
import logging
from typing import Dict, Any, Optional
from datetime import datetime
# Using fastapi as our web framework 
from fastapi import FastAPI, HTTPException, Depends, Header, Request, Response
from fastapi.middleware.cors import CORSMiddleware  # Handles cross-origin resource sharing policies (for web security)
from pydantic import BaseModel                      # Used for data validation and serialization
import groq
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Intializing FastAPI
app = FastAPI(
    title="TerminAI API",
    description="Backend API for TerminAI CLI tool - transforms natural language queries into terminal commands",
    version="0.1.0",
)

# CORS middleware to allow requests from CLI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development - restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get Groq API key
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
if not GROQ_API_KEY:
    logger.error("GROQ_API_KEY environment variable not set")
    raise ValueError("GROQ_API_KEY environment variable not set")

# Initializing Groq client
groq_client = groq.Groq(api_key=GROQ_API_KEY)

# API key for securing our API
API_KEY = os.environ.get("TERMINAI_API_KEY")
if not API_KEY:
    logger.error("TERMINAI_API_KEY environment variable not set")
    raise ValueError("TERMINAI_API_KEY environment variable not set")

def verify_api_key(x_api_key: str = Header(None, description="API key for authentication")):
    if not x_api_key:
        logger.warning("API request was missing API key")
        raise HTTPException(status_code=401, detail="API key is required")
    
    if x_api_key != API_KEY:
        logger.warning(f"Invalid API key attempted: {x_api_key[:5]}...")
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    return x_api_key        # Returning API key if valid 

# Defining data model for request and response 

class CommandRequest(BaseModel):
    """Request model for generating commands"""
    query: str
    context: Dict[str, Any] = {}
    
    class Config:               # Examples for API documentation
        schema_extra = {
            "example" : {
                "query" : "How do I find large files in the current directory?",
                "context": {
                    "os": "Darwin 22.1.0",
                    "shell": "/bin/zsh",
                    "current_dir": "~/projects"
                }
            }
        }
        
class CommandResponse(BaseModel):
    """Response model for generated commands"""
    command: str
    explanation: Optional[str] = None
    
    class Config:
        schema_extra = {
            "example": {
                "command": "find . -type f -size +10M | sort -rh",
                "explanation": "This command finds files larger than 10MB and sorts them by size in descending order."
            }
        }
        
        
# Adding API endpoints
@app.post("/generate-command", response_model=CommandResponse)
async def generate_command(
    request: CommandRequest, 
    api_key: str = Depends(verify_api_key)      # Depends function injects the result of verify_api_key
):
    """
    Generate a terminal command based on the natural language query and context.
    
    Args:
        request: The request containing the query and context
        api_key: Verified API key from the dependency
        
    Returns:
        CommandResponse: The generated command and optional explanation
        
    Raises:
        HTTPException: For errors in processing the request
    """
    try: 
        logger.info(f"Processing query: {request.query}")
        
        # Preparing the prompt
        system_prompt = """
        You are TerminAI, an AI assistant specialized in terminal commands and operations.
        Provide clear, concise, and accurate responses to user queries.
        For command suggestions, output ONLY the exact command the user should run.
        Do not include explanations, comments, or markdown formatting.
        """
        
        # Formatting the context information
        context_prompt = "Context information:\n"
        if request.context.get("os"):
            context_prompt += f"Operating System: {request.context['os']}\n"
        if request.context.get("shell"):
            context_prompt += f"Shell: {request.context['shell']}\n"
        if request.context.get("current_dir"):
            context_prompt += f"Current Directory: {request.context['current_dir']}\n"
        
        # Basic prompt engineering
        user_prompt = f"{context_prompt}\nUser Query: {request.query}\n\nPlease provide the exact terminal command for this query:"
        
        logger.debug(f"Sending prompt to Groq: {user_prompt[:100]}...")
        
        # Call to Groq API
        chat_completion = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            model="llama3-70b-8192",  # You can make this configurable
            temperature=0.2,  # Lower for more deterministic responses
            max_tokens=256,  # Smaller responses for just commands
        )
        
        # Extract the generated command response 
        commandRes = chat_completion.choices[0].message.content.strip()
        logger.info(f"Generated command: {commandRes}") 
        
        # Returning the result
        return CommandResponse(command=commandRes)
    
    except Exception as e:
        logger.error(f"Error generating command: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error generating command: {str(e)}")
        
@app.get("/health")
async def health_check():
    """Health check endpoint to verify the API is running"""
    return {"status": "healthy", "service": "TerminAI API"}

# Setting up main entry point
# Run the application when executed directly
if __name__ == "__main__":
    import uvicorn
    logger.info("Starting TerminAI API server")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
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
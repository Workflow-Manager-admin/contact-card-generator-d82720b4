import os
from typing import List, Optional, Dict, Any
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, HttpUrl, validator
from pydantic_settings import BaseSettings

# Configuration using environment variables
class Settings(BaseSettings):
    app_name: str = Field("Contact Card Generator", description="Name of the FastAPI application")
    debug: bool = Field(default=False, description="Debug mode flag")
    allowed_origins: List[str] = Field(default=["*"], description="CORS allowed origins (as JSON list or comma separated)")

    class Config:
        env_prefix = ''  # No prefix so we can just use app_name, debug, allowed_origins, etc.

# Load config from environment
settings = Settings(
    allowed_origins=os.getenv('ALLOWED_ORIGINS', '*').split(',') if os.getenv('ALLOWED_ORIGINS') else ["*"]
)

app = FastAPI(
    title=settings.app_name,
    description="API to generate a contact card as JSON from posted user information.",
    version="1.0.0",
    debug=settings.debug,
    openapi_tags=[
        {
            "name": "Contact Card",
            "description": "Operations for generating contact card JSON."
        }
    ]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic model for incoming contact request
class SocialMediaLink(BaseModel):
    platform: str = Field(..., description="Social media platform, e.g., 'twitter', 'linkedin'.")
    url: HttpUrl = Field(..., description="Full URL to the social media profile.")

class ContactCardRequest(BaseModel):
    name: str = Field(..., description="Full name of the contact.")
    title: Optional[str] = Field(None, description="Job title or role.")
    description: Optional[str] = Field(None, description="A short description or bio.")
    social_media: Optional[List[SocialMediaLink]] = Field(default_factory=list, description="List of social media links.")

    # PUBLIC_INTERFACE
    @validator('social_media', pre=True, always=True)
    def non_null_social_media(cls, v):
        """Ensure social_media is a list even if not provided."""
        return v or []

class ContactCardResponse(BaseModel):
    name: str = Field(..., description="Full name")
    title: Optional[str] = Field(None, description="Job title")
    description: Optional[str] = Field(None, description="Description")
    social_media: Optional[List[Dict[str, Any]]] = Field(default_factory=list, description="List of social media profiles")

@app.get("/", tags=["Health"])
def health_check():
    """Health check endpoint. Returns a simple message if server is running."""
    return {"message": "Healthy"}

# PUBLIC_INTERFACE
@app.post(
    "/contact-card",
    response_model=ContactCardResponse,
    summary="Create Contact Card JSON",
    description="""
Receive contact info (name, title, description, social media links) and return a contact card as JSON.
All fields except name are optional, social media is an array with platform and url fields.
""",
    tags=["Contact Card"],
    responses={
        200: {
            "description": "Contact Card successfully generated",
            "content": {
                "application/json": {
                    "example": {
                        "name": "John Doe",
                        "title": "Engineer",
                        "description": "Developer at ExampleCorp",
                        "social_media": [
                            {"platform": "twitter", "url": "https://twitter.com/johndoe"}
                        ]
                    }
                }
            },
        },
        422: {"description": "Validation Failed"}
    }
)
async def create_contact_card(card: ContactCardRequest):
    """
    PUBLIC_INTERFACE

    Receives contact information and returns a contact card JSON object.

    - **name** (str): Full name (required)
    - **title** (str): Title or role (optional)
    - **description** (str): Description or bio (optional)
    - **social_media** (list): Optional, array of { platform: str, url: str(URL) }

    Returns:
        JSON object with all provided fields.

    Raises:
        HTTPException 422 if the body is invalid.
    """
    # create a response object, filter out empty social_media
    social_media = [sm.dict() for sm in card.social_media] if card.social_media else []
    return {
        "name": card.name,
        "title": card.title,
        "description": card.description,
        "social_media": social_media,
    }

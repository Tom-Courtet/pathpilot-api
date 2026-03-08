from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router

app = FastAPI(
    title="Gemini AI API",
    description="API permettant de lier une webapp à Google Gemini",
    version="1.0.0"
)

origins = [
    "http://localhost:3000",      
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "https://pathpilot-webapp.vercel.app",    
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,            
    allow_credentials=True,           
    allow_methods=["*"],              
    allow_headers=["*"],              
)

app.include_router(router, prefix="/api/v1")

@app.get("/", tags=["Health"])
def root():
    return {"message": "L'API Gemini est en ligne. Allez sur /docs pour voir la documentation."}
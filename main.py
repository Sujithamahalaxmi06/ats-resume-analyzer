from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import re
from typing import List, Dict
import PyPDF2
import docx

# Create FastAPI app
app = FastAPI(title="ATS Resume Analyzer")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create uploads directory
os.makedirs("uploads", exist_ok=True)

# Serve frontend HTML
@app.get("/")
async def serve_frontend():
    return FileResponse("index.html")

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/api/analyze")
async def analyze_resume(
    resume: UploadFile = File(...),
    job_description: UploadFile = File(...)
):
    """Main analysis endpoint"""
    try:
        # Save files temporarily
        resume_path = f"uploads/{resume.filename}"
        jd_path = f"uploads/{job_description.filename}"
        
        # Save resume file
        with open(resume_path, "wb") as f:
            content = await resume.read()
            f.write(content)
        
        # Save job description file
        with open(jd_path, "wb") as f:
            content = await job_description.read()
            f.write(content)
        
        # Parse files
        resume_data = parse_resume(resume_path)
        jd_data = parse_job_description(jd_path)
        
        # Analyze compatibility
        results = compare_resume_jd(resume_data, jd_data)
        
        # Clean up files
        os.remove(resume_path)
        os.remove(jd_path)
        
        return results
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def extract_text_from_pdf(file_path: str) -> str:
    """Extract text from PDF file"""
    text = ""
    try:
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
    except:
        text = "Error reading PDF"
    return text

def extract_text_from_docx(file_path: str) -> str:
    """Extract text from DOCX file"""
    text = ""
    try:
        doc = docx.Document(file_path)
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
    except:
        text = "Error reading DOCX"
    return text

def extract_text_from_txt(file_path: str) -> str:
    """Extract text from TXT file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except:
        return "Error reading TXT"

def parse_resume(file_path: str) -> Dict:
    """Parse resume and extract information"""
    
    # Extract text based on file extension
    if file_path.lower().endswith('.pdf'):
        text = extract_text_from_pdf(file_path)
    elif file_path.lower().endswith('.docx'):
        text = extract_text_from_docx(file_path)
    else:
        text = "Unsupported file format"
    
    # Extract information
    name = extract_name(text)
    email = extract_email(text)
    phone = extract_phone(text)
    skills = extract_skills(text)
    
    return {
        "text": text,
        "name": name,
        "email": email,
        "phone": phone,
        "skills": skills
    }

def parse_job_description(file_path: str) -> Dict:
    """Parse job description and extract requirements"""
    
    # Extract text based on file extension
    if file_path.lower().endswith('.pdf'):
        text = extract_text_from_pdf(file_path)
    elif file_path.lower().endswith('.docx'):
        text = extract_text_from_docx(file_path)
    elif file_path.lower().endswith('.txt'):
        text = extract_text_from_txt(file_path)
    else:
        text = "Unsupported file format"
    
    # Extract requirements
    required_skills = extract_skills(text)
    keywords = extract_keywords(text)
    
    return {
        "text": text,
        "required_skills": required_skills,
        "keywords": keywords
    }

def extract_name(text: str) -> str:
    """Extract name from resume"""
    lines = text.split('\n')
    for line in lines[:5]:  # Check first 5 lines
        line = line.strip()
        if len(line) > 0 and len(line.split()) <= 4:
            if not any(char.isdigit() for char in line) and '@' not in line:
                return line
    return "Name not found"

def extract_email(text: str) -> str:
    """Extract email from text"""
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = re.findall(email_pattern, text)
    return emails[0] if emails else "Email not found"

def extract_phone(text: str) -> str:
    """Extract phone number from text"""
    phone_patterns = [
        r'\+?1?[-.\s]?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})',
        r'\b\d{10}\b',
        r'\b\d{3}[-.\s]\d{3}[-.\s]\d{4}\b'
    ]
    
    for pattern in phone_patterns:
        matches = re.findall(pattern, text)
        if matches:
            return str(matches[0])
    
    return "Phone not found"

def extract_skills(text: str) -> List[str]:
    """Extract technical skills from text"""
    # Common technical skills
    skill_keywords = [
        'python', 'java', 'javascript', 'react', 'angular', 'vue', 'nodejs',
        'html', 'css', 'sql', 'mongodb', 'postgresql', 'mysql', 'docker',
        'kubernetes', 'aws', 'azure', 'git', 'linux', 'spring', 'django',
        'flask', 'fastapi', 'rest api', 'api', 'microservices', 'agile',
        'machine learning', 'ai', 'data science', 'pandas', 'numpy',
        'tensorflow', 'pytorch', 'scikit-learn', 'excel', 'powerbi',
        'tableau', 'spark', 'hadoop', 'scala', 'r', 'matlab', 'c++', 'c#',
        'php', 'ruby', 'go', 'rust', 'swift', 'kotlin', 'flutter', 'react native'
    ]
    
    found_skills = []
    text_lower = text.lower()
    
    for skill in skill_keywords:
        if skill in text_lower:
            found_skills.append(skill.title())
    
    return list(set(found_skills))  # Remove duplicates

def extract_keywords(text: str) -> List[str]:
    """Extract important keywords from text"""
    # Professional keywords
    keywords = [
        'experience', 'develop', 'design', 'implement', 'manage', 'lead',
        'create', 'build', 'maintain', 'optimize', 'analyze', 'collaborate',
        'teamwork', 'leadership', 'communication', 'problem solving',
        'project management', 'agile', 'scrum', 'devops', 'ci/cd'
    ]
    
    found_keywords = []
    text_lower = text.lower()
    
    for keyword in keywords:
        if keyword in text_lower:
            found_keywords.append(keyword.title())
    
    return list(set(found_keywords))

def compare_resume_jd(resume_data: Dict, jd_data: Dict) -> Dict:
    """Compare resume against job description"""
    
    resume_skills = set(skill.lower() for skill in resume_data.get('skills', []))
    jd_skills = set(skill.lower() for skill in jd_data.get('required_skills', []))
    jd_keywords = set(keyword.lower() for keyword in jd_data.get('keywords', []))
    
    # Calculate skill match percentage
    if jd_skills:
        matching_skills = resume_skills.intersection(jd_skills)
        skill_match = int((len(matching_skills) / len(jd_skills)) * 100)
    else:
        skill_match = 100
    
    # Calculate keyword coverage
    resume_text_lower = resume_data.get('text', '').lower()
    keyword_matches = sum(1 for keyword in jd_keywords if keyword in resume_text_lower)
    keyword_coverage = int((keyword_matches / len(jd_keywords)) * 100) if jd_keywords else 100
    
    # Calculate overall score (weighted average)
    overall_score = int((skill_match * 0.7) + (keyword_coverage * 0.3))
    
    # Generate suggestions
    suggestions = generate_suggestions(skill_match, keyword_coverage, resume_skills, jd_skills)
    
    return {
        "overall_score": overall_score,
        "skill_match": skill_match,
        "keyword_coverage": keyword_coverage,
        "suggestions": suggestions
    }

def generate_suggestions(skill_match: int, keyword_coverage: int, 
                        resume_skills: set, jd_skills: set) -> List[str]:
    """Generate improvement suggestions"""
    suggestions = []
    
    # Skill-based suggestions
    if skill_match < 70:
        missing_skills = list(jd_skills - resume_skills)[:3]
        if missing_skills:
            suggestions.append(f"Add these missing skills: {', '.join(missing_skills)}")
    
    # Keyword suggestions
    if keyword_coverage < 60:
        suggestions.append("Include more keywords from the job description")
    
    # General suggestions
    if skill_match < 50:
        suggestions.append("Focus on highlighting relevant technical skills")
    
    if keyword_coverage < 50:
        suggestions.append("Use more industry-specific terminology")
    
    # Default suggestions
    suggestions.extend([
        "Use action verbs like 'developed', 'implemented', 'managed'",
        "Include quantifiable achievements with numbers and percentages",
        "Ensure your resume is ATS-friendly with simple formatting",
        "Add a skills section with relevant technical skills"
    ])
    
    return suggestions[:6]  # Limit to 6 suggestions

# Run the application
if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting ATS Resume Analyzer...")
    print("📍 Open browser: http://localhost:8000")
    uvicorn.run(app, host="127.0.0.1", port=8000)
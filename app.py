from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
import PyPDF2
from docx import Document
import spacy
import re
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'doc'}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Load spaCy model
try:
    nlp = spacy.load('en_core_web_sm')
    logger.info("Successfully loaded spaCy model")
except Exception as e:
    logger.error(f"Failed to load spaCy model: {str(e)}")
    raise

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def identify_sections(text):
    """Identify the start and end indices of different sections in the text."""
    sections = {}
    lines = text.split('\n')
    current_section = None
    
    # Common section headers and their variations
    section_patterns = {
        'education': r'(?i)^(?:education|academic background|educational qualifications|academic details|qualification)s?(?:\s*:|\s*$)',
        'experience': r'(?i)^(?:experience|work experience|employment|professional experience|work history)s?(?:\s*:|\s*$)',
        'skills': r'(?i)^(?:skills|technical skills|core competencies|expertise|technologies|technical expertise)s?(?:\s*:|\s*$)',
        'projects': r'(?i)^(?:projects?|personal projects?|academic projects?|major projects?)(?:\s*:|\s*$)',
        'competitive': r'(?i)^(?:competitive programming|coding profiles?|programming profiles?|competitive coding|online judges?|coding platforms?)(?:\s*:|\s*$)',
        'achievements': r'(?i)^(?:achievements?|accomplishments?|honors?|awards?|certifications?)(?:\s*:|\s*$)'
    }
    
    # Keep track of section order for better accuracy
    section_order = []
    
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
            
        # Check if this line is a section header
        for section, pattern in section_patterns.items():
            if re.match(pattern, line):
                if current_section:
                    sections[current_section]['end'] = i
                current_section = section
                sections[current_section] = {
                    'start': i + 1,
                    'end': len(lines),
                    'header': line
                }
                section_order.append(section)
                break
    
    # Adjust section ends based on the next section's start
    for i in range(len(section_order) - 1):
        current = section_order[i]
        next_section = section_order[i + 1]
        sections[current]['end'] = sections[next_section]['start'] - 1
    
    return sections

def extract_name(text):
    # Look for name in the first 1000 characters
    first_chunk = text[:1000]
    doc = nlp(first_chunk)
    
    # First try to find a person entity
    for ent in doc.ents:
        if ent.label_ == "PERSON":
            return ent.text
    
    # If no person entity found, try to find a name in the first few lines
    lines = first_chunk.split('\n')
    for line in lines[:3]:  # Check first 3 lines
        if len(line.strip()) > 0 and not any(keyword in line.lower() for keyword in ['resume', 'cv', 'curriculum']):
            doc = nlp(line)
            for ent in doc.ents:
                if ent.label_ == "PERSON":
                    return ent.text
    
    return ""

def extract_contact_info(text):
    # Email pattern
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = re.findall(email_pattern, text)
    
    # Phone pattern (handles various formats)
    phone_pattern = r'\b(?:\+?\d{1,3}[-. ]?)?\(?\d{3}\)?[-. ]?\d{3}[-. ]?\d{4}\b'
    phones = re.findall(phone_pattern, text)
    
    # Location/Address pattern (basic)
    location_pattern = r'(?i)(?:address|location|residing at|based in).*?(?=\n|$)'
    locations = re.findall(location_pattern, text)
    location = locations[0].split(':', 1)[1].strip() if locations else ""
    
    # LinkedIn URL pattern
    linkedin_pattern = r'(?:https?:\/\/)?(?:www\.)?linkedin\.com\/in\/[a-zA-Z0-9-]+'
    linkedin = re.findall(linkedin_pattern, text)
    
    return {
        'email': emails[0] if emails else "",
        'phone': phones[0] if phones else "",
        'location': location,
        'linkedin': linkedin[0] if linkedin else ""
    }

def extract_education(text, sections):
    if 'education' not in sections:
        return []
        
    education = []
    lines = text.split('\n')[sections['education']['start']:sections['education']['end']]
    current_edu = {}
    
    # Patterns for education information
    degree_pattern = r'(?i)(b\.?tech|m\.?tech|b\.?e|m\.?e|b\.?sc|m\.?sc|phd|bachelor|master|diploma)'
    year_pattern = r'(?:19|20)\d{2}(?:\s*-\s*(?:19|20)\d{2}|(?:\s*-\s*)?present)?'
    grade_pattern = r'(?i)(?:(?:cgpa|gpa|percentage|score)\s*:?\s*)((?:\d+\.?\d*)|(?:\d+\.?\d*%?))'
    institution_pattern = r'(?i)(?:university|institute|college|school)\s+(?:of\s+)?[A-Za-z\s,]+'
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Start new education entry if degree or year is found
        if re.search(degree_pattern, line, re.I) or re.search(year_pattern, line):
            if current_edu:
                education.append(current_edu)
            current_edu = {'degree': '', 'year': '', 'institution': '', 'grade': ''}
        
        if current_edu:
            # Extract degree
            degree_match = re.search(degree_pattern, line, re.I)
            if degree_match and not current_edu['degree']:
                current_edu['degree'] = line.strip()
            
            # Extract year
            year_match = re.search(year_pattern, line)
            if year_match and not current_edu['year']:
                current_edu['year'] = year_match.group(0)
            
            # Extract grade
            grade_match = re.search(grade_pattern, line, re.I)
            if grade_match and not current_edu['grade']:
                current_edu['grade'] = grade_match.group(1)
            
            # Extract institution
            inst_match = re.search(institution_pattern, line, re.I)
            if inst_match and not current_edu['institution']:
                current_edu['institution'] = line.strip()
    
    if current_edu:
        education.append(current_edu)
    
    return education

def extract_skills(text, sections):
    if 'skills' not in sections:
        return {}
        
    lines = text.split('\n')[sections['skills']['start']:sections['skills']['end']]
    skills_by_category = {
        'Programming Languages': set(),
        'Web Technologies': set(),
        'Frameworks': set(),
        'Databases': set(),
        'Cloud & DevOps': set(),
        'Tools & Technologies': set(),
        'Other Skills': set()
    }
    
    # Comprehensive skill patterns
    skill_patterns = {
        'Programming Languages': r'(?i)(python|java|c\+\+|javascript|ruby|php|swift|kotlin|go|rust|c#|scala|r|matlab|perl|typescript|dart)',
        'Web Technologies': r'(?i)(html5?|css3?|sass|less|jquery|ajax|rest|graphql|xml|json|websocket)',
        'Frameworks': r'(?i)(react|angular|vue|django|flask|spring|express|laravel|rails|next\.?js|node\.?js|bootstrap|tailwind)',
        'Databases': r'(?i)(mysql|postgresql|mongodb|oracle|sqlite|redis|cassandra|elasticsearch|neo4j|mariadb|dynamodb)',
        'Cloud & DevOps': r'(?i)(aws|azure|gcp|docker|kubernetes|jenkins|git|ci/cd|terraform|ansible|nginx|apache)',
        'Tools & Technologies': r'(?i)(vs\s*code|intellij|eclipse|git|docker|postman|jira|confluence|maven|gradle|npm|yarn|webpack)'
    }
    
    current_category = 'Other Skills'
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Check if line is a category header
        if re.match(r'^[\w\s&]+:?$', line):
            current_category = line.rstrip(':')
            if current_category not in skills_by_category:
                skills_by_category[current_category] = set()
            continue
        
        # Extract skills based on patterns
        for category, pattern in skill_patterns.items():
            matches = re.finditer(pattern, line, re.I)
            for match in matches:
                skills_by_category[category].add(match.group(1).strip().title())
        
        # Add remaining skills to current category
        skills = [s.strip() for s in re.split(r'[,|•]', line)]
        for skill in skills:
            if skill and not any(re.search(pattern, skill, re.I) for pattern in skill_patterns.values()):
                skills_by_category[current_category].add(skill.strip().title())
    
    # Clean up and format
    return {k: sorted(list(v)) for k, v in skills_by_category.items() if v}

def extract_experience(text, sections):
    if 'experience' not in sections:
        return []
        
    lines = text.split('\n')[sections['experience']['start']:sections['experience']['end']]
    experience = []
    current_exp = {}
    
    # Patterns for experience information
    company_pattern = r'(?i)(?:at|with|@)\s+([\w\s&\-.,]+)'
    role_pattern = r'(?i)(software|developer|engineer|intern|analyst|consultant|manager|lead|architect)'
    date_pattern = r'(?:(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s*(?:19|20)\d{2}|(?:19|20)\d{2})(?:\s*-\s*(?:(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s*(?:19|20)\d{2}|(?:19|20)\d{2}|present))?'
    
    description = []
    
    for line in lines:
        line = line.strip()
        if not line:
            if current_exp and description:
                current_exp['details'] = ' '.join(description)
                experience.append(current_exp)
                current_exp = {}
                description = []
            continue
        
        # Start new experience entry if role or date is found
        if re.search(role_pattern, line, re.I) or re.search(date_pattern, line):
            if current_exp:
                current_exp['details'] = ' '.join(description)
                experience.append(current_exp)
                description = []
            current_exp = {'role': '', 'company': '', 'dates': '', 'details': ''}
            
            # Extract role
            role_match = re.search(role_pattern, line, re.I)
            if role_match:
                current_exp['role'] = line.strip()
            
            # Extract company
            company_match = re.search(company_pattern, line)
            if company_match:
                current_exp['company'] = company_match.group(1).strip()
            
            # Extract dates
            date_match = re.search(date_pattern, line)
            if date_match:
                current_exp['dates'] = date_match.group(0)
        elif current_exp:
            description.append(line)
    
    if current_exp and description:
        current_exp['details'] = ' '.join(description)
        experience.append(current_exp)
    
    return experience

def extract_projects(text, sections):
    if 'projects' not in sections:
        return []
        
    lines = text.split('\n')[sections['projects']['start']:sections['projects']['end']]
    projects = []
    current_project = {}
    
    # Patterns for project information
    title_pattern = r'(?i)^(?:project|•|\d+\.|\*)\s*(.+?)(?::|$)'
    tech_pattern = r'(?i)(?:technologies?|tech stack|built with|developed using|tools used)[:\s]*(.*?)(?:\.|$)'
    
    description = []
    
    for line in lines:
        line = line.strip()
        if not line:
            if current_project and description:
                current_project['description'] = ' '.join(description)
                projects.append(current_project)
                current_project = {}
                description = []
            continue
        
        # Start new project entry if title pattern is found
        title_match = re.match(title_pattern, line)
        if title_match:
            if current_project:
                current_project['description'] = ' '.join(description)
                projects.append(current_project)
                description = []
            current_project = {'title': '', 'description': '', 'technologies': ''}
            current_project['title'] = title_match.group(1).strip()
            
            # Check for technologies on the same line
            tech_match = re.search(tech_pattern, line)
            if tech_match:
                current_project['technologies'] = tech_match.group(1).strip()
        elif current_project:
            # Check for technologies
            tech_match = re.search(tech_pattern, line)
            if tech_match and not current_project['technologies']:
                current_project['technologies'] = tech_match.group(1).strip()
            else:
                description.append(line)
    
    if current_project and description:
        current_project['description'] = ' '.join(description)
        projects.append(current_project)
    
    return projects

def extract_competitive_programming(text, sections):
    cp_info = {
        'profiles': {},
        'achievements': []
    }
    
    # First try to find competitive programming section
    if 'competitive' in sections:
        lines = text.split('\n')[sections['competitive']['start']:sections['competitive']['end']]
    else:
        # If no dedicated section, search in the entire text
        lines = text.split('\n')
    
    # Patterns for competitive programming information
    platform_patterns = {
        'leetcode': r'(?i)leetcode[:\s]*([\w\d_-]+)(?:\s*\(.*?(\d+).*?\))?',
        'codechef': r'(?i)codechef[:\s]*([\w\d_-]+)(?:\s*\(.*?(\d+).*?\))?',
        'codeforces': r'(?i)codeforces[:\s]*([\w\d_-]+)(?:\s*\(.*?(\d+).*?\))?',
        'hackerrank': r'(?i)hackerrank[:\s]*([\w\d_-]+)(?:\s*\(.*?(\d+).*?\))?',
        'geeksforgeeks': r'(?i)(?:geeksforgeeks|gfg)[:\s]*([\w\d_-]+)(?:\s*\(.*?(\d+).*?\))?'
    }
    
    rating_pattern = r'(?i)(?:rating|score)[:\s]*(\d+)'
    rank_pattern = r'(?i)(?:rank|ranking)[:\s]*(?:global|world|india)?[:\s]*(?:#)?(\d+)'
    contest_pattern = r'(?i)(?:contest|competition)[:\s]*(.*?)(?:\(.*?\)|\.|$)'
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Extract platform profiles and ratings
        for platform, pattern in platform_patterns.items():
            matches = re.search(pattern, line, re.I)
            if matches:
                username = matches.group(1)
                rating = matches.group(2) if matches.group(2) else None
                
                cp_info['profiles'][platform] = {
                    'username': username,
                    'rating': rating
                }
                
                # Look for additional rating/rank information
                rating_match = re.search(rating_pattern, line)
                rank_match = re.search(rank_pattern, line)
                
                if rating_match or rank_match:
                    achievement = line.strip()
                    if achievement not in cp_info['achievements']:
                        cp_info['achievements'].append(achievement)
        
        # Extract contest achievements
        contest_match = re.search(contest_pattern, line, re.I)
        if contest_match and not any(platform.lower() in line.lower() for platform in platform_patterns.keys()):
            achievement = line.strip()
            if achievement not in cp_info['achievements']:
                cp_info['achievements'].append(achievement)
    
    return cp_info

def extract_achievements(text, sections):
    achievements = []
    
    # First check dedicated achievements section
    if 'achievements' in sections:
        lines = text.split('\n')[sections['achievements']['start']:sections['achievements']['end']]
        
        current_achievement = []
        for line in lines:
            line = line.strip()
            if not line:
                if current_achievement:
                    achievements.append(' '.join(current_achievement))
                    current_achievement = []
                continue
            
            # Check if line starts a new achievement
            if re.match(r'(?i)^(?:[-•*]|\d+\.|\(?\d+\))', line):
                if current_achievement:
                    achievements.append(' '.join(current_achievement))
                    current_achievement = []
                current_achievement.append(line.lstrip('[-•*1234567890.) ]'))
            else:
                current_achievement.append(line)
        
        if current_achievement:
            achievements.append(' '.join(current_achievement))
    
    # Also look for achievements in the entire text
    achievement_patterns = [
        r'(?i)(?:won|winner|awarded|received|achieved|secured|qualified).*?(?:award|prize|medal|certification|rank)',
        r'(?i)(?:first|1st|second|2nd|third|3rd).*?(?:place|position|prize|rank)',
        r'(?i)(?:gold|silver|bronze).*?(?:medal|award|prize)',
        r'(?i)(?:national|international|global).*?(?:competition|contest|championship)'
    ]
    
    lines = text.split('\n')
    for line in lines:
        line = line.strip()
        if any(re.search(pattern, line) for pattern in achievement_patterns):
            if line not in achievements:
                achievements.append(line)
    
    return achievements

def parse_pdf(file_path):
    text = ""
    with open(file_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
    return text

def parse_docx(file_path):
    text = ""
    doc = Document(file_path)
    for paragraph in doc.paragraphs:
        text += paragraph.text + "\n"
    return text

@app.route('/upload', methods=['POST'])
def upload_file():
    logger.info("Received file upload request")
    
    if 'file' not in request.files:
        logger.error("No file part in request")
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        logger.error("No selected file")
        return jsonify({'error': 'No selected file'}), 400
    
    if file and allowed_file(file.filename):
        try:
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            logger.info(f"Saving file to {filepath}")
            file.save(filepath)
            
            # Extract text based on file type
            if filename.endswith('.pdf'):
                logger.info("Processing PDF file")
                text = parse_pdf(filepath)
            else:
                logger.info("Processing DOCX file")
                text = parse_docx(filepath)
            
            logger.info("Identifying sections in the text")
            sections = identify_sections(text)
            logger.debug(f"Found sections: {list(sections.keys())}")
            
            # Extract information
            logger.info("Extracting information from resume")
            name = extract_name(text)
            contact_info = extract_contact_info(text)
            education = extract_education(text, sections)
            skills = extract_skills(text, sections)
            experience = extract_experience(text, sections)
            projects = extract_projects(text, sections)
            competitive = extract_competitive_programming(text, sections)
            achievements = extract_achievements(text, sections)
            
            # Clean up the uploaded file
            os.remove(filepath)
            logger.info("Cleaned up uploaded file")
            
            # Prepare response data
            response_data = {
                'data': {
                    'name': name,
                    'contact': contact_info,
                    'education': education,
                    'skills': skills,
                    'experience': experience,
                    'projects': projects,
                    'competitive_programming': competitive,
                    'achievements': achievements
                }
            }
            
            logger.info("Successfully processed resume")
            logger.debug(f"Response data: {response_data}")
            
            return jsonify(response_data)
            
        except Exception as e:
            logger.error(f"Error processing file: {str(e)}", exc_info=True)
            # Clean up the uploaded file in case of error
            if os.path.exists(filepath):
                os.remove(filepath)
            return jsonify({'error': str(e)}), 500
            
    logger.error("Invalid file type")
    return jsonify({'error': 'Invalid file type'}), 400

if __name__ == '__main__':
    app.run(debug=True) 
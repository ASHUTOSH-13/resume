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
        'education': r'(?i)^\b(?:education|academic (?:background|qualifications|details)|qualifications|educational details)\b\s*:?',
        'experience/projects': r'(?i)^\b(?:experience|work (?:experience|history)|employment|professional experience|projects?|personal projects?|academic projects?|major projects?|capstone project|research projects?)\b\s*:?',
        'skills': r'(?i)^\b(?:skills|technical (?:skills|expertise|proficiency)|core competencies|technologies|expertise)\b\s*:?',
        'competitive': r'(?i)^\b(?:competitive programming|coding (?:profiles?|experience)|programming profiles?|competitive coding|online judges?|coding platforms?)\b\s*:?',
        'achievements': r'(?i)^\b(?:achievements?|accomplishments?|honors?|awards?|certifications?|recognition|notable achievements?)\b\s*:?'
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

def parse_pdf(file_path):
    text = ""
    name_candidates = []
    
    with open(file_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        # Only check first page for name
        if len(pdf_reader.pages) > 0:
            page = pdf_reader.pages[0]
            
            # Extract text with font information
            def visitor_body(text, cm, tm, font_dict, font_size):
                if text.strip():
                    name_candidates.append({
                        'text': text.strip(),
                        'font_size': font_size,
                        'y_pos': tm[5] if tm else 0  # Y position on page
                    })
            
            page.extract_text(visitor_text=visitor_body)
            
            # Extract remaining text normally
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
    
    return text, name_candidates

def parse_docx(file_path):
    text = ""
    doc = Document(file_path)
    for paragraph in doc.paragraphs:
        text += paragraph.text + "\n"
    return text

def extract_name(text, name_candidates=None):
    """Extract name using font size and position information."""
    
    # Skip words that shouldn't be considered as names
    skip_words = {
        'resume', 'cv', 'curriculum vitae', 'contact', 'email', 'phone', 'address',
        'linkedin', 'github', 'leetcode', 'codechef', 'codeforces', 'portfolio',
        'profile', 'website', 'web', 'developer', 'engineer', 'software', 'experience',
        'education', 'skills', 'projects', 'achievements'
    }
    
    # If we have font information from PDF
    if name_candidates and len(name_candidates) > 0:
        # Sort by font size (descending) and y-position (descending)
        sorted_candidates = sorted(
            name_candidates, 
            key=lambda x: (-x['font_size'], -x['y_pos'])
        )
        
        # Check the largest font size entries
        for candidate in sorted_candidates[:3]:  # Check top 3 largest font sizes
            text = candidate['text'].strip()
            words = text.split()
            
            # Check if it looks like a name
            if (2 <= len(words) <= 4 and  # Most names are 2-4 words
                all(word[0].isupper() for word in words if word.isalpha()) and  # Words are capitalized
                not any(word.lower() in skip_words for word in words) and  # No skip words
                not re.search(r'[@\d]', text)):  # No @ or numbers
                return text
    
    # Fallback to traditional method if no name found from font information
    lines = text.split('\n')[:10]  # Check first 10 lines
    
    # Look for explicit name field
    for line in lines:
        line = line.strip()
        if ':' in line and 'name' in line.lower():
            name_part = line.split(':', 1)[1].strip()
            words = name_part.split()
            if (2 <= len(words) <= 4 and
                all(word[0].isupper() for word in words if word.isalpha()) and
                not any(word.lower() in skip_words for word in words) and
                not re.search(r'[@\d]', text)):
                return name_part
    
    # Look for name in first few lines
    for line in lines[:3]:
        line = line.strip()
        if not line or any(word in line.lower() for word in skip_words):
            continue
        
        words = line.split()
        if (2 <= len(words) <= 4 and
            all(word[0].isupper() for word in words if word.isalpha()) and
            not re.search(r'[@\d]', line)):
            return line
    
    return ""



# ✅ Extended list of Indian cities and countries for better location extraction
CITIES_AND_COUNTRIES = {
    # Major Indian Cities
    "delhi", "new delhi", "mumbai", "bangalore", "hyderabad", "pune", "kolkata", "chennai",
    "ahmedabad", "jaipur", "lucknow", "kanpur", "nagpur", "bhopal", "visakhapatnam",
    "patna", "vadodara", "ghaziabad", "ludhiana", "agra", "nashik", "faridabad", "meerut",
    "rajkot", "varanasi", "srinagar", "aurangabad", "dhanbad", "amritsar", "allahabad",
    "ranchi", "howrah", "jodhpur", "coimbatore", "vijayawada", "madurai", "raipur",
    "kota", "guwahati", "chandigarh", "solapur", "hubballi", "tiruchirappalli",
    "bareilly", "moradabad", "mysore", "tiruppur", "gwalior", "salem", "bhubaneswar",
    "warangal", "guntur", "dehradun", "noida", "gurgaon", "greater noida", "Jaunpur"
    
    # Other Countries for Global Matching
    "india", "usa", "canada", "germany", "france", "uk", "australia", "japan", "china",
    "brazil", "mexico", "russia", "south korea", "italy", "spain", "netherlands"
}

def extract_contact_info(text):
    """Extracts contact details including email, phone, location, and LinkedIn."""
    
    contact_info = {
        'email': '',
        'phone': '',
        'location': '',
        'linkedin': ''
    }
    
    # ✅ Extract email
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    email_match = re.search(email_pattern, text)
    if email_match:
        contact_info['email'] = email_match.group(0)
    
    # ✅ Extract phone number
    phone_pattern = r'\+?\d{1,3}[-.\s]?\(?\d{2,4}\)?[-.\s]?\d{3,5}[-.\s]?\d{4,6}'
    phone_match = re.search(phone_pattern, text)
    if phone_match:
        contact_info['phone'] = phone_match.group(0)
    
    # ✅ Extract location intelligently
    lines = text.split('\n')
    for line in lines:
        line = line.strip().lower()
        
        # If line contains "location:" or "address:"
        if ':' in line and ('location' in line or 'address' in line):
            location = line.split(':', 1)[1].strip()
            if location.lower() in CITIES_AND_COUNTRIES:
                contact_info['location'] = location.title()  # Convert to title case
                break

        # If the line itself is a known city or country
        if line in CITIES_AND_COUNTRIES:
            contact_info['location'] = line.title()
            break
    
    # ✅ Extract LinkedIn (supports usernames and URLs)
    linkedin_pattern = r'(?:https?:\/\/)?(?:www\.)?linkedin\.com\/(in|company)\/[a-zA-Z0-9-]+'
    linkedin_match = re.search(linkedin_pattern, text, re.IGNORECASE)
    if linkedin_match:
        contact_info['linkedin'] = linkedin_match.group(0) if linkedin_match.group(0).startswith('http') else f'https://{linkedin_match.group(0)}'
    else:
        # Handle cases where LinkedIn is given as "LinkedIn: Ashutosh Bhatt"
        for line in lines:
            if ':' in line and 'linkedin' in line.lower():
                name_part = line.split(':', 1)[1].strip()
                if name_part and "linkedin" not in name_part.lower():  # Ensure it's a name, not another link
                    contact_info['linkedin'] = name_part
                    break
    
    return contact_info


def extract_education(text, sections):
    """Extracts structured education details, ensuring degree, institution, year, and grade are properly captured."""
    if 'education' not in sections:
        return []

    education = []
    lines = text.split('\n')[sections['education']['start']:sections['education']['end']]
    current_edu = {}

    # Patterns for extracting education details
    degree_pattern = r'(?i)\b(?:Bachelor|Master|B\.?Tech|M\.?Tech|Ph\.?D|BSc|MSc|BCA|MCA|Intermediate|Higher Secondary|High School|Diploma|B\.E\.?|M\.E\.?)\b[^.,\n]*'
    year_pattern = r'\b(?:19|20)\d{2}(?:\s*-\s*(?:19|20)\d{2}|(?:\s*-\s*)?present)?\b'
    grade_pattern = r'(?i)(?:CGPA|GPA|Percentage|Score)\s*:?\s*(\d+\.?\d*%?)'
    institution_pattern = r'(?i)(?:[A-Za-z&.\s-]+University|Institute of Technology|College of [A-Za-z\s]+|National Institute of [A-Za-z\s]+|[A-Za-z\s]+ School)'

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # If a new degree is found, store the previous one and start a new entry
        if re.search(degree_pattern, line, re.I) or re.search(year_pattern, line):
            if current_edu:
                education.append(current_edu)
            current_edu = {'degree': '', 'institution': '', 'year': '', 'grade': ''}

        if current_edu:
            # Extract degree
            degree_match = re.search(degree_pattern, line, re.I)
            if degree_match and not current_edu['degree']:
                current_edu['degree'] = degree_match.group(0).strip()

            # Extract year
            year_match = re.search(year_pattern, line)
            if year_match and not current_edu['year']:
                current_edu['year'] = year_match.group(0).strip()

            # Extract grade
            grade_match = re.search(grade_pattern, line, re.I)
            if grade_match and not current_edu['grade']:
                current_edu['grade'] = grade_match.group(1).strip()

            # Extract institution
            inst_match = re.search(institution_pattern, line, re.I)
            if inst_match and not current_edu['institution']:
                current_edu['institution'] = inst_match.group(0).strip()

    # Add the last captured education entry
    if current_edu:
        education.append(current_edu)

    return education

def extract_skills(text, sections):
    """Extract skills with improved categorization, accuracy, and noise filtering."""
    if 'skills' not in sections:
        return {}

    lines = text.split('\n')[sections['skills']['start']:sections['skills']['end']]
    
    skills_by_category = {
        'Programming Languages': set(),
        'Web Technologies': set(),
        'Frameworks & Libraries': set(),
        'Databases': set(),
        'Cloud & DevOps': set(),
        'Tools & Technologies': set(),
        'Other Skills': set()
    }

    # Comprehensive skill patterns - removed (?i) from inside the patterns
    skill_patterns = {
        'Programming Languages': r'\b(Python|Java|C\+\+|JavaScript|C|C#|Ruby|PHP|Swift|Kotlin|Go|Rust|Scala|R|Matlab|Perl|TypeScript|Dart)\b',
        'Web Technologies': r'\b(HTML5?|CSS3?|SASS|LESS|jQuery|AJAX|REST|GraphQL|XML|JSON|WebSocket)\b',
        'Frameworks & Libraries': r'\b(React|Angular|Vue|Django|Flask|Spring|Express|Laravel|Rails|Next\.?js|Node\.?js|Bootstrap|Tailwind)\b',
        'Databases': r'\b(MySQL|PostgreSQL|MongoDB|Oracle|SQLite|Redis|Cassandra|Elasticsearch|Neo4j|MariaDB|DynamoDB)\b',
        'Cloud & DevOps': r'\b(AWS|Azure|GCP|Docker|Kubernetes|Jenkins|Git|CI/CD|Terraform|Ansible|Nginx|Apache|Cloudflare|OpenShift|Bash|Zsh)\b',
        'Tools & Technologies': r'\b(VS\s*Code|IntelliJ|Eclipse|Git|Postman|JIRA|Confluence|Maven|Gradle|NPM|Yarn|Webpack|PowerBI|Tableau)\b'
    }

    # Remove unnecessary characters for better parsing
    lines = [re.sub(r'[•:|\t]', ',', line).strip() for line in lines]

    for line in lines:
        if not line:
            continue

        # Split skills by commas or newlines
        skills = [s.strip() for s in re.split(r'[,\n]', line) if s.strip()]

        for skill in skills:
            matched = False
            for category, pattern in skill_patterns.items():
                # Move re.I flag to the search function call
                if re.search(pattern, skill, re.IGNORECASE):
                    skills_by_category[category].add(skill.strip())
                    matched = True
                    break

            # If skill doesn't match any category, add it to "Other Skills"
            if not matched and len(skill) > 1:  # Only add if skill is more than 1 character
                # Check if it's not just a special character or number
                if re.search(r'[a-zA-Z]', skill):
                    skills_by_category['Other Skills'].add(skill.strip())

    # Convert sets to sorted lists and remove empty categories
    return {k: sorted(list(v)) for k, v in skills_by_category.items() if v}

def extract_experience(text, sections):
    """Extract experience details with improved accuracy, handling freshers and different experience types."""
    
    if 'experience' not in sections:
        return []
    
    experience = []
    lines = text.split('\n')[sections['experience']['start']:sections['experience']['end']]
    
    # Keywords to help categorize experience type
    job_titles = {'developer', 'engineer', 'intern', 'analyst', 'consultant', 'manager', 'lead', 'architect', 'designer'}
    project_keywords = {'project', 'freelance', 'contract', 'open-source'}
    
    # Tech keywords to ignore as experience entries
    tech_words = {
        'numpy', 'pandas', 'matplotlib', 'tailwind', 'bootstrap', 'react', 'vue',
        'express', 'node', 'python', 'java', 'javascript', 'html', 'css', 'jquery',
        'git', 'docker', 'kubernetes', 'api', 'rest', 'graphql', 'sql', 'nosql',
        'mongodb', 'postgresql', 'mysql', 'redis', 'aws', 'azure', 'gcp'
    }

    work_entries = []
    current_entry = []

    # **First Pass: Identify Work Experience Entries**
    for line in lines:
        line = line.strip()
        if not line:
            if current_entry:
                work_entries.append(current_entry)
                current_entry = []
            continue

        # Skip standalone tech keyword lines
        words = set(line.lower().split())
        if words and all(word in tech_words for word in words):
            continue

        current_entry.append(line)
    
    if current_entry:
        work_entries.append(current_entry)

    # **Second Pass: Parse Each Work Entry**
    for entry in work_entries:
        if not entry:
            continue

        exp = {
            'role': '',
            'company': '',
            'duration': '',
            'description': [],
            'type': 'Job'  # Default to job; updated based on keywords
        }

        first_line = entry[0]

        # **Extract Role**
        role_pattern = r'(?i)\b(?:' + '|'.join(job_titles) + r')\b.*'
        role_match = re.search(role_pattern, first_line, re.I)
        if role_match:
            exp['role'] = role_match.group(0).strip()

        # **Extract Company**
        company_pattern = r'(?i)(?:at|@|with|for)\s+([\w\s&\-.,]+)'
        company_match = re.search(company_pattern, first_line)
        if company_match:
            exp['company'] = company_match.group(1).strip()

        # **Extract Duration**
        date_pattern = r'(?:(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s*(?:19|20)\d{2}|(?:19|20)\d{2})(?:\s*-\s*(?:(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s*(?:19|20)\d{2}|(?:19|20)\d{2}|present))?'
        date_match = re.search(date_pattern, first_line)
        if date_match:
            exp['duration'] = date_match.group(0)

        # **Classify Type (Internship, Job, Project)**
        if any(word in first_line.lower() for word in project_keywords):
            exp['type'] = 'Project'
        elif 'intern' in first_line.lower():
            exp['type'] = 'Internship'

        # **Extract Description**
        if len(entry) > 1:
            for line in entry[1:]:
                if not all(word in tech_words for word in line.lower().split()):
                    exp['description'].append(line.strip())

        if exp['role'] or exp['company'] or exp['duration']:
            experience.append(exp)

    return experience

def extract_projects(text, sections):
    """Extract project details including title, timeline, and a brief 1-2 line description (including tech stack)."""

    if 'projects' not in sections:
        return []
    
    lines = text.split('\n')[sections['projects']['start']:sections['projects']['end']]
    projects = []
    current_project = {}

    # **Regex Patterns**
    title_pattern = r'(?i)^(?:project|•|\d+\.|\*)\s*(.+?)(?::|$)'
    timeline_pattern = r'(?:(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s*(?:19|20)\d{2}|(?:19|20)\d{2})(?:\s*-\s*(?:(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s*(?:19|20)\d{2}|(?:19|20)\d{2}|present))?'
    
    description = []

    for line in lines:
        line = line.strip()
        if not line:
            if current_project and description:
                current_project['description'] = ' '.join(description[:2])  # Keep it concise (1-2 lines)
                projects.append(current_project)
                current_project = {}
                description = []
            continue
        
        # **Start new project entry if title pattern is found**
        title_match = re.match(title_pattern, line)
        if title_match:
            if current_project:
                current_project['description'] = ' '.join(description[:2])  # Keep it concise (1-2 lines)
                projects.append(current_project)
                description = []
            
            current_project = {'title': '', 'timeline': '', 'description': ''}
            current_project['title'] = title_match.group(1).strip()

            # **Check for timeline in the same line**
            timeline_match = re.search(timeline_pattern, line)
            if timeline_match:
                current_project['timeline'] = timeline_match.group(0).strip()

        elif current_project:
            # **Extract timeline from another line**
            timeline_match = re.search(timeline_pattern, line)
            if timeline_match and not current_project['timeline']:
                current_project['timeline'] = timeline_match.group(0).strip()

            # **Append line to description**
            description.append(line)

    if current_project and description:
        current_project['description'] = ' '.join(description[:2])  # Keep it concise (1-2 lines)
        projects.append(current_project)

    return projects

def extract_competitive_programming(text, sections):
    """Extract competitive programming details with improved accuracy."""
    cp_info = {
        'profiles': {},
        'achievements': []
    }
    
    # Look for competitive programming section first
    if 'competitive' in sections:
        lines = text.split('\n')[sections['competitive']['start']:sections['competitive']['end']]
    else:
        # If no dedicated section, search in the entire text
        lines = text.split('\n')
    
    # Platform patterns with ratings and ranks
    platform_patterns = {
        'leetcode': [
            r'(?i)leetcode.*?(?:rating|rank)[:\s]*(\d+)',
            r'(?i)(?:global rank|rank)[:\s]*(\d+).*?leetcode',
            r'(?i)leetcode.*?weekly.*?(?:contest|rank)[:\s]*(\d+)',
            r'(?i)leetcode.*?rating[:\s]*(\d+)',
            r'(?i)rating[:\s]*(\d+).*?leetcode'
        ],
        'codechef': [
            r'(?i)codechef.*?(?:rating|rank)[:\s]*(\d+)',
            r'(?i)(?:rating|rank)[:\s]*(\d+).*?codechef',
            r'(?i)codechef.*?rating[:\s]*(\d+)',
            r'(?i)rating[:\s]*(\d+).*?codechef'
        ],
        'codeforces': [
            r'(?i)codeforces.*?(?:rating|rank)[:\s]*(\d+)',
            r'(?i)(?:rating|rank)[:\s]*(\d+).*?codeforces',
            r'(?i)codeforces.*?rating[:\s]*(\d+)',
            r'(?i)rating[:\s]*(\d+).*?codeforces'
        ]
    }
    
    # First pass: Look for platform-specific ratings
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        for platform, patterns in platform_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, line, re.I)
                if match:
                    rating = match.group(1)
                    if platform not in cp_info['profiles']:
                        cp_info['profiles'][platform] = {
                            'rating': rating,
                            'details': line.strip()
                        }
                    elif not cp_info['profiles'][platform].get('rating'):
                        cp_info['profiles'][platform]['rating'] = rating
                        cp_info['profiles'][platform]['details'] = line.strip()
    
    # Second pass: Look for achievements
    achievement_patterns = [
        r'(?i)global rank.*?\d+.*?(?:leetcode|codechef|codeforces)',
        r'(?i)(?:contest|competition).*?rank.*?\d+',
        r'(?i)(?:solved|completed).*?\d+\+?.*?(?:problems|questions)',
        r'(?i)(?:badge|achievement).*?(?:leetcode|codechef|codeforces)',
        r'(?i)weekly contest.*?rank.*?\d+'
    ]
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        if any(re.search(pattern, line, re.I) for pattern in achievement_patterns):
            achievement = line.strip()
            if achievement not in cp_info['achievements']:
                cp_info['achievements'].append(achievement)
    
    return cp_info

def extract_achievements(text, sections):
    """Extract achievements with improved patterns."""
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
        r'(?i)(?:national|international|global).*?(?:competition|contest|championship)',
        r'(?i)(?:hackathon|project|research|publication|patent)'
    ]
    
    lines = text.split('\n')
    for line in lines:
        line = line.strip()
        if any(re.search(pattern, line) for pattern in achievement_patterns):
            if line not in achievements:
                achievements.append(line)
    
    return achievements

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
            name_candidates = []
            if filename.endswith('.pdf'):
                logger.info("Processing PDF file")
                text, name_candidates = parse_pdf(filepath)
            else:
                logger.info("Processing DOCX file")
                text = parse_docx(filepath)
            
            logger.info("Identifying sections in the text")
            sections = identify_sections(text)
            logger.debug(f"Found sections: {list(sections.keys())}")
            
            # Extract information
            logger.info("Extracting information from resume")
            name = extract_name(text, name_candidates)
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
# Resume Parser

A powerful and accurate resume parsing system that extracts structured information from PDF and DOCX resumes.

## Features

- **Smart Name Detection**: Uses font size and positioning to accurately identify names
- **Contact Information Extraction**: Accurately extracts email, phone, and location
- **Education Details**: Parses educational qualifications with institutions and years
- **Work Experience**: Extracts and structures professional experience
- **Skills Classification**: Categorizes technical skills into relevant domains
- **Competitive Programming**: Extracts profiles, ratings, and achievements from platforms like LeetCode, CodeChef, etc.
- **Project Details**: Parses project information with technologies used
- **Achievements**: Extracts notable achievements and certifications

## Tech Stack

- **Backend**: Python, Flask
- **PDF Processing**: PyPDF2, pdfplumber
- **DOCX Processing**: python-docx
- **Text Processing**: spaCy, regex
- **Frontend**: React, Material-UI
- **API**: RESTful endpoints

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd resume-parser
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Install spaCy model:
```bash
python -m spacy download en_core_web_sm
```

5. Start the server:
```bash
python app.py
```

## API Endpoints

### POST /upload
Upload and parse a resume file.

**Request**:
- Method: POST
- Content-Type: multipart/form-data
- Body: file (PDF or DOCX)

**Response**:
```json
{
    "name": "John Doe",
    "contact": {
        "email": "john@example.com",
        "phone": "+1234567890",
        "location": "New York",
        "linkedin": "linkedin.com/in/johndoe"
    },
    "education": [{
        "degree": "B.Tech Computer Science",
        "institution": "Example University",
        "year": "2020-2024",
        "grade": "8.5 CGPA"
    }],
    "skills": {
        "Programming Languages": ["Python", "Java", "C++"],
        "Web Technologies": ["HTML5", "CSS3", "JavaScript"],
        "Frameworks": ["React", "Django", "Flask"]
    },
    "experience": [{
        "role": "Software Engineer",
        "company": "Tech Corp",
        "duration": "Jan 2023 - Present",
        "description": ["Developed feature X", "Improved performance by Y%"]
    }],
    "competitive_programming": {
        "profiles": {
            "leetcode": {
                "rating": "2000",
                "details": "Global rank 500"
            }
        },
        "achievements": [
            "Solved 500+ problems",
            "Weekly contest rank 100"
        ]
    }
}
```

## Code Structure

```
resume-parser/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── static/               # Static files
├── templates/            # HTML templates
├── utils/               
│   ├── parser.py         # Core parsing functions
│   ├── validators.py     # Input validation
│   └── helpers.py        # Helper utilities
└── tests/                # Test cases
```

## Parser Components

### Name Extraction
- Uses font size information from PDFs to identify names
- Falls back to position-based and pattern matching for DOCX
- Validates against common technology terms to avoid false positives

### Location Detection
- Uses a database of cities and countries
- Pattern matching for address formats
- Validates against technology terms

### Skills Classification
Categories:
- Programming Languages
- Web Technologies
- Frameworks & Libraries
- Databases
- Cloud & DevOps
- Tools & Technologies
- Other Skills

### Experience Parsing
- Two-pass algorithm for accurate extraction
- Role and company detection
- Date range parsing
- Description bullet points extraction

### Competitive Programming
Supported Platforms:
- LeetCode
- CodeChef
- Codeforces
- HackerRank
- GeeksforGeeks

## Best Practices

1. **Resume Format**:
   - PDF format preferred
   - Clear section headers
   - Consistent formatting
   - Standard font usage

2. **Section Headers**:
   - Use clear, standard section names
   - Maintain consistent capitalization
   - Add clear separation between sections

3. **Content Structure**:
   - Use bullet points for experience and projects
   - Include dates in standard formats
   - Structure contact information clearly
   - List skills with proper categorization

## Error Handling

The parser includes robust error handling for:
- Invalid file formats
- Missing sections
- Malformed content
- Extraction failures
- File processing issues

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- spaCy for NLP capabilities
- PyPDF2 and pdfplumber for PDF processing
- python-docx for DOCX processing 
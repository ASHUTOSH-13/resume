# Technical Documentation

## Architecture Overview

The Resume Parser is built with a modular architecture focusing on:
- Clear separation of concerns
- Extensibility
- Maintainability
- Error handling

### Core Components

1. **File Processing Layer**
   - Handles PDF and DOCX file inputs
   - Extracts text and metadata
   - Manages file cleanup

2. **Text Processing Layer**
   - Section identification
   - Text normalization
   - Pattern matching
   - NLP processing

3. **Information Extraction Layer**
   - Specialized extractors for each section
   - Data validation
   - Structure formatting

4. **API Layer**
   - RESTful endpoints
   - Request validation
   - Response formatting
   - Error handling

## Detailed Component Documentation

### 1. PDF Processing

```python
def parse_pdf(file_path):
    """
    Extracts text and font information from PDF files.
    
    Args:
        file_path (str): Path to the PDF file
        
    Returns:
        tuple: (extracted_text, name_candidates)
            - extracted_text (str): Full text content
            - name_candidates (list): List of text blocks with font information
    """
```

Key Features:
- Font size extraction
- Text positioning
- Metadata handling
- Page management

### 2. Name Extraction

```python
def extract_name(text, name_candidates):
    """
    Extracts the candidate's name using font information and fallback methods.
    
    Strategy:
    1. Use largest font size text from first page
    2. Check for explicit name fields
    3. Apply NLP for person entity recognition
    4. Validate against technology terms
    """
```

Validation Rules:
- 2-4 words length
- Capitalized words
- No special characters
- No technology terms

### 3. Skills Extraction

```python
def extract_skills(text, sections):
    """
    Extracts and categorizes skills from the resume.
    
    Categories:
    - Programming Languages
    - Web Technologies
    - Frameworks & Libraries
    - Databases
    - Cloud & DevOps
    - Tools & Technologies
    """
```

Pattern Matching:
```python
skill_patterns = {
    'Programming Languages': r'\b(Python|Java|C\+\+|...)\b',
    'Web Technologies': r'\b(HTML5?|CSS3?|...)\b',
    ...
}
```

### 4. Experience Extraction

Two-pass algorithm:
1. **First Pass**: Identify experience blocks
   ```python
   def identify_experience_blocks(text):
       """
       Identifies distinct experience entries using role and date patterns.
       """
   ```

2. **Second Pass**: Extract details
   ```python
   def extract_experience_details(block):
       """
       Extracts role, company, duration, and description from an experience block.
       """
   ```

### 5. Competitive Programming Extraction

Pattern-based extraction:
```python
platform_patterns = {
    'leetcode': [
        r'(?i)leetcode.*?rating[:\s]*(\d+)',
        r'(?i)global rank[:\s]*(\d+).*?leetcode'
    ],
    ...
}
```

Achievement patterns:
```python
achievement_patterns = [
    r'(?i)global rank.*?\d+',
    r'(?i)weekly contest.*?rank.*?\d+'
]
```

## Error Handling

### 1. File Processing Errors
```python
try:
    process_file(file_path)
except FileNotFoundError:
    handle_missing_file()
except InvalidFileFormat:
    handle_invalid_format()
```

### 2. Extraction Errors
```python
try:
    extract_information(text)
except ExtractionError:
    handle_extraction_failure()
except ValidationError:
    handle_validation_failure()
```

## Performance Optimization

1. **Text Processing**
   - Caching of processed text
   - Efficient regex patterns
   - Minimal use of expensive NLP operations

2. **Memory Management**
   - Proper file handling
   - Cleanup of temporary files
   - Stream processing for large files

3. **Response Time**
   - Asynchronous processing
   - Efficient data structures
   - Optimized algorithms

## Testing

### Unit Tests
```python
def test_name_extraction():
    """Test cases for name extraction"""
    assert extract_name("John Doe\nSoftware Engineer", []) == "John Doe"
    assert extract_name("Name: Jane Smith", []) == "Jane Smith"
```

### Integration Tests
```python
def test_full_parse():
    """Test full resume parsing pipeline"""
    result = parse_resume("test_resume.pdf")
    assert "name" in result
    assert "skills" in result
```

## Deployment

### Requirements
- Python 3.8+
- 2GB RAM minimum
- 1GB disk space
- Network access for NLP model download

### Environment Variables
```bash
FLASK_ENV=production
MAX_CONTENT_LENGTH=16777216  # 16MB max file size
ALLOWED_EXTENSIONS=pdf,docx
```

### Security Considerations
- File type validation
- Size limits
- Content sanitization
- Error message sanitization

## Maintenance

### Adding New Skills
1. Update skill patterns in `skill_patterns` dictionary
2. Add validation rules if needed
3. Update tests

### Adding New Platforms
1. Add platform patterns in `platform_patterns`
2. Update extraction logic
3. Add validation rules
4. Update response format

## Troubleshooting

Common Issues:
1. **PDF Extraction Fails**
   - Check PDF format
   - Verify file permissions
   - Check for encryption

2. **Name Not Found**
   - Check font size extraction
   - Verify name format
   - Check for special characters

3. **Skills Not Categorized**
   - Update skill patterns
   - Check section identification
   - Verify text normalization 
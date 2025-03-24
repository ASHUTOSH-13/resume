import { useState, useRef } from 'react'
import './App.css'

// Icons as components
const UploadIcon = () => (
  <svg 
    xmlns="http://www.w3.org/2000/svg" 
    width="24" 
    height="24" 
    viewBox="0 0 24 24" 
    fill="none" 
    stroke="currentColor" 
    strokeWidth="2" 
    strokeLinecap="round" 
    strokeLinejoin="round"
  >
    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
    <polyline points="17 8 12 3 7 8" />
    <line x1="12" y1="3" x2="12" y2="15" />
  </svg>
)

const FileIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
  </svg>
)

const HomeIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 12l8.954-8.955c.44-.439 1.152-.439 1.591 0L21.75 12M4.5 9.75v10.125c0 .621.504 1.125 1.125 1.125H9.75v-4.875c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21h4.125c.621 0 1.125-.504 1.125-1.125V9.75M8.25 21h8.25" />
  </svg>
)

const HistoryIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z" />
  </svg>
)

const SettingsIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" d="M9.594 3.94c.09-.542.56-.94 1.11-.94h2.593c.55 0 1.02.398 1.11.94l.213 1.281c.063.374.313.686.645.87.074.04.147.083.22.127.324.196.72.257 1.075.124l1.217-.456a1.125 1.125 0 011.37.49l1.296 2.247a1.125 1.125 0 01-.26 1.431l-1.003.827c-.293.24-.438.613-.431.992a6.759 6.759 0 010 .255c-.007.378.138.75.43.99l1.005.828c.424.35.534.954.26 1.43l-1.298 2.247a1.125 1.125 0 01-1.369.491l-1.217-.456c-.355-.133-.75-.072-1.076.124a6.57 6.57 0 01-.22.128c-.331.183-.581.495-.644.869l-.213 1.28c-.09.543-.56.941-1.11.941h-2.594c-.55 0-1.02-.398-1.11-.94l-.213-1.281c-.062-.374-.312-.686-.644-.87a6.52 6.52 0 01-.22-.127c-.325-.196-.72-.257-1.076-.124l-1.217.456a1.125 1.125 0 01-1.369-.49l-1.297-2.247a1.125 1.125 0 01.26-1.431l1.004-.827c.292-.24.437-.613.43-.992a6.932 6.932 0 010-.255c.007-.378-.138-.75-.43-.99l-1.004-.828a1.125 1.125 0 01-.26-1.43l1.297-2.247a1.125 1.125 0 011.37-.491l1.216.456c.356.133.751.072 1.076-.124.072-.044.146-.087.22-.128.332-.183.582-.495.644-.869l.214-1.281z" />
    <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
  </svg>
)

const SuccessIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
  </svg>
)

const ErrorIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
  </svg>
)

function App() {
  const [file, setFile] = useState(null)
  const [status, setStatus] = useState('')
  const [isDragging, setIsDragging] = useState(false)
  const [parsedData, setParsedData] = useState(null)
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(false)
  const fileInputRef = useRef(null)

  const allowedTypes = [
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
  ]

  const validateFile = (file) => {
    if (!file) return false;
    
    if (!allowedTypes.includes(file.type)) {
      setStatus('Error: Only PDF and DOC/DOCX files are allowed')
      return false
    }
    
    const maxSize = 10 * 1024 * 1024; // 10MB in bytes
    if (file.size > maxSize) {
      setStatus('Error: File size should be less than 10MB')
      return false
    }

    return true
  }

  const handleFileChange = (event) => {
    const selectedFile = event.target.files && event.target.files[0]
    if (selectedFile && validateFile(selectedFile)) {
      setFile(selectedFile)
      setStatus('')
      setParsedData(null)
      setError(null)
    } else if (selectedFile) {
      setFile(null)
      setParsedData(null)
      setError(null)
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
    }
  }

  const handleDragOver = (event) => {
    event.preventDefault()
    setIsDragging(true)
  }

  const handleDragLeave = (event) => {
    event.preventDefault()
    setIsDragging(false)
  }

  const handleDrop = (event) => {
    event.preventDefault()
    setIsDragging(false)
    
    const droppedFile = event.dataTransfer.files && event.dataTransfer.files[0]
    if (droppedFile && validateFile(droppedFile)) {
      setFile(droppedFile)
      setStatus('')
      setParsedData(null)
      setError(null)
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!file) {
      setError('Please select a file')
      return
    }

    setLoading(true)
    setError(null)

    const formData = new FormData()
    formData.append('file', file)

    try {
      setStatus('Parsing resume...')
      const response = await fetch('http://localhost:5000/upload', {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.error || 'Failed to parse resume')
      }

      const data = await response.json()
      console.log('Parsed Data:', data) // Debug log
      
      if (!data || !data.data) {
        throw new Error('Invalid response format')
      }

      setStatus('Resume parsed successfully!')
      setParsedData(data.data)
      setFile(null)
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
    } catch (err) {
      console.error('Error:', err) // Debug log
      setError(err.message)
      setStatus('Upload failed: Server error')
      setParsedData(null)
    } finally {
      setLoading(false)
    }
  }

  const formatBytes = (bytes) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  const getFileTypeText = (fileType) => {
    switch(fileType) {
      case 'application/pdf':
        return 'PDF'
      case 'application/msword':
      case 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
        return 'Document'
      default:
        return 'File'
    }
  }

  return (
    <div className="container">
      <h1 className="title">Resume Parser</h1>
      <div className="upload-container">
        <div 
          className={`drop-zone ${isDragging ? 'dragging' : ''}`}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
        >
          <input
            ref={fileInputRef}
            type="file"
            onChange={handleFileChange}
            className="file-input"
            accept=".pdf,.doc,.docx,application/pdf,application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
          />
          <div className="drop-zone-text">
            <UploadIcon />
            <p>{file ? file.name : 'Drag & Drop your resume here or click to browse'}</p>
            <span className="file-types">Allowed types: PDF, DOC, DOCX (Max: 10MB)</span>
          </div>
        </div>

        {file && (
          <div className="file-info">
            <p className="file-name">{file.name}</p>
            <p className="file-size">
              {getFileTypeText(file.type)} • {formatBytes(file.size)}
            </p>
          </div>
        )}

        <button 
          className="upload-button"
          onClick={handleSubmit}
          disabled={!file || loading}
        >
          {loading ? 'Parsing...' : 'Parse Resume'}
        </button>

        {status && (
          <div className={`status ${status.includes('success') ? 'success' : 'error'}`}>
            {status}
          </div>
        )}

        {error && (
          <div className="error-message">
            Error: {error}
          </div>
        )}

        {loading && (
          <div className="loading">
            Processing your resume...
          </div>
        )}

        {parsedData && (
          <div className="parsed-data">
            {/* Card 1: Personal Information */}
            <div className="card personal-info">
              <h2>Personal Information</h2>
              <div className="personal-details">
                {parsedData.name && (
                  <div className="detail-item">
                    <i className="fas fa-user"></i>
                    <span className="detail-label">Name:</span>
                    <span className="detail-value">{parsedData.name}</span>
                  </div>
                )}
                {parsedData.contact?.email && (
                  <div className="detail-item">
                    <i className="fas fa-envelope"></i>
                    <span className="detail-label">Email:</span>
                    <span className="detail-value">{parsedData.contact.email}</span>
                  </div>
                )}
                {parsedData.contact?.phone && (
                  <div className="detail-item">
                    <i className="fas fa-phone"></i>
                    <span className="detail-label">Phone:</span>
                    <span className="detail-value">{parsedData.contact.phone}</span>
                  </div>
                )}
                {parsedData.contact?.location && (
                  <div className="detail-item">
                    <i className="fas fa-map-marker-alt"></i>
                    <span className="detail-label">Location:</span>
                    <span className="detail-value">{parsedData.contact.location}</span>
                  </div>
                )}
                {parsedData.contact?.linkedin && (
                  <div className="detail-item">
                    <i className="fab fa-linkedin"></i>
                    <span className="detail-label">LinkedIn:</span>
                    <a href={parsedData.contact.linkedin} target="_blank" rel="noopener noreferrer" className="detail-value">
                      {parsedData.contact.linkedin}
                    </a>
                  </div>
                )}
              </div>
            </div>

            {/* Card 2: Education */}
            {parsedData.education && parsedData.education.length > 0 && (
              <div className="card education">
                <h2>Education</h2>
                <div className="education-timeline">
                  {parsedData.education.map((edu, index) => (
                    <div key={index} className="education-item">
                      {edu.year && <div className="education-year">{edu.year}</div>}
                      <div className="education-content">
                        {edu.degree && <h3 className="education-degree">{edu.degree}</h3>}
                        <div className="education-details">
                          {edu.institution && <p className="institution">{edu.institution}</p>}
                          {edu.grade && <p className="grade">Grade: {edu.grade}</p>}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Card 3: Skills */}
            {parsedData.skills && Object.keys(parsedData.skills).length > 0 && (
              <div className="card skills">
                <h2>Technical Skills</h2>
                <div className="skills-grid">
                  {Object.entries(parsedData.skills).map(([category, skills]) => (
                    skills && skills.length > 0 && (
                      <div key={category} className="skill-category">
                        <h3>{category}</h3>
                        <div className="skill-tags">
                          {skills.map((skill, index) => (
                            <span key={index} className="skill-tag">{skill}</span>
                          ))}
                        </div>
                      </div>
                    )
                  ))}
                </div>
              </div>
            )}

            {/* Card 4: Experience */}
            {parsedData.experience && parsedData.experience.length > 0 && (
              <div className="card experience">
                <h2>Work Experience</h2>
                <div className="experience-timeline">
                  {parsedData.experience.map((exp, index) => (
                    <div key={index} className="experience-item">
                      <div className="experience-header">
                        {exp.role && <h3 className="experience-role">{exp.role}</h3>}
                        {exp.company && <div className="experience-company">{exp.company}</div>}
                        {exp.dates && <div className="experience-duration">{exp.dates}</div>}
                      </div>
                      {exp.details && <div className="experience-description">{exp.details}</div>}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Card 5: Projects */}
            {parsedData.projects && parsedData.projects.length > 0 && (
              <div className="card projects">
                <h2>Projects</h2>
                <div className="projects-grid">
                  {parsedData.projects.map((project, index) => (
                    <div key={index} className="project-card">
                      {project.title && <h3 className="project-title">{project.title}</h3>}
                      {project.description && <p className="project-description">{project.description}</p>}
                      {project.technologies && (
                        <div className="project-tech">
                          <h4>Technologies Used:</h4>
                          <div className="tech-tags">
                            {project.technologies.split(',').map((tech, i) => (
                              <span key={i} className="tech-tag">{tech.trim()}</span>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Card 6: Programming Profiles */}
            {parsedData.competitive_programming && Object.keys(parsedData.competitive_programming.profiles).length > 0 && (
              <div className="card programming-profiles">
                <h2>Programming Profiles</h2>
                <div className="profiles-grid">
                  {Object.entries(parsedData.competitive_programming.profiles).map(([platform, data]) => (
                    <div key={platform} className="profile-card">
                      <div className="platform-icon">
                        <i className={`fab fa-${platform.toLowerCase()}`}></i>
                      </div>
                      <div className="platform-details">
                        <h3 className="platform-name">{platform}</h3>
                        <p className="username">{data.username}</p>
                        {data.rating && <p className="rating">Rating: {data.rating}</p>}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Card 7: Achievements */}
            {parsedData.achievements && parsedData.achievements.length > 0 && (
              <div className="card achievements">
                <h2>Achievements</h2>
                <div className="achievements-list">
                  {parsedData.achievements.map((achievement, index) => (
                    <div key={index} className="achievement-item">
                      <i className="fas fa-trophy"></i>
                      <span>{achievement}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

export default App

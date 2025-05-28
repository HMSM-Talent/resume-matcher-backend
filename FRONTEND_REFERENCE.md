# Frontend Development Reference

## Key Backend Files

### Models
- `resumes/models.py`: Contains all data models (Resume, JobDescription, SimilarityScore)
- `accounts/models.py`: Contains user model and authentication

### API Endpoints
- `resumes/views.py`: Contains all API views and logic
- `resumes/urls.py`: Contains URL routing
- `backend/urls.py`: Main URL configuration

### Serializers
- `resumes/serializers.py`: Contains all API response serializers

### Authentication
- `accounts/views.py`: Contains authentication views
- `backend/settings.py`: Contains JWT and CORS settings

### File Processing
- `matcher/utils.py`: Contains text extraction and similarity calculation

## Important Considerations for Frontend

1. **Authentication**
   - All requests need JWT token
   - Token format: `Bearer <token>`
   - Token expiration: 24 hours

2. **File Upload**
   - Max file size: 10MB
   - Supported formats: PDF, DOCX
   - Use multipart/form-data

3. **API Response Format**
   - All responses are JSON
   - Error responses include 'error' and 'detail' fields
   - Success responses include requested data

4. **Filtering Options**
   - Job type: full-time, part-time, contract, internship
   - Experience level: entry, mid, senior, lead
   - Score threshold: 0.0 to 1.0

5. **Rate Limiting**
   - 100 requests/hour per user
   - 1000 requests/hour per IP

6. **CORS Configuration**
   - Allowed methods: GET, POST, OPTIONS
   - Allowed headers: Content-Type, Authorization
   - Configure allowed origins in settings

## Development Tips

1. **Testing API**
   - Use Postman or similar tool
   - Test file uploads with actual PDF/DOCX files
   - Verify JWT token handling

2. **Error Handling**
   - Handle 401 (Unauthorized) for invalid/missing tokens
   - Handle 400 (Bad Request) for invalid file types
   - Handle 413 (Payload Too Large) for large files

3. **File Processing**
   - Show loading state during file upload
   - Handle text extraction errors gracefully
   - Display similarity scores with proper formatting

4. **Security**
   - Never store JWT tokens in localStorage
   - Use secure HTTP-only cookies
   - Implement proper CORS settings

5. **Performance**
   - Implement pagination for large result sets
   - Use proper caching headers
   - Optimize file uploads with progress indicators 
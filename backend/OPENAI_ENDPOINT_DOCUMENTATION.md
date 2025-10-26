# OpenAI Chat Completions API Endpoint Documentation

## `/api/generate-treatment` Endpoint

This endpoint uses the OpenAI Chat Completions API to generate evidence-based stroke treatment recommendations.

### Endpoint Details

- **URL**: `POST /api/generate-treatment`
- **Content-Type**: `application/json`
- **Model**: `gpt-4o-mini`
- **Timeout**: 30 seconds

### Request Body

The endpoint accepts a JSON body with the following required fields:

```json
{
  "name": "string",
  "age": "integer",
  "nhiss_score": "integer",
  "systolic_bp": "integer",
  "diastolic_bp": "integer",
  "glucose": "integer",
  "oxygen_saturation": "integer",
  "symptoms": "string"
}
```

#### Field Descriptions

| Field | Type | Description | Range |
|-------|------|-------------|-------|
| `name` | string | Patient's full name | Any string |
| `age` | integer | Patient's age in years | 1-120 |
| `nhiss_score` | integer | NIH Stroke Scale score | 0-42 |
| `systolic_bp` | integer | Systolic blood pressure in mmHg | 50-300 |
| `diastolic_bp` | integer | Diastolic blood pressure in mmHg | 30-200 |
| `glucose` | integer | Blood glucose level in mg/dL | 50-500 |
| `oxygen_saturation` | integer | Oxygen saturation percentage | 70-100 |
| `symptoms` | string | Detailed description of patient symptoms | Any string |

### Response Format

#### Success Response (200 OK)

```json
{
  "treatment_plan": "Generated treatment plan text...",
  "model_used": "gpt-4o-mini",
  "patient_name": "John Doe",
  "generated_at": "2024-01-15T10:30:45.123456"
}
```

#### Error Responses

**400 Bad Request** - Missing required fields
```json
{
  "detail": "Missing required fields: nhiss_score, symptoms"
}
```

**500 Internal Server Error** - OpenAI API key not configured
```json
{
  "detail": "OpenAI API key not configured. Please set OPENAI_API_KEY environment variable."
}
```

**502 Bad Gateway** - OpenAI API error
```json
{
  "detail": "OpenAI API error: Invalid API key"
}
```

**504 Gateway Timeout** - Request timeout
```json
{
  "detail": "Request to OpenAI API timed out"
}
```

### Example Usage

#### cURL Example

```bash
curl -X POST "http://localhost:8000/api/generate-treatment" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "age": 65,
    "nhiss_score": 8,
    "systolic_bp": 160,
    "diastolic_bp": 95,
    "glucose": 120,
    "oxygen_saturation": 96,
    "symptoms": "Sudden onset of left-sided weakness, slurred speech, and facial droop."
  }'
```

#### Python Example

```python
import requests

url = "http://localhost:8000/api/generate-treatment"
patient_data = {
    "name": "John Doe",
    "age": 65,
    "nhiss_score": 8,
    "systolic_bp": 160,
    "diastolic_bp": 95,
    "glucose": 120,
    "oxygen_saturation": 96,
    "symptoms": "Sudden onset of left-sided weakness, slurred speech, and facial droop."
}

response = requests.post(url, json=patient_data)
if response.status_code == 200:
    result = response.json()
    print("Treatment Plan:", result["treatment_plan"])
else:
    print("Error:", response.json()["detail"])
```

#### JavaScript Example

```javascript
const patientData = {
    name: "John Doe",
    age: 65,
    nhiss_score: 8,
    systolic_bp: 160,
    diastolic_bp: 95,
    glucose: 120,
    oxygen_saturation: 96,
    symptoms: "Sudden onset of left-sided weakness, slurred speech, and facial droop."
};

fetch('/api/generate-treatment', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
    },
    body: JSON.stringify(patientData)
})
.then(response => response.json())
.then(data => {
    if (data.treatment_plan) {
        console.log('Treatment Plan:', data.treatment_plan);
    } else {
        console.error('Error:', data.detail);
    }
});
```

### AI Prompt Structure

The endpoint sends a structured prompt to the OpenAI API that includes:

1. **System Message**: Defines the AI as a medical assistant following stroke management guidelines
2. **Patient Information**: All provided patient data formatted clearly
3. **Request Structure**: Asks for comprehensive treatment recommendations including:
   - Immediate assessment and monitoring
   - tPA eligibility evaluation and recommendations
   - Alternative treatment options if tPA is not indicated
   - Monitoring parameters
   - Follow-up care plan

### Configuration Requirements

1. **Environment Variable**: `OPENAI_API_KEY` must be set
2. **Dependencies**: `requests` library must be installed
3. **Network Access**: Server must have internet access to reach OpenAI API

### Security Considerations

- API key is stored securely in environment variables
- Input validation prevents injection attacks
- Timeout protection prevents hanging requests
- Error handling prevents information leakage

### Rate Limiting

- OpenAI API has its own rate limits
- Consider implementing client-side rate limiting for production use
- Monitor API usage and costs

### Testing

Use the provided test files:
- `backend/test_generate_treatment.py` - Python test script
- `frontend/test_generate_treatment.html` - Web-based test interface

### Troubleshooting

#### Common Issues

1. **"OpenAI API key not configured"**
   - Set the `OPENAI_API_KEY` environment variable
   - Restart the server after setting the variable

2. **"Request to OpenAI API timed out"**
   - Check internet connectivity
   - Verify OpenAI API status
   - Consider increasing timeout if needed

3. **"Invalid response from OpenAI API"**
   - Check API key validity
   - Verify OpenAI account has sufficient credits
   - Check OpenAI service status

4. **Missing fields error**
   - Ensure all required fields are provided
   - Check field names match exactly (case-sensitive)

### Integration Notes

This endpoint is designed to work alongside the existing treatment plan system but provides a simpler, more direct interface for generating AI-powered treatment recommendations without requiring database storage.

For persistent treatment plans, use the existing `/api/treatment-plan/generate` endpoint which stores plans in the database.

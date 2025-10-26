# ChatGPT Integration for Stroke Treatment Plans

This document explains how to set up and use the ChatGPT API integration for generating AI-powered treatment plans in the Stroke Detection System.

## 🚀 Features

- **AI-Powered Treatment Plans**: Generate comprehensive treatment plans using ChatGPT based on patient data and scan results
- **tPA Eligibility-Based Plans**: Different treatment approaches for eligible vs non-eligible patients
- **Physician Collaboration**: Physicians can add notes, refine plans, and approve treatments
- **Plan Management**: Save, update, and track treatment plan status
- **Real-time Refinement**: Use ChatGPT to refine plans based on physician input

## 📋 Prerequisites

1. **OpenAI API Key**: You need a valid OpenAI API key
2. **Python Dependencies**: Install the required packages
3. **Database Migration**: Update the database schema

## 🛠️ Setup Instructions

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create a `.env` file in the backend directory:

```bash
# Copy the example file
cp .env.example .env

# Edit the .env file and add your OpenAI API key
OPENAI_API_KEY=your_actual_openai_api_key_here
```

### 3. Database Migration

Run the migration script to add the TreatmentPlan table:

```bash
python migrate_database.py
```

### 4. Start the Server

```bash
python main.py
```

## 🎯 How to Use

### For Physicians

1. **Access the Physician Dashboard**: Navigate to the physician dashboard
2. **Generate Treatment Plan**: 
   - Enter Patient Code (e.g., P001)
   - Enter Scan ID
   - Click "Generate Plan"
3. **Review AI Plan**: The system will generate a comprehensive treatment plan
4. **Add Physician Notes**: Add your observations and modifications
5. **Refine Plan**: Use "Refine with AI" to improve the plan based on your notes
6. **Save or Approve**: Save as draft or approve the final plan

### API Endpoints

#### Generate Treatment Plan
```http
POST /api/treatment-plan/generate
Content-Type: application/json

{
  "patient_code": "P001",
  "scan_id": 123,
  "physician_username": "Dr. Smith"
}
```

#### Get Treatment Plan
```http
GET /api/treatment-plan/{treatment_plan_id}
```

#### Update Treatment Plan
```http
PUT /api/treatment-plan/{treatment_plan_id}
Content-Type: application/json

{
  "physician_notes": "Additional monitoring required",
  "status": "approved"
}
```

#### Refine Treatment Plan
```http
POST /api/treatment-plan/{treatment_plan_id}/refine
Content-Type: application/json

{
  "physician_notes": "Patient has diabetes, adjust glucose monitoring"
}
```

#### Get Patient Treatment Plans
```http
GET /api/patients/{patient_code}/treatment-plans
```

## 🧠 AI Treatment Plan Features

### For tPA Eligible Patients
- Immediate interventions (first 24 hours)
- tPA administration protocol and monitoring
- Post-tPA care and monitoring
- Secondary prevention measures
- Rehabilitation planning
- Follow-up schedule
- Potential complications to watch for

### For Non-tPA Eligible Patients
- Immediate supportive care (first 24 hours)
- Medical management strategies
- Secondary prevention measures
- Rehabilitation planning
- Follow-up schedule
- Alternative interventions if applicable
- Monitoring parameters

## 📊 Database Schema

### TreatmentPlan Table
```sql
CREATE TABLE treatmentplans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER NOT NULL,
    scan_id INTEGER NOT NULL,
    plan_type VARCHAR(50),           -- "tpa_eligible", "not_eligible", "alternative"
    ai_generated_plan TEXT,          -- ChatGPT generated plan
    physician_notes TEXT,            -- Physician modifications
    status VARCHAR(20) DEFAULT 'draft', -- "draft", "approved", "implemented"
    created_by VARCHAR(100),         -- Physician username
    created_at DATETIME,
    updated_at DATETIME,
    FOREIGN KEY (patient_id) REFERENCES patients (id),
    FOREIGN KEY (scan_id) REFERENCES strokescans (id)
);
```

## 🔧 Configuration

### ChatGPT Service Configuration

The ChatGPT service is configured in `backend/chatgpt_service.py`:

- **Model**: Uses GPT-3.5-turbo for cost-effectiveness
- **Temperature**: Set to 0.3 for consistent, medical-focused responses
- **Max Tokens**: 1500 tokens for comprehensive plans
- **System Prompt**: Configured as expert neurologist

### Customization Options

You can customize the AI prompts by modifying the `_create_tpa_eligible_prompt()` and `_create_not_eligible_prompt()` methods in `chatgpt_service.py`.

## 🚨 Error Handling

The system includes comprehensive error handling:

- **API Key Validation**: Checks for valid OpenAI API key
- **Patient/Scan Validation**: Verifies patient and scan exist
- **Network Errors**: Handles API timeouts and connection issues
- **Database Errors**: Rollback on failed operations

## 💡 Best Practices

1. **API Key Security**: Never commit your API key to version control
2. **Rate Limiting**: Be mindful of OpenAI API rate limits
3. **Data Privacy**: Ensure patient data is handled according to HIPAA guidelines
4. **Plan Review**: Always review AI-generated plans before approval
5. **Backup Plans**: Keep manual treatment protocols as backup

## 🔍 Troubleshooting

### Common Issues

1. **"OPENAI_API_KEY environment variable is required"**
   - Solution: Ensure your `.env` file contains a valid API key

2. **"Error generating treatment plan"**
   - Check your internet connection
   - Verify OpenAI API key is valid and has credits
   - Check OpenAI service status

3. **Database migration fails**
   - Ensure the database file exists
   - Check file permissions
   - Run the migration script from the correct directory

### Debug Mode

Enable debug logging by setting `DEBUG=True` in your `.env` file.

## 📈 Future Enhancements

- **Multi-language Support**: Generate plans in different languages
- **Template Customization**: Allow custom prompt templates
- **Integration with EMR**: Direct integration with Electronic Medical Records
- **Audit Trail**: Enhanced logging and tracking of plan modifications
- **Mobile Support**: Mobile-optimized interface for treatment plans

## 📞 Support

For technical support or questions about the ChatGPT integration:

1. Check the troubleshooting section above
2. Review the API documentation
3. Check OpenAI's API documentation for service status
4. Contact the development team

---

**Note**: This integration is designed to assist physicians in creating treatment plans. All AI-generated plans should be reviewed and approved by qualified medical professionals before implementation.

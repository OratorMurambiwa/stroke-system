import os
import openai
from typing import Dict, Any, Optional
from datetime import datetime
import json

class ChatGPTTreatmentPlanService:
    def __init__(self):
        # Initialize OpenAI client
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key or self.api_key == "your_openai_api_key_here":
            self.api_key = None
            print("Warning: OPENAI_API_KEY not configured. AI features will be disabled.")
        else:
            openai.api_key = self.api_key
    
    def generate_treatment_plan(self, patient_data: Dict[str, Any], scan_data: Dict[str, Any], 
                              eligibility_result: str, is_eligible: bool) -> str:
        """
        Generate a comprehensive treatment plan using ChatGPT based on patient data and scan results.
        """
        if not self.api_key:
            return "AI service is not configured. Please set OPENAI_API_KEY environment variable."
        
        try:
            # Prepare the prompt based on eligibility
            if is_eligible:
                prompt = self._create_tpa_eligible_prompt(patient_data, scan_data, eligibility_result)
            else:
                prompt = self._create_not_eligible_prompt(patient_data, scan_data, eligibility_result)
            
            # Call OpenAI API
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system", 
                        "content": "You are an expert neurologist specializing in stroke treatment. Provide detailed, evidence-based treatment plans following current medical guidelines."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                max_tokens=1500,
                temperature=0.3  # Lower temperature for more consistent, medical-focused responses
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            return f"Error generating treatment plan: {str(e)}"
    
    def _create_tpa_eligible_prompt(self, patient_data: Dict[str, Any], scan_data: Dict[str, Any], 
                                   eligibility_result: str) -> str:
        """Create prompt for tPA eligible patients"""
        prompt = f"""
        Patient Information:
        - Name: {patient_data.get('name', 'N/A')}
        - Age: {patient_data.get('age', 'N/A')} years
        - Gender: {patient_data.get('gender', 'N/A')}
        - Chief Complaint: {patient_data.get('chief_complaint', 'N/A')}
        - Time since onset: {patient_data.get('time_since_onset', 'N/A')}
        
        Vital Signs:
        - Blood Pressure: {patient_data.get('systolic_bp', 'N/A')}/{patient_data.get('diastolic_bp', 'N/A')} mmHg
        - Heart Rate: {patient_data.get('heart_rate', 'N/A')} bpm
        - Temperature: {patient_data.get('temperature', 'N/A')}°F
        - Oxygen Saturation: {patient_data.get('oxygen_saturation', 'N/A')}%
        - Glucose: {patient_data.get('glucose', 'N/A')} mg/dL
        - INR: {patient_data.get('inr', 'N/A')}
        
        Scan Results:
        - Imaging Confirmed: {scan_data.get('imaging_confirmed', 'N/A')}
        - Diagnosis: {scan_data.get('prediction', 'N/A')}
        - Eligibility Assessment: {eligibility_result}
        
        Please provide a comprehensive treatment plan for this tPA-eligible stroke patient. Include:
        1. Immediate interventions (first 24 hours)
        2. tPA administration protocol and monitoring
        3. Post-tPA care and monitoring
        4. Secondary prevention measures
        5. Rehabilitation planning
        6. Follow-up schedule
        7. Potential complications to watch for
        
        Format the response in clear sections with specific medical recommendations.
        """
        return prompt
    
    def _create_not_eligible_prompt(self, patient_data: Dict[str, Any], scan_data: Dict[str, Any], 
                                   eligibility_result: str) -> str:
        """Create prompt for non-tPA eligible patients"""
        prompt = f"""
        Patient Information:
        - Name: {patient_data.get('name', 'N/A')}
        - Age: {patient_data.get('age', 'N/A')} years
        - Gender: {patient_data.get('gender', 'N/A')}
        - Chief Complaint: {patient_data.get('chief_complaint', 'N/A')}
        - Time since onset: {patient_data.get('time_since_onset', 'N/A')}
        
        Vital Signs:
        - Blood Pressure: {patient_data.get('systolic_bp', 'N/A')}/{patient_data.get('diastolic_bp', 'N/A')} mmHg
        - Heart Rate: {patient_data.get('heart_rate', 'N/A')} bpm
        - Temperature: {patient_data.get('temperature', 'N/A')}°F
        - Oxygen Saturation: {patient_data.get('oxygen_saturation', 'N/A')}%
        - Glucose: {patient_data.get('glucose', 'N/A')} mg/dL
        - INR: {patient_data.get('inr', 'N/A')}
        
        Scan Results:
        - Imaging Confirmed: {scan_data.get('imaging_confirmed', 'N/A')}
        - Diagnosis: {scan_data.get('prediction', 'N/A')}
        - Eligibility Assessment: {eligibility_result}
        
        This patient is NOT eligible for tPA therapy. Please provide a comprehensive alternative treatment plan including:
        1. Immediate supportive care (first 24 hours)
        2. Medical management strategies
        3. Secondary prevention measures
        4. Rehabilitation planning
        5. Follow-up schedule
        6. Alternative interventions if applicable
        7. Monitoring parameters
        
        Format the response in clear sections with specific medical recommendations.
        """
        return prompt
    
    def refine_treatment_plan(self, existing_plan: str, physician_notes: str) -> str:
        """
        Refine an existing treatment plan based on physician input using ChatGPT.
        """
        if not self.api_key:
            return "AI service is not configured. Please set OPENAI_API_KEY environment variable."
        
        try:
            prompt = f"""
            Below is an existing treatment plan for a stroke patient:
            
            {existing_plan}
            
            The physician has provided the following additional notes and modifications:
            
            {physician_notes}
            
            Please refine and update the treatment plan incorporating the physician's notes while maintaining medical accuracy and evidence-based recommendations. 
            Highlight any changes made and provide the updated comprehensive treatment plan.
            """
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system", 
                        "content": "You are an expert neurologist. Refine treatment plans based on physician input while maintaining medical accuracy."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                max_tokens=1500,
                temperature=0.3
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            return f"Error refining treatment plan: {str(e)}"

# Global instance - lazy loaded
chatgpt_service = None

def get_chatgpt_service():
    global chatgpt_service
    if chatgpt_service is None:
        chatgpt_service = ChatGPTTreatmentPlanService()
    return chatgpt_service

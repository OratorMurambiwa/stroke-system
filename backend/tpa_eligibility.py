from typing import Tuple

def check_tpa_eligibility(data: dict) -> Tuple[bool, str]:
    # Initial assessment
    if data["hours_since_onset"] > 4.5:
        return False, "Initial Assessment: Patient presented beyond 4.5-hour treatment window"
    if data["imaging_confirmed"] != "yes":
        return False, "Initial Assessment: Ischemic stroke not confirmed by neuroimaging (CT/MRI)"
    if data["consent"] != "yes":
        return False, "Initial Assessment: Informed consent not obtained from patient or representative"

    # Inclusion criteria
    if data["age"] < 18:
        return False, "Exclusion: Patient is under 18 years old"
    if data["nhiss_score"] < 4:
        return False, "Exclusion: NIHSS score below minimum threshold for thrombolytic therapy"
    if data["inr"] > 1.7:
        return False, "Exclusion: INR exceeds safe threshold for thrombolysis (INR > 1.7)"

    if not (60 <= data["heart_rate"] <= 100):
        return False, "Exclusion: Abnormal heart rate outside 60–100 bpm"
    if not (12 <= data["respiratory_rate"] <= 20):
        return False, "Exclusion: Abnormal respiratory rate outside 12–20 breaths/min"
    if not (97 <= data["temperature"] <= 100.4):
        return False, "Exclusion: Abnormal body temperature outside acceptable range (97–100.4 °F)"
    if not (95 <= data["oxygen_saturation"] <= 100):
        return False, "Exclusion: Oxygen saturation below 95%"

    # Exclusion criteria
    if data["recent_trauma"] == "yes":
        return False, "Exclusion: Recent head or spinal trauma within 3 months"
    if data["recent_stroke_or_injury"] == "yes":
        return False, "Exclusion: History of stroke or serious head injury within 3 months"
    if data["intracranial_issue"] == "yes":
        return False, "Exclusion: Presence of intracranial hemorrhage, tumor, or vascular malformation"
    if data["recent_mi"] == "yes":
        return False, "Exclusion: Recent myocardial infarction (heart attack)"
    if data["systolic_bp"] > 185 or data["diastolic_bp"] > 110:
        return False, "Exclusion: Blood pressure exceeds safe threshold for tPA (SBP > 185 or DBP > 110 mmHg)"
    if data["glucose"] < 50 or data["glucose"] > 400:
        return False, "Exclusion: Blood glucose outside acceptable range (<50 or >400 mg/dL)"
    if data["anticoagulant_risk"] == "yes":
        return False, "Exclusion: Use of anticoagulants with elevated INR ≥ 3"
    if data["platelet_count"] < 100:
        return False, "Exclusion: Platelet count below safe minimum (<100,000/μL)"
    if data["recent_surgery"] == "yes":
        return False, "Exclusion: Recent surgery or biopsy of parenchymal organ"

    return True, "Meets all criteria for intravenous thrombolysis (tPA administration)"

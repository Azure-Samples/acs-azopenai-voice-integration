# Recruitment Interview Persona Guide

## Overview

A comprehensive recruitment interview system message has been added to conduct preliminary phone screenings for technical positions. The AI acts as "Alex," a recruitment specialist conducting structured interviews.

## What's Included

### 📋 Candidate CV - Sarah Mitchell
- **Role**: Full Stack Developer with 5 years experience
- **Current Position**: Senior Full Stack Developer at DigitalWave Technologies
- **Key Skills**: React.js, Node.js, Python, AWS, Docker, Kubernetes
- **Notable Achievements**:
  - Led customer portal serving 50,000+ users
  - Improved system scalability by 300% through microservices
  - Reduced API response time by 40%
- **Certifications**: AWS Certified Developer, MongoDB Certified Developer
- **Open Source**: Active contributor to React ecosystem

### 💼 Job Description - Senior Full Stack Developer
- **Company**: CloudScale Innovations
- **Location**: London, UK (Hybrid - 3 days office, 2 remote)
- **Salary**: £70,000 - £90,000 + benefits
- **Key Requirements**:
  - 4+ years Full Stack experience
  - JavaScript/TypeScript, React.js/Vue.js
  - Node.js or Python backend
  - SQL/NoSQL databases
  - Cloud platforms (AWS/Azure/GCP)
  - Docker and CI/CD

### 🎯 Interview Structure (15-20 minutes)

1. **Opening (2 minutes)**
   - Introduction and role explanation
   - Confirm availability for the call
   - Set expectations

2. **Experience & Background (5-7 minutes)**
   - Current role and achievements
   - Key projects and technical decisions
   - Leadership and mentoring experience
   - Reason for seeking new opportunities

3. **Technical Assessment (5-7 minutes)**
   - Microservices architecture knowledge
   - Cloud experience and optimization
   - API design approaches
   - Database optimization techniques
   - Testing and CI/CD strategies

4. **Cultural Fit & Logistics (3-5 minutes)**
   - Work style preferences
   - Hybrid working suitability
   - Salary expectations
   - Notice period
   - Career goals

5. **Closing (2 minutes)**
   - Candidate questions
   - Next steps explanation
   - Follow-up timeline

## How to Use

### Method 1: Via API Payload (Recommended)

Include `"persona": "recruitment"` in your API request:

```json
POST http://localhost:8000/api/initiateOutboundCall
Content-Type: application/json

{
    "phone_number": "+447427404900",
    "customer_name": "Sarah Mitchell",
    "customer_email": "sarah.mitchell@email.com",
    "persona": "recruitment",
    "use_agent": false
}
```

### Method 2: Test with HTTP File

Use the examples in `outbound_call.http`:

```http
### RECRUITMENT INTERVIEW - conduct phone screening
POST http://localhost:8000/api/initiateOutboundCall
Content-Type: application/json

{
    "phone_number": "+447427404900",
    "customer_name": "Sarah Mitchell",
    "customer_email": "sarah.mitchell@email.com",
    "persona": "recruitment",
    "use_agent": false
}
```

## Available Personas

| Persona | Description | Use Case |
|---------|-------------|----------|
| `default` | Travel agent (Kira) | Travel booking and vacation planning |
| `recruitment` | Recruitment specialist (Alex) | Technical job interviews and candidate screening |

## Example Interview Flow

### AI Opening
> "Hello! Am I speaking with Sarah Mitchell? Great! My name is Alex, and I'm an AI recruitment specialist with TechTalent Solutions. I'm calling about an exciting Senior Full Stack Developer opportunity with CloudScale Innovations that I think would be a great fit for your background. Do you have about 15-20 minutes to discuss this role?"

### Sample Questions the AI Will Ask

**About Current Role:**
- "I see you're currently at DigitalWave Technologies. Can you tell me about the customer portal you led development on? What were some of the key challenges in scaling to 50,000 users?"

**Technical Deep Dive:**
- "You mentioned implementing microservices architecture. What prompted that architectural decision, and how did you approach migrating from a monolithic system?"
- "When would you choose a microservices architecture over a monolithic approach for a new project?"

**Problem Solving:**
- "You achieved a 40% improvement in API response time. Can you walk me through your approach to identifying and solving that performance bottleneck?"

**Cultural Fit:**
- "The role offers a hybrid model - 3 days in office, 2 days remote. How does that align with your preferred work style?"
- "What are you looking for in your next role that's driving your interest in making a move?"

### AI Closing
> "That's been really helpful, Sarah. Based on our conversation today, I think you'd be a strong fit for this role. Do you have any questions for me about the position, the team, or CloudScale Innovations? ... Perfect! Here are the next steps: I'll send you a detailed job description and information about the team via email. If you're still interested after reviewing, we'll schedule a technical interview with the engineering team within the next week. You can expect to hear from me within 48 hours. Thank you so much for your time today!"

## Customization

To create additional personas for different roles:

1. **Add to constants.py**:
```python
SYSTEM_MESSAGE_YOUR_PERSONA = """
Your system message here...
"""

system_message_dict = {
    "default": SYSTEM_MESSAGE_DEFAULT,
    "recruitment": SYSTEM_MESSAGE_RECRUITMENT,
    "your_persona": SYSTEM_MESSAGE_YOUR_PERSONA  # Add here
}
```

2. **Use in API calls**:
```json
{
    "phone_number": "+44...",
    "customer_name": "Name",
    "persona": "your_persona"
}
```

## Tips for Best Results

### For the Candidate (Person Answering the Call)

- **Be Prepared**: Have your CV/resume handy
- **Be Specific**: Use concrete examples from your experience
- **Ask Questions**: Show interest by asking about the role
- **Be Honest**: About experience, availability, and expectations

### For Testing

- **Use a Real Phone**: Test the full experience, including audio quality
- **Time It**: Ensure the interview stays within 15-20 minutes
- **Listen for Flow**: Check if questions follow logically
- **Evaluate Assessment**: Does the AI properly assess technical depth?

### For Production Use

- **Customize the CV**: Update Sarah Mitchell's details to match your actual candidates
- **Adjust Job Description**: Modify for your specific roles
- **Update Questions**: Tailor technical questions to your tech stack
- **Set Salary Expectations**: Adjust ranges to match your offers
- **Modify Company Name**: Change CloudScale Innovations to your client companies

## What the AI Evaluates

✅ **Technical Competency**
- Understanding of relevant technologies
- Depth of experience with required skills
- Problem-solving approach
- Ability to explain technical concepts

✅ **Experience Validation**
- Actual role responsibilities
- Project involvement and impact
- Leadership and collaboration
- Career progression

✅ **Cultural Fit**
- Communication skills
- Work style preferences
- Team collaboration approach
- Learning and growth mindset

✅ **Practical Considerations**
- Salary alignment with budget
- Notice period compatibility
- Location/hybrid work suitability
- Career goals alignment

## Next Steps After Interview

The AI will:
1. ✅ Thank the candidate for their time
2. ✅ Explain the next steps (technical interview if successful)
3. ✅ Commit to following up within 48 hours via email
4. ✅ Answer any candidate questions

You should:
1. Review the call recording/transcript
2. Assess candidate responses against job requirements
3. Make go/no-go decision for technical interview
4. Follow up as promised (within 48 hours)

## Files Modified

- ✅ `api/src/config/constants.py` - Added SYSTEM_MESSAGE_RECRUITMENT
- ✅ `api/src/models/models.py` - Added persona field
- ✅ `api/src/interfaces/ai_voice_base.py` - Updated to read persona from payload
- ✅ `api/src/services/ai_voice_agent_service.py` - Updated persona handling
- ✅ `outbound_call.http` - Added recruitment examples

## Troubleshooting

**AI uses wrong persona:**
- Check the `persona` field in your API payload
- Verify it's set to `"recruitment"` exactly
- Check logs for "Using persona: recruitment"

**Interview feels too short/long:**
- Adjust the timing in the system message
- Modify the question list
- Update conversation flow instructions

**Questions don't match your needs:**
- Edit SYSTEM_MESSAGE_RECRUITMENT in `constants.py`
- Add/remove questions in the "EXAMPLE QUESTIONS TO USE" section
- Adjust the interview structure sections

**Want different candidate/job:**
- Edit the CV section in SYSTEM_MESSAGE_RECRUITMENT
- Update the Job Description section
- Modify the required skills and experience


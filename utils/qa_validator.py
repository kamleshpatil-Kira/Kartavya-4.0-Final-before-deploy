"""
QA Validation module to ensure content quality and compliance
Validates generated content for factual accuracy, compliance, and quality
"""
import re
from typing import Dict, Any, List, Tuple
from utils.logger import logger, log_activity

class QAValidator:
    """Validates course content for quality and compliance"""
    
    def __init__(self):
        # Keywords that might indicate non-compliance or issues
        self.compliance_keywords = {
            'hallucination_indicators': [
                'according to sources', 'some say', 'it is believed',
                'experts suggest without citation', 'unverified claims'
            ],
            'plagiarism_indicators': [
                'as stated in', 'according to [specific source]',
                'quoted from', 'excerpt from'
            ],
            'compliance_requirements': [
                'us federal', 'federal guidelines', 'compliance',
                'regulatory', 'legal requirements'
            ]
        }
    
    def validate_course_content(self, course_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate entire course content
        Returns: (is_valid, list_of_issues)
        """
        issues = []
        
        # Validate course structure
        if 'course' not in course_data:
            issues.append("Missing course information")
            return False, issues
        
        if 'modules' not in course_data or len(course_data['modules']) == 0:
            issues.append(f"Course has no modules (found {len(course_data.get('modules', []))})")
        
        # Validate each module
        for idx, module in enumerate(course_data.get('modules', []), 1):
            module_issues = self.validate_module(module, idx)
            issues.extend(module_issues)
        
        # Validate quiz
        quiz_issues = self.validate_quiz(course_data.get('quiz', {}))
        issues.extend(quiz_issues)
        
        is_valid = len(issues) == 0
        log_activity("QA Validation", {
            "is_valid": is_valid,
            "issues_count": len(issues),
            "issues": issues
        })
        
        return is_valid, issues
    
    def validate_module(self, module: Dict[str, Any], module_num: int) -> List[str]:
        """Validate a single module"""
        issues = []
        
        # Check required fields
        required_fields = ['moduleNumber', 'moduleTitle', 'content', 'knowledgeCheck']
        for field in required_fields:
            if field not in module:
                issues.append(f"Module {module_num}: Missing required field '{field}'")
        
        # Validate content structure
        if 'content' in module:
            content_issues = self.validate_content_structure(module['content'], module_num)
            issues.extend(content_issues)
        
        # Validate knowledge check
        if 'knowledgeCheck' in module:
            kc_issues = self.validate_knowledge_check(module['knowledgeCheck'], module_num)
            issues.extend(kc_issues)
        
        # Check for compliance keywords
        compliance_issues = self.check_compliance(module, module_num)
        issues.extend(compliance_issues)
        
        return issues
    
    def validate_content_structure(self, content: Dict[str, Any], module_num: int) -> List[str]:
        """Validate content structure"""
        issues = []
        
        if isinstance(content, dict):
            if 'sections' not in content:
                issues.append(f"Module {module_num}: Content missing 'sections'")
            else:
                for idx, section in enumerate(content.get('sections', []), 1):
                    if 'sectionTitle' not in section:
                        issues.append(f"Module {module_num}, Section {idx}: Missing 'sectionTitle'")
                    if 'content' not in section and 'concepts' not in section:
                        issues.append(f"Module {module_num}, Section {idx}: Missing content or concepts")
                    
                    if 'concepts' in section:
                        for c_idx, concept in enumerate(section['concepts'], 1):
                            explanation = str(concept.get('explanation', '')).lower()
                            # Reject generic AI filler phrases (Fix 6: Content Depth)
                            filler_phrases = ["is important because", "plays a crucial role", "it is essential to note that"]
                            for filler in filler_phrases:
                                if filler in explanation:
                                    issues.append(f"Module {module_num}, Section {idx}, Concept {c_idx}: Contains generic filler ({filler}).")
        
        return issues
    
    def validate_knowledge_check(self, kc: Dict[str, Any], module_num: int) -> List[str]:
        """Validate knowledge check structure"""
        issues = []
        
        required_fields = ['question', 'options', 'correctAnswer', 'feedback']
        for field in required_fields:
            if field not in kc:
                issues.append(f"Module {module_num}: Knowledge check missing '{field}'")
        
        # Validate options
        if 'options' in kc:
            if len(kc['options']) != 4:
                issues.append(f"Module {module_num}: Knowledge check should have exactly 4 options")
            
            # Check if correct answer exists in options
            if 'correctAnswer' in kc:
                correct = kc['correctAnswer']
                if correct not in kc['options']:
                    issues.append(f"Module {module_num}: Correct answer '{correct}' not found in options")
        
        return issues
    
    def validate_quiz(self, quiz: Dict[str, Any]) -> List[str]:
        """Validate quiz structure"""
        issues = []
        
        if not quiz:
            issues.append("Quiz is missing")
            return issues
        
        if 'questions' not in quiz:
            issues.append("Quiz missing 'questions'")
            return issues
        
        questions = quiz['questions']
        if len(questions) == 0:
            issues.append("Quiz has no questions")
        
        for idx, question in enumerate(questions, 1):
            q_issues = self.validate_quiz_question(question, idx)
            issues.extend(q_issues)
        
        return issues
    
    def validate_quiz_question(self, question: Dict[str, Any], q_num: int) -> List[str]:
        """Validate a single quiz question strictly"""
        issues = []
        
        required_fields = ['question', 'options', 'correctAnswer', 'feedback']
        for field in required_fields:
            if field not in question:
                issues.append(f"Quiz Question {q_num}: Missing '{field}'")
        
        if 'options' in question:
            options = question['options']
            if len(options) != 4:
                issues.append(f"Quiz Question {q_num}: Should have exactly 4 options. Found {len(options)}.")
            
            if 'correctAnswer' in question:
                correct = question['correctAnswer']
                if correct not in options:
                    issues.append(f"Quiz Question {q_num}: Correct answer '{correct}' not in options {list(options.keys())}")
                    
        if 'feedback' in question:
            feedback = question['feedback']
            if 'correct' not in feedback or 'incorrect' not in feedback:
                issues.append(f"Quiz Question {q_num}: Feedback missing 'correct' or 'incorrect' baseline explanations.")
                
            # Generic filler checks for feedback
            if len(str(feedback.get('correct', ''))) < 20:
                issues.append(f"Quiz Question {q_num}: Correct feedback too short/generic.")
        
        return issues
    
    def check_compliance(self, module: Dict[str, Any], module_num: int) -> List[str]:
        """Check for compliance and quality issues"""
        issues = []
        
        # Extract text content for analysis
        text_content = self._extract_text(module)
        
        # Check for potential hallucinations (basic check)
        if self._has_hallucination_indicators(text_content):
            issues.append(f"Module {module_num}: Potential hallucination indicators found")
        
        # Check for explicit compliance mentions if required
        # This is a basic check - can be enhanced
        
        return issues
    
    def _extract_text(self, module: Dict[str, Any]) -> str:
        """Extract all text content from module"""
        text_parts = []
        
        if 'moduleTitle' in module:
            text_parts.append(str(module['moduleTitle']))
        
        if 'content' in module:
            content = module['content']
            if isinstance(content, dict):
                if 'sections' in content:
                    for section in content['sections']:
                        text_parts.append(str(section.get('sectionTitle', '')))
                        text_parts.append(str(section.get('content', '')))
                        if 'concepts' in section:
                            for concept in section['concepts']:
                                text_parts.append(str(concept.get('explanation', '')))
        
        return ' '.join(text_parts).lower()
    
    def _has_hallucination_indicators(self, text: str) -> bool:
        """Basic check for hallucination indicators"""
        indicators = [
            'according to sources',
            'some experts believe without citation',
            'it is widely believed',
            'unverified'
        ]
        
        for indicator in indicators:
            if indicator in text:
                return True
        return False
    
    def enhance_prompts_with_qa(self, base_prompt: str) -> str:
        """Enhance prompts with QA requirements"""
        qa_requirements = """
        
CRITICAL QA REQUIREMENTS (MUST FOLLOW):
1. Factual Accuracy: All information must be factually correct and verifiable
2. No Hallucinations: Do not invent facts, statistics, or citations
3. No Plagiarism: Generate original content, do not copy from sources
4. Compliance: Ensure all content complies with US Federal Guidelines
5. Contextual Relevance: Content must be relevant to the user's specified context
6. Quality: Content must be professional, clear, and educational
7. Completeness: All required fields must be filled
8. Consistency: Maintain consistent tone and style throughout
"""
        return base_prompt + qa_requirements

# Create instance
qa_validator = QAValidator()


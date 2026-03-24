"""
PDF Generator for Course Content (without audio)
Generates a PDF file containing course content, images, and text
"""
from pathlib import Path
from typing import Dict, Any, List
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Image, Table, TableStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from utils.logger import logger, log_activity
from io import BytesIO


class PDFGenerator:
    """Generate PDF files from course content"""
    
    def _get_font_paths_for_language(self, language: str):
        """Return a list of (regular, bold) font paths to try for the given language."""
        language = language.lower()
        
        # DejaVuSans: Excellent coverage for Latin, Cyrillic, Greek, Arabic scripts
        dejavu = [
            ('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'),
        ]
        # DroidSansFallbackFull: CJK (Chinese, Japanese, Korean) + basic Latin
        cjk = [
            ('/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf', '/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf'),
        ]
        # Lohit-Devanagari: Hindi, Marathi, Nepali, Sanskrit
        devanagari = [
            ('/usr/share/fonts/truetype/lohit-devanagari/Lohit-Devanagari.ttf', '/usr/share/fonts/truetype/lohit-devanagari/Lohit-Devanagari.ttf'),
        ]
        
        # Priority: language-specific font first, then fallbacks
        font_map = {
            'hindi': devanagari,
            'marathi': devanagari,
            'nepali': devanagari,
            'sanskrit': devanagari,
            'japanese': cjk,
            'chinese': cjk,
            'chinese (simplified)': cjk,
            'chinese (traditional)': cjk,
            'korean': cjk,
        }
        
        # Default fonts: DejaVuSans covers English, Spanish, French, German, Portuguese,
        # Italian, Dutch, Turkish, Russian, Arabic, Vietnamese, and many more
        default_fonts = dejavu
        
        return font_map.get(language, []) + default_fonts

    def _setup_custom_styles(self, language: str):
        """Setup custom paragraph styles based on course language"""
        import os
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        self.styles = getSampleStyleSheet()
        
        font_name = 'Helvetica'
        font_name_bold = 'Helvetica-Bold'
        
        font_paths = self._get_font_paths_for_language(language)
        
        # Use a unique font name per language to avoid ReportLab cache collisions
        safe_lang = language.lower().replace(' ', '_').replace('(', '').replace(')', '')
        reg_name = f'KartavyaFont_{safe_lang}'
        bold_name = f'KartavyaFont_{safe_lang}_Bold'
        
        for regular, bold in font_paths:
            if os.path.exists(regular) and os.path.exists(bold):
                try:
                    pdfmetrics.registerFont(TTFont(reg_name, regular))
                    pdfmetrics.registerFont(TTFont(bold_name, bold))
                    font_name = reg_name
                    font_name_bold = bold_name
                    logger.info(f"PDF font registered: {reg_name} -> {regular}")
                    break
                except Exception as e:
                    logger.warning(f"Could not register font {regular}: {e}")
        # Override ALL built-in styles so no Helvetica leaks through
        for style_name in ['Normal', 'Heading1', 'Heading2', 'Heading3', 'Heading4', 'BodyText']:
            if style_name in self.styles.byName:
                self.styles[style_name].fontName = font_name
        for style_name in ['Heading1', 'Heading2', 'Heading3', 'Heading4']:
            if style_name in self.styles.byName:
                self.styles[style_name].fontName = font_name_bold

        # Title style — matches reference PDF: 18pt bold #1f4e79, left-aligned
        self.styles.add(ParagraphStyle(
            name='CourseTitle',
            parent=self.styles['Heading1'],
            fontSize=18,
            leading=22,
            textColor=colors.HexColor('#1f4e79'),
            spaceAfter=12,
            alignment=TA_LEFT,
            fontName=font_name_bold
        ))
        
        # Module title style — matches reference PDF: 14pt bold #2e75b6
        self.styles.add(ParagraphStyle(
            name='ModuleTitle',
            parent=self.styles['Heading2'],
            fontSize=14,
            leading=18,
            textColor=colors.HexColor('#2e75b6'),
            spaceAfter=4,
            spaceBefore=12,
            fontName=font_name_bold
        ))
        
        # Section title style — matches reference PDF: 10pt regular #000000 with bullet
        self.styles.add(ParagraphStyle(
            name='SectionTitle',
            parent=self.styles['Normal'],
            fontSize=10,
            leading=14,
            textColor=colors.HexColor('#000000'),
            leftIndent=15,
            spaceBefore=1,
            spaceAfter=1,
            fontName=font_name
        ))
        
        # Content style
        self.styles.add(ParagraphStyle(
            name='Content',
            parent=self.styles['Normal'],
            fontSize=11,
            leading=14,
            alignment=TA_JUSTIFY,
            spaceAfter=6,
            fontName=font_name
        ))
        
        # Learning objectives style
        self.styles.add(ParagraphStyle(
            name='LearningObjectives',
            parent=self.styles['Normal'],
            fontSize=10,
            leading=12,
            leftIndent=20,
            spaceAfter=3,
            fontName=font_name
        ))
        
        # Heading 5 style for scenarios (only add if it doesn't exist)
        if 'Heading5' not in self.styles.byName:
            self.styles.add(ParagraphStyle(
                name='Heading5',
                parent=self.styles['Heading4'],
                fontSize=14,
                textColor=colors.HexColor('#025e9b'),
                spaceAfter=10,
                spaceBefore=10,
                fontName=font_name_bold
            ))

    def _render_interactive_block_pdf(self, story: 'List', block: Dict):
        """Render interactive block into PDF story"""
        if not block or "type" not in block or "data" not in block:
            return
            
        b_type = block["type"].lower()
        data = block["data"]
        
        if b_type == "tabs":
            tabs = data.get("tabs", [])
            for i, tab in enumerate(tabs):
                title = tab.get("title", f"Tab {i+1}")
                story.append(Spacer(1, 0.04*inch))
                story.append(Paragraph(f"<b>{self._escape_html(title)}</b>", self.styles['Heading5']))
                
                content = tab.get("content", "")
                if content:
                    paragraphs = content.split('\n\n')
                    for para in paragraphs:
                        if para.strip():
                            story.append(Paragraph(self._escape_html(para.strip()), self.styles['Content']))
                            story.append(Spacer(1, 0.02*inch))
                            
        elif b_type == "accordion":
            items = data.get("items", [])
            for i, item in enumerate(items):
                q = item.get("question", f"Item {i+1}")
                a = item.get("answer", "")
                story.append(Spacer(1, 0.04*inch))
                story.append(Paragraph(f"<b>{self._escape_html(q)}</b>", self.styles['Heading5']))
                if a:
                    paragraphs = a.split('\n\n')
                    for para in paragraphs:
                        if para.strip():
                            story.append(Paragraph(self._escape_html(para.strip()), self.styles['Content']))
                            story.append(Spacer(1, 0.02*inch))
                            
        elif b_type == "note":
            variant = data.get("variant", "info")
            text = data.get("text", "")
            if text:
                icon = "ℹ️"
                if variant == "tip": icon = "💡"
                elif variant == "warning": icon = "⚠️"
                
                story.append(Spacer(1, 0.04*inch))
                story.append(Paragraph(f"<b>{icon} Note:</b>", self.styles['Heading5']))
                paragraphs = text.split('\n\n')
                for para in paragraphs:
                    if para.strip():
                        story.append(Paragraph(self._escape_html(para.strip()), self.styles['Content']))
                        story.append(Spacer(1, 0.02*inch))
                        
        elif b_type == "table":
            headers = data.get("headers", [])
            rows = data.get("rows", [])
            if headers or rows:
                story.append(Spacer(1, 0.04*inch))
                table_data = []
                if headers:
                    table_data.append([Paragraph(f"<b>{self._escape_html(h)}</b>", self.styles['Content']) for h in headers])
                for row in rows:
                    table_data.append([Paragraph(self._escape_html(cell), self.styles['Content']) for cell in row])
                
                if table_data:
                    t = Table(table_data)
                    t.setStyle(TableStyle([
                        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#f0fdfa')) if headers else ('BACKGROUND', (0,0), (-1,-1), colors.white),
                        ('TEXTCOLOR', (0,0), (-1,-1), colors.black),
                        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
                        ('FONTNAME', (0,0), (-1,-1), self.styles['Content'].fontName),
                        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
                        ('TOPPADDING', (0,0), (-1,-1), 8),
                        ('GRID', (0,0), (-1,-1), 1, colors.HexColor('#e2e8f0')),
                    ]))
                    story.append(t)
                    story.append(Spacer(1, 0.04*inch))
                    
        elif b_type == "flipcard" or b_type == "flashcards" or b_type == "flashcard":
            cards = data.get("cards") or data.get("flashcards", [])
            if cards:
                story.append(Spacer(1, 0.04*inch))
                for i, card in enumerate(cards):
                    front = card.get("front", f"Card {i+1}")
                    back = card.get("back", "")
                    story.append(Paragraph(f"<b>{self._escape_html(front)}</b>", self.styles['Heading5']))
                    if back:
                        paragraphs = back.split('\n\n')
                        for para in paragraphs:
                            if para.strip():
                                story.append(Paragraph(self._escape_html(para.strip()), self.styles['Content']))
                                story.append(Spacer(1, 0.02*inch))
                                
    
    def generate_pdf(self, course_data: Dict[str, Any], output_path: Path) -> str:
        """
        Generate PDF file from course data (without audio)
        
        Args:
            course_data: Course data dictionary
            output_path: Path where PDF should be saved
            
        Returns:
            Path to generated PDF file
        """
        log_activity("PDF generation started", {"output_path": str(output_path)})
        
        try:
            # Get course language for font selection
            # Get course language for font selection
            course = course_data.get('course') or {}
            outline = course_data.get('outline') or {}
            
            language = course.get('courseLanguage') or 'English'
            
            # Setup styles for this specific language
            self._setup_custom_styles(language)
            
            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Create PDF document
            pdf_path = output_path
            doc = SimpleDocTemplate(
                str(pdf_path),
                pagesize=letter,
                rightMargin=0.75*inch,
                leftMargin=0.75*inch,
                topMargin=0.75*inch,
                bottomMargin=0.75*inch
            )
            # Build PDF content
            story = []
            
            # Course header
            title = course.get('title') or outline.get('courseTitle') or 'Course'
            story.append(Paragraph(self._escape_html(title), self.styles['CourseTitle']))
            story.append(Spacer(1, 0.08*inch))
            
            # Course description
            if course.get('description'):
                story.append(Paragraph(f"<b>Description:</b> {self._escape_html(course['description'])}", self.styles['Content']))
                story.append(Spacer(1, 0.08*inch))
            
            # Course overview
            if course.get('overview'):
                story.append(Paragraph("<b>Course Overview</b>", self.styles['Heading2']))
                story.append(Paragraph(self._escape_html(course['overview']), self.styles['Content']))
                story.append(Spacer(1, 0.08*inch))
            
            # Learning objectives
            if course.get('learningObjectives'):
                story.append(Paragraph("<b>Learning Objectives</b>", self.styles['Heading3']))
                for obj in course['learningObjectives']:
                    story.append(Paragraph(f"• {self._escape_html(obj)}", self.styles['LearningObjectives']))
                story.append(Spacer(1, 0.08*inch))
            
            # Page break only if we have full modules
            if course_data.get('modules'):
                story.append(PageBreak())
            else:
                story.append(Spacer(1, 0.2*inch))
            # Modules
            # Modules or Outline
            modules = course_data.get('modules') or []
            
            if not modules and outline:
                # Render Outline Only Content
                
                outline_modules = outline.get('modules') or []
                for idx, module in enumerate(outline_modules, 1):
                    story.append(Paragraph(f"Module {idx}: {self._escape_html(module.get('moduleTitle', ''))}", self.styles['ModuleTitle']))
                    
                    if module.get('outlineSections'):
                        for s_idx, sec in enumerate(module['outlineSections'], 1):
                            import re
                            sec_title = str(sec.get("sectionTitle", ""))
                            clean_title = re.sub(r'^([\d\.]+|Module\s*\d+:?)\s*', '', sec_title).strip()
                            numbered_title = f"{idx}.{s_idx} {clean_title}"
                            story.append(Paragraph(self._escape_html(numbered_title), self.styles['SectionTitle']))
                    story.append(Spacer(1, 0.04*inch))
                
                # Automatically append Final Quiz module to the outline
                if outline_modules:
                    last_idx = len(outline_modules) + 1
                    story.append(Paragraph(f"Module {last_idx}: Final Course Assessment", self.styles['ModuleTitle']))
                    story.append(Spacer(1, 0.04*inch))
            
            for idx, module in enumerate(modules, 1):
                module_num = module.get('moduleNumber', idx)
                module_title = module.get('moduleTitle', f'Module {module_num}')
                
                # Module title
                story.append(Paragraph(f"Module {module_num}: {self._escape_html(module_title)}", self.styles['ModuleTitle']))
                
                # Module learning objectives removed - only shown in course overview
                
                # Module image
                if module.get('imagePath'):
                    image_path = Path(module['imagePath'])
                    if image_path.exists():
                        try:
                            # Calculate image dimensions maintaining aspect ratio
                            from PIL import Image as PILImage
                            pil_img = PILImage.open(str(image_path))
                            img_width, img_height = pil_img.size
                            aspect_ratio = img_height / img_width
                            display_width = 5 * inch
                            display_height = display_width * aspect_ratio
                            # Limit height to 4 inches max
                            if display_height > 4 * inch:
                                display_height = 4 * inch
                                display_width = display_height / aspect_ratio
                            
                            img = Image(str(image_path), width=display_width, height=display_height)
                            img.hAlign = 'CENTER'
                            story.append(Spacer(1, 0.04*inch))
                            story.append(img)
                            story.append(Spacer(1, 0.08*inch))
                        except Exception as e:
                            logger.warning(f"Could not add image to PDF: {e}")
                
                # Module content
                content = module.get('content', {})
                if isinstance(content, dict):
                    # Handle structured content
                    sections = content.get('sections', [])
                    for section in sections:
                        section_title = section.get('sectionTitle', '')
                        section_text = section.get('content', '')
                        
                        if section_title:
                            story.append(Paragraph(f"<b>{self._escape_html(section_title)}</b>", self.styles['Heading4']))
                        
                        if section_text:
                            # Split into paragraphs
                            paragraphs = section_text.split('\n\n')
                            for para in paragraphs:
                                if para.strip():
                                    story.append(Paragraph(self._escape_html(para.strip()), self.styles['Content']))
                                    story.append(Spacer(1, 0.04*inch))
                        
                        # Handle concepts within sections
                        if 'concepts' in section:
                            scenario_rendered_this_section = False
                            for concept in section['concepts']:
                                concept_title = concept.get('conceptTitle', '')
                                concept_explanation = concept.get('explanation', '')

                                if concept_title:
                                    story.append(Spacer(1, 0.04*inch))
                                    story.append(Paragraph(f"<b>{self._escape_html(concept_title)}</b>", self.styles['Heading4']))

                                if concept_explanation:
                                    paragraphs = concept_explanation.split('\n\n')
                                    for para in paragraphs:
                                        if para.strip():
                                            story.append(Paragraph(self._escape_html(para.strip()), self.styles['Content']))
                                            story.append(Spacer(1, 0.02*inch))

                                # Handle scenario — max one per section (matches xAPI behaviour)
                                if not scenario_rendered_this_section and concept.get('scenario') and isinstance(concept.get('scenario'), dict):
                                    scenario = concept['scenario']
                                    if scenario.get('whatToDo') or scenario.get('whyItMatters') or scenario.get('howToPrevent'):
                                        story.append(Spacer(1, 0.04*inch))
                                        story.append(Paragraph("<b>Real-World Scenario</b>", self.styles['Heading5']))

                                        if scenario.get('description'):
                                            story.append(Paragraph(self._escape_html(scenario['description']), self.styles['Content']))

                                        if scenario.get('whatToDo'):
                                            story.append(Paragraph(f"<b>What you should do:</b> {self._escape_html(scenario['whatToDo'])}", self.styles['Content']))

                                        if scenario.get('whyItMatters'):
                                            story.append(Paragraph(f"<b>Why does it matter:</b> {self._escape_html(scenario['whyItMatters'])}", self.styles['Content']))

                                        if scenario.get('howToPrevent'):
                                            story.append(Paragraph(f"<b>How to prevent:</b> {self._escape_html(scenario['howToPrevent'])}", self.styles['Content']))

                                        story.append(Spacer(1, 0.04*inch))
                                        scenario_rendered_this_section = True

                if isinstance(content, dict) and content.get('interactiveBlock'):
                    self._render_interactive_block_pdf(story, content['interactiveBlock'])
                
                # Check for Flashcards in content
                if isinstance(content, dict) and content.get('flashcards'):
                    flashcards = content.get('flashcards', [])
                    if flashcards:
                        story.append(Spacer(1, 0.08*inch))
                        story.append(Paragraph("<b>Flashcards</b>", self.styles['Heading4']))
                        for i, card in enumerate(flashcards):
                            front = card.get("front", f"Card {i+1}")
                            back = card.get("back", "")
                            story.append(Paragraph(f"<b>{self._escape_html(front)}</b>", self.styles['Heading5']))
                            if back:
                                paragraphs = back.split('\n\n')
                                for para in paragraphs:
                                    if para.strip():
                                        story.append(Paragraph(self._escape_html(para.strip()), self.styles['Content']))
                                        story.append(Spacer(1, 0.02*inch))
                
                # Handle summary if it exists at the content level
                if isinstance(content, dict) and content.get('summary'):
                    story.append(Spacer(1, 0.08*inch))
                    story.append(Paragraph("<b>Module Summary</b>", self.styles['Heading4']))
                    summary_paragraphs = content['summary'].split('\n\n')
                    for para in summary_paragraphs:
                        if para.strip():
                            story.append(Paragraph(self._escape_html(para.strip()), self.styles['Content']))
                            story.append(Spacer(1, 0.04*inch))
                elif not isinstance(content, dict):
                    # Fallback: only render as plain text when content is NOT a dict
                    # (avoids dumping raw JSON into the PDF when content is a dict without a summary)
                    if content:
                        paragraphs = str(content).split('\n\n')
                        for para in paragraphs:
                            if para.strip():
                                story.append(Paragraph(self._escape_html(para.strip()), self.styles['Content']))
                                story.append(Spacer(1, 0.04*inch))
                
                
                # Knowledge check
                if module.get('knowledgeCheck'):
                    story.append(Spacer(1, 0.08*inch))
                    story.append(Paragraph("<b>Knowledge Check</b>", self.styles['Heading4']))
                    kc = module['knowledgeCheck']
                    if isinstance(kc, dict):
                        question = kc.get('question', '')
                        if question:
                            story.append(Paragraph(f"<b>Q:</b> {self._escape_html(question)}", self.styles['Content']))
                    story.append(Spacer(1, 0.04*inch))
                
                # Page break between modules (except last)
                # 'idx' here is the outer module enumerate var — now safe because inner loops use fi/qi
                if idx < len(modules):
                    story.append(PageBreak())
            
            # Final Quiz — use 'qi' to avoid shadowing outer 'idx'
            quiz = course_data.get('quiz') or {}
            if quiz and quiz.get('questions'):
                story.append(PageBreak())
                story.append(Paragraph("<b>Final Quiz</b>", self.styles['ModuleTitle']))
                story.append(Spacer(1, 0.08*inch))
                
                for qi, question in enumerate(quiz['questions'], 1):
                    story.append(Paragraph(f"<b>Question {qi}</b>", self.styles['Heading4']))
                    story.append(Paragraph(self._escape_html(question.get('question', '')), self.styles['Content']))
                    story.append(Spacer(1, 0.04*inch))
                    
                    # Options
                    options = question.get('options', {})
                    for key, value in options.items():
                        story.append(Paragraph(f"{key}. {self._escape_html(value)}", self.styles['Content']))
                    
                    story.append(Spacer(1, 0.04*inch))
                    story.append(Paragraph(f"<b>Correct Answer:</b> {question.get('correctAnswer', 'N/A')}", self.styles['Content']))
                    
                    # Feedback
                    feedback = question.get('feedback', {})
                    if feedback.get('correct'):
                        story.append(Paragraph(f"<b>Correct Feedback:</b> {self._escape_html(feedback['correct'])}", self.styles['Content']))
                    if feedback.get('incorrect'):
                        story.append(Paragraph(f"<b>Incorrect Feedback:</b> {self._escape_html(feedback['incorrect'])}", self.styles['Content']))
                    
                    story.append(Spacer(1, 0.08*inch))
            
            # Build PDF
            doc.build(story)
            
            log_activity("PDF generation completed", {"pdf_path": str(pdf_path)})
            logger.info(f"✅ PDF generated successfully: {pdf_path}")
            
            return str(pdf_path)
            
        except Exception as e:
            logger.error(f"Failed to generate PDF: {e}", exc_info=True)
            raise
    
    def _escape_html(self, text: str) -> str:
        """Escape HTML special characters for ReportLab Paragraph parser.
        Order matters: & must be first to avoid double-escaping.
        """
        import html
        if not text:
            return ""
        text = str(text)
        # Unescape first to prevent double-escaping (e.g. &amp; -> &amp;amp;)
        text = html.unescape(text)
        text = text.replace('&', '&amp;')   # must be first
        text = text.replace('<', '&lt;')
        text = text.replace('>', '&gt;')
        text = text.replace('"', '&quot;')  # needed inside HTML attribute values
        text = text.replace("'", '&#39;')   # apostrophes can break ReportLab XML parser
        return text


# Singleton instance
pdf_generator_instance = PDFGenerator()


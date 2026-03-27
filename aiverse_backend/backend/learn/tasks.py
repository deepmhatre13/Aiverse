"""
Celery Tasks for Course System.

Tasks:
- Certificate PDF generation
- Receipt PDF generation (removed)
- Course analytics aggregation
- Progress recalculation
"""

import io
import logging
import qrcode
from datetime import date
from celery import shared_task
from django.conf import settings
from django.core.files.base import ContentFile
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def generate_certificate_task(self, enrollment_id):
    """
    Generate certificate PDF for completed course.
    
    Called when:
    - User reaches 100% completion
    
    Generates:
    - Certificate with unique ID
    - QR code for verification
    - PDF document
    """
    
    from .models import Enrollment, Certificate
    
    try:
        enrollment = Enrollment.objects.select_related(
            'user', 'course'
        ).get(id=enrollment_id)
        
        # Verify completion
        if enrollment.completion_percentage < 100:
            logger.warning(
                f"Certificate generation skipped - incomplete: "
                f"{enrollment.completion_percentage}%"
            )
            return
        
        # Check if already issued
        if enrollment.certificate_issued:
            logger.info(f"Certificate already issued for enrollment: {enrollment_id}")
            return
        
        # Check if certificate exists
        existing = Certificate.objects.filter(enrollment=enrollment).first()
        if existing:
            logger.info(f"Certificate already exists: {existing.certificate_id}")
            return
        
        user = enrollment.user
        course = enrollment.course
        
        # Create certificate record
        certificate = Certificate.objects.create(
            user=user,
            course=course,
            enrollment=enrollment,
            user_name=user.get_full_name() or user.username,
            course_title=course.title,
            course_level=course.level,
            completion_date=date.today(),
        )
        
        # Build verification URL
        base_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:5173')
        verification_url = f"{base_url}/certificates/verify/{certificate.certificate_id}"
        certificate.verification_url = verification_url
        
        # Generate QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=4,
        )
        qr.add_data(verification_url)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white")
        
        # Save QR code
        qr_buffer = io.BytesIO()
        qr_img.save(qr_buffer, format='PNG')
        qr_buffer.seek(0)
        
        qr_filename = f"qr_{certificate.certificate_id}.png"
        certificate.qr_code_url = f"{settings.MEDIA_URL}certificates/qr/{qr_filename}"
        
        # Generate PDF
        pdf_content = _generate_certificate_pdf(certificate, qr_buffer.getvalue())
        
        if pdf_content:
            pdf_filename = f"certificate_{certificate.certificate_id}.pdf"
            certificate.pdf_file.save(pdf_filename, ContentFile(pdf_content))
            
            # Build PDF URL
            if settings.DEBUG:
                pdf_url = f"http://127.0.0.1:8000{settings.MEDIA_URL}{certificate.pdf_file.name}"
            else:
                pdf_url = f"{getattr(settings, 'SITE_URL', '')}{settings.MEDIA_URL}{certificate.pdf_file.name}"
            certificate.pdf_url = pdf_url
        
        certificate.save()
        
        # Update enrollment
        enrollment.certificate_issued = True
        enrollment.certificate_issued_at = timezone.now()
        enrollment.save(update_fields=['certificate_issued', 'certificate_issued_at'])
        
        logger.info(
            f"Certificate generated: {certificate.certificate_id} for "
            f"{user.email} - {course.title}"
        )
        
        return str(certificate.id)
        
    except Enrollment.DoesNotExist:
        logger.error(f"Enrollment not found: {enrollment_id}")
        return None
    except Exception as e:
        logger.error(f"Certificate generation failed: {e}")
        self.retry(exc=e)


def _generate_certificate_pdf(certificate, qr_code_bytes):
    """
    Generate PDF certificate using ReportLab.
    
    Design:
    - Professional layout
    - Course and user details
    - Completion date
    - QR code for verification
    - Unique certificate ID
    """
    
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
        from reportlab.lib.enums import TA_CENTER
        
        buffer = io.BytesIO()
        
        # Landscape A4
        doc = SimpleDocTemplate(
            buffer,
            pagesize=landscape(A4),
            rightMargin=0.5*inch,
            leftMargin=0.5*inch,
            topMargin=0.5*inch,
            bottomMargin=0.5*inch,
        )
        
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CertTitle',
            parent=styles['Heading1'],
            fontSize=36,
            spaceAfter=20,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#1a1a2e'),
        )
        
        subtitle_style = ParagraphStyle(
            'CertSubtitle',
            parent=styles['Normal'],
            fontSize=14,
            spaceAfter=10,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#4a4a4a'),
        )
        
        name_style = ParagraphStyle(
            'CertName',
            parent=styles['Heading2'],
            fontSize=28,
            spaceBefore=20,
            spaceAfter=10,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#0f3460'),
        )
        
        course_style = ParagraphStyle(
            'CertCourse',
            parent=styles['Normal'],
            fontSize=20,
            spaceBefore=10,
            spaceAfter=20,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#16213e'),
        )
        
        detail_style = ParagraphStyle(
            'CertDetail',
            parent=styles['Normal'],
            fontSize=12,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#666666'),
        )
        
        elements = []
        
        # Title
        elements.append(Spacer(1, 0.5*inch))
        elements.append(Paragraph("CERTIFICATE OF COMPLETION", title_style))
        elements.append(Spacer(1, 0.25*inch))
        
        # Subtitle
        elements.append(Paragraph("This is to certify that", subtitle_style))
        elements.append(Spacer(1, 0.25*inch))
        
        # User name
        elements.append(Paragraph(certificate.user_name, name_style))
        elements.append(Spacer(1, 0.25*inch))
        
        # Course completion text
        elements.append(Paragraph("has successfully completed the course", subtitle_style))
        elements.append(Spacer(1, 0.1*inch))
        
        # Course title
        elements.append(Paragraph(f'"{certificate.course_title}"', course_style))
        elements.append(Spacer(1, 0.25*inch))
        
        # Level badge
        level_text = f"Level: {certificate.course_level.title()}"
        elements.append(Paragraph(level_text, detail_style))
        elements.append(Spacer(1, 0.25*inch))
        
        # Date
        date_text = f"Completed on: {certificate.completion_date.strftime('%B %d, %Y')}"
        elements.append(Paragraph(date_text, detail_style))
        elements.append(Spacer(1, 0.5*inch))
        
        # QR Code
        if qr_code_bytes:
            qr_image = Image(io.BytesIO(qr_code_bytes), width=1*inch, height=1*inch)
            elements.append(qr_image)
            elements.append(Spacer(1, 0.1*inch))
        
        # Certificate ID
        cert_id_text = f"Certificate ID: {certificate.certificate_id}"
        elements.append(Paragraph(cert_id_text, detail_style))
        
        # Verification text
        verify_text = "Scan QR code or visit the verification link to verify this certificate"
        elements.append(Paragraph(verify_text, detail_style))
        
        # Build PDF
        doc.build(elements)
        
        return buffer.getvalue()
        
    except ImportError:
        logger.error("ReportLab not installed - cannot generate certificate PDF")
        return None
    except Exception as e:
        logger.error(f"PDF generation failed: {e}")
        return None


@shared_task
def aggregate_course_analytics():
    """
    Daily task to aggregate course analytics.
    
    Called by Celery Beat scheduler.
    """
    
    from django.db.models import Count, Sum, Avg, Q
    from .models import Course, CourseAnalytics, Enrollment, LessonProgress, Payment
    
    today = date.today()
    
    for course in Course.objects.filter(is_published=True):
        # Get today's metrics
        enrollments_today = Enrollment.objects.filter(
            course=course,
            enrolled_at__date=today
        ).count()
        
        completions_today = Enrollment.objects.filter(
            course=course,
            completion_percentage=100,
            certificate_issued_at__date=today
        ).count()
        
        revenue_today = Payment.objects.filter(
            enrollment__course=course,
            status='succeeded',
            succeeded_at__date=today
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        watch_stats = LessonProgress.objects.filter(
            lesson__course=course,
            last_watched_at__date=today
        ).aggregate(
            total_watch_time=Sum('watch_time_seconds'),
            lesson_completions=Count('id', filter=Q(is_completed=True))
        )
        
        avg_watch_time = (watch_stats['total_watch_time'] or 0) / 60  # Convert to minutes
        
        # Create or update analytics record
        CourseAnalytics.objects.update_or_create(
            course=course,
            date=today,
            defaults={
                'enrollments': enrollments_today,
                'completions': completions_today,
                'revenue': revenue_today,
                'average_watch_time_minutes': avg_watch_time,
                'lesson_completions': watch_stats['lesson_completions'] or 0,
            }
        )
    
    logger.info(f"Course analytics aggregated for {today}")


@shared_task
def recalculate_all_course_stats():
    """
    Recalculate all course statistics.
    
    Run occasionally to ensure consistency.
    """
    
    from .models import Course
    
    for course in Course.objects.all():
        try:
            course.update_stats()
            logger.info(f"Stats recalculated for course: {course.title}")
        except Exception as e:
            logger.error(f"Failed to recalculate stats for {course.title}: {e}")


# -----------------------------------------------------------------
# MCQ Generation Tasks (Gemini AI)
# -----------------------------------------------------------------

@shared_task(bind=True, max_retries=3, default_retry_delay=120)
def generate_quiz_mcqs_task(self, lesson_id, transcript=None, num_questions=5):
    """
    Generate MCQs for a lesson using Gemini AI.
    
    Called when:
    - New lesson is created
    - Admin triggers regeneration
    - Lesson content is updated
    
    Args:
        lesson_id: ID of the lesson
        transcript: Optional lesson transcript/content for generation
        num_questions: Number of MCQs to generate (default: 5)
    
    Steps:
    1. Load lesson and course context
    2. Build generation prompt
    3. Call Gemini API
    4. Parse JSON response
    5. Create Quiz and MCQ records
    """
    
    from django.conf import settings
    from .models import Lesson, Quiz, MCQ
    import google.generativeai as genai
    import json
    import re
    
    try:
        lesson = Lesson.objects.select_related('course').get(id=lesson_id)
    except Lesson.DoesNotExist:
        logger.error(f"Lesson not found: {lesson_id}")
        return None
    
    # Check if quiz already exists
    existing_quiz = Quiz.objects.filter(lesson=lesson).first()
    if existing_quiz and existing_quiz.questions.count() >= num_questions:
        logger.info(f"Quiz already exists for lesson: {lesson.title}")
        return str(existing_quiz.id)
    
    # Build context for generation
    course = lesson.course
    lesson_context = transcript or lesson.description or lesson.notes or ""
    
    if not lesson_context:
        # Fallback: use lesson title and course context
        lesson_context = f"""
        Course: {course.title}
        Level: {course.level}
        Lesson: {lesson.title}
        Description: {lesson.description}
        """
    
    # Build Gemini prompt
    prompt = f"""You are an expert ML educator creating quiz questions.

CONTEXT:
Course: {course.title}
Course Level: {course.level}
Lesson Title: {lesson.title}
Lesson Content: {lesson_context[:3000]}

TASK:
Generate exactly {num_questions} multiple choice questions to test understanding of this lesson.

REQUIREMENTS:
1. Questions should test core concepts, not trivia
2. Each question must have exactly 4 options (A, B, C, D)
3. Only one option should be correct
4. Include a brief explanation for the correct answer
5. Mix difficulty levels (easy, medium, hard)
6. Focus on practical understanding and application

OUTPUT FORMAT (strict JSON):
{{
    "questions": [
        {{
            "question": "Your question text here?",
            "option_a": "First option",
            "option_b": "Second option",
            "option_c": "Third option",
            "option_d": "Fourth option",
            "correct_option": "A|B|C|D",
            "explanation": "Why this answer is correct",
            "difficulty": "easy|medium|hard",
            "topic": "specific topic being tested"
        }}
    ]
}}

Generate {num_questions} questions following this exact JSON format.
"""
    
    try:
        # Configure Gemini
        api_key = getattr(settings, 'GEMINI_API_KEY', None)
        if not api_key:
            logger.error("GEMINI_API_KEY not configured")
            return None
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Generate MCQs
        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                temperature=0.7,
                max_output_tokens=4096,
            )
        )
        
        # Parse response
        response_text = response.text.strip()
        
        # Remove markdown code blocks if present
        if response_text.startswith('```'):
            response_text = re.sub(r'^```(?:json)?\s*', '', response_text)
            response_text = re.sub(r'\s*```$', '', response_text)
        
        # Parse JSON
        try:
            mcq_data = json.loads(response_text)
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error in MCQ generation: {e}")
            logger.error(f"Raw response: {response_text[:500]}")
            self.retry(exc=e)
            return None
        
        questions = mcq_data.get('questions', [])
        if not questions:
            logger.error("No questions in Gemini response")
            return None
        
        # Create or update Quiz
        quiz, created = Quiz.objects.update_or_create(
            lesson=lesson,
            defaults={
                'title': f"Quiz: {lesson.title}",
                'description': f"Test your understanding of {lesson.title}",
                'total_questions': len(questions),
                'generated_by': 'gemini',
                'generation_prompt': prompt[:2000],
                'source_transcript': lesson_context[:2000],
            }
        )
        
        # Clear existing MCQs if regenerating
        if not created:
            quiz.questions.all().delete()
        
        # Create MCQ records
        for idx, q in enumerate(questions):
            MCQ.objects.create(
                quiz=quiz,
                question=q.get('question', ''),
                order=idx + 1,
                option_a=q.get('option_a', ''),
                option_b=q.get('option_b', ''),
                option_c=q.get('option_c', ''),
                option_d=q.get('option_d', ''),
                correct_option=q.get('correct_option', 'A').upper(),
                explanation=q.get('explanation', ''),
                difficulty=q.get('difficulty', 'medium'),
                topic=q.get('topic', ''),
            )
        
        logger.info(
            f"Generated {len(questions)} MCQs for lesson: {lesson.title} "
            f"(Quiz ID: {quiz.id})"
        )
        
        return str(quiz.id)
        
    except Exception as e:
        logger.error(f"MCQ generation failed for lesson {lesson_id}: {e}")
        self.retry(exc=e)
        return None


@shared_task
def generate_all_missing_quizzes():
    """
    Generate quizzes for all lessons that don't have one.
    
    Called via management command or admin action.
    """
    
    from .models import Lesson, Quiz
    
    lessons_without_quiz = Lesson.objects.filter(
        quiz__isnull=True
    ).select_related('course')
    
    count = 0
    for lesson in lessons_without_quiz:
        # Queue MCQ generation
        generate_quiz_mcqs_task.delay(lesson.id)
        count += 1
        logger.info(f"Queued MCQ generation for: {lesson.title}")
    
    logger.info(f"Queued MCQ generation for {count} lessons")
    return count


@shared_task
def regenerate_quiz_for_lesson(lesson_id, num_questions=5):
    """
    Regenerate quiz MCQs for a specific lesson.
    
    Deletes existing MCQs and generates new ones.
    """
    
    from .models import Lesson, Quiz
    
    try:
        lesson = Lesson.objects.get(id=lesson_id)
    except Lesson.DoesNotExist:
        logger.error(f"Lesson not found: {lesson_id}")
        return None
    
    # Delete existing quiz
    Quiz.objects.filter(lesson=lesson).delete()
    
    # Generate new quiz
    return generate_quiz_mcqs_task.delay(lesson_id, num_questions=num_questions)


@shared_task(bind=True, max_retries=3, default_retry_delay=120)
def generate_final_quiz_task(self, course_id, num_questions=10):
    """
    Generate final course quiz from all lesson content.
    
    Called when:
    - User completes all lessons
    - Admin triggers generation
    
    Args:
        course_id: ID of the course
        num_questions: Number of MCQs to generate (default: 10)
    """
    
    from django.conf import settings
    from .models import Course, Lesson, CourseQuiz, CourseMCQ
    import google.generativeai as genai
    import json
    import re
    
    try:
        course = Course.objects.prefetch_related('lessons').get(id=course_id)
    except Course.DoesNotExist:
        logger.error(f"Course not found: {course_id}")
        return None
    
    # Check if final quiz already exists
    existing_quiz = CourseQuiz.objects.filter(course=course).first()
    if existing_quiz and existing_quiz.questions.count() >= num_questions:
        logger.info(f"Final quiz already exists for course: {course.title}")
        return str(existing_quiz.id)
    
    # Build context from all lessons
    lessons = course.lessons.all().order_by('order')
    lesson_context = []
    for lesson in lessons:
        lesson_context.append(f"Lesson {lesson.order}: {lesson.title}")
        if lesson.description:
            lesson_context.append(f"  Description: {lesson.description[:500]}")
        if lesson.notes:
            lesson_context.append(f"  Notes: {lesson.notes[:500]}")
    
    context_text = "\\n".join(lesson_context)
    
    # Build Gemini prompt
    prompt = f"""You are an expert ML educator creating a final assessment quiz.

COURSE INFORMATION:
Course: {course.title}
Level: {course.level}
Description: {course.description[:1000]}

LESSON CONTENT:
{context_text[:4000]}

TASK:
Generate exactly {num_questions} comprehensive multiple choice questions for the final course assessment.

REQUIREMENTS:
1. Questions should span all lessons covered in the course
2. Mix difficulty levels (easy, medium, hard)
3. Focus on core concepts and practical applications
4. Each question must have exactly 4 options (A, B, C, D)
5. Only one option should be correct
6. Include a brief explanation for the correct answer
7. This is a summative assessment - questions should test mastery

OUTPUT FORMAT (strict JSON):
{{
    "questions": [
        {{
            "question": "Your question text here?",
            "option_a": "First option",
            "option_b": "Second option",
            "option_c": "Third option",
            "option_d": "Fourth option",
            "correct_option": "A|B|C|D",
            "explanation": "Why this answer is correct",
            "difficulty": "easy|medium|hard",
            "topic": "specific topic being tested",
            "lesson_reference": "Lesson number this relates to (optional)"
        }}
    ]
}}

Generate {num_questions} questions following this exact JSON format.
"""
    
    try:
        # Configure Gemini
        api_key = getattr(settings, 'GEMINI_API_KEY', None)
        if not api_key:
            logger.error("GEMINI_API_KEY not configured")
            return None
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Generate MCQs
        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                temperature=0.7,
                max_output_tokens=6000,
            )
        )
        
        # Parse response
        response_text = response.text.strip()
        
        # Remove markdown code blocks if present
        if response_text.startswith('```'):
            response_text = re.sub(r'^```(?:json)?\\s*', '', response_text)
            response_text = re.sub(r'\\s*```$', '', response_text)
        
        # Parse JSON
        try:
            mcq_data = json.loads(response_text)
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error in final quiz generation: {e}")
            logger.error(f"Raw response: {response_text[:500]}")
            self.retry(exc=e)
            return None
        
        questions = mcq_data.get('questions', [])
        if not questions:
            logger.error("No questions in Gemini response for final quiz")
            return None
        
        # Create or update CourseQuiz
        quiz, created = CourseQuiz.objects.update_or_create(
            course=course,
            defaults={
                'title': f"Final Assessment: {course.title}",
                'description': f"Comprehensive assessment covering all {course.total_lessons} lessons in {course.title}",
                'total_questions': len(questions),
                'passing_score': 75,
                'generated_by': 'gemini',
                'generation_prompt': prompt[:2000],
            }
        )
        
        # Clear existing MCQs if regenerating
        if not created:
            quiz.questions.all().delete()
        
        # Create CourseMCQ records
        for idx, q in enumerate(questions):
            # Try to link to source lesson
            source_lesson = None
            lesson_ref = q.get('lesson_reference', '')
            if lesson_ref:
                try:
                    lesson_num = int(re.search(r'\\d+', lesson_ref).group())
                    source_lesson = lessons.filter(order=lesson_num).first()
                except (AttributeError, ValueError):
                    pass
            
            CourseMCQ.objects.create(
                course_quiz=quiz,
                question=q.get('question', ''),
                order=idx + 1,
                option_a=q.get('option_a', ''),
                option_b=q.get('option_b', ''),
                option_c=q.get('option_c', ''),
                option_d=q.get('option_d', ''),
                correct_option=q.get('correct_option', 'A').upper(),
                explanation=q.get('explanation', ''),
                difficulty=q.get('difficulty', 'medium'),
                topic=q.get('topic', ''),
                source_lesson=source_lesson,
            )
        
        logger.info(
            f"Generated {len(questions)} MCQs for final quiz: {course.title} "
            f"(Quiz ID: {quiz.id})"
        )
        
        return str(quiz.id)
        
    except Exception as e:
        logger.error(f"Final quiz generation failed for course {course_id}: {e}")
        self.retry(exc=e)
        return None


@shared_task
def generate_all_final_quizzes():
    """
    Generate final quizzes for all courses that don't have one.
    """
    
    from .models import Course, CourseQuiz
    
    courses_without_quiz = Course.objects.filter(
        final_quiz__isnull=True,
        is_published=True
    )
    
    count = 0
    for course in courses_without_quiz:
        generate_final_quiz_task.delay(course.id)
        count += 1
        logger.info(f"Queued final quiz generation for: {course.title}")
    
    logger.info(f"Queued final quiz generation for {count} courses")
    return count


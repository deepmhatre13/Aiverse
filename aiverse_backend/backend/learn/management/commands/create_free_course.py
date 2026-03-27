"""
Management command to create the free ML Foundations course.

Usage:
    python manage.py create_free_course
"""

from django.core.management.base import BaseCommand
from learn.models import Course, Lesson
from learn.youtube_utils import normalize_youtube_input


class Command(BaseCommand):
    help = 'Create the free Machine Learning Foundations course with YouTube lessons'

    def handle(self, *args, **options):
        self.stdout.write('Creating free ML Foundations course...')
        
        # Create or get course
        course, created = Course.objects.get_or_create(
            slug='machine-learning-foundations-free',
            defaults={
                'title': 'Machine Learning Foundations (Free)',
                'description': '''Master the fundamentals of machine learning with this comprehensive free course. 
                Learn core concepts, understand the math behind ML algorithms, and build intuition for real-world applications.
                
                This course covers:
                • What machine learning is and why it matters
                • Supervised vs unsupervised learning
                • The bias-variance tradeoff
                • Overfitting and underfitting
                • Real-world ML examples and applications
                
                Perfect for beginners who want to understand ML from first principles.''',
                'thumbnail': 'https://images.unsplash.com/photo-1555949963-aa79dcee981c?w=800',
                'cover_image': 'https://images.unsplash.com/photo-1555949963-aa79dcee981c?w=800',
                'difficulty': 'beginner',
                'duration_hours': 3,
                'is_paid': False,
                'is_free': True,
                'price': None,
                'is_published': True,
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'✓ Created course: {course.title}'))
        else:
            self.stdout.write(f'Course already exists: {course.title}')
            # Update existing course
            course.is_paid = False
            course.is_free = True
            course.price = None
            course.is_published = True
            course.save()
            self.stdout.write(self.style.SUCCESS('✓ Updated course settings'))
        
        # Define lessons with YouTube video IDs
        lessons_data = [
            {
                'title': 'What is Machine Learning?',
                'slug': 'what-is-machine-learning',
                'description': 'Introduction to machine learning, its history, and why it\'s transforming industries today.',
                'youtube_id': 'aircAruvnKk',  # 3Blue1Brown Neural Networks series
                'duration_minutes': 15,
                'order': 1,
                'is_preview': True,
            },
            {
                'title': 'Supervised vs Unsupervised Learning',
                'slug': 'supervised-vs-unsupervised-learning',
                'description': 'Learn the fundamental distinction between supervised and unsupervised learning, with real-world examples.',
                'youtube_id': 'nE8mZC6yPmk',  # StatQuest
                'duration_minutes': 12,
                'order': 2,
                'is_preview': False,
            },
            {
                'title': 'Bias–Variance Tradeoff',
                'slug': 'bias-variance-tradeoff',
                'description': 'Understand one of the most important concepts in machine learning: the bias-variance tradeoff.',
                'youtube_id': 'EuBBz3bI-aA',  # StatQuest
                'duration_minutes': 18,
                'order': 3,
                'is_preview': False,
            },
            {
                'title': 'Overfitting & Underfitting',
                'slug': 'overfitting-underfitting',
                'description': 'Learn how to recognize and prevent overfitting and underfitting in your ML models.',
                'youtube_id': 'Anq4Xg51rVg',  # StatQuest
                'duration_minutes': 14,
                'order': 4,
                'is_preview': False,
            },
            {
                'title': 'Real-world ML Examples',
                'slug': 'real-world-ml-examples',
                'description': 'Explore how machine learning is used in practice: recommendation systems, image recognition, and more.',
                'youtube_id': 'aircAruvnKk',  # Using same video as placeholder - replace with actual ML examples video
                'duration_minutes': 20,
                'order': 5,
                'is_preview': False,
            },
        ]
        
        created_count = 0
        updated_count = 0
        
        for lesson_data in lessons_data:
            youtube_id = lesson_data.pop('youtube_id')
            
            lesson, created = Lesson.objects.get_or_create(
                course=course,
                slug=lesson_data['slug'],
                defaults={
                    **lesson_data,
                    'video_type': 'YOUTUBE',
                    'youtube_id': youtube_id,
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'  ✓ Created lesson: {lesson.title}'))
            else:
                # Update existing lesson
                lesson.video_type = 'YOUTUBE'
                lesson.youtube_id = youtube_id
                for key, value in lesson_data.items():
                    setattr(lesson, key, value)
                lesson.save()
                updated_count += 1
                self.stdout.write(f'  Updated lesson: {lesson.title}')
        
        self.stdout.write(self.style.SUCCESS(
            f'\n✓ Course setup complete! Created {created_count} lessons, updated {updated_count} lessons.'
        ))
        self.stdout.write(f'Course URL: /learn/courses/{course.slug}/')

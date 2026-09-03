"""
Load 41 courses with modules and lessons.

Usage:
    python manage.py load_courses
    python manage.py load_courses --clear
"""

from urllib.parse import quote_plus

from django.core.management.base import BaseCommand
from django.utils.text import slugify

from learn.models import Course, Lesson, Module
from learn.data.courses_catalog import MODULES, COURSES


class Command(BaseCommand):
    help = 'Load 41 structured courses with modules and lessons'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Delete catalog courses before loading (preserves non-catalog courses)',
        )

    def handle(self, *args, **options):
        module_map = {}
        for mod_data in MODULES:
            mod, _ = Module.objects.update_or_create(
                slug=mod_data['slug'],
                defaults={
                    'name': mod_data['name'],
                    'description': mod_data['description'],
                    'order': mod_data['order'],
                    'icon': mod_data.get('icon', ''),
                },
            )
            module_map[mod_data['slug']] = mod
        self.stdout.write(f'Modules ready: {len(module_map)}')

        catalog_slugs = [c['slug'] for c in COURSES]
        if options['clear']:
            deleted, _ = Course.objects.filter(slug__in=catalog_slugs).delete()
            self.stdout.write(self.style.WARNING(f'Deleted {deleted} catalog course records'))

        courses_created = 0
        lessons_created = 0

        for order, course_data in enumerate(COURSES, start=1):
            module = module_map.get(course_data.get('module_slug'))
            price = course_data.get('price', 0)
            is_free = price == 0

            course, was_created = Course.objects.update_or_create(
                slug=course_data['slug'],
                defaults={
                    'title': course_data['title'],
                    'description': course_data.get('description', course_data['title']),
                    'short_description': (course_data.get('description') or course_data['title'])[:300],
                    'module': module,
                    'concept_tag': course_data.get('concept_tag', ''),
                    'level': course_data.get('difficulty', 'beginner'),
                    'order': order,
                    'is_free': is_free,
                    'is_paid': not is_free,
                    'price': price if not is_free else None,
                    'is_published': True,
                    'instructor_name': 'AIverse ML Team',
                    'tags': [t for t in [course_data.get('concept_tag', ''), module.slug if module else ''] if t],
                },
            )
            if was_created:
                courses_created += 1

            course.lessons.all().delete()

            lesson_objs = []
            for lesson_data in course_data.get('lessons', []):
                lesson_slug = slugify(lesson_data['title'])[:200]
                youtube_query = lesson_data.get('youtube_query', '')
                youtube_url = lesson_data.get('youtube_url', '')
                if not youtube_url and youtube_query:
                    youtube_url = (
                        f'https://www.youtube.com/results?search_query={quote_plus(youtube_query)}'
                    )

                lesson_objs.append(Lesson(
                    course=course,
                    slug=lesson_slug,
                    title=lesson_data['title'],
                    order=lesson_data.get('order', 0),
                    duration_minutes=lesson_data.get('duration_minutes', 15),
                    concept_tag=lesson_data.get('concept_tag', course_data.get('concept_tag', '')),
                    learning_objectives=lesson_data.get(
                        'learning_objectives', lesson_data.get('objectives', [])
                    ),
                    youtube_url=youtube_url,
                    video_type='youtube',
                    is_preview=lesson_data.get('order', 1) == 1,
                    is_active=True,
                    module=module,
                ))

            if lesson_objs:
                Lesson.objects.bulk_create(lesson_objs)
                lessons_created += len(lesson_objs)

            course.total_lessons = len(lesson_objs)
            course.total_duration_minutes = sum(l.duration_minutes for l in lesson_objs)
            course.estimated_duration_hours = round(course.total_duration_minutes / 60, 1)
            course.save(update_fields=[
                'total_lessons', 'total_duration_minutes', 'estimated_duration_hours',
            ])

            if order % 10 == 0:
                self.stdout.write(f'  ... {order}/{len(COURSES)} courses')

        total_courses = Course.objects.filter(is_published=True).count()
        total_lessons = Lesson.objects.filter(is_active=True).count()
        self.stdout.write(
            self.style.SUCCESS(
                f'Loaded courses: {courses_created} new courses, {lessons_created} new lessons. '
                f'Total published: {total_courses} courses, {total_lessons} lessons'
            )
        )

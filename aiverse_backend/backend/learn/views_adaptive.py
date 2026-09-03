"""Adaptive learning API views: problems, modules, playground, personalisation."""

from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from learner.models import ConceptMastery, LearnerProfile
from learn.models import CodingProblem, Course, Module, Lesson, Enrollment, LessonProgress
from playground.models import Experiment


class ModuleListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        modules = Module.objects.all().order_by('order')
        data = []
        for mod in modules:
            courses = mod.courses.filter(is_published=True).order_by('order')
            data.append({
                'id': mod.id,
                'name': mod.name,
                'slug': mod.slug,
                'description': mod.description,
                'order': mod.order,
                'icon': mod.icon,
                'course_count': courses.count(),
                'courses': [
                    {
                        'slug': c.slug,
                        'title': c.title,
                        'concept_tag': c.concept_tag,
                        'level': c.level,
                        'total_lessons': c.total_lessons,
                        'is_free': c.is_free,
                        'price': str(c.price) if c.price else '0',
                    }
                    for c in courses
                ],
            })
        return Response(data)


class ProblemListView(APIView):
    """List all coding problems from DB with optional filters."""

    permission_classes = [AllowAny]

    def get(self, request):
        qs = CodingProblem.objects.filter(is_active=True).order_by('order', 'difficulty')
        difficulty = request.query_params.get('difficulty')
        category = request.query_params.get('category')
        concept = request.query_params.get('concept_tag')
        if difficulty:
            qs = qs.filter(difficulty=difficulty)
        if category:
            qs = qs.filter(category__iexact=category)
        if concept:
            qs = qs.filter(concept_tag=concept)

        data = [
            {
                'id': p.id,
                'slug': p.slug,
                'title': p.title,
                'difficulty': p.difficulty,
                'category': p.category.lower().replace(' ', '_'),
                'concept_tag': p.concept_tag,
                'metric': p.metric,
                'points': p.points,
                'description': p.description[:300] if p.description else '',
                'tags': p.tags,
                'solve_count': p.solve_count,
            }
            for p in qs
        ]
        return Response(data)


class ProblemDetailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, slug):
        problem = get_object_or_404(CodingProblem, slug=slug, is_active=True)
        return Response({
            'slug': problem.slug,
            'title': problem.title,
            'difficulty': problem.difficulty,
            'category': problem.category,
            'concept_tag': problem.concept_tag,
            'metric': problem.metric,
            'points': problem.points,
            'description': problem.description,
            'starter_code': problem.starter_code,
            'hints': problem.hints,
            'tags': problem.tags,
            'constraints': problem.constraints,
            'test_cases': problem.test_cases,
            'expected_output_format': problem.expected_output_format,
        })


class PersonalReadinessView(APIView):
    """Returns personal readiness badge for a problem for the logged-in user."""

    permission_classes = [IsAuthenticated]

    def get(self, request, slug):
        concept_tag = 'classification'
        difficulty = 'medium'

        try:
            problem = CodingProblem.objects.get(slug=slug, is_active=True)
            concept_tag = problem.concept_tag
            difficulty = problem.difficulty
        except CodingProblem.DoesNotExist:
            try:
                from ml.registry import get_problem_definition
                pdef = get_problem_definition(slug)
                difficulty = pdef.difficulty
                concept_tag = getattr(pdef, 'concept_tag', None) or _slug_to_concept(slug)
            except ValueError:
                return Response({'error': 'Problem not found'}, status=status.HTTP_404_NOT_FOUND)

        try:
            mastery = ConceptMastery.objects.get(
                user=request.user,
                concept_tag=concept_tag,
            )
            score = mastery.mastery_score
        except ConceptMastery.DoesNotExist:
            score = 0.0

        difficulty_threshold = {
            'easy': 0.0,
            'medium': 0.35,
            'hard': 0.55,
            'expert': 0.75,
        }
        threshold = difficulty_threshold.get(difficulty, 0.0)

        if score >= threshold + 0.25:
            readiness = 'ready'
            label = 'Ready for you'
        elif score >= threshold:
            readiness = 'stretch'
            label = 'Stretch goal'
        else:
            readiness = 'prerequisite'
            label = 'Build prerequisites first'

        return Response({
            'readiness': readiness,
            'label': label,
            'concept_mastery': round(score * 100),
            'concept_tag': concept_tag,
            'reason': (
                f"Your mastery of {concept_tag.replace('_', ' ')} "
                f"is {round(score * 100)}%"
            ),
        })


def _slug_to_concept(slug):
    """Map problem slug to concept tag when not in DB."""
    mapping = {
        'credit-risk-modeling': 'classification',
        'customer-churn': 'ensemble_learning',
        'loan-default': 'feature_engineering',
        'house-price-regression': 'regression',
        'timeseries-forecasting': 'feature_engineering',
        'sentiment-analysis': 'transformers',
        'multiclass-classification': 'classification',
        'feature-selection': 'feature_engineering',
        'recommender-system': 'collaborative_filtering',
        'pipeline-optimization': 'mlops',
    }
    return mapping.get(slug, 'classification')


class GuidedExperimentView(APIView):
    """Returns a personalised guided experiment based on user's weak concepts."""

    permission_classes = [IsAuthenticated]

    EXPERIMENTS = {
        'overfitting': {
            'title': 'See Overfitting Happen Live',
            'description': 'Watch your model memorise training data while failing on test data',
            'steps': [
                {
                    'config': {
                        'algorithm': 'DecisionTreeClassifier',
                        'hyperparameters': {'max_depth': None},
                        'dataset': 'iris',
                    },
                    'instruction': 'Run this: notice train accuracy 100%, test ~72%',
                },
                {
                    'config': {
                        'algorithm': 'DecisionTreeClassifier',
                        'hyperparameters': {'max_depth': 3},
                        'dataset': 'iris',
                    },
                    'instruction': 'Now add max_depth=3: notice the gap closes significantly',
                },
                {
                    'config': {
                        'algorithm': 'RandomForestClassifier',
                        'hyperparameters': {'n_estimators': 100},
                        'dataset': 'iris',
                    },
                    'instruction': 'Finally, try Random Forest: bagging reduces overfitting further',
                },
            ],
            'mastery_boost_concept': 'regularization',
        },
        'feature_engineering': {
            'title': 'Feature Scaling: Before vs After',
            'description': 'See how unscaled features break KNN and gradient descent',
            'steps': [
                {
                    'config': {
                        'algorithm': 'KNeighborsClassifier',
                        'preprocessing': {'scaler': 'None'},
                        'dataset': 'wine',
                    },
                    'instruction': 'Without scaling: KNN struggles because features are on different scales',
                },
                {
                    'config': {
                        'algorithm': 'KNeighborsClassifier',
                        'preprocessing': {'scaler': 'StandardScaler'},
                        'dataset': 'wine',
                    },
                    'instruction': 'With StandardScaler: same model, dramatically better result',
                },
            ],
            'mastery_boost_concept': 'feature_engineering',
        },
    }

    WEAKNESS_MAP = {
        'regularization': 'overfitting',
        'feature_scaling': 'feature_engineering',
        'feature_engineering': 'feature_engineering',
    }

    def get(self, request):
        profile = LearnerProfile.objects.filter(user=request.user).first()
        weak = profile.weak_concepts if profile else []

        for concept in weak:
            key = self.WEAKNESS_MAP.get(concept, concept)
            if key in self.EXPERIMENTS:
                return Response(self.EXPERIMENTS[key])

        return Response(self.EXPERIMENTS['overfitting'])


class PlaygroundHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        experiments = Experiment.objects.filter(user=request.user).order_by('-created_at')[:50]
        data = [
            {
                'id': exp.id,
                'dataset_name': exp.dataset_name or (exp.dataset.name if exp.dataset_id else ''),
                'algorithm': exp.algorithm or exp.model_type or '',
                'hyperparameters': exp.hyperparameters,
                'preprocessing_config': exp.preprocessing_config,
                'results': exp.results or exp.metrics,
                'concept_tag': exp.concept_tag,
                'notes': exp.notes,
                'tags': exp.tags,
                'run_time_seconds': exp.run_time_seconds,
                'status': exp.status,
                'created_at': exp.created_at.isoformat(),
            }
            for exp in experiments
        ]
        return Response(data)

    def delete(self, request):
        exp_id = request.query_params.get('id')
        if exp_id:
            Experiment.objects.filter(user=request.user, pk=exp_id).delete()
            return Response({'deleted': exp_id})
        return Response({'error': 'id required'}, status=status.HTTP_400_BAD_REQUEST)


class PlaygroundRunView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Save experiment configuration and results."""
        data = request.data
        from playground.models import Dataset

        dataset_name = data.get('dataset', 'iris')
        dataset, _ = Dataset.objects.get_or_create(
            name=dataset_name,
            defaults={'task_type': 'classification', 'n_samples': 100, 'n_features': 4},
        )

        exp = Experiment.objects.create(
            user=request.user,
            dataset=dataset,
            dataset_name=dataset_name,
            algorithm=data.get('algorithm', ''),
            model_type=data.get('algorithm', ''),
            hyperparameters=data.get('hyperparameters', {}),
            preprocessing_config=data.get('preprocessing', {}),
            results=data.get('results', {}),
            metrics=data.get('results', {}),
            concept_tag=data.get('concept_tag', ''),
            notes=data.get('notes', ''),
            tags=data.get('tags', []),
            run_time_seconds=data.get('run_time_seconds', 0),
            status=Experiment.STATUS_COMPLETED,
        )
        return Response({'id': exp.id, 'created_at': exp.created_at.isoformat()}, status=status.HTTP_201_CREATED)


class PlaygroundCompareView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        ids = request.data.get('experiment_ids', [])
        if not ids or len(ids) < 2:
            return Response(
                {'error': 'Provide 2-5 experiment_ids'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        experiments = Experiment.objects.filter(user=request.user, pk__in=ids[:5])
        comparison = []
        for exp in experiments:
            results = exp.results or exp.metrics or {}
            comparison.append({
                'id': exp.id,
                'dataset': exp.dataset_name or (exp.dataset.name if exp.dataset_id else ''),
                'algorithm': exp.algorithm or exp.model_type,
                'accuracy': results.get('accuracy'),
                'f1': results.get('f1'),
                'auc': results.get('auc'),
                'train_time': results.get('train_time'),
                'predict_time': results.get('predict_time'),
                'created_at': exp.created_at.isoformat(),
            })
        return Response({'experiments': comparison})


class CourseProgressSummaryView(APIView):
    """Navbar progress indicator for Learn pages."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        course_slug = request.query_params.get('course')
        if not course_slug:
            enrollment = Enrollment.objects.filter(
                user=request.user, status='active'
            ).order_by('-enrolled_at').first()
            if not enrollment:
                return Response({'progress_percent': 0, 'completed': 0, 'total': 0})
            course = enrollment.course
        else:
            course = get_object_or_404(Course, slug=course_slug)
            enrollment = Enrollment.objects.filter(
                user=request.user, course=course, status='active'
            ).first()

        total = course.lessons.filter(is_active=True).count()
        if not enrollment:
            return Response({
                'course_slug': course.slug,
                'progress_percent': 0,
                'completed': 0,
                'total': total,
            })

        completed = LessonProgress.objects.filter(
            user=request.user,
            enrollment=enrollment,
            is_completed=True,
        ).count()

        return Response({
            'course_slug': course.slug,
            'course_title': course.title,
            'progress_percent': round((completed / total) * 100) if total else 0,
            'completed': completed,
            'total': total,
        })

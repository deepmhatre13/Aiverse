"""
Seed courses for ML Engineering Academy.

Creates 8 production-ready courses:
- 3 FREE courses (YouTube-based)
- 5 PAID courses (Stripe required)

Usage:
    python manage.py seed_courses
    python manage.py seed_courses --clear  # Clear existing and reseed
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.text import slugify
from learn.models import Course, Lesson


# =========================================================================
# COURSE DATA
# =========================================================================

COURSES = [
    # -------------------------------------------------------------------
    # FREE COURSES (YouTube-based)
    # -------------------------------------------------------------------
    {
        "title": "Machine Learning Foundations",
        "slug": "machine-learning-foundations",
        "description": """Master the fundamental concepts of Machine Learning from scratch.

This comprehensive course covers:
• What is Machine Learning and its types (supervised, unsupervised, reinforcement)
• Linear algebra and calculus basics for ML
• Probability and statistics fundamentals
• The ML workflow: data collection, preprocessing, training, evaluation
• Bias-variance tradeoff and model selection
• Practical implementation with Python and scikit-learn

Perfect for beginners who want to build a solid foundation in ML concepts before diving into advanced topics.""",
        "short_description": "Build a solid foundation in Machine Learning concepts and mathematics.",
        "is_free": True,
        "is_paid": False,
        "price": None,
        "level": "beginner",
        "instructor_name": "AIverse ML Team",
        "what_youll_learn": [
            "Understand the core concepts of Machine Learning",
            "Learn the math foundations: linear algebra, calculus, probability",
            "Implement basic ML algorithms from scratch",
            "Use scikit-learn for practical ML projects",
            "Evaluate and compare different ML models",
        ],
        "prerequisites": [
            "Basic Python programming knowledge",
            "High school level mathematics",
        ],
        "target_audience": [
            "Beginners who want to start their ML journey",
            "Software developers looking to transition into ML",
            "Students studying computer science or data science",
        ],
        "tags": ["machine learning", "beginner", "fundamentals", "python", "scikit-learn"],
        "thumbnail": "https://images.unsplash.com/photo-1555949963-aa79dcee981c?w=800",
        "lessons": [
            {
                "title": "Introduction to Machine Learning",
                "description": "What is ML? Types of ML, and real-world applications.",
                "youtube_url": "https://www.youtube.com/watch?v=ukzFI9rgwfU",
                "duration_minutes": 15,
                "is_preview": True,
            },
            {
                "title": "Supervised vs Unsupervised Learning",
                "description": "Understanding the two main paradigms of machine learning.",
                "youtube_url": "https://www.youtube.com/watch?v=W01tIRP_Rqs",
                "duration_minutes": 20,
            },
            {
                "title": "Linear Algebra for ML",
                "description": "Vectors, matrices, and operations essential for ML.",
                "youtube_url": "https://www.youtube.com/watch?v=fNk_zzaMoSs",
                "duration_minutes": 25,
            },
            {
                "title": "Probability and Statistics Basics",
                "description": "Probability distributions, Bayes theorem, and statistics for ML.",
                "youtube_url": "https://www.youtube.com/watch?v=sbbYntt5CJk",
                "duration_minutes": 30,
            },
            {
                "title": "Your First ML Model",
                "description": "Building a simple classifier with scikit-learn.",
                "youtube_url": "https://www.youtube.com/watch?v=0Lt9w-BxKFQ",
                "duration_minutes": 35,
            },
            {
                "title": "Model Evaluation Metrics",
                "description": "Accuracy, precision, recall, F1, and when to use each.",
                "youtube_url": "https://www.youtube.com/watch?v=LbX4X71-TFI",
                "duration_minutes": 25,
            },
        ],
    },
    {
        "title": "Python for Data Science",
        "slug": "python-for-data-science",
        "description": """Master Python programming for Data Science and ML applications.

This course teaches you:
• Python fundamentals refresher for data work
• NumPy for numerical computing
• Pandas for data manipulation and analysis
• Matplotlib and Seaborn for visualization
• Data cleaning and preprocessing techniques
• Working with real-world datasets

Build the Python skills essential for any ML practitioner.""",
        "short_description": "Learn Python, NumPy, Pandas, and visualization for data science.",
        "is_free": True,
        "is_paid": False,
        "price": None,
        "level": "beginner",
        "instructor_name": "AIverse ML Team",
        "what_youll_learn": [
            "Master NumPy for efficient numerical computing",
            "Use Pandas for data manipulation and analysis",
            "Create stunning visualizations with Matplotlib and Seaborn",
            "Clean and preprocess real-world datasets",
            "Handle missing data and outliers",
        ],
        "prerequisites": [
            "Basic programming concepts (any language)",
        ],
        "target_audience": [
            "Beginners learning Python for data science",
            "Programmers from other languages transitioning to Python",
            "Anyone who wants to work with data in Python",
        ],
        "tags": ["python", "numpy", "pandas", "data science", "visualization", "beginner"],
        "thumbnail": "https://images.unsplash.com/photo-1526379095098-d400fd0bf935?w=800",
        "lessons": [
            {
                "title": "Python Refresher for Data Science",
                "description": "Quick review of Python syntax, data structures, and functions.",
                "youtube_url": "https://www.youtube.com/watch?v=_uQrJ0TkZlc",
                "duration_minutes": 20,
                "is_preview": True,
            },
            {
                "title": "NumPy Fundamentals",
                "description": "Arrays, broadcasting, and vectorized operations.",
                "youtube_url": "https://www.youtube.com/watch?v=QUT1VHiLmmI",
                "duration_minutes": 30,
            },
            {
                "title": "Advanced NumPy Operations",
                "description": "Indexing, slicing, reshaping, and linear algebra.",
                "youtube_url": "https://www.youtube.com/watch?v=lLRBYKwP8GQ",
                "duration_minutes": 25,
            },
            {
                "title": "Pandas DataFrames",
                "description": "Creating, indexing, and manipulating DataFrames.",
                "youtube_url": "https://www.youtube.com/watch?v=vmEHCJofslg",
                "duration_minutes": 35,
            },
            {
                "title": "Data Cleaning with Pandas",
                "description": "Handling missing values, duplicates, and data types.",
                "youtube_url": "https://www.youtube.com/watch?v=bDhvCp3_lYw",
                "duration_minutes": 30,
            },
            {
                "title": "Data Visualization Essentials",
                "description": "Matplotlib, Seaborn, and creating insightful charts.",
                "youtube_url": "https://www.youtube.com/watch?v=UO98lJQ3QGI",
                "duration_minutes": 40,
            },
        ],
    },
    {
        "title": "Introduction to Deep Learning",
        "slug": "introduction-to-deep-learning",
        "description": """Understand the fundamentals of Deep Learning and Neural Networks.

Course contents:
• Neural network architecture and components
• Activation functions and their properties
• Backpropagation and gradient descent
• Introduction to TensorFlow and Keras
• Building your first neural network
• CNNs, RNNs, and their applications
• Transfer learning basics

Start your deep learning journey with this foundational course.""",
        "short_description": "Learn neural networks, backpropagation, and build with Keras.",
        "is_free": True,
        "is_paid": False,
        "price": None,
        "level": "intermediate",
        "instructor_name": "AIverse ML Team",
        "what_youll_learn": [
            "Understand how neural networks work",
            "Implement backpropagation from scratch",
            "Build neural networks with TensorFlow/Keras",
            "Understand CNNs for image tasks",
            "Learn RNN basics for sequential data",
        ],
        "prerequisites": [
            "Machine Learning fundamentals",
            "Python programming",
            "Basic linear algebra",
        ],
        "target_audience": [
            "ML practitioners ready to learn deep learning",
            "Developers interested in neural networks",
            "Students studying AI/ML",
        ],
        "tags": ["deep learning", "neural networks", "tensorflow", "keras", "cnn", "rnn"],
        "thumbnail": "https://images.unsplash.com/photo-1620712943543-bcc4688e7485?w=800",
        "lessons": [
            {
                "title": "Neural Networks Explained",
                "description": "Architecture, neurons, weights, and biases.",
                "youtube_url": "https://www.youtube.com/watch?v=aircAruvnKk",
                "duration_minutes": 20,
                "is_preview": True,
            },
            {
                "title": "Activation Functions Deep Dive",
                "description": "Sigmoid, ReLU, Tanh, and when to use each.",
                "youtube_url": "https://www.youtube.com/watch?v=-7scQpJT7uo",
                "duration_minutes": 15,
            },
            {
                "title": "Backpropagation Intuition",
                "description": "How neural networks learn through gradient descent.",
                "youtube_url": "https://www.youtube.com/watch?v=Ilg3gGewQ5U",
                "duration_minutes": 25,
            },
            {
                "title": "Building with TensorFlow/Keras",
                "description": "Your first neural network in code.",
                "youtube_url": "https://www.youtube.com/watch?v=tPYj3fFJGjk",
                "duration_minutes": 35,
            },
            {
                "title": "Convolutional Neural Networks",
                "description": "Understanding CNNs for image recognition.",
                "youtube_url": "https://www.youtube.com/watch?v=YRhxdVk_sIs",
                "duration_minutes": 30,
            },
            {
                "title": "Recurrent Neural Networks",
                "description": "RNNs and LSTMs for sequential data.",
                "youtube_url": "https://www.youtube.com/watch?v=AsNTP8Kwu80",
                "duration_minutes": 25,
            },
        ],
    },
    
    # -------------------------------------------------------------------
    # PAID COURSES (Stripe required)
    # -------------------------------------------------------------------
    {
        "title": "Applied Machine Learning Engineering",
        "slug": "applied-ml-engineering",
        "description": """Transform from ML beginner to production ML engineer.

This comprehensive course teaches you:
• End-to-end ML pipeline development
• Feature engineering at scale
• Model selection and hyperparameter tuning
• Cross-validation strategies
• Handling imbalanced datasets
• Ensemble methods and model stacking
• A/B testing for ML models
• Production deployment considerations

Real-world projects with industry datasets. Build a portfolio of production-ready ML solutions.""",
        "short_description": "Build production-ready ML pipelines and real-world solutions.",
        "is_free": False,
        "is_paid": True,
        "price": 79.00,
        "level": "intermediate",
        "instructor_name": "AIverse ML Team",
        "what_youll_learn": [
            "Build end-to-end ML pipelines",
            "Master advanced feature engineering",
            "Implement ensemble methods and stacking",
            "Handle real-world data challenges",
            "Deploy models to production",
        ],
        "prerequisites": [
            "Machine Learning Foundations course",
            "Python proficiency",
            "Basic statistics knowledge",
        ],
        "target_audience": [
            "ML practitioners ready for production work",
            "Data scientists building real products",
            "Engineers transitioning to ML roles",
        ],
        "tags": ["machine learning", "production", "pipelines", "feature engineering", "intermediate"],
        "thumbnail": "https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=800",
        "lessons": [
            {
                "title": "Course Overview & Setup",
                "description": "What you'll build and environment setup.",
                "duration_minutes": 15,
                "is_preview": True,
            },
            {
                "title": "ML Pipeline Architecture",
                "description": "Designing robust, scalable ML pipelines.",
                "duration_minutes": 45,
            },
            {
                "title": "Advanced Feature Engineering",
                "description": "Creating powerful features from raw data.",
                "duration_minutes": 50,
            },
            {
                "title": "Hyperparameter Optimization",
                "description": "Grid search, random search, and Bayesian optimization.",
                "duration_minutes": 40,
            },
            {
                "title": "Handling Class Imbalance",
                "description": "SMOTE, class weights, and threshold tuning.",
                "duration_minutes": 35,
            },
            {
                "title": "Ensemble Methods",
                "description": "Bagging, boosting, and model stacking.",
                "duration_minutes": 55,
            },
            {
                "title": "Model Evaluation in Production",
                "description": "A/B testing, monitoring, and iteration.",
                "duration_minutes": 40,
            },
            {
                "title": "Capstone Project",
                "description": "Build a complete ML pipeline for real data.",
                "duration_minutes": 90,
            },
        ],
    },
    {
        "title": "Production ML Systems Design",
        "slug": "production-ml-systems-design",
        "description": """Design and architect ML systems that scale to millions of users.

Learn how top companies build ML systems:
• ML system design patterns
• Data pipelines and feature stores
• Model serving architectures (online vs batch)
• Scalability and latency optimization
• Monitoring and observability
• ML infrastructure in the cloud (AWS/GCP/Azure)
• Cost optimization strategies
• Case studies from Netflix, Uber, and Google

Essential for ML engineers working on production systems.""",
        "short_description": "Design scalable ML systems for production environments.",
        "is_free": False,
        "is_paid": True,
        "price": 99.00,
        "level": "advanced",
        "instructor_name": "AIverse ML Team",
        "what_youll_learn": [
            "Design ML systems at scale",
            "Build efficient data and feature pipelines",
            "Implement model serving strategies",
            "Monitor ML systems in production",
            "Optimize for latency and cost",
        ],
        "prerequisites": [
            "Applied ML Engineering course",
            "Software engineering experience",
            "Basic cloud platform knowledge",
        ],
        "target_audience": [
            "Senior ML engineers",
            "ML architects and tech leads",
            "Platform engineers supporting ML teams",
        ],
        "tags": ["systems design", "production", "mlops", "architecture", "advanced"],
        "thumbnail": "https://images.unsplash.com/photo-1558494949-ef010cbdcc31?w=800",
        "lessons": [
            {
                "title": "ML Systems Design Overview",
                "description": "Introduction to production ML architecture.",
                "duration_minutes": 30,
                "is_preview": True,
            },
            {
                "title": "Data Pipeline Design",
                "description": "Building robust data ingestion and processing pipelines.",
                "duration_minutes": 55,
            },
            {
                "title": "Feature Stores",
                "description": "Centralized feature management for ML.",
                "duration_minutes": 45,
            },
            {
                "title": "Model Serving Strategies",
                "description": "Online inference, batch prediction, and edge deployment.",
                "duration_minutes": 50,
            },
            {
                "title": "Scaling ML Systems",
                "description": "Horizontal scaling, caching, and load balancing.",
                "duration_minutes": 45,
            },
            {
                "title": "Monitoring & Observability",
                "description": "Metrics, alerts, and debugging production ML.",
                "duration_minutes": 40,
            },
            {
                "title": "Cloud ML Architecture",
                "description": "AWS SageMaker, GCP Vertex AI, Azure ML patterns.",
                "duration_minutes": 60,
            },
            {
                "title": "Case Study: Netflix Recommendations",
                "description": "Deep dive into Netflix's ML infrastructure.",
                "duration_minutes": 35,
            },
            {
                "title": "Case Study: Uber Michelangelo",
                "description": "Uber's end-to-end ML platform.",
                "duration_minutes": 35,
            },
        ],
    },
    {
        "title": "Advanced Feature Engineering",
        "slug": "advanced-feature-engineering",
        "description": """Master the art of creating features that make models win.

Topics covered:
• Feature engineering philosophy and workflow
• Numeric feature transformations
• Categorical encoding strategies
• Text feature extraction (TF-IDF, embeddings)
• Time series feature engineering
• Geospatial features
• Automated feature generation
• Feature selection methods
• Domain-specific feature engineering

Features are often more important than algorithms. Learn to create winning features.""",
        "short_description": "Create powerful features that make AI models excel.",
        "is_free": False,
        "is_paid": True,
        "price": 69.00,
        "level": "intermediate",
        "instructor_name": "AIverse ML Team",
        "what_youll_learn": [
            "Transform raw data into powerful features",
            "Handle different data types effectively",
            "Use automated feature generation tools",
            "Select the most predictive features",
            "Apply domain knowledge to feature design",
        ],
        "prerequisites": [
            "Machine Learning Foundations",
            "Python and Pandas proficiency",
        ],
        "target_audience": [
            "Data scientists improving model performance",
            "ML engineers working with diverse data",
            "Kaggle competitors and ML practitioners",
        ],
        "tags": ["feature engineering", "preprocessing", "data science", "intermediate"],
        "thumbnail": "https://images.unsplash.com/photo-1518186285589-2f7649de83e0?w=800",
        "lessons": [
            {
                "title": "Feature Engineering Mindset",
                "description": "Why features matter more than algorithms.",
                "duration_minutes": 20,
                "is_preview": True,
            },
            {
                "title": "Numeric Transformations",
                "description": "Scaling, binning, and polynomial features.",
                "duration_minutes": 35,
            },
            {
                "title": "Categorical Encoding Mastery",
                "description": "One-hot, target encoding, and embeddings.",
                "duration_minutes": 40,
            },
            {
                "title": "Text Feature Engineering",
                "description": "Bag of words, TF-IDF, and word embeddings.",
                "duration_minutes": 45,
            },
            {
                "title": "Time Series Features",
                "description": "Lag features, rolling windows, and seasonality.",
                "duration_minutes": 50,
            },
            {
                "title": "Geospatial Features",
                "description": "Distance calculations and spatial clustering.",
                "duration_minutes": 30,
            },
            {
                "title": "Automated Feature Generation",
                "description": "Using Featuretools and domain-agnostic approaches.",
                "duration_minutes": 40,
            },
            {
                "title": "Feature Selection",
                "description": "Filter, wrapper, and embedded methods.",
                "duration_minutes": 35,
            },
        ],
    },
    {
        "title": "MLOps & Deployment",
        "slug": "mlops-deployment",
        "description": """Bridge the gap between ML development and production deployment.

Comprehensive MLOps coverage:
• MLOps principles and maturity model
• Version control for ML (code, data, models)
• CI/CD pipelines for ML
• Model packaging and containerization
• Kubernetes for ML workloads
• Model registries and artifact management
• Deployment strategies (canary, blue-green)
• Monitoring model performance and drift
• Retraining automation

Become a full-stack ML engineer with deployment expertise.""",
        "short_description": "Deploy, monitor, and maintain ML models in production.",
        "is_free": False,
        "is_paid": True,
        "price": 109.00,
        "level": "advanced",
        "instructor_name": "AIverse ML Team",
        "what_youll_learn": [
            "Implement MLOps best practices",
            "Build CI/CD pipelines for ML",
            "Deploy models with Docker and Kubernetes",
            "Monitor models for drift and degradation",
            "Automate model retraining",
        ],
        "prerequisites": [
            "Applied ML Engineering course",
            "Basic Docker knowledge",
            "Command line proficiency",
        ],
        "target_audience": [
            "ML engineers deploying models",
            "DevOps engineers supporting ML teams",
            "Data scientists wanting deployment skills",
        ],
        "tags": ["mlops", "deployment", "docker", "kubernetes", "ci/cd", "advanced"],
        "thumbnail": "https://images.unsplash.com/photo-1667372393119-3d4c48d07fc9?w=800",
        "lessons": [
            {
                "title": "MLOps Fundamentals",
                "description": "What is MLOps and why it matters.",
                "duration_minutes": 25,
                "is_preview": True,
            },
            {
                "title": "Version Control for ML",
                "description": "Git, DVC, and ML experiment tracking.",
                "duration_minutes": 40,
            },
            {
                "title": "CI/CD for Machine Learning",
                "description": "Building automated ML pipelines.",
                "duration_minutes": 55,
            },
            {
                "title": "Model Packaging with Docker",
                "description": "Containerizing ML models for deployment.",
                "duration_minutes": 45,
            },
            {
                "title": "Kubernetes for ML",
                "description": "Deploying and scaling ML on K8s.",
                "duration_minutes": 60,
            },
            {
                "title": "Model Registry & Artifacts",
                "description": "Managing models with MLflow and similar tools.",
                "duration_minutes": 35,
            },
            {
                "title": "Deployment Strategies",
                "description": "Canary deployments, A/B testing, rollbacks.",
                "duration_minutes": 40,
            },
            {
                "title": "Monitoring & Drift Detection",
                "description": "Tracking model performance in production.",
                "duration_minutes": 50,
            },
            {
                "title": "Automated Retraining",
                "description": "Triggering retraining on data/performance changes.",
                "duration_minutes": 45,
            },
        ],
    },
    {
        "title": "Real-World ML Case Studies",
        "slug": "real-world-ml-case-studies",
        "description": """Learn from production ML systems at top tech companies.

Deep dive into:
• Recommendation systems (Netflix, Spotify, YouTube)
• Search ranking (Google, Amazon)
• Fraud detection (Stripe, PayPal)
• Dynamic pricing (Uber, Airbnb)
• Computer vision in production (Tesla, Meta)
• NLP at scale (OpenAI, ChatGPT architecture)
• Personalization systems
• Ad targeting and bidding

Each case study covers problem formulation, system design, and lessons learned.""",
        "short_description": "Learn from production ML systems at top tech companies.",
        "is_free": False,
        "is_paid": True,
        "price": 89.00,
        "level": "advanced",
        "instructor_name": "AIverse ML Team",
        "what_youll_learn": [
            "Understand real-world ML system design",
            "Learn from industry successes and failures",
            "Apply lessons to your own ML projects",
            "Think like a senior ML engineer",
            "Design systems for specific domains",
        ],
        "prerequisites": [
            "Production ML Systems Design recommended",
            "Understanding of ML fundamentals",
        ],
        "target_audience": [
            "ML engineers learning system design",
            "Architects designing ML solutions",
            "Tech leads evaluating ML approaches",
        ],
        "tags": ["case studies", "system design", "production", "advanced"],
        "thumbnail": "https://images.unsplash.com/photo-1460925895917-afdab827c52f?w=800",
        "lessons": [
            {
                "title": "Netflix Recommendations Deep Dive",
                "description": "How Netflix recommends content to 200M+ users.",
                "duration_minutes": 45,
                "is_preview": True,
            },
            {
                "title": "YouTube's Video Recommendation",
                "description": "Two-tower architecture and engagement optimization.",
                "duration_minutes": 40,
            },
            {
                "title": "Google Search Ranking",
                "description": "From PageRank to BERT: evolution of search.",
                "duration_minutes": 50,
            },
            {
                "title": "Stripe Fraud Detection",
                "description": "Real-time fraud detection at scale.",
                "duration_minutes": 45,
            },
            {
                "title": "Uber Dynamic Pricing",
                "description": "Surge pricing and demand forecasting.",
                "duration_minutes": 40,
            },
            {
                "title": "Tesla Autopilot Vision",
                "description": "Computer vision for autonomous driving.",
                "duration_minutes": 55,
            },
            {
                "title": "ChatGPT Architecture",
                "description": "How large language models are trained and served.",
                "duration_minutes": 60,
            },
            {
                "title": "Meta Ads Ranking",
                "description": "Ad targeting and real-time bidding systems.",
                "duration_minutes": 45,
            },
        ],
    },
]


class Command(BaseCommand):
    help = 'Seed ML Engineering Academy courses'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing courses before seeding'
        )
        parser.add_argument(
            '--generate-quizzes',
            action='store_true',
            help='Generate quizzes for all lessons after seeding (requires Celery or sync mode)'
        )
        parser.add_argument(
            '--sync-quizzes',
            action='store_true',
            help='Generate quizzes synchronously (slow but works without Celery)'
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write(self.style.WARNING('Clearing existing courses...'))
            Lesson.objects.all().delete()
            Course.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('Cleared!'))
        
        self.stdout.write('Seeding ML Engineering Academy courses...\n')
        
        for course_data in COURSES:
            lessons_data = course_data.pop('lessons')
            
            # Create course
            course, created = Course.objects.update_or_create(
                slug=course_data['slug'],
                defaults={
                    **course_data,
                    'is_published': True,
                    'published_at': timezone.now(),
                }
            )
            
            status = 'Created' if created else 'Updated'
            price_str = f"${course.price}" if course.price else "FREE"
            self.stdout.write(
                f"  {status}: {course.title} ({price_str})"
            )
            
            # Create lessons
            for idx, lesson_data in enumerate(lessons_data, 1):
                lesson, _ = Lesson.objects.update_or_create(
                    course=course,
                    slug=slugify(lesson_data['title']),
                    defaults={
                        **lesson_data,
                        'order': idx,
                        'video_type': 'youtube' if lesson_data.get('youtube_url') else 'hosted',
                    }
                )
            
            # Update course stats
            course.update_stats()
        
        # Summary
        free_count = Course.objects.filter(is_free=True).count()
        paid_count = Course.objects.filter(is_paid=True).count()
        total_lessons = Lesson.objects.count()
        
        self.stdout.write('\n' + '=' * 50)
        self.stdout.write(self.style.SUCCESS(
            f'Seeded {free_count + paid_count} courses ({free_count} free, {paid_count} paid)'
        ))
        self.stdout.write(self.style.SUCCESS(f'Total lessons: {total_lessons}'))
        self.stdout.write('=' * 50)
        
        # Generate quizzes if requested
        if options.get('generate_quizzes') or options.get('sync_quizzes'):
            self._generate_quizzes(sync=options.get('sync_quizzes', False))
    
    def _generate_quizzes(self, sync=False):
        """Generate quizzes for all lessons."""
        from learn.models import Quiz
        from learn.tasks import generate_quiz_mcqs_task
        
        lessons_without_quiz = Lesson.objects.filter(quiz__isnull=True)
        count = lessons_without_quiz.count()
        
        if count == 0:
            self.stdout.write(self.style.SUCCESS('\nAll lessons already have quizzes.'))
            return
        
        self.stdout.write(f'\nGenerating quizzes for {count} lessons...')
        
        if sync:
            # Synchronous generation (slower but doesn't require Celery)
            self.stdout.write(self.style.WARNING('Running in sync mode (may take a while)...\n'))
            for i, lesson in enumerate(lessons_without_quiz, 1):
                try:
                    self.stdout.write(f'  [{i}/{count}] Generating quiz for: {lesson.title}...')
                    result = generate_quiz_mcqs_task(lesson.id)
                    if result:
                        self.stdout.write(self.style.SUCCESS(' Done'))
                    else:
                        self.stdout.write(self.style.WARNING(' Skipped/Error'))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f' Failed: {e}'))
        else:
            # Async generation via Celery
            self.stdout.write('Queueing quiz generation tasks (requires Celery running)...\n')
            for lesson in lessons_without_quiz:
                try:
                    generate_quiz_mcqs_task.delay(lesson.id)
                    self.stdout.write(f'  Queued: {lesson.title}')
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'  Failed to queue {lesson.title}: {e}'))
            
            self.stdout.write(self.style.SUCCESS(f'\nQueued {count} quiz generation tasks.'))
            self.stdout.write('Run Celery worker to process: celery -A backend worker -l info')

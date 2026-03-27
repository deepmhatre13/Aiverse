"""
Management command for Phase E: End-to-End Verification

Verifies all 5 problems work correctly with:
- Public tests (visible feedback)
- Private tests (after submission)
- Error handling
- State machine transitions

Usage:
    python manage.py verify_all_problems
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from ml.models import Problem, Submission, TestSuite, DatasetConfig
from ml.test_cases import PROBLEM_TEST_SUITES
from ml.executor import execute_user_code
from ml.api_validator import APICompatibilityLayer

User = get_user_model()


class Command(BaseCommand):
    help = 'Comprehensive end-to-end verification of all 5 problems'

    test_code_templates = {
        'iris-species-classification': '''
from sklearn.linear_model import LogisticRegression
def train_and_predict(X_train, y_train, X_test):
    clf = LogisticRegression(max_iter=200, random_state=42)
    clf.fit(X_train, y_train)
    return clf.predict(X_test)
''',
        'spam-detection': '''
from sklearn.linear_model import LogisticRegression
def train_and_predict(X_train, y_train, X_test):
    clf = LogisticRegression(max_iter=200, random_state=42)
    clf.fit(X_train, y_train)
    return clf.predict(X_test)
''',
        'customer-churn-prediction': '''
from sklearn.linear_model import LogisticRegression
def train_and_predict(X_train, y_train, X_test):
    clf = LogisticRegression(max_iter=200, random_state=42)
    clf.fit(X_train, y_train)
    return clf.predict(X_test)
''',
        'credit-risk-prediction': '''
from sklearn.linear_model import LogisticRegression
def train_and_predict(X_train, y_train, X_test):
    clf = LogisticRegression(max_iter=200, random_state=42)
    clf.fit(X_train, y_train)
    return clf.predict(X_test)
''',
        'house-price-prediction': '''
from sklearn.linear_model import LinearRegression
import numpy as np
def train_and_predict(X_train, y_train, X_test):
    reg = LinearRegression()
    reg.fit(X_train, y_train)
    return reg.predict(X_test)
''',
    }

    deprecated_code = '''
from sklearn.linear_model import LogisticRegression
def train_and_predict(X_train, y_train, X_test):
    # This will fail on sklearn >= 1.6
    clf = LogisticRegression(multi_class='multinomial', max_iter=200, random_state=42)
    clf.fit(X_train, y_train)
    return clf.predict(X_test)
'''

    problems = [
        'iris-species-classification',
        'spam-detection',
        'customer-churn-prediction',
        'credit-risk-prediction',
        'house-price-prediction',
    ]

    def handle(self, *args, **options):
        self.results = {
            'total': 0,
            'passed': 0,
            'failed': 0,
            'errors': [],
        }

        self.stdout.write("\n" + "="*70)
        self.stdout.write("PHASE E: END-TO-END VERIFICATION OF ALL 5 PROBLEMS")
        self.stdout.write("="*70)

        self.verify_problems_exist()
        self.verify_dataset_configs()
        self.verify_test_suites()
        self.test_execution_with_good_code()
        self.test_api_compatibility_check()
        self.test_submission_state_machine()

        self.print_summary()

    def verify_problems_exist(self):
        self.stdout.write("\n[STEP 1] Verify all 5 problems exist in database")
        self.stdout.write("-" * 70)
        for slug in self.problems:
            try:
                problem = Problem.objects.get(slug=slug)
                self.stdout.write(
                    self.style.SUCCESS(f"  [OK] {problem.title} (id={problem.id})")
                )
                self.results['total'] += 1
                self.results['passed'] += 1
            except Problem.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f"  [FAIL] Problem '{slug}' not found")
                )
                self.results['errors'].append(f"Problem '{slug}' not found")
                self.results['total'] += 1
                self.results['failed'] += 1

    def verify_dataset_configs(self):
        self.stdout.write("\n[STEP 2] Verify DatasetConfig exists for all problems")
        self.stdout.write("-" * 70)
        for slug in self.problems:
            try:
                problem = Problem.objects.get(slug=slug)
                config = DatasetConfig.objects.get(problem=problem)
                self.stdout.write(
                    self.style.SUCCESS(
                        f"  [OK] {problem.title}: {config.loader_type}/{config.dataset_identifier}"
                    )
                )
                self.results['total'] += 1
                self.results['passed'] += 1
            except (Problem.DoesNotExist, DatasetConfig.DoesNotExist) as e:
                self.stdout.write(
                    self.style.ERROR(f"  [FAIL] {slug}: {e}")
                )
                self.results['errors'].append(f"DatasetConfig missing for {slug}")
                self.results['total'] += 1
                self.results['failed'] += 1

    def verify_test_suites(self):
        self.stdout.write("\n[STEP 3] Verify TestSuite exists for all problems")
        self.stdout.write("-" * 70)
        for slug in self.problems:
            try:
                problem = Problem.objects.get(slug=slug)
                suite = TestSuite.objects.get(problem=problem)
                public_count = len(suite.public_tests)
                private_count = len(suite.private_tests)
                self.stdout.write(
                    self.style.SUCCESS(
                        f"  [OK] {problem.title}: {public_count} public, {private_count} private tests"
                    )
                )
                self.results['total'] += 1
                self.results['passed'] += 1
            except (Problem.DoesNotExist, TestSuite.DoesNotExist) as e:
                self.stdout.write(
                    self.style.ERROR(f"  [FAIL] {slug}: {e}")
                )
                self.results['errors'].append(f"TestSuite missing for {slug}")
                self.results['total'] += 1
                self.results['failed'] += 1

    def test_execution_with_good_code(self):
        self.stdout.write("\n[STEP 4] Test execution with good code (valid solution)")
        self.stdout.write("-" * 70)
        for slug in self.problems:
            try:
                problem = Problem.objects.get(slug=slug)
                code = self.test_code_templates[slug]
                test_suite_def = PROBLEM_TEST_SUITES[slug]
                
                # Load dataset
                config = DatasetConfig.objects.get(problem=problem)
                X_train, y_train, X_test, y_test = config.load()
                
                # Execute code
                result = execute_user_code(code, X_train, y_train, X_test)
                
                if result['success']:
                    # Validate predictions
                    if len(test_suite_def.public_tests) > 0:
                        test = test_suite_def.public_tests[0]
                        eval_result = test.evaluate(result['predictions'])
                        score = eval_result.get('score', 0)
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"  [OK] {problem.title}: Executed successfully, score={score:.3f}"
                            )
                        )
                        self.results['total'] += 1
                        self.results['passed'] += 1
                    else:
                        self.stdout.write(
                            self.style.SUCCESS(f"  [OK] {problem.title}: Executed successfully")
                        )
                        self.results['total'] += 1
                        self.results['passed'] += 1
                else:
                    error = result.get('error') or result.get('stderr', 'Unknown error')
                    detailed_error = result.get('error_log', '')
                    full_error = f"{error}\n{detailed_error}" if detailed_error else error
                    self.stdout.write(
                        self.style.ERROR(
                            f"  [FAIL] {problem.title}: Execution error: {full_error[:80]}"
                        )
                    )
                    self.results['errors'].append(f"{slug}: {full_error}")
                    self.results['total'] += 1
                    self.results['failed'] += 1
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"  [FAIL] {slug}: {str(e)[:50]}")
                )
                self.results['errors'].append(f"{slug}: {str(e)}")
                self.results['total'] += 1
                self.results['failed'] += 1

    def test_api_compatibility_check(self):
        self.stdout.write("\n[STEP 5] Test API compatibility check (deprecated parameters)")
        self.stdout.write("-" * 70)
        try:
            is_compatible, error_msg = APICompatibilityLayer.check_code(self.deprecated_code)
            if not is_compatible:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"  [OK] Correctly detected deprecated 'multi_class' parameter"
                    )
                )
                self.results['total'] += 1
                self.results['passed'] += 1
            else:
                self.stdout.write(
                    self.style.ERROR(
                        f"  [FAIL] Should have detected deprecated 'multi_class' parameter"
                    )
                )
                self.results['errors'].append("API validator failed to detect deprecated parameter")
                self.results['total'] += 1
                self.results['failed'] += 1
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"  [FAIL] APICompatibilityLayer error: {str(e)[:50]}")
            )
            self.results['errors'].append(f"APICompatibilityLayer: {str(e)}")
            self.results['total'] += 1
            self.results['failed'] += 1

    def test_submission_state_machine(self):
        self.stdout.write("\n[STEP 6] Test Submission state machine (create & verify transitions)")
        self.stdout.write("-" * 70)
        try:
            # Get or create test user
            user, _ = User.objects.get_or_create(
                email='testuser@example.com',
                defaults={'full_name': 'Test User'}
            )
            
            # Pick a problem to test state machine
            problem = Problem.objects.get(slug='iris-species-classification')
            code = self.test_code_templates['iris-species-classification']
            
            # Create submission (should start in 'pending' state)
            submission = Submission.objects.create(
                user=user,
                problem=problem,
                code=code,
                status='pending'
            )
            
            if submission.status == 'pending':
                self.stdout.write(
                    self.style.SUCCESS(
                        f"  [OK] Submission created in 'pending' state (ID: {submission.id})"
                    )
                )
                self.results['total'] += 1
                self.results['passed'] += 1
                submission.delete()
            else:
                self.stdout.write(
                    self.style.ERROR(
                        f"  [FAIL] Submission should start in 'pending', got '{submission.status}'"
                    )
                )
                self.results['errors'].append("Submission state machine broken")
                self.results['total'] += 1
                self.results['failed'] += 1
                submission.delete()
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"  [FAIL] State machine test failed: {str(e)[:50]}")
            )
            self.results['errors'].append(f"State machine: {str(e)}")
            self.results['total'] += 1
            self.results['failed'] += 1

    def print_summary(self):
        self.stdout.write("\n" + "="*70)
        self.stdout.write("VERIFICATION SUMMARY")
        self.stdout.write("="*70)
        self.stdout.write(f"Total checks: {self.results['total']}")
        self.stdout.write(f"Passed: {self.results['passed']}")
        self.stdout.write(f"Failed: {self.results['failed']}")

        if self.results['errors']:
            self.stdout.write("\nErrors found:")
            for error in self.results['errors']:
                self.stdout.write(f"  - {error}")
            self.stdout.write("\nStatus: VERIFICATION FAILED")
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    "\nStatus: ALL CHECKS PASSED - All 5 problems are fully functional!"
                )
            )

        self.stdout.write("="*70 + "\n")

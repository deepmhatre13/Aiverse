"""
Admin-only management command for testing reference solutions.

Usage:
    python manage.py test_reference_solution <problem_slug>
    python manage.py test_reference_solution --all
    python manage.py test_reference_solution --validate-thresholds
    
Security:
    - This command is for admin/development use only
    - Output should never be exposed to users
    - Reference solutions remain hidden
"""

from django.core.management.base import BaseCommand, CommandError
from ml.reference_solutions import (
    run_reference_solution,
    validate_threshold,
    list_available_solutions,
)
from ml.registry import list_problems, get_problem_definition


class Command(BaseCommand):
    help = 'Test reference solutions for ML problems (admin-only)'

    def add_arguments(self, parser):
        parser.add_argument(
            'problem_slug',
            nargs='?',
            type=str,
            help='Problem slug to test (e.g., linear-binary-classification)'
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Test all available reference solutions'
        )
        parser.add_argument(
            '--validate-thresholds',
            action='store_true',
            help='Validate that all reference solutions meet their thresholds'
        )
        parser.add_argument(
            '--verbose',
            '-v',
            action='store_true',
            help='Show detailed output'
        )

    def handle(self, *args, **options):
        if options['all'] or options['validate_thresholds']:
            self.test_all_solutions(options)
        elif options['problem_slug']:
            self.test_single_solution(options['problem_slug'], options)
        else:
            self.stdout.write(
                self.style.WARNING('Specify a problem slug or use --all')
            )
            self.stdout.write('\nAvailable reference solutions:')
            for slug in list_available_solutions():
                self.stdout.write(f'  - {slug}')

    def test_single_solution(self, problem_slug: str, options: dict):
        """Test a single reference solution."""
        self.stdout.write(f'\nTesting reference solution: {problem_slug}')
        self.stdout.write('-' * 50)
        
        result = run_reference_solution(problem_slug, verbose=options['verbose'])
        
        if result['status'] == 'success':
            self.stdout.write(f"Status: {self.style.SUCCESS('SUCCESS')}")
            self.stdout.write(f"Metric: {result['metric']}")
            self.stdout.write(f"Score: {result['score']:.4f}")
            self.stdout.write(f"Threshold: {result['threshold']}")
            self.stdout.write(f"Latency: {result['latency_ms']:.1f}ms")
            
            if result['meets_threshold']:
                self.stdout.write(
                    self.style.SUCCESS(f"✓ Meets threshold")
                )
            else:
                self.stdout.write(
                    self.style.ERROR(f"✗ DOES NOT meet threshold!")
                )
        else:
            self.stdout.write(
                self.style.ERROR(f"Error: {result.get('error', 'Unknown error')}")
            )

    def test_all_solutions(self, options: dict):
        """Test all available reference solutions."""
        self.stdout.write('\nReference Solution Validation Report')
        self.stdout.write('=' * 70)
        
        available = list_available_solutions()
        problems = list_problems()
        
        results = {
            'passed': [],
            'failed': [],
            'missing': [],
        }
        
        # Check each problem
        for problem in problems:
            slug = problem.slug
            
            # Check if reference solution exists
            solution_slug = slug.replace('-', '_')
            if slug not in available and solution_slug not in [s.replace('-', '_') for s in available]:
                results['missing'].append(slug)
                continue
            
            # Run the reference solution
            result = run_reference_solution(slug)
            
            if result['status'] == 'success' and result['meets_threshold']:
                results['passed'].append({
                    'slug': slug,
                    'score': result['score'],
                    'threshold': result['threshold'],
                    'metric': result['metric'],
                })
            elif result['status'] == 'success':
                results['failed'].append({
                    'slug': slug,
                    'score': result['score'],
                    'threshold': result['threshold'],
                    'metric': result['metric'],
                    'reason': 'Below threshold',
                })
            else:
                results['failed'].append({
                    'slug': slug,
                    'reason': result.get('error', 'Unknown error'),
                })
        
        # Print results
        self.stdout.write(f"\n{self.style.SUCCESS('PASSED')} ({len(results['passed'])} problems):")
        for r in results['passed']:
            self.stdout.write(
                f"  ✓ {r['slug']}: {r['score']:.4f} ({r['metric']} >= {r['threshold']})"
            )
        
        if results['failed']:
            self.stdout.write(f"\n{self.style.ERROR('FAILED')} ({len(results['failed'])} problems):")
            for r in results['failed']:
                if 'score' in r:
                    self.stdout.write(
                        f"  ✗ {r['slug']}: {r['score']:.4f} ({r['reason']})"
                    )
                else:
                    self.stdout.write(
                        f"  ✗ {r['slug']}: {r['reason']}"
                    )
        
        if results['missing']:
            self.stdout.write(f"\n{self.style.WARNING('MISSING')} ({len(results['missing'])} problems):")
            for slug in results['missing']:
                self.stdout.write(f"  ? {slug}: No reference solution file")
        
        # Summary
        self.stdout.write('\n' + '=' * 70)
        total = len(results['passed']) + len(results['failed']) + len(results['missing'])
        self.stdout.write(
            f"Summary: {len(results['passed'])}/{total} passed, "
            f"{len(results['failed'])} failed, {len(results['missing'])} missing"
        )
        
        if results['failed']:
            raise CommandError('Some reference solutions failed validation')

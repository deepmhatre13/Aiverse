"""
Grader: calls Piston API to execute user code against problem test cases.
Test cases format (stored in Problem.test_cases):
[
  {
    "input": "...",  # stdin or setup code
    "expected_output": "...",  # expected stdout
    "points": 25,  # points for this test
    "is_public": true,
  }
]
"""
import requests
import os
from decimal import Decimal

PISTON_URL = os.getenv('PISTON_API_URL', 'https://emkc.org/api/v2/piston')
PISTON_TIMEOUT = 15  # seconds


LANGUAGE_MAP = {
    'python': {'language': 'python', 'version': '3.10.0'},
    'r': {'language': 'r', 'version': '4.1.1'},
}


def run_code(code: str, language: str = 'python', stdin: str = '', timeout: int = 10) -> dict:
    """Run code via Piston API. Returns {stdout, stderr, exit_code, execution_time}."""
    lang_config = LANGUAGE_MAP.get(language, LANGUAGE_MAP['python'])
    payload = {
        'language': lang_config['language'],
        'version': lang_config['version'],
        'files': [{'content': code}],
        'stdin': stdin,
        'run_timeout': timeout * 1000,  # ms
    }
    try:
        resp = requests.post(f'{PISTON_URL}/execute', json=payload, timeout=PISTON_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        run = data.get('run', {})
        return {
            'stdout': run.get('stdout', ''),
            'stderr': run.get('stderr', ''),
            'exit_code': run.get('code', -1),
            'execution_time': run.get('cpu_time', 0),
        }
    except requests.Timeout:
        return {'stdout': '', 'stderr': 'Execution timed out', 'exit_code': -1, 'execution_time': timeout * 1000}
    except Exception as e:
        return {'stdout': '', 'stderr': str(e), 'exit_code': -1, 'execution_time': 0}


def grade_submission(code: str, language: str, test_cases: list, problem_points: int) -> dict:
    """
    Grade user code against all test cases.
    Returns:
        {
          status: 'accepted' | 'wrong_answer' | 'runtime_error' | 'time_limit_exceeded',
          score: Decimal,
          max_score: Decimal,
          test_results: [...],
          execution_time_ms: int,
          error_message: str,
        }
    """
    if not test_cases:
        # No test cases: just check code runs without error
        result = run_code(code, language)
        ok = result['exit_code'] == 0
        return {
            'status': 'accepted' if ok else 'runtime_error',
            'score': Decimal(str(problem_points)) if ok else Decimal('0'),
            'max_score': Decimal(str(problem_points)),
            'test_results': [],
            'execution_time_ms': result.get('execution_time', 0),
            'error_message': result.get('stderr', '') if not ok else '',
        }

    test_results = []
    total_points = Decimal('0')
    max_points = Decimal('0')
    total_time = 0
    overall_status = 'accepted'
    error_msg = ''

    for i, tc in enumerate(test_cases):
        points = Decimal(str(tc.get('points', problem_points // len(test_cases))))
        max_points += points
        stdin = tc.get('input', '')
        expected = (tc.get('expected_output') or '').strip()

        result = run_code(code, language, stdin=stdin)
        actual = (result.get('stdout') or '').strip()
        exec_time = result.get('execution_time', 0)
        total_time += exec_time
        exit_code = result.get('exit_code', -1)

        if exit_code != 0:
            test_status = 'runtime_error'
            if overall_status == 'accepted':
                overall_status = 'runtime_error'
                error_msg = result.get('stderr', '')[:500]
        elif expected and actual != expected:
            test_status = 'wrong_answer'
            if overall_status == 'accepted':
                overall_status = 'wrong_answer'
        else:
            test_status = 'passed'
            total_points += points

        test_results.append({
            'index': i,
            'status': test_status,
            'points_earned': float(points) if test_status == 'passed' else 0,
            'points_available': float(points),
            'is_public': tc.get('is_public', True),
            'execution_time_ms': exec_time,
            'stdout': actual[:200] if tc.get('is_public', True) else '(hidden)',
            'expected': expected[:200] if tc.get('is_public', True) else '(hidden)',
            'stderr': result.get('stderr', '')[:200],
        })

    return {
        'status': overall_status,
        'score': total_points,
        'max_score': max_points,
        'test_results': test_results,
        'execution_time_ms': int(total_time),
        'error_message': error_msg,
    }


def run_sample(code: str, language: str, test_cases: list) -> dict:
    """Quick run against public test cases only (for 'Run' button — no score saved)."""
    public_cases = [tc for tc in test_cases if tc.get('is_public', True)][:3]
    return grade_submission(code, language, public_cases, problem_points=0)

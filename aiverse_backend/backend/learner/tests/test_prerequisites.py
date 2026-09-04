"""Tests for the canonical prerequisite resolver (Phase 2).

These tests are isolated to the resolver logic (PREREQUISITE_MAP + ConceptMastery)
and only need the learner app tables, so they do not pull in the ML app
migrations.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model

from learner.models import ConceptMastery
from learner.services.prerequisites import PrerequisiteResolver, resolve_prerequisites
from learner.services.prerequisite_map import PREREQUISITE_MAP

User = get_user_model()


class PrerequisiteResolverTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="bob@example.com", username="bob", password="pw")

    def _set_mastery(self, concept_tag, score):
        return ConceptMastery.objects.update_or_create(
            user=self.user, concept_tag=concept_tag,
            defaults={'mastery_score': score},
        )[0]

    def test_foundation_concept_has_no_prerequisites(self):
        res = resolve_prerequisites(self.user.id, 'statistics')
        self.assertEqual(res['concept'], 'statistics')
        self.assertEqual(res['prerequisites'], [])
        self.assertEqual(res['recommended_next'], [])

    def test_new_user_all_prerequisites_missing(self):
        prereqs = PREREQUISITE_MAP['neural_networks']
        res = resolve_prerequisites(self.user.id, 'neural_networks')
        self.assertEqual([s['concept'] for s in res['prerequisites']], prereqs)
        self.assertTrue(all(s['readiness'] == 'unknown' for s in res['prerequisites']))
        self.assertTrue(all(s['status'] == 'unknown' for s in res['prerequisites']))
        # Weakest-first ordering of the unknown prerequisites.
        self.assertEqual(res['recommended_next'], prereqs)

    def test_all_prerequisites_satisfied(self):
        for tag in PREREQUISITE_MAP['neural_networks']:
            self._set_mastery(tag, 0.9)
        res = PrerequisiteResolver(self.user.id).resolve('neural_networks')
        self.assertTrue(all(s['status'] == 'satisfied' for s in res['prerequisites']))
        self.assertEqual(res['recommended_next'], [])
        for s in res['prerequisites']:
            self.assertAlmostEqual(s['mastery'], 0.9, places=3)

    def test_partial_then_missing_classification(self):
        for tag in PREREQUISITE_MAP['neural_networks']:
            self._set_mastery(tag, 0.9)
        self._set_mastery('gradient_descent', 0.45)  # partial
        self._set_mastery('linear_algebra', 0.1)      # missing
        res = resolve_prerequisites(self.user.id, 'neural_networks')
        by = {s['concept']: s for s in res['prerequisites']}
        self.assertEqual(by['gradient_descent']['status'], 'partial')
        self.assertEqual(by['linear_algebra']['status'], 'missing')
        self.assertEqual(by['regression']['status'], 'satisfied')
        self.assertEqual(res['recommended_next'], ['linear_algebra'])

    def test_status_thresholds_at_boundaries(self):
        # 0.75 == satisfied, 0.30 == partial, (0.29 would be missing)
        self._set_mastery('gradient_descent', 0.75)
        self._set_mastery('linear_algebra', 0.30)
        res = resolve_prerequisites(self.user.id, 'neural_networks')
        by = {s['concept']: s for s in res['prerequisites']}
        self.assertEqual(by['gradient_descent']['status'], 'satisfied')
        self.assertEqual(by['linear_algebra']['status'], 'partial')

    def test_canonical_readiness_labels_are_exposed(self):
        self._set_mastery('gradient_descent', 0.90)
        self._set_mastery('linear_algebra', 0.60)
        self._set_mastery('regression', 0.20)
        res = resolve_prerequisites(self.user.id, 'neural_networks')
        by = {s['concept']: s for s in res['prerequisites']}
        self.assertEqual(by['gradient_descent']['readiness'], 'satisfied')
        self.assertEqual(by['linear_algebra']['readiness'], 'partially_mastered')
        self.assertEqual(by['regression']['readiness'], 'missing')
        self.assertEqual(by['gradient_descent']['status'], 'satisfied')
        self.assertEqual(by['linear_algebra']['status'], 'partial')
        self.assertEqual(by['regression']['status'], 'missing')

    def test_unknown_prerequisite_when_no_mastery_record_exists(self):
        res = resolve_prerequisites(self.user.id, 'neural_networks')
        by = {s['concept']: s for s in res['prerequisites']}
        self.assertEqual(by['gradient_descent']['readiness'], 'unknown')
        self.assertEqual(by['gradient_descent']['status'], 'unknown')

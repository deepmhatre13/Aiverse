import { useLearner } from '../contexts/LearnerContext';
import { useRecommendations } from '../hooks/useRecommendations';

export default function PostActionCard({ type, score, conceptTag, passed }) {
  const { getMasteryForConcept } = useLearner();
  const { recommendations } = useRecommendations();
  const mastery = getMasteryForConcept(conceptTag);
  const nextRec = recommendations.find((r) => r.concept_tag === conceptTag);

  const conceptLabel = (conceptTag || 'this concept').replace(/_/g, ' ');

  return (
    <div className="bg-[#111] border border-[#E8392A]/20 rounded-xl p-5 mt-4">
      <div className="flex items-center gap-3 mb-3">
        <span className="text-2xl">{passed ? '🎯' : '📚'}</span>
        <div>
          <p className="font-semibold text-foreground">
            {passed ? 'Mastery updated!' : 'Keep going'}
          </p>
          <p className="text-sm text-muted-foreground">
            {conceptLabel} mastery: {Math.round(mastery * 100)}%
            {type === 'quiz' && score != null ? ` · Quiz score: ${score}%` : ''}
          </p>
        </div>
      </div>
      <div className="w-full h-1.5 bg-[#222] rounded-full mb-4">
        <div
          className="h-full bg-[#E8392A] rounded-full transition-all"
          style={{ width: `${Math.min(100, mastery * 100)}%` }}
        />
      </div>
      {nextRec && (
        <div className="flex items-center justify-between text-sm gap-4">
          <span className="text-muted-foreground">{nextRec.reason}</span>
          <button type="button" className="text-[#E8392A] font-medium hover:underline shrink-0">
            {nextRec.recommendation_type === 'prerequisite'
              ? 'Review prerequisite →'
              : nextRec.recommendation_type === 'revision'
                ? 'Revise →'
                : 'Continue →'}
          </button>
        </div>
      )}
    </div>
  );
}

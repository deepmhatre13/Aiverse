import { useNavigate } from 'react-router-dom';

const TYPE_CONFIG = {
  prerequisite: {
    color: 'text-red-400 border-red-900 bg-red-950',
    label: '⚡ Prerequisite',
  },
  revision: {
    color: 'text-amber-400 border-amber-900 bg-amber-950',
    label: '🔁 Revision',
  },
  next: {
    color: 'text-green-400 border-green-900 bg-green-950',
    label: '▶ Next',
  },
  next_lesson: {
    color: 'text-green-400 border-green-900 bg-green-950',
    label: '▶ Next',
  },
  practice: {
    color: 'text-blue-400 border-blue-900 bg-blue-950',
    label: '💻 Practice',
  },
  coding_problem: {
    color: 'text-blue-400 border-blue-900 bg-blue-950',
    label: '💻 Practice',
  },
  quiz: {
    color: 'text-purple-400 border-purple-900 bg-purple-950',
    label: '📝 Quiz',
  },
};

export default function RecommendationCard({ rec }) {
  const navigate = useNavigate();
  const config = TYPE_CONFIG[rec.recommendation_type] || TYPE_CONFIG.next;
  const score = rec.final_score ?? rec.score ?? 0;
  const explanation = rec.explanation || rec.reason || '';

  const handleClick = () => {
    if (rec.content_type === 'lesson') {
      if (rec.course_slug && rec.slug) {
        navigate(`/learn/courses/${rec.course_slug}/lessons/${rec.slug}`);
      } else {
        navigate(`/learn/lesson/${rec.content_id || rec.id}`);
      }
      return;
    }
    if (rec.content_type === 'problem' || rec.content_type === 'coding_problem') {
      navigate(`/problems/${rec.slug || rec.content_id}`);
      return;
    }
    if (rec.content_type === 'quiz') {
      navigate(`/quiz/${rec.content_id || rec.id}`);
    }
  };

  return (
    <div
      onClick={handleClick}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => e.key === 'Enter' && handleClick()}
      className="bg-[#111111] border border-[#222222] rounded-xl p-5 cursor-pointer
                 hover:border-[#E8392A]/40 hover:shadow-[0_0_16px_rgba(232,57,42,0.08)]
                 transition-all duration-200 group"
    >
      <div className="flex items-start justify-between mb-3">
        <span className={`text-xs font-medium px-2.5 py-1 rounded-full border ${config.color}`}>
          {config.label}
        </span>
        {rec.why_badge && (
          <span className="text-xs text-gray-600 opacity-0 group-hover:opacity-100 transition-opacity">
            {rec.why_badge}
          </span>
        )}
      </div>
      <p className="text-sm text-white font-medium mb-1 group-hover:text-[#E8392A] transition-colors line-clamp-2">
        {rec.title || `Content #${rec.content_id}`}
      </p>
      {(rec.concept_tag || rec.difficulty) && (
        <p className="text-xs text-gray-500 mb-2">
          {rec.concept_tag?.replace(/_/g, ' ')}
          {rec.difficulty ? ` • ${rec.difficulty}` : ''}
        </p>
      )}
      {explanation && (
        <p className="text-xs text-gray-500 italic line-clamp-2 mb-2">&ldquo;{explanation}&rdquo;</p>
      )}
      {rec.mastery_after != null && (
        <div className="flex items-center gap-2 text-xs mb-2">
          <span className="text-gray-600">Mastery after:</span>
          <span className="text-green-400 font-medium">
            {Math.round(rec.mastery_after * 100)}%
          </span>
        </div>
      )}
      <div className="mt-3 pt-3 border-t border-[#1a1a1a] flex items-center justify-between">
        <span className="text-[10px] text-gray-700">
          {rec.why_badge || (score > 0 ? `${Math.round(score * 100)}% match` : '')}
        </span>
        <span className="text-[10px] text-[#E8392A] opacity-0 group-hover:opacity-100 transition-opacity font-medium">
          Open →
        </span>
      </div>
    </div>
  );
}

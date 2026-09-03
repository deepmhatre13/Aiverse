import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getAfterProblemRecommendations } from '../api/recommendationsApi';

export default function AfterProblemPanel({ problemSlug }) {
  const navigate = useNavigate();
  const [data, setData] = useState(null);

  useEffect(() => {
    if (!problemSlug) return;
    getAfterProblemRecommendations(problemSlug)
      .then((r) => setData(r.data))
      .catch(() => setData(null));
  }, [problemSlug]);

  if (!data) return null;

  return (
    <div className="mt-6 bg-[#111] border border-[#222] rounded-2xl p-6">
      <h3 className="font-semibold text-white mb-1">What&apos;s next for you</h3>
      <p className="text-sm text-gray-400 mb-4">{data.message}</p>

      {data.related_lessons?.length > 0 && (
        <div className="mb-5">
          <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-3">
            Related lessons — strengthen this concept
          </p>
          <div className="space-y-2">
            {data.related_lessons.map((lesson) => (
              <button
                key={lesson.id}
                type="button"
                onClick={() => {
                  if (lesson.course_slug && lesson.slug) {
                    navigate(`/learn/courses/${lesson.course_slug}/lessons/${lesson.slug}`);
                  } else {
                    navigate(`/learn/lesson/${lesson.id}`);
                  }
                }}
                className="w-full text-left flex items-center gap-3 px-4 py-3 rounded-xl
                           bg-[#1a1a1a] border border-[#333]
                           hover:border-[#E8392A]/40 hover:text-[#E8392A] transition-all group"
              >
                <span className="text-[#E8392A] text-lg">📹</span>
                <div>
                  <p className="text-sm font-medium text-white group-hover:text-[#E8392A]">
                    {lesson.title}
                  </p>
                  <p className="text-xs text-gray-500">
                    {lesson.concept_tag?.replace(/_/g, ' ')} • {lesson.difficulty}
                  </p>
                </div>
                <span className="ml-auto text-xs text-gray-600 group-hover:text-[#E8392A]">
                  Open →
                </span>
              </button>
            ))}
          </div>
        </div>
      )}

      {data.next_problems?.length > 0 && (
        <div>
          <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-3">
            Next challenges
          </p>
          <div className="space-y-2">
            {data.next_problems.map((problem) => (
              <button
                key={problem.id}
                type="button"
                onClick={() => navigate(`/problems/${problem.slug}`)}
                className="w-full text-left flex items-center gap-3 px-4 py-3 rounded-xl
                           bg-[#1a1a1a] border border-[#333]
                           hover:border-[#E8392A]/40 transition-all group"
              >
                <span className="text-lg">💻</span>
                <div>
                  <p className="text-sm font-medium text-white">{problem.title}</p>
                  <p className="text-xs text-gray-500">
                    {problem.difficulty} • {problem.points} pts
                  </p>
                </div>
                <span className="ml-auto text-xs text-[#E8392A] opacity-0 group-hover:opacity-100 transition-opacity">
                  Try it →
                </span>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

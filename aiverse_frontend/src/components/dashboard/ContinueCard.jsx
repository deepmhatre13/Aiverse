import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Play } from 'lucide-react';
import { useLearner } from '../../contexts/LearnerContext';
import { getEnrollments } from '../../api/coursesApi';

export default function ContinueCard() {
  const { recommendations } = useLearner();
  const navigate = useNavigate();
  const [item, setItem] = useState(null);

  useEffect(() => {
    const nextRec = recommendations.find((r) => r.recommendation_type === 'next_lesson');
    if (nextRec) {
      setItem({ kind: 'rec', data: nextRec });
      return;
    }

    getEnrollments()
      .then((res) => {
        const enrollment = res.data?.enrollments?.find(
          (e) => e.status === 'active' && (e.completion_percentage || 0) < 100
        );
        if (enrollment) setItem({ kind: 'enrollment', data: enrollment });
      })
      .catch(() => {});
  }, [recommendations]);

  const handleContinue = () => {
    if (!item) {
      navigate('/learn');
      return;
    }
    if (item.kind === 'rec') {
      navigate(`/learn/lesson/${item.data.content_id}`);
    } else if (item.data.course?.slug) {
      navigate(`/learn/courses/${item.data.course.slug}`);
    }
  };

  const title =
    item?.kind === 'rec'
      ? item.data.reason || 'Continue your next lesson'
      : item?.data?.course?.title || 'Pick up where you left off';

  const subtitle =
    item?.kind === 'enrollment'
      ? `${item.data.completion_percentage || 0}% complete · ${item.data.lessons_completed || 0} lessons done`
      : 'Personalized based on your progress';

  return (
    <div className="bg-[#111111] border border-[#222222] rounded-xl p-6 h-full flex flex-col">
      <h3 className="text-base font-semibold mb-2 text-gray-300">Continue learning</h3>
      <p className="text-sm text-white font-medium mb-1 line-clamp-2">{title}</p>
      <p className="text-xs text-gray-500 mb-6 flex-1">{subtitle}</p>
      <button
        type="button"
        onClick={handleContinue}
        className="w-full flex items-center justify-center gap-2 bg-[#E8392A] hover:bg-[#c42d1f]
                   text-white py-2.5 rounded-lg font-medium transition-colors"
      >
        <Play className="w-4 h-4" />
        Continue →
      </button>
    </div>
  );
}

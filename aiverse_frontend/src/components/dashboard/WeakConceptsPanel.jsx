import { useNavigate } from 'react-router-dom';

const CONCEPT_LABELS = {
  gradient_descent: 'Gradient Descent',
  statistics: 'Statistics',
  neural_networks: 'Neural Networks',
  linear_algebra: 'Linear Algebra',
  python_ml: 'Python for ML',
  numpy_pandas: 'NumPy/Pandas',
  regression: 'Regression',
  classification: 'Classification',
  evaluation_metrics: 'Evaluation Metrics',
  cnn: 'CNN',
  rnn: 'RNN',
  transformers: 'Transformers',
};

export default function WeakConceptsPanel({ concepts }) {
  const navigate = useNavigate();

  return (
    <div className="bg-[#111111] border border-[#E8392A]/20 rounded-xl p-6">
      <h3 className="text-base font-semibold mb-3 flex items-center gap-2">
        <span className="text-[#E8392A]">⚠</span> Focus Areas
        <span className="text-xs text-gray-500 font-normal">
          — strengthen these to unlock harder content
        </span>
      </h3>
      <div className="flex flex-wrap gap-3">
        {concepts.map((concept) => (
          <button
            key={concept}
            type="button"
            onClick={() => navigate(`/learn?concept=${concept}`)}
            className="px-4 py-2 rounded-lg bg-[#1a1a1a] border border-[#333] text-sm text-gray-300
                       hover:border-[#E8392A]/50 hover:text-[#E8392A] transition-all"
          >
            {CONCEPT_LABELS[concept] || concept.replace(/_/g, ' ')}
          </button>
        ))}
      </div>
      <p className="text-xs text-gray-600 mt-3">
        Your AI Mentor also knows about these weak spots — ask it for help.
      </p>
    </div>
  );
}

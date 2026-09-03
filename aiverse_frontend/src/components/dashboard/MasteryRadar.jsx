import {
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  Radar,
  ResponsiveContainer,
  Tooltip,
} from 'recharts';

const CONCEPT_LABELS = {
  python_ml: 'Python',
  numpy_pandas: 'NumPy/Pandas',
  statistics: 'Statistics',
  linear_algebra: 'Lin. Algebra',
  regression: 'Regression',
  classification: 'Classification',
  evaluation_metrics: 'Eval Metrics',
  gradient_descent: 'Grad. Descent',
  neural_networks: 'Neural Nets',
  cnn: 'CNN',
  rnn: 'RNN',
  transformers: 'Transformers',
};

export default function MasteryRadar({ masteries }) {
  const data = masteries.map((m) => ({
    concept: CONCEPT_LABELS[m.concept_tag] || m.concept_tag,
    score: Math.round(m.mastery_score * 100),
    fullMark: 100,
  }));

  if (data.length === 0) {
    return (
      <div className="bg-[#111111] border border-[#222222] rounded-xl p-6 h-full flex items-center justify-center">
        <p className="text-gray-500 text-sm">Complete lessons to see your mastery scores</p>
      </div>
    );
  }

  return (
    <div className="bg-[#111111] border border-[#222222] rounded-xl p-6">
      <h3 className="text-base font-semibold mb-4 text-gray-300">Concept Mastery</h3>
      <ResponsiveContainer width="100%" height={280}>
        <RadarChart data={data}>
          <PolarGrid stroke="#222" />
          <PolarAngleAxis dataKey="concept" tick={{ fill: '#9ca3af', fontSize: 11 }} />
          <Radar
            name="Mastery"
            dataKey="score"
            stroke="#E8392A"
            fill="#E8392A"
            fillOpacity={0.15}
            strokeWidth={2}
          />
          <Tooltip
            contentStyle={{ background: '#111', border: '1px solid #333', borderRadius: 8 }}
            labelStyle={{ color: '#fff' }}
            formatter={(val) => [`${val}%`, 'Mastery']}
          />
        </RadarChart>
      </ResponsiveContainer>
      <div className="mt-4 flex flex-wrap gap-2">
        {masteries
          .filter((m) => m.is_struggling)
          .map((m) => (
            <span
              key={m.concept_tag}
              className="text-xs px-2.5 py-1 rounded-full bg-red-950 text-red-400 border border-red-900"
            >
              ⚠ {CONCEPT_LABELS[m.concept_tag] || m.concept_tag}
            </span>
          ))}
      </div>
    </div>
  );
}

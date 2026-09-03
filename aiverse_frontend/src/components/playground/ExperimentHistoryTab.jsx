import { useState, useEffect } from 'react';
import api from '../../api/axios';

export default function ExperimentHistoryTab() {
  const [experiments, setExperiments] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get('/api/learn/playground/history/')
      .then((res) => setExperiments(res.data || []))
      .catch(() => setExperiments([]))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <p className="text-muted-foreground p-8">Loading history...</p>;

  if (experiments.length === 0) {
    return (
      <div className="p-12 text-center text-muted-foreground">
        No experiments yet. Run your first experiment in the Lab tab.
      </div>
    );
  }

  return (
    <div className="p-6 overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-border text-left text-muted-foreground">
            <th className="py-3 pr-4">#</th>
            <th className="py-3 pr-4">Dataset</th>
            <th className="py-3 pr-4">Algorithm</th>
            <th className="py-3 pr-4">Score</th>
            <th className="py-3 pr-4">Date</th>
          </tr>
        </thead>
        <tbody>
          {experiments.map((exp) => (
            <tr key={exp.id} className="border-b border-border/50 hover:bg-muted/30">
              <td className="py-3 pr-4 font-mono">{exp.id}</td>
              <td className="py-3 pr-4">{exp.dataset_name || '—'}</td>
              <td className="py-3 pr-4">{exp.algorithm || exp.model_type || '—'}</td>
              <td className="py-3 pr-4">
                {exp.results?.accuracy != null
                  ? `${(exp.results.accuracy * 100).toFixed(1)}%`
                  : '—'}
              </td>
              <td className="py-3 pr-4 text-muted-foreground">
                {new Date(exp.created_at).toLocaleDateString()}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

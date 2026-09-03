import { useState, useEffect } from 'react';
import api from '../../api/axios';
import { Button } from '../ui/button';

export default function GuidedExperimentsTab() {
  const [guided, setGuided] = useState(null);
  const [stepIndex, setStepIndex] = useState(0);

  useEffect(() => {
    api.get('/api/learn/playground/guided/')
      .then((res) => setGuided(res.data))
      .catch(() => setGuided(null));
  }, []);

  if (!guided) {
    return <p className="text-muted-foreground p-8">Loading personalised experiment...</p>;
  }

  const step = guided.steps?.[stepIndex];

  return (
    <div className="p-8 max-w-2xl mx-auto">
      <h2 className="text-xl font-semibold text-foreground mb-2">{guided.title}</h2>
      <p className="text-muted-foreground mb-8">{guided.description}</p>

      {step && (
        <div className="border border-border rounded-xl p-6 bg-card mb-6">
          <p className="text-sm text-muted-foreground mb-2">
            Step {stepIndex + 1} of {guided.steps.length}
          </p>
          <p className="text-foreground mb-4">{step.instruction}</p>
          <pre className="text-xs bg-muted p-4 rounded-lg overflow-x-auto">
            {JSON.stringify(step.config, null, 2)}
          </pre>
        </div>
      )}

      <div className="flex gap-3">
        <Button
          variant="outline"
          disabled={stepIndex === 0}
          onClick={() => setStepIndex((i) => i - 1)}
        >
          Previous
        </Button>
        <Button
          className="btn-wine"
          disabled={stepIndex >= (guided.steps?.length || 1) - 1}
          onClick={() => setStepIndex((i) => i + 1)}
        >
          Next step
        </Button>
      </div>
    </div>
  );
}

import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Cpu, ChevronLeft, Loader2, Zap } from 'lucide-react';
import Layout from '../components/Layout';
import { playgroundAPI } from '../api/playground';
import { toast } from 'sonner';
import {
  LabStepper,
  DatasetCard,
  LabContentPanel,
  LabContentTransition,
  PlaygroundParticleGrid,
} from '../components/playground';
import { GlowButton } from '@/design-system';

const STEP_ORDER = ['dataset', 'model', 'hyperparams', 'train'];

function ModelCard({ option, isSelected, onClick, className }) {
  return (
    <motion.button
      type="button"
      onClick={onClick}
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ y: -3 }}
      whileTap={{ scale: 0.98 }}
      className={`
        relative w-full p-5 rounded-xl text-left
        border-2 backdrop-blur-xl transition-all duration-200
        focus:outline-none focus-visible:ring-2 focus-visible:ring-primary/50
        ${isSelected
          ? 'border-primary bg-primary/10 shadow-[0_0_24px_rgba(225,6,0,0.18)]'
          : 'border-foreground/10 bg-foreground/[0.03] hover:border-primary/40 hover:shadow-[0_0_20px_rgba(225,6,0,0.1)]'
        }
        ${className}
      `}
    >
      <div className="flex items-center gap-3">
        <div className="p-2 rounded-lg bg-primary/10">
          <Cpu className="w-5 h-5 text-primary" />
        </div>
        <div>
          <div className="font-semibold text-foreground">{option?.label ?? option?.name}</div>
          {option?.description && (
            <div className="text-xs text-muted-foreground mt-0.5">{option.description}</div>
          )}
        </div>
      </div>
    </motion.button>
  );
}

function InitialState({ onStart }) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 flex flex-col items-center justify-center z-10"
    >
      <motion.div
        animate={{ y: [0, -8, 0] }}
        transition={{ duration: 2.5, repeat: Infinity, ease: 'easeInOut' }}
        className="text-center"
      >
        <div className="text-4xl md:text-5xl font-light text-foreground mb-3">
          ML Training Lab
        </div>
        <div className="text-sm text-muted-foreground mb-10">
          Create an experiment • Enter the training chamber
        </div>
        <GlowButton
          onClick={onStart}
          size="lg"
          className="px-8 py-3 h-auto"
        >
          Initiate <Zap className="w-4 h-4 ml-2 inline" />
        </GlowButton>
      </motion.div>
    </motion.div>
  );
}

function ConfigurationPhase({ config, onConfigChange, onLaunch, isLaunching, options }) {
  const [currentStep, setCurrentStep] = useState('dataset');
  const [direction, setDirection] = useState(0);

  const datasetOptions = options?.datasets || [];
  const modelOptions = options?.models || [];
  const compatibility = options?.compatibility || {};
  const selectedDataset = datasetOptions.find((d) => d.id === config.dataset);
  const compatibleModelIds = selectedDataset ? (compatibility[config.dataset] || []) : [];
  const compatibleModels = modelOptions.filter((m) => compatibleModelIds.includes(m.id));

  const goTo = (step) => {
    const from = STEP_ORDER.indexOf(currentStep);
    const to = STEP_ORDER.indexOf(step);
    setDirection(to > from ? 1 : -1);
    setCurrentStep(step);
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="min-h-screen flex relative z-10"
    >
      <div className="w-full max-w-6xl mx-auto flex gap-8 lg:gap-12 p-6 lg:p-10">
        {/* Left: Stepper */}
        <aside className="w-44 shrink-0 pt-2">
          <LabStepper
            currentStep={currentStep}
            onStepClick={goTo}
            stepsOrder={STEP_ORDER.map((k) => ({
              key: k,
              label: k === 'dataset' ? 'Dataset' : k === 'model' ? 'Model' : k === 'hyperparams' ? 'Hyperparameters' : 'Train',
              short: STEP_ORDER.indexOf(k) + 1,
            }))}
          />
        </aside>

        {/* Right: Content */}
        <main className="flex-1 min-w-0">
          <LabContentPanel>
            <LabContentTransition stepKey={currentStep} direction={direction}>
              {currentStep === 'dataset' && (
                <div>
                  <h2 className="text-xl font-semibold text-foreground mb-1">Dataset</h2>
                  <p className="text-sm text-muted-foreground mb-6">
                    Select a dataset for your experiment
                  </p>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {datasetOptions.map((d) => (
                      <DatasetCard
                        key={d.id}
                        option={{ label: d.name, description: d.description, ...d }}
                        isSelected={config.dataset === d.id}
                        onClick={() => onConfigChange('dataset', d.id)}
                        taskType={d.task_type || 'classification'}
                        numFeatures={d.num_features}
                        numSamples={d.num_samples}
                      />
                    ))}
                  </div>
                  {datasetOptions.length > 0 && (
                    <div className="mt-6 flex justify-end">
                      <GlowButton
                        variant="secondary"
                        onClick={() => goTo('model')}
                        disabled={!config.dataset}
                        className="text-sm"
                      >
                        Next: Model →
                      </GlowButton>
                    </div>
                  )}
                </div>
              )}

              {currentStep === 'model' && (
                <div>
                  <h2 className="text-xl font-semibold text-foreground mb-1">Model</h2>
                  <p className="text-sm text-muted-foreground mb-6">
                    Choose model architecture
                  </p>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {compatibleModels.map((m) => (
                      <ModelCard
                        key={m.id}
                        option={m}
                        isSelected={config.model === m.id}
                        onClick={() => {
                          onConfigChange('model', m.id);
                          goTo('hyperparams');
                        }}
                      />
                    ))}
                  </div>
                  <div className="mt-6 flex justify-between">
                    <button
                      type="button"
                      onClick={() => goTo('dataset')}
                      className="text-sm text-muted-foreground hover:text-foreground flex items-center gap-1"
                    >
                      <ChevronLeft className="w-4 h-4" /> Back
                    </button>
                    <GlowButton
                      variant="secondary"
                      onClick={() => goTo('hyperparams')}
                      disabled={!config.model}
                      className="text-sm"
                    >
                      Next: Hyperparameters →
                    </GlowButton>
                  </div>
                </div>
              )}

              {currentStep === 'hyperparams' && (
                <HyperparamsForm
                  config={config}
                  onConfigChange={onConfigChange}
                  options={options}
                  onBack={() => goTo('model')}
                  onNext={() => goTo('train')}
                />
              )}

              {currentStep === 'train' && (
                <div className="text-center py-8">
                  <p className="text-muted-foreground mb-4">Ready to launch training</p>
                  <GlowButton onClick={onLaunch} disabled={isLaunching} size="lg">
                    {isLaunching ? (
                      <>
                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                        Launching...
                      </>
                    ) : (
                      'Launch Training'
                    )}
                  </GlowButton>
                </div>
              )}
            </LabContentTransition>
          </LabContentPanel>
        </main>
      </div>
    </motion.div>
  );
}

function HyperparamsForm({ config, onConfigChange, options, onBack, onNext }) {
  const selectedModel = options?.models?.find((m) => m.id === config.model);
  const modelHyperparams = selectedModel?.hyperparameters || {};

  return (
    <div>
      <h2 className="text-xl font-semibold text-foreground mb-1">Hyperparameters</h2>
      <p className="text-sm text-muted-foreground mb-6">
        Fine-tune training behavior
      </p>

      <div className="space-y-6">
        {'learning_rate' in modelHyperparams && (
          <div>
            <label className="block text-sm font-medium text-foreground mb-2">
              Learning Rate
            </label>
            <input
              type="range"
              min={0.0001}
              max={0.1}
              step={0.001}
              value={config.learning_rate}
              onChange={(e) => onConfigChange('learning_rate', parseFloat(e.target.value))}
              className="w-full h-2 rounded-full appearance-none bg-foreground/10 accent-primary"
            />
            <div className="flex justify-between text-xs text-muted-foreground mt-1">
              <span>0.0001</span>
              <span className="font-mono text-primary">{config.learning_rate?.toFixed(4)}</span>
              <span>0.1</span>
            </div>
          </div>
        )}

        {'epochs' in modelHyperparams && (
          <div>
            <label className="block text-sm font-medium text-foreground mb-2">Epochs</label>
            <div className="flex gap-2 flex-wrap">
              {[10, 50, 100, 250, 500].map((n) => (
                <button
                  key={n}
                  type="button"
                  onClick={() => onConfigChange('epochs', n)}
                  className={`
                    px-4 py-2 rounded-lg text-sm font-medium transition-all
                    ${config.epochs === n
                      ? 'bg-primary/20 border border-primary text-primary'
                      : 'bg-foreground/5 border border-foreground/10 text-muted-foreground hover:border-primary/30'
                    }
                  `}
                >
                  {n}
                </button>
              ))}
            </div>
          </div>
        )}

        {'hidden_units' in modelHyperparams && (
          <div>
            <label className="block text-sm font-medium text-foreground mb-2">Hidden Units</label>
            <div className="flex gap-2 flex-wrap">
              {[16, 32, 64, 128, 256].map((n) => (
                <button
                  key={n}
                  type="button"
                  onClick={() => onConfigChange('hidden_units', n)}
                  className={`
                    px-4 py-2 rounded-lg text-sm font-medium transition-all
                    ${config.hidden_units === n
                      ? 'bg-primary/20 border border-primary text-primary'
                      : 'bg-foreground/5 border border-foreground/10 text-muted-foreground hover:border-primary/30'
                    }
                  `}
                >
                  {n}
                </button>
              ))}
            </div>
          </div>
        )}

        {'batch_size' in modelHyperparams && (
          <div>
            <label className="block text-sm font-medium text-foreground mb-2">Batch Size</label>
            <div className="flex gap-2 flex-wrap">
              {[16, 32, 64, 128].map((n) => (
                <button
                  key={n}
                  type="button"
                  onClick={() => onConfigChange('batch_size', n)}
                  className={`
                    px-4 py-2 rounded-lg text-sm font-medium transition-all
                    ${config.batch_size === n
                      ? 'bg-primary/20 border border-primary text-primary'
                      : 'bg-foreground/5 border border-foreground/10 text-muted-foreground hover:border-primary/30'
                    }
                  `}
                >
                  {n}
                </button>
              ))}
            </div>
          </div>
        )}

        {config.model === 'neural_network' && (
          <div className="p-4 rounded-lg border border-primary/20 bg-primary/5">
            <label className="block text-sm font-medium text-foreground mb-2">Batch Size</label>
            <div className="flex gap-2 flex-wrap">
              {[16, 32, 64, 128, 256].map((n) => (
                <button
                  key={n}
                  type="button"
                  onClick={() => onConfigChange('batch_size', n)}
                  className={`
                    px-3 py-1.5 rounded text-sm font-medium
                    ${config.batch_size === n
                      ? 'bg-primary/20 border border-primary text-primary'
                      : 'bg-foreground/5 border border-foreground/10 text-muted-foreground hover:border-primary/30'
                    }
                  `}
                >
                  {n}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>

      <div className="mt-8 flex justify-between">
        <button
          type="button"
          onClick={onBack}
          className="text-sm text-muted-foreground hover:text-foreground flex items-center gap-1"
        >
          <ChevronLeft className="w-4 h-4" /> Back
        </button>
        <GlowButton
          variant="secondary"
          onClick={onNext}
          className="text-sm"
        >
          Next: Train →
        </GlowButton>
      </div>
    </div>
  );
}

function TrainingVisualization({ job, metrics }) {
  if (!job || job.status !== 'training') return null;

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="min-h-screen flex flex-col items-center justify-center relative z-10"
    >
      <div className="max-w-4xl w-full px-6">
        <motion.div
          animate={{ y: [0, -4, 0] }}
          transition={{ duration: 2, repeat: Infinity }}
          className="text-center mb-12"
        >
          <div className="text-3xl md:text-4xl font-light text-foreground mb-2">
            Training
          </div>
          <div className="flex items-center justify-center gap-2 text-sm text-muted-foreground">
            <motion.div
              animate={{ scale: [1, 1.2, 1] }}
              transition={{ duration: 1, repeat: Infinity }}
              className="w-2 h-2 rounded-full bg-blue-400"
            />
            {job.dataset_type} → {job.model_type?.replace('_', ' ')}
          </div>
        </motion.div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-10">
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="p-6 rounded-xl border border-cyan-500/20 bg-cyan-500/5 backdrop-blur"
          >
            <div className="text-sm font-medium text-muted-foreground mb-4">Loss</div>
            {metrics.length > 0 && (
              <div className="text-3xl font-light text-cyan-400">
                {metrics[metrics.length - 1].loss?.toFixed(4)}
              </div>
            )}
            <div className="mt-4 h-14 flex items-end gap-1">
              {metrics.slice(-20).map((m, i) => {
                const maxL = Math.max(...metrics.map((x) => x.loss), 0.01);
                const h = (m.loss / maxL) * 100;
                return (
                  <motion.div
                    key={i}
                    initial={{ height: 0 }}
                    animate={{ height: `${h}%` }}
                    className="flex-1 bg-cyan-500/60 rounded-t min-h-[4px]"
                  />
                );
              })}
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.05 }}
            className="p-6 rounded-xl border border-emerald-500/20 bg-emerald-500/5 backdrop-blur"
          >
            <div className="text-sm font-medium text-muted-foreground mb-4">Accuracy</div>
            {metrics.length > 0 && (
              <div className="text-3xl font-light text-emerald-400">
                {((metrics[metrics.length - 1].accuracy || 0) * 100).toFixed(2)}%
              </div>
            )}
            <div className="mt-4 h-14 flex items-end gap-1">
              {metrics.slice(-20).map((m, i) => {
                const h = (m.accuracy || 0) * 100;
                return (
                  <motion.div
                    key={i}
                    initial={{ height: 0 }}
                    animate={{ height: `${h}%` }}
                    className="flex-1 bg-emerald-500/60 rounded-t min-h-[4px]"
                  />
                );
              })}
            </div>
          </motion.div>
        </div>

        <div className="text-center">
          <div className="text-sm text-muted-foreground mb-3">Epoch {metrics.length}</div>
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
            className="w-10 h-10 border-2 border-blue-500/30 border-t-blue-400 rounded-full mx-auto"
          />
        </div>
      </div>
    </motion.div>
  );
}

function CompletionScreen({ job, metrics }) {
  const isSuccess = job.status === 'completed';

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="min-h-screen flex flex-col items-center justify-center relative z-10"
    >
      <div className="max-w-2xl w-full px-6">
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ type: 'spring', damping: 15 }}
          className="text-center mb-8"
        >
          {isSuccess ? (
            <motion.div
              className="w-20 h-20 rounded-full bg-emerald-500/10 border-2 border-emerald-500/30 flex items-center justify-center mx-auto mb-4"
              animate={{ boxShadow: ['0 0 0px rgba(16,185,129,0)', '0 0 30px rgba(16,185,129,0.2)', '0 0 0px rgba(16,185,129,0)'] }}
              transition={{ duration: 3, repeat: Infinity }}
            >
              <svg className="w-10 h-10 text-emerald-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                <motion.path
                  strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7"
                  initial={{ pathLength: 0 }} animate={{ pathLength: 1 }}
                  transition={{ duration: 0.6, delay: 0.3 }}
                />
              </svg>
            </motion.div>
          ) : (
            <div className="text-6xl mb-4">⚠</div>
          )}
        </motion.div>

        <div className="text-center mb-8">
          <div className={`text-3xl font-light mb-2 ${isSuccess ? 'text-emerald-400' : 'text-foreground'}`}>
            {isSuccess ? 'Training Complete' : 'Training Failed'}
          </div>
          <span
            className={`
              inline-block px-4 py-2 rounded-lg text-sm font-medium
              ${isSuccess
                ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30'
                : 'bg-destructive/20 text-destructive border border-destructive/30'
              }
            `}
          >
            {job.status}
          </span>
        </div>

        {isSuccess && job.final_accuracy != null && (
          <div className="grid grid-cols-2 gap-4 mb-8">
            <motion.div
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.4 }}
              className="p-6 rounded-xl border border-emerald-500/20 bg-emerald-500/5 hover:bg-emerald-500/8 transition-colors"
            >
              <div className="text-xs uppercase tracking-wider text-muted-foreground mb-2">
                Accuracy
              </div>
              <div className="text-2xl font-light text-emerald-400">
                {(job.final_accuracy * 100).toFixed(2)}%
              </div>
            </motion.div>
            <motion.div
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.5 }}
              className="p-6 rounded-xl border border-emerald-500/20 bg-emerald-500/5 hover:bg-emerald-500/8 transition-colors"
            >
              <div className="text-xs uppercase tracking-wider text-muted-foreground mb-2">
                Final Loss
              </div>
              <div className="text-2xl font-light text-emerald-400">
                {job.final_loss?.toFixed(4) ?? '—'}
              </div>
            </motion.div>
          </div>
        )}

        {job.status === 'failed' && job.error_message && (
          <div className="mb-8 p-4 rounded-xl border border-destructive/30 bg-destructive/5">
            <div className="text-sm font-medium text-destructive mb-2">Error</div>
            <pre className="text-xs text-muted-foreground font-mono overflow-x-auto max-h-32">
              {job.error_message}
            </pre>
          </div>
        )}

        <div className="flex justify-center">
          <GlowButton onClick={() => window.location.reload()} size="lg">
            New Experiment
          </GlowButton>
        </div>
      </div>
    </motion.div>
  );
}

export default function Playground() {
  const [phase, setPhase] = useState('initial');
  const [config, setConfig] = useState({
    dataset: null,
    model: null,
    learning_rate: 0.01,
    epochs: 50,
    batch_size: 32,
    hidden_units: 64,
  });
  const [options, setOptions] = useState(null);
  const [optionsLoading, setOptionsLoading] = useState(true);
  const [currentJob, setCurrentJob] = useState(null);
  const [metrics, setMetrics] = useState([]);
  const [isLaunching, setIsLaunching] = useState(false);
  const pollingRef = useRef(null);
  const pollCountRef = useRef(0);
  const MAX_POLLS = 300;

  useEffect(() => {
    const fetchOptions = async () => {
      try {
        setOptionsLoading(true);
        const data = await playgroundAPI.getOptions();
        setOptions(data);
        if (data?.datasets?.length > 0) {
          const first = data.datasets[0];
          setConfig((prev) => ({
            ...prev,
            dataset: first.id,
            model: data.compatibility?.[first.id]?.[0] ?? null,
          }));
        }
      } catch (err) {
        console.error('[Playground] Failed to fetch options:', err);
        toast.error('Failed to load options');
      } finally {
        setOptionsLoading(false);
      }
    };
    fetchOptions();
  }, []);

  const handleConfigChange = (key, value) => {
    setConfig((prev) => {
      const next = { ...prev, [key]: value };
      if (key === 'dataset' && options) {
        const comp = options.compatibility?.[value] || [];
        next.model = comp[0] ?? null;
      }
      return next;
    });
  };

  const handleLaunch = async () => {
    setIsLaunching(true);
    pollCountRef.current = 0;
    try {
      const payload = {
        dataset_type: config.dataset,
        model_type: config.model,
        learning_rate: config.learning_rate,
        epochs: config.epochs,
      };
      const selectedModel = options?.models?.find((m) => m.id === config.model);
      if (selectedModel?.hyperparameters) {
        if ('batch_size' in selectedModel.hyperparameters) payload.batch_size = config.batch_size;
        if ('hidden_units' in selectedModel.hyperparameters) payload.hidden_units = config.hidden_units;
      }

      const job = await playgroundAPI.createJob(payload);
      if (!job?.id) {
        toast.error('Failed to create job');
        setIsLaunching(false);
        return;
      }

      setCurrentJob(job);
      setPhase('training');
      setMetrics([]);

      pollingRef.current = setInterval(async () => {
        pollCountRef.current++;
        if (pollCountRef.current > MAX_POLLS) {
          clearInterval(pollingRef.current);
          toast.error('Training timeout');
          return;
        }
        try {
          const updated = await playgroundAPI.getJobStatus(job.id);
          setCurrentJob(updated);
          const m = await playgroundAPI.getMetrics(job.id);
          if (Array.isArray(m)) setMetrics(m);
          if (updated.status === 'completed' || updated.status === 'failed') {
            clearInterval(pollingRef.current);
            toast[updated.status === 'completed' ? 'success' : 'error'](
              updated.status === 'completed' ? 'Training completed' : updated.error_message || 'Training failed'
            );
          }
        } catch {
          toast.error('Error checking status');
        }
      }, 2000);
    } catch (err) {
      console.error('[Playground] Launch error:', err);
      const errData = err.response?.data;
      toast.error(errData?.error || errData?.fields ? 'Invalid configuration' : 'Failed to launch training');
    } finally {
      setIsLaunching(false);
    }
  };

  useEffect(
    () => () => {
      if (pollingRef.current) clearInterval(pollingRef.current);
    },
    []
  );

  if (optionsLoading) {
    return (
      <Layout>
        <div className="min-h-screen bg-background flex items-center justify-center">
          <div className="text-center">
            <Loader2 className="w-10 h-10 animate-spin text-primary mx-auto mb-3" />
            <div className="text-sm text-muted-foreground">Loading lab...</div>
          </div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="min-h-screen bg-background">
        <div className="hidden dark:block"><PlaygroundParticleGrid /></div>
        <div
          className="fixed inset-0 pointer-events-none z-[1] hidden dark:block"
          style={{
            background: 'radial-gradient(ellipse 100% 60% at 50% 0%, rgba(225,6,0,0.04) 0%, transparent 50%)',
          }}
        />

        <AnimatePresence mode="wait">
          {phase === 'initial' && (
            <InitialState key="initial" onStart={() => setPhase('config')} />
          )}
          {phase === 'config' && (
            <ConfigurationPhase
              key="config"
              config={config}
              onConfigChange={handleConfigChange}
              onLaunch={handleLaunch}
              isLaunching={isLaunching}
              options={options}
            />
          )}
          {phase === 'training' && currentJob && (
            currentJob.status === 'training' ? (
              <TrainingVisualization key="training" job={currentJob} metrics={metrics} />
            ) : (
              <CompletionScreen key="done" job={currentJob} metrics={metrics} />
            )
          )}
        </AnimatePresence>
      </div>
    </Layout>
  );
}

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { useLearner } from '../contexts/LearnerContext';
import { submitOnboarding } from '../api/learnerApi';
import api from '../api/axios';

const STEPS = [
  {
    id: 'knowledge',
    title: 'Quick knowledge check',
    subtitle: 'Help us personalize your learning path',
    questions: [
      { id: 'python', label: 'Python programming' },
      { id: 'statistics', label: 'Statistics & probability' },
      { id: 'linear_algebra', label: 'Linear algebra' },
      { id: 'ml_basics', label: 'Machine learning basics' },
    ],
    options: ['Never heard', 'Heard of it', 'Used it', 'Comfortable'],
  },
  {
    id: 'goal',
    title: "What's your goal?",
    subtitle: "We'll shape your path around this",
    choices: [
      { id: 'theory', label: 'Understand ML theory deeply', icon: '🧠' },
      { id: 'projects', label: 'Build real ML projects', icon: '🔨' },
      { id: 'interview', label: 'Prepare for ML interviews', icon: '💼' },
      { id: 'career', label: 'Switch into Data Science / MLE', icon: '🚀' },
    ],
  },
  {
    id: 'time',
    title: 'How much time can you commit?',
    subtitle: 'Be honest — consistency matters more than intensity',
    choices: [
      { id: 'light', label: '15 min / day', sub: 'Light — great for reviewing concepts' },
      { id: 'steady', label: '30 min / day', sub: 'Steady — solid progress pace' },
      { id: 'serious', label: '1 hour / day', sub: 'Serious — fast-track your skills' },
      { id: 'intense', label: '2+ hours / day', sub: 'Intense — full-time learning' },
    ],
  },
];

export default function Onboarding() {
  const [step, setStep] = useState(0);
  const [answers, setAnswers] = useState({});
  const [submitting, setSubmitting] = useState(false);
  const [particles, setParticles] = useState([]);
  const navigate = useNavigate();
  const { refetch } = useLearner();

  const currentStep = STEPS[step];
  const progress = ((step + 1) / STEPS.length) * 100;

  const handleKnowledgeAnswer = (questionId, optionIdx) => {
    setAnswers((prev) => ({
      ...prev,
      knowledge: { ...prev.knowledge, [questionId]: optionIdx },
    }));
  };

  const handleChoice = (field, value) => {
    setAnswers((prev) => ({ ...prev, [field]: value }));
  };

  const handleSubmit = async () => {
    setParticles(
      Array.from({ length: 20 }, (_, i) => ({
        id: i,
        x: Math.random() * 400 - 200,
        y: Math.random() * -300,
        rotate: Math.random() * 360,
        color: ['#E8392A', '#f97316', '#eab308'][i % 3],
      }))
    );
    setSubmitting(true);
    try {
      await submitOnboarding(answers).catch(() => null);
      await api.post('/api/learner/seed-mastery/', { knowledge: answers.knowledge || {} });
      await refetch();
      setTimeout(() => navigate('/dashboard'), 800);
    } catch {
      navigate('/dashboard');
    }
  };

  const handleNext = () => {
    if (step < STEPS.length - 1) {
      setStep((s) => s + 1);
    } else {
      handleSubmit();
    }
  };

  return (
    <div className="min-h-screen bg-[#0a0a0a] text-white flex flex-col items-center justify-center px-6 py-12">
      <div className="w-full max-w-lg mb-8">
        <div className="flex justify-between text-sm text-gray-500 mb-2">
          <span>
            Step {step + 1} of {STEPS.length}
          </span>
          <button
            type="button"
            onClick={() => navigate('/dashboard')}
            className="text-gray-600 hover:text-gray-400 transition-colors text-xs"
          >
            Skip for now
          </button>
        </div>
        <div className="w-full h-1 bg-[#222] rounded-full overflow-hidden">
          <motion.div
            animate={{ width: `${progress}%` }}
            transition={{ duration: 0.4, ease: 'easeOut' }}
            className="h-full bg-[#E8392A] rounded-full"
          />
        </div>
      </div>

      <div className="w-full max-w-lg">
        <h2 className="text-2xl font-bold mb-2">{currentStep.title}</h2>
        <p className="text-gray-400 mb-8">{currentStep.subtitle}</p>

        <AnimatePresence mode="wait">
          <motion.div
            key={step}
            initial={{ opacity: 0, x: 40 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -40 }}
            transition={{ duration: 0.3 }}
          >
            {currentStep.id === 'knowledge' && (
              <div className="space-y-6">
                {currentStep.questions.map((q) => (
                  <div key={q.id}>
                    <p className="text-sm font-medium text-gray-300 mb-3">{q.label}</p>
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                      {currentStep.options.map((opt, idx) => {
                        const selected = answers.knowledge?.[q.id] === idx;
                        return (
                          <motion.button
                            key={idx}
                            type="button"
                            whileTap={{ scale: 0.94 }}
                            whileHover={{ scale: 1.02 }}
                            onClick={() => handleKnowledgeAnswer(q.id, idx)}
                            className={`py-2.5 px-3 rounded-lg border text-xs font-medium transition-all ${
                              selected
                                ? 'border-[#E8392A] bg-[#E8392A]/10 text-[#E8392A] ring-2 ring-[#E8392A]'
                                : 'border-[#333] bg-[#111] text-gray-400 hover:border-[#444] hover:text-white'
                            }`}
                          >
                            {opt}
                          </motion.button>
                        );
                      })}
                    </div>
                  </div>
                ))}
              </div>
            )}

            {(currentStep.id === 'goal' || currentStep.id === 'time') && (
              <div className="space-y-3">
                {currentStep.choices.map((choice) => {
                  const selected = answers[currentStep.id] === choice.id;
                  return (
                    <motion.button
                      key={choice.id}
                      type="button"
                      whileTap={{ scale: 0.98 }}
                      onClick={() => handleChoice(currentStep.id, choice.id)}
                      className={`w-full text-left px-5 py-4 rounded-xl border transition-all ${
                        selected
                          ? 'border-[#E8392A] bg-[#E8392A]/10'
                          : 'border-[#333] bg-[#111] hover:border-[#444]'
                      }`}
                    >
                      <div className="flex items-center gap-3">
                        {choice.icon && <span className="text-xl">{choice.icon}</span>}
                        <div>
                          <p className={`font-medium ${selected ? 'text-white' : 'text-gray-300'}`}>
                            {choice.label}
                          </p>
                          {choice.sub && (
                            <p className="text-xs text-gray-500 mt-0.5">{choice.sub}</p>
                          )}
                        </div>
                      </div>
                    </motion.button>
                  );
                })}
              </div>
            )}
          </motion.div>
        </AnimatePresence>

        <button
          type="button"
          onClick={handleNext}
          disabled={submitting}
          className="w-full mt-8 bg-[#E8392A] hover:bg-[#c42d1f] disabled:opacity-50 text-white py-3.5 rounded-xl font-medium transition-colors"
        >
          {submitting
            ? 'Setting up your path...'
            : step === STEPS.length - 1
              ? 'Build my learning path →'
              : 'Continue →'}
        </button>
      </div>

      <div className="fixed inset-0 pointer-events-none z-50 flex items-center justify-center">
        {particles.map((p) => (
          <motion.div
            key={p.id}
            initial={{ opacity: 1, x: 0, y: 0, scale: 1, rotate: 0 }}
            animate={{ opacity: 0, x: p.x, y: p.y, scale: 0.3, rotate: p.rotate }}
            transition={{ duration: 0.9, ease: 'easeOut' }}
            className="absolute w-2 h-2 rounded-full"
            style={{ backgroundColor: p.color }}
          />
        ))}
      </div>
    </div>
  );
}

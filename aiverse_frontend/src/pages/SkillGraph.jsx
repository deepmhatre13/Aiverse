import { useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import Layout from '../components/Layout';
import { useLearner } from '../contexts/LearnerContext';

const GRAPH_DATA = {
  nodes: [
    { id: 'python_ml', label: 'Python for ML', group: 'foundations' },
    { id: 'numpy_pandas', label: 'NumPy/Pandas', group: 'foundations' },
    { id: 'statistics', label: 'Statistics', group: 'foundations' },
    { id: 'linear_algebra', label: 'Linear Algebra', group: 'foundations' },
    { id: 'regression', label: 'Regression', group: 'core' },
    { id: 'classification', label: 'Classification', group: 'core' },
    { id: 'evaluation_metrics', label: 'Eval Metrics', group: 'core' },
    { id: 'gradient_descent', label: 'Gradient Descent', group: 'core' },
    { id: 'regularization', label: 'Regularization', group: 'core' },
    { id: 'feature_engineering', label: 'Feature Eng.', group: 'core' },
    { id: 'ensemble_learning', label: 'Ensemble Learning', group: 'advanced' },
    { id: 'svm', label: 'SVM', group: 'advanced' },
    { id: 'clustering', label: 'Clustering', group: 'advanced' },
    { id: 'pca', label: 'PCA', group: 'advanced' },
    { id: 'neural_networks', label: 'Neural Networks', group: 'deep' },
    { id: 'backpropagation', label: 'Backpropagation', group: 'deep' },
    { id: 'cnn', label: 'CNN', group: 'deep' },
    { id: 'rnn', label: 'RNN', group: 'deep' },
    { id: 'transformers', label: 'Transformers', group: 'deep' },
  ],
  links: [
    { source: 'python_ml', target: 'numpy_pandas' },
    { source: 'statistics', target: 'regression' },
    { source: 'statistics', target: 'gradient_descent' },
    { source: 'linear_algebra', target: 'regression' },
    { source: 'linear_algebra', target: 'pca' },
    { source: 'linear_algebra', target: 'svm' },
    { source: 'regression', target: 'classification' },
    { source: 'gradient_descent', target: 'neural_networks' },
    { source: 'gradient_descent', target: 'regression' },
    { source: 'classification', target: 'ensemble_learning' },
    { source: 'neural_networks', target: 'backpropagation' },
    { source: 'neural_networks', target: 'cnn' },
    { source: 'neural_networks', target: 'rnn' },
    { source: 'rnn', target: 'transformers' },
    { source: 'linear_algebra', target: 'neural_networks' },
  ],
};

const GROUP_LAYERS = {
  foundations: { y: 70, color: '#3b82f6' },
  core: { y: 190, color: '#f59e0b' },
  advanced: { y: 310, color: '#8b5cf6' },
  deep: { y: 430, color: '#E8392A' },
};

const SVG_W = 900;
const SVG_H = 520;

function layoutNodes(nodes) {
  const byGroup = {};
  nodes.forEach((n) => {
    if (!byGroup[n.group]) byGroup[n.group] = [];
    byGroup[n.group].push(n);
  });

  const positioned = {};
  Object.entries(byGroup).forEach(([group, groupNodes]) => {
    const layer = GROUP_LAYERS[group];
    const step = SVG_W / (groupNodes.length + 1);
    groupNodes.forEach((node, i) => {
      positioned[node.id] = { x: step * (i + 1), y: layer.y, ...node };
    });
  });
  return positioned;
}

export default function SkillGraph() {
  const { getMasteryForConcept } = useLearner();
  const navigate = useNavigate();
  const [hoveredId, setHoveredId] = useState(null);

  const nodeMap = useMemo(() => layoutNodes(GRAPH_DATA.nodes), []);

  const getFill = (id) => {
    const m = getMasteryForConcept(id);
    if (m === 0) return '#2a2a2a';
    if (m < 0.35) return '#7f1d1d';
    if (m < 0.65) return '#78350f';
    return '#14532d';
  };

  const getStroke = (id) => {
    const m = getMasteryForConcept(id);
    if (m === 0) return '#444';
    if (m < 0.35) return '#E8392A';
    if (m < 0.65) return '#f59e0b';
    return '#22c55e';
  };

  const hoveredNode = hoveredId ? nodeMap[hoveredId] : null;

  return (
    <Layout>
      <div className="min-h-screen bg-[#0a0a0a] text-white">
        <div className="max-w-7xl mx-auto px-6 py-10">
          <div className="mb-8">
            <h1 className="text-3xl font-bold mb-2">Skill Graph</h1>
            <p className="text-gray-400">
              Fixed curriculum DAG — your ML knowledge map. Click any concept to start learning.
            </p>
          </div>

          <div className="flex flex-wrap gap-4 mb-6 text-sm">
            {[
              { color: '#444', label: 'Not started' },
              { color: '#E8392A', label: 'Struggling (< 35%)' },
              { color: '#f59e0b', label: 'Developing (35–65%)' },
              { color: '#22c55e', label: 'Mastered (> 65%)' },
            ].map((item) => (
              <div key={item.label} className="flex items-center gap-2">
                <span className="w-3 h-3 rounded-full" style={{ background: item.color }} />
                <span className="text-gray-400">{item.label}</span>
              </div>
            ))}
          </div>

          <div
            className="bg-[#0d0d0d] border border-[#222] rounded-2xl overflow-hidden w-full"
            style={{ height: SVG_H }}
          >
            <svg viewBox={`0 0 ${SVG_W} ${SVG_H}`} className="w-full h-full">
              {Object.entries(GROUP_LAYERS).map(([group, layer]) => (
                <g key={group}>
                  <line
                    x1={40}
                    y1={layer.y}
                    x2={SVG_W - 40}
                    y2={layer.y}
                    stroke="#222"
                    strokeDasharray="4 4"
                  />
                  <text x={12} y={layer.y + 4} fill={layer.color} fontSize={10} className="capitalize">
                    {group}
                  </text>
                </g>
              ))}

              {GRAPH_DATA.links.map((link, index) => {
                const from = nodeMap[link.source];
                const to = nodeMap[link.target];
                if (!from || !to) return null;
                return (
                  <motion.line
                    key={`${link.source}-${link.target}`}
                    x1={from.x}
                    y1={from.y}
                    x2={to.x}
                    y2={to.y}
                    stroke="#333"
                    strokeWidth={1}
                    initial={{ pathLength: 0, opacity: 0 }}
                    animate={{ pathLength: 1, opacity: 1 }}
                    transition={{ duration: 0.8, delay: 0.4 + index * 0.03 }}
                  />
                );
              })}

              <defs>
                <marker id="arrow" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto">
                  <path d="M0,0 L6,3 L0,6 Z" fill="#555" />
                </marker>
              </defs>

              {Object.values(nodeMap).map((node, index) => {
                const mastery = getMasteryForConcept(node.id);
                const isWeak = mastery > 0 && mastery < 0.35;
                const isHovered = hoveredId === node.id;
                return (
                  <g
                    key={node.id}
                    onMouseEnter={() => setHoveredId(node.id)}
                    onMouseLeave={() => setHoveredId(null)}
                    style={{ cursor: 'pointer' }}
                    onClick={() => navigate(`/learn?concept=${node.id}`)}
                  >
                    {isWeak && (
                      <motion.circle
                        cx={node.x}
                        cy={node.y}
                        animate={{ r: [22, 28, 22], opacity: [0.5, 0.1, 0.5] }}
                        transition={{ repeat: Infinity, duration: 2, ease: 'easeInOut' }}
                        fill="none"
                        stroke="#E8392A"
                        strokeWidth={1.5}
                      />
                    )}
                    <motion.circle
                      cx={node.x}
                      cy={node.y}
                      fill={getFill(node.id)}
                      stroke={getStroke(node.id)}
                      strokeWidth={1.5}
                      initial={{ r: 0, opacity: 0 }}
                      animate={{ r: isHovered ? 22 : 18, opacity: 1 }}
                      transition={{ type: 'spring', stiffness: 200, delay: index * 0.04 }}
                    />
                    <text
                      x={node.x}
                      y={node.y + 32}
                      textAnchor="middle"
                      fill="#9ca3af"
                      fontSize={10}
                    >
                      {node.label}
                    </text>
                    {isHovered && (
                      <motion.g
                        initial={{ opacity: 0, y: 4 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.15 }}
                      >
                        <rect
                          x={node.x - 64}
                          y={node.y - 82}
                          width={128}
                          height={58}
                          rx={8}
                          fill="#1a1a1a"
                          stroke="#333"
                        />
                        <text
                          x={node.x}
                          y={node.y - 62}
                          textAnchor="middle"
                          fill="white"
                          fontSize={12}
                          fontWeight="600"
                        >
                          {node.label}
                        </text>
                        <text
                          x={node.x}
                          y={node.y - 44}
                          textAnchor="middle"
                          fill="#9ca3af"
                          fontSize={11}
                        >
                          Mastery: {mastery > 0 ? `${(mastery * 100).toFixed(0)}%` : 'Not started'}
                        </text>
                        <text
                          x={node.x}
                          y={node.y - 28}
                          textAnchor="middle"
                          fill="#E8392A"
                          fontSize={10}
                        >
                          {isWeak ? 'Needs practice →' : mastery >= 0.7 ? 'Mastered ✓' : 'In progress'}
                        </text>
                      </motion.g>
                    )}
                  </g>
                );
              })}

              <g transform={`translate(${SVG_W - 160}, 16)`}>
                <rect x={0} y={0} width={148} height={70} rx={8} fill="#111" stroke="#222" />
                {[
                  { color: '#14532d', label: 'Mastered (>70%)' },
                  { color: '#78350f', label: 'In progress (40–70%)' },
                  { color: '#7f1d1d', label: 'Needs work (<40%)' },
                ].map(({ color, label }, i) => (
                  <g key={label} transform={`translate(12, ${16 + i * 18})`}>
                    <circle r={5} fill={color} />
                    <text x={14} y={4} fill="#9ca3af" fontSize={10}>
                      {label}
                    </text>
                  </g>
                ))}
              </g>
            </svg>
          </div>
        </div>
      </div>
    </Layout>
  );
}

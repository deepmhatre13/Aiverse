const COURSE_VISUALS = {
  'Real-World ML Case Studies': {
    image: '/course-covers/real-world-ml-case-studies.svg',
    bestType: 'system-diagram',
    description:
      'Real-world ML workflows across fraud, recommendations, and forecasting with measurable impact layers.',
    queries: [
      'real world machine learning case study architecture diagram',
      'fraud detection machine learning pipeline diagram production',
      'recommendation system production architecture diagram',
      'demand forecasting ml workflow architecture diagram',
      'end to end ml lifecycle case study diagram dark theme',
    ],
  },
  'MLOps & Deployment': {
    image: '/course-covers/mlops-deployment.svg',
    bestType: 'deployment-architecture-diagram',
    description:
      'CI/CD-driven ML deployment with container orchestration, serving, and monitoring.',
    queries: [
      'mlops pipeline diagram ci cd model deployment',
      'kubernetes model serving architecture machine learning',
      'dockerized ml deployment workflow diagram',
      'model registry and monitoring architecture mlops',
      'canary deployment machine learning system diagram',
    ],
  },
  'Advanced Feature Engineering': {
    image: '/course-covers/advanced-feature-engineering.svg',
    bestType: 'data-pipeline-diagram',
    description:
      'Feature transformation pipeline for tabular and time-series data ending in a feature store.',
    queries: [
      'feature engineering pipeline diagram tabular data',
      'feature store architecture online offline features',
      'data preprocessing workflow feature transformation diagram',
      'feature selection encoding scaling pipeline diagram',
      'time series feature engineering architecture diagram',
    ],
  },
  'Production ML Systems Design': {
    image: '/course-covers/production-ml-systems-design.svg',
    bestType: 'system-architecture-diagram',
    description:
      'Scalable distributed architecture for production training, inference, and observability.',
    queries: [
      'scalable ml system architecture diagram production',
      'distributed machine learning serving architecture',
      'event driven ml platform design diagram',
      'low latency online inference architecture diagram',
      'ml microservices architecture with monitoring',
    ],
  },
  'Applied Machine Learning Engineering': {
    image: '/course-covers/applied-ml-engineering.svg',
    bestType: 'workflow-system-diagram',
    description:
      'End-to-end ML engineering lifecycle from experiment to validated deployment.',
    queries: [
      'applied machine learning engineering workflow diagram',
      'notebook to production ml pipeline architecture',
      'model training evaluation deployment lifecycle diagram',
      'reproducible ml experimentation architecture',
      'ml engineering best practices system diagram',
    ],
  },
  'Introduction to Deep Learning': {
    image: '/course-covers/introduction-deep-learning.svg',
    bestType: 'neural-network-diagram',
    description:
      'Neural network layer connectivity and training dynamics in a high-contrast technical style.',
    queries: [
      'deep learning neural network layers diagram dark',
      'cnn architecture feature map visualization diagram',
      'neural network training loss accuracy graph',
      'transformer architecture simplified technical diagram',
      'backpropagation neural network visualization',
    ],
  },
  'Python for Data Science': {
    image: '/course-covers/python-data-science.svg',
    bestType: 'code-notebook-visual',
    description:
      'Notebook-focused Python data workflow with pandas, numpy, and analytical visualizations.',
    queries: [
      'python data science notebook pandas numpy visual',
      'jupyter notebook data analysis workflow dark theme',
      'python dataframe transformation code screenshot clean',
      'matplotlib seaborn notebook analytics view',
      'python data science stack architecture diagram',
    ],
  },
  'Machine Learning Foundations': {
    image: '/course-covers/ml-foundations.svg',
    bestType: 'concept-diagram',
    description:
      'Foundational concepts: regression, classification, and decision trees with clear visual separation.',
    queries: [
      'machine learning foundations decision tree regression diagram',
      'classification boundary plot supervised learning visual',
      'linear vs logistic regression comparison chart',
      'bias variance tradeoff machine learning diagram',
      'confusion matrix precision recall visualization',
    ],
  },
};

export function getCourseVisual(title, fallbackThumbnail = '') {
  const mapped = COURSE_VISUALS[title];
  if (mapped) {
    return {
      ...mapped,
      src: mapped.image,
      isCurated: true,
    };
  }

  return {
    src: fallbackThumbnail || '',
    bestType: 'system-diagram',
    description: 'Technical course visual',
    queries: [],
    isCurated: false,
  };
}

export { COURSE_VISUALS };

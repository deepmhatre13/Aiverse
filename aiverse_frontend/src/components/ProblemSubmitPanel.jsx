import React, { useState } from 'react';
import { Upload, FileText, X, CheckCircle2, XCircle, Clock, Loader2 } from 'lucide-react';
import { Button } from './ui/button';
import { Progress } from './ui/progress';

const ProblemSubmitPanel = ({ 
  onSubmit, 
  submissionState = 'idle', // idle, running, evaluating, completed, failed
  result = null,
  allowCsv = true 
}) => {
  const [csvFile, setCsvFile] = useState(null);
  const [dragActive, setDragActive] = useState(false);

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      if (file.name.endsWith('.csv')) {
        setCsvFile(file);
      }
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setCsvFile(e.target.files[0]);
    }
  };

  const removeFile = () => {
    setCsvFile(null);
  };

  const getStateIcon = () => {
    switch (submissionState) {
      case 'running':
        return <Loader2 className="h-5 w-5 animate-spin text-primary" />;
      case 'evaluating':
        return <Clock className="h-5 w-5 text-yellow-500 animate-pulse" />;
      case 'completed':
        return <CheckCircle2 className="h-5 w-5 text-green-500" />;
      case 'failed':
        return <XCircle className="h-5 w-5 text-destructive" />;
      default:
        return null;
    }
  };

  const getStateMessage = () => {
    switch (submissionState) {
      case 'running':
        return 'Running your code...';
      case 'evaluating':
        return 'Evaluating predictions...';
      case 'completed':
        return 'Submission successful!';
      case 'failed':
        return 'Submission failed';
      default:
        return null;
    }
  };

  return (
    <div className="space-y-4">
      {/* CSV Upload Section */}
      {allowCsv && (
        <div className="space-y-2">
          <label className="text-sm font-medium text-foreground">
            Predictions CSV (Optional)
          </label>
          
          {!csvFile ? (
            <div
              className={`
                relative border-2 border-dashed rounded-lg p-6 text-center transition-all
                ${dragActive 
                  ? 'border-primary bg-primary/5' 
                  : 'border-border hover:border-primary/50'
                }
              `}
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
            >
              <input
                type="file"
                accept=".csv"
                onChange={handleFileChange}
                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
              />
              <Upload className="h-8 w-8 mx-auto mb-2 text-muted-foreground" />
              <p className="text-sm text-muted-foreground">
                Drag & drop your CSV or <span className="text-primary">browse</span>
              </p>
              <p className="text-xs text-muted-foreground mt-1">
                submission.csv format required
              </p>
            </div>
          ) : (
            <div className="flex items-center justify-between p-3 bg-muted/50 rounded-lg border border-border">
              <div className="flex items-center gap-3">
                <FileText className="h-5 w-5 text-primary" />
                <div>
                  <p className="text-sm font-medium">{csvFile.name}</p>
                  <p className="text-xs text-muted-foreground">
                    {(csvFile.size / 1024).toFixed(1)} KB
                  </p>
                </div>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={removeFile}
                className="h-8 w-8 p-0"
              >
                <X className="h-4 w-4" />
              </Button>
            </div>
          )}
        </div>
      )}

      {/* Submission State */}
      {submissionState !== 'idle' && (
        <div className={`
          p-4 rounded-lg border transition-all
          ${submissionState === 'completed' 
            ? 'bg-green-500/10 border-green-500/30' 
            : submissionState === 'failed'
            ? 'bg-destructive/10 border-destructive/30'
            : 'bg-muted/50 border-border'
          }
        `}>
          <div className="flex items-center gap-3 mb-3">
            {getStateIcon()}
            <span className="font-medium">{getStateMessage()}</span>
          </div>
          
          {(submissionState === 'running' || submissionState === 'evaluating') && (
            <Progress 
              value={submissionState === 'running' ? 45 : 75} 
              className="h-2"
            />
          )}

          {/* Results */}
          {result && submissionState === 'completed' && (
            <div className="mt-4 space-y-3">
              <div className="grid grid-cols-2 gap-4">
                <div className="p-3 bg-background rounded-lg">
                  <p className="text-xs text-muted-foreground mb-1">Score</p>
                  <p className="text-2xl font-bold text-green-500">
                    {result.score?.toFixed(4) || '0.9234'}
                  </p>
                </div>
                <div className="p-3 bg-background rounded-lg">
                  <p className="text-xs text-muted-foreground mb-1">Rank Impact</p>
                  <p className="text-2xl font-bold text-primary">
                    +{result.rank_change || 12}
                  </p>
                </div>
              </div>
              
              {result.metric_explanation && (
                <div className="p-3 bg-background rounded-lg">
                  <p className="text-xs text-muted-foreground mb-1">Metric Explanation</p>
                  <p className="text-sm">{result.metric_explanation}</p>
                </div>
              )}
            </div>
          )}

          {result && submissionState === 'failed' && (
            <div className="mt-3 p-3 bg-background rounded-lg">
              <p className="text-sm text-destructive">
                {result.error || 'An error occurred during evaluation.'}
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default ProblemSubmitPanel;

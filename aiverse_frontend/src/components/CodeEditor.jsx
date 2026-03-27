import React, { useEffect, useState } from 'react';
import Editor from '@monaco-editor/react';
import { Play, Upload, RotateCcw, Copy, Check } from 'lucide-react';
import { Button } from './ui/button';

const CodeEditor = ({ 
  initialCode = '', 
  language = 'python',
  onCodeChange,
  onRun,
  onSubmit,
  isRunning = false,
  readOnly = false,
  height = '500px'
}) => {
  const [code, setCode] = useState(initialCode);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    setCode(initialCode || '');
  }, [initialCode]);

  const handleEditorChange = (value) => {
    setCode(value || '');
    if (onCodeChange) {
      onCodeChange(value || '');
    }
  };

  const handleCopy = async () => {
    await navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleReset = () => {
    setCode(initialCode);
    if (onCodeChange) {
      onCodeChange(initialCode);
    }
  };

  const editorOptions = {
    minimap: { enabled: false },
    fontSize: 14,
    fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
    lineNumbers: 'on',
    roundedSelection: true,
    scrollBeyondLastLine: false,
    automaticLayout: true,
    tabSize: 4,
    wordWrap: 'on',
    readOnly: readOnly,
    padding: { top: 16, bottom: 16 },
    suggestOnTriggerCharacters: true,
    quickSuggestions: true,
    folding: true,
    lineDecorationsWidth: 10,
    renderLineHighlight: 'all',
    cursorBlinking: 'smooth',
    cursorSmoothCaretAnimation: 'on',
  };

  return (
    <div className="flex flex-col h-full border border-border rounded-lg overflow-hidden bg-card">
      {/* Editor Header */}
      <div className="flex items-center justify-between px-4 py-2 bg-muted/50 border-b border-border">
        <div className="flex items-center gap-2">
          <div className="flex gap-1.5">
            <div className="w-3 h-3 rounded-full bg-destructive/60" />
            <div className="w-3 h-3 rounded-full bg-yellow-500/60" />
            <div className="w-3 h-3 rounded-full bg-green-500/60" />
          </div>
          <span className="text-sm font-medium text-muted-foreground ml-2">
            solution.py
          </span>
        </div>
        
        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={handleCopy}
            className="h-8"
          >
            {copied ? (
              <Check className="h-4 w-4 text-green-500" />
            ) : (
              <Copy className="h-4 w-4" />
            )}
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={handleReset}
            className="h-8"
            disabled={readOnly}
          >
            <RotateCcw className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Monaco Editor */}
      <div className="flex-1" style={{ height }}>
        <Editor
          height="100%"
          language={language}
          value={code}
          onChange={handleEditorChange}
          theme="vs-dark"
          options={editorOptions}
          loading={
            <div className="flex items-center justify-center h-full bg-card">
              <div className="animate-pulse text-muted-foreground">
                Loading editor...
              </div>
            </div>
          }
        />
      </div>

      {/* Editor Footer */}
      {(onRun || onSubmit) && (
        <div className="flex items-center justify-between px-4 py-3 bg-muted/50 border-t border-border">
          <div className="text-xs text-muted-foreground">
            Python 3.10 • Auto-save enabled
          </div>
          
          <div className="flex items-center gap-2">
            {onRun && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => onRun(code)}
                disabled={isRunning}
                className="gap-2"
              >
                <Play className="h-4 w-4" />
                Evaluate
              </Button>
            )}
            {onSubmit && (
              <Button
                size="sm"
                onClick={() => onSubmit(code)}
                disabled={isRunning}
                className="gap-2 bg-primary hover:bg-primary/90"
              >
                <Upload className="h-4 w-4" />
                Submit
              </Button>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default CodeEditor;

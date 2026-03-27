import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, Loader2, Sparkles } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { ScrollArea } from '@/components/ui/scroll-area';

const MentorChat = ({ 
  messages = [], 
  onSendMessage, 
  isTyping = false,
  sessionId = null 
}) => {
  const [input, setInput] = useState('');
  const scrollRef = useRef(null);
  const textareaRef = useRef(null);

  useEffect(() => {
    // Scroll to bottom on new messages
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isTyping]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (input.trim() && onSendMessage) {
      onSendMessage(input.trim());
      setInput('');
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const formatMessageContent = (content) => {
    // Simple markdown-like formatting
    return content
      .split('\n')
      .map((line, i) => {
        // Code blocks
        if (line.startsWith('```')) {
          return null; // Handle separately if needed
        }
        // Headers
        if (line.startsWith('### ')) {
          return <h4 key={i} className="font-semibold mt-3 mb-1">{line.slice(4)}</h4>;
        }
        if (line.startsWith('## ')) {
          return <h3 key={i} className="font-semibold text-lg mt-4 mb-2">{line.slice(3)}</h3>;
        }
        // Lists
        if (line.startsWith('- ') || line.startsWith('• ')) {
          return <li key={i} className="ml-4">{line.slice(2)}</li>;
        }
        // Regular text
        return line ? <p key={i} className="mb-2">{line}</p> : <br key={i} />;
      });
  };

  return (
    <div className="flex flex-col h-full">
      {/* Messages Area */}
      <ScrollArea className="flex-1 p-4" ref={scrollRef}>
        <div className="space-y-6 max-w-3xl mx-auto">
          {messages.length === 0 && (
            <div className="text-center py-12">
              <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-primary/10 flex items-center justify-center">
                <Sparkles className="h-8 w-8 text-primary" />
              </div>
              <h3 className="text-lg font-semibold mb-2">Start a Conversation</h3>
              <p className="text-muted-foreground max-w-sm mx-auto">
                Ask me anything about machine learning concepts, algorithms, 
                best practices, or your learning journey.
              </p>
            </div>
          )}

          {messages.map((message, index) => (
            <div
              key={message.id || index}
              className={`
                flex gap-4 animate-fade-in
                ${message.role === 'user' ? 'flex-row-reverse' : ''}
              `}
              style={{ animationDelay: `${index * 50}ms` }}
            >
              {/* Avatar */}
              <div className={`
                flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center
                ${message.role === 'user' 
                  ? 'bg-primary/10' 
                  : 'bg-muted border border-border'
                }
              `}>
                {message.role === 'user' ? (
                  <User className="h-5 w-5 text-primary" />
                ) : (
                  <Bot className="h-5 w-5 text-muted-foreground" />
                )}
              </div>

              {/* Message Content */}
              <div className={`
                flex-1 max-w-[80%]
                ${message.role === 'user' ? 'text-right' : ''}
              `}>
                <div className={`
                  inline-block p-4 rounded-2xl text-left
                  ${message.role === 'user'
                    ? 'bg-primary text-primary-foreground rounded-tr-md'
                    : 'bg-muted/50 border border-border rounded-tl-md'
                  }
                `}>
                  <div className="text-sm leading-relaxed">
                    {formatMessageContent(message.content)}
                  </div>
                </div>
                
                {message.timestamp && (
                  <p className="text-xs text-muted-foreground mt-1 px-2">
                    {new Date(message.timestamp).toLocaleTimeString([], { 
                      hour: '2-digit', 
                      minute: '2-digit' 
                    })}
                  </p>
                )}
              </div>
            </div>
          ))}

          {/* Typing Indicator */}
          {isTyping && (
            <div className="flex gap-4 animate-fade-in">
              <div className="flex-shrink-0 w-10 h-10 rounded-full bg-muted border border-border flex items-center justify-center">
                <Bot className="h-5 w-5 text-muted-foreground" />
              </div>
              <div className="bg-muted/50 border border-border rounded-2xl rounded-tl-md p-4">
                <div className="flex gap-1">
                  <span className="w-2 h-2 bg-muted-foreground/50 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                  <span className="w-2 h-2 bg-muted-foreground/50 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                  <span className="w-2 h-2 bg-muted-foreground/50 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                </div>
              </div>
            </div>
          )}
        </div>
      </ScrollArea>

      {/* Input Area */}
      <div className="p-4 border-t border-border bg-background/95 backdrop-blur">
        <form onSubmit={handleSubmit} className="max-w-3xl mx-auto">
          <div className="relative">
            <Textarea
              ref={textareaRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask your ML mentor anything..."
              className="min-h-[60px] max-h-[200px] pr-14 resize-none bg-muted/50"
              disabled={isTyping}
            />
            <Button
              type="submit"
              size="icon"
              disabled={!input.trim() || isTyping}
              className="absolute right-2 bottom-2 h-9 w-9 bg-primary hover:bg-primary/90"
            >
              {isTyping ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Send className="h-4 w-4" />
              )}
            </Button>
          </div>
          <p className="text-xs text-muted-foreground mt-2 text-center">
            Press Enter to send, Shift+Enter for new line
          </p>
        </form>
      </div>
    </div>
  );
};

export default MentorChat;

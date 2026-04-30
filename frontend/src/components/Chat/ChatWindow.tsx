import React, { useEffect, useRef, useState } from 'react';
import { Brain, Sparkles, Code, BookCheck, Search, X, Mic, Send, RefreshCw } from 'lucide-react';
import { useSSE } from '../../hooks/useSSE';
import MessageBubble from './MessageBubble';
import InputBar from './InputBar';
import { getMessages, startInterview, submitAnswer, InterviewStatus } from '../../api/chat';

interface ChatWindowProps {
  activeChatId: string;
}

export default function ChatWindow({ activeChatId }: ChatWindowProps) {
  const { messages, setMessages, isStreaming, sendMessage, clearMessages } = useSSE();
  const [showResumeModal, setShowResumeModal] = useState(false);
  const [resumeText, setResumeText] = useState('');
  const [jdText, setJdText] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Mock Interview State
  const [interviewActive, setInterviewActive] = useState(false);
  const [interviewTopic, setInterviewTopic] = useState('');
  const [interviewState, setInterviewState] = useState<InterviewStatus | null>(null);
  const [userAnswer, setUserAnswer] = useState('');
  const [interviewLoading, setInterviewLoading] = useState(false);
  const [showTopicModal, setShowTopicModal] = useState(false);

  // Quiz and Explain Modals
  const [showQuizModal, setShowQuizModal] = useState(false);
  const [quizTopic, setQuizTopic] = useState('');
  const [showExplainModal, setShowExplainModal] = useState(false);
  const [explainTopic, setExplainTopic] = useState('');

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Load chat history when activeChatId changes
  useEffect(() => {
    if (activeChatId) {
      clearMessages();
      setInterviewActive(false);
      setInterviewState(null);
      
      const fetchHistory = async () => {
        try {
          const history = await getMessages(activeChatId);
          const formatted = history.map((h, index) => ({
            id: 'hist_' + index,
            role: h.role === 'human' ? 'user' : 'assistant' as const,
            content: h.content,
            timestamp: new Date(h.created_at),
          }));
          setMessages(formatted);
          
          // Check if there's an active interview session in history or status
          // (Simplify by loading standard history; users can restart mock interviews as needed)
        } catch (err) {
          console.error('Failed to load chat history:', err);
        }
      };
      
      fetchHistory();
    }
  }, [activeChatId, clearMessages, setMessages]);

  const handleSend = (text: string) => {
    if (!activeChatId) return;
    sendMessage(text, activeChatId);
  };

  const handleQuickAction = (action: string) => {
    switch (action) {
      case 'quiz':
        setShowQuizModal(true);
        break;
      case 'resume':
        setShowResumeModal(true);
        break;
      case 'explain':
        setShowExplainModal(true);
        break;
      case 'gaps':
        handleSend('Based on my materials, what topics should I study more for placements?');
        break;
      case 'interview':
        setShowTopicModal(true);
        break;
    }
  };

  const handleResumeSubmit = () => {
    if (jdText.trim()) {
      const input = JSON.stringify({
        resume_text: resumeText.trim() || undefined,
        jd_text: jdText.trim(),
      });
      
      if (resumeText.trim()) {
        handleSend(`Compare my resume with this JD: ${input}`);
      } else {
        handleSend(`Compare my resume from my knowledge base with this JD: ${input}`);
      }
      
      setShowResumeModal(false);
      setResumeText('');
      setJdText('');
    }
  };

  const handleStartInterviewSubmit = async (topic: string) => {
    if (!activeChatId || !topic.trim()) return;
    setInterviewLoading(true);
    try {
      const state = await startInterview(activeChatId, topic);
      setInterviewState(state);
      setInterviewTopic(topic);
      setInterviewActive(true);
      setShowTopicModal(false);
      
      // Reload chat history to show the mock interview starting message and first question
      const history = await getMessages(activeChatId);
      setMessages(history.map((h, index) => ({
        id: 'hist_' + index,
        role: h.role === 'human' ? 'user' : 'assistant' as const,
        content: h.content,
        timestamp: new Date(h.created_at),
      })));
    } catch (err) {
      alert('Failed to start interview: ' + err);
    } finally {
      setInterviewLoading(false);
    }
  };

  const handleSendAnswerSubmit = async () => {
    if (!activeChatId || !userAnswer.trim() || interviewLoading) return;
    setInterviewLoading(true);
    const ans = userAnswer;
    setUserAnswer('');
    try {
      const state = await submitAnswer(activeChatId, ans);
      setInterviewState(state);
      
      // Reload messages to show user's response, evaluation feedback, and next question
      const history = await getMessages(activeChatId);
      setMessages(history.map((h, index) => ({
        id: 'hist_' + index,
        role: h.role === 'human' ? 'user' : 'assistant' as const,
        content: h.content,
        timestamp: new Date(h.created_at),
      })));
      
      if (state.status === 'completed') {
        setInterviewActive(false);
      }
    } catch (err) {
      alert('Failed to submit answer: ' + err);
    } finally {
      setInterviewLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full bg-gray-950">
      {/* Interviewer Active State Header */}
      {interviewActive && interviewState && (
        <div className="bg-gradient-to-r from-purple-900/40 to-brand-900/30 border-b border-purple-500/20 px-6 py-4 flex-shrink-0 backdrop-blur-md">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <span className="flex h-2 w-2 relative">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-purple-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-purple-500"></span>
              </span>
              <span className="text-xs font-semibold uppercase tracking-wider text-purple-400">Mock Interview Mode</span>
              <span className="text-xs text-gray-500">•</span>
              <span className="text-xs font-medium text-gray-300">Topic: {interviewTopic}</span>
            </div>
            <button
              onClick={() => {
                if(confirm("Exit interview mode? Your progress will be saved in chat history.")) {
                  setInterviewActive(false);
                }
              }}
              className="text-xs text-gray-400 hover:text-gray-200 border border-gray-800 hover:border-gray-700 px-2 py-0.5 rounded transition-all"
            >
              Exit Interview
            </button>
          </div>
          
          <div className="glass-card p-4 border border-purple-500/30 shadow-md">
            <div className="text-xs font-semibold text-purple-300 mb-1">
              Question {interviewState.question_index} of 5
            </div>
            <div className="text-sm font-medium text-gray-100 mb-3">
              {interviewState.current_question}
            </div>
            <div className="flex gap-2">
              <input
                type="text"
                value={userAnswer}
                onChange={(e) => setUserAnswer(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSendAnswerSubmit()}
                placeholder="Type your answer here..."
                disabled={interviewLoading}
                className="input-field flex-1"
              />
              <button
                onClick={handleSendAnswerSubmit}
                disabled={!userAnswer.trim() || interviewLoading}
                className="btn-primary flex items-center justify-center gap-1.5 px-4"
              >
                {interviewLoading ? (
                  <RefreshCw size={14} className="animate-spin" />
                ) : (
                  <Send size={14} />
                )}
                Submit
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Messages area */}
      <div className="flex-1 overflow-y-auto px-4 py-6 space-y-1">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-brand-500 to-purple-600 flex items-center justify-center mb-4 shadow-lg shadow-brand-500/30">
              <Brain size={32} className="text-white" />
            </div>
            <h2 className="text-xl font-semibold text-gray-200 mb-2">
              PlacementBrain
            </h2>
            <p className="text-gray-500 text-sm max-w-md">
              Ask questions about your uploaded materials (including C++, HTML, and CSS code), generate quizzes,
              compare your resume with job descriptions, or start a mock interview.
            </p>
          </div>
        )}

        {messages.map((msg) => (
          <MessageBubble key={msg.id} message={msg} />
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* Quick actions (Disabled during interview) */}
      {!interviewActive && (
        <div className="flex gap-2 px-4 pb-2 overflow-x-auto">
          <button
            onClick={() => handleQuickAction('quiz')}
            disabled={isStreaming}
            className="btn-ghost flex items-center gap-1.5 text-xs whitespace-nowrap"
          >
            <BookCheck size={14} />
            Quiz me
          </button>
          <button
            onClick={() => handleQuickAction('resume')}
            disabled={isStreaming}
            className="btn-ghost flex items-center gap-1.5 text-xs whitespace-nowrap"
          >
            <Sparkles size={14} />
            Resume vs JD
          </button>
          <button
            onClick={() => handleQuickAction('explain')}
            disabled={isStreaming}
            className="btn-ghost flex items-center gap-1.5 text-xs whitespace-nowrap"
          >
            <Code size={14} />
            Explain code
          </button>
          <button
            onClick={() => handleQuickAction('gaps')}
            disabled={isStreaming}
            className="btn-ghost flex items-center gap-1.5 text-xs whitespace-nowrap"
          >
            <Search size={14} />
            What am I missing?
          </button>
          <button
            onClick={() => handleQuickAction('interview')}
            disabled={isStreaming}
            className="btn-ghost flex items-center gap-1.5 text-xs whitespace-nowrap text-purple-400 border border-purple-500/20 hover:border-purple-500/40 bg-purple-500/5"
          >
            <Brain size={14} />
            Mock Interview
          </button>
        </div>
      )}

      {/* Input bar (Disabled during interview) */}
      {!interviewActive && (
        <InputBar onSend={handleSend} disabled={isStreaming || !activeChatId} />
      )}

      {/* Resume vs JD Modal */}
      {showResumeModal && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="glass-card p-6 max-w-2xl w-full max-h-[80vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-100">
                Resume vs Job Description
              </h3>
              <button
                onClick={() => setShowResumeModal(false)}
                className="text-gray-400 hover:text-gray-200"
              >
                <X size={20} />
              </button>
            </div>
            <div className="space-y-4">
              <div>
                <label className="block text-sm text-gray-400 mb-1">
                  Resume Text (Optional)
                </label>
                <textarea
                  value={resumeText}
                  onChange={(e) => setResumeText(e.target.value)}
                  className="input-field w-full h-32 resize-none text-xs"
                  placeholder="Paste your resume text here. If left blank, we will auto-detect your uploaded resume PDF from the knowledge base!"
                />
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">
                  Job Description (Required)
                </label>
                <textarea
                  value={jdText}
                  onChange={(e) => setJdText(e.target.value)}
                  className="input-field w-full h-32 resize-none text-xs"
                  placeholder="Paste the job description here..."
                />
              </div>
              <button
                onClick={handleResumeSubmit}
                disabled={!jdText.trim()}
                className="btn-primary w-full text-xs py-2.5"
              >
                Compare & Analyze
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Interview Topic Modal */}
      {showTopicModal && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="glass-card p-6 max-w-md w-full">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-100 flex items-center gap-2">
                <Brain size={18} className="text-purple-400" />
                Select Mock Interview Topic
              </h3>
              <button
                onClick={() => setShowTopicModal(false)}
                className="text-gray-400 hover:text-gray-200"
              >
                <X size={20} />
              </button>
            </div>
            <div className="space-y-4">
              <p className="text-xs text-gray-400">
                Type the topic or technology you want to be interviewed on. We will extract relevant details from your knowledge base materials.
              </p>
              <div>
                <input
                  type="text"
                  placeholder="e.g. C++ OOP, React Hooks, Docker..."
                  className="input-field w-full text-xs py-2"
                  id="interview-topic-input"
                />
              </div>
              <button
                onClick={() => {
                  const input = document.getElementById('interview-topic-input') as HTMLInputElement;
                  if (input && input.value.trim()) {
                    handleStartInterviewSubmit(input.value.trim());
                  }
                }}
                disabled={interviewLoading}
                className="btn-primary w-full text-xs py-2 flex items-center justify-center gap-1.5"
              >
                {interviewLoading ? (
                  <RefreshCw size={14} className="animate-spin" />
                ) : (
                  "Start Interview"
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Quiz Modal */}
      {showQuizModal && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="glass-card p-6 max-w-md w-full">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-100 flex items-center gap-2">
                <BookCheck size={18} className="text-yellow-400" />
                Generate Quiz
              </h3>
              <button
                onClick={() => setShowQuizModal(false)}
                className="text-gray-400 hover:text-gray-200"
              >
                <X size={20} />
              </button>
            </div>
            <div className="space-y-4">
              <p className="text-xs text-gray-400">
                What topic should the quiz cover? We'll generate 5 multiple-choice questions based on your knowledge base.
              </p>
              <div>
                <input
                  type="text"
                  value={quizTopic}
                  onChange={(e) => setQuizTopic(e.target.value)}
                  placeholder="e.g. Data Structures, System Design..."
                  className="input-field w-full text-xs py-2"
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && quizTopic.trim()) {
                      handleSend(`Generate a quiz on ${quizTopic.trim()}`);
                      setShowQuizModal(false);
                      setQuizTopic('');
                    }
                  }}
                />
              </div>
              <button
                onClick={() => {
                  if (quizTopic.trim()) {
                    handleSend(`Generate a quiz on ${quizTopic.trim()}`);
                    setShowQuizModal(false);
                    setQuizTopic('');
                  }
                }}
                disabled={!quizTopic.trim()}
                className="btn-primary w-full text-xs py-2 flex items-center justify-center gap-1.5"
              >
                Create Quiz
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Explain Code Modal */}
      {showExplainModal && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="glass-card p-6 max-w-md w-full">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-100 flex items-center gap-2">
                <Code size={18} className="text-brand-400" />
                Explain Code
              </h3>
              <button
                onClick={() => setShowExplainModal(false)}
                className="text-gray-400 hover:text-gray-200"
              >
                <X size={20} />
              </button>
            </div>
            <div className="space-y-4">
              <p className="text-xs text-gray-400">
                Enter a function name, class, or coding concept from your knowledge base to explain.
              </p>
              <div>
                <input
                  type="text"
                  value={explainTopic}
                  onChange={(e) => setExplainTopic(e.target.value)}
                  placeholder="e.g. DFS algorithm, AuthMiddleware..."
                  className="input-field w-full text-xs py-2"
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && explainTopic.trim()) {
                      handleSend(`Explain ${explainTopic.trim()}`);
                      setShowExplainModal(false);
                      setExplainTopic('');
                    }
                  }}
                />
              </div>
              <button
                onClick={() => {
                  if (explainTopic.trim()) {
                    handleSend(`Explain ${explainTopic.trim()}`);
                    setShowExplainModal(false);
                    setExplainTopic('');
                  }
                }}
                disabled={!explainTopic.trim()}
                className="btn-primary w-full text-xs py-2 flex items-center justify-center gap-1.5"
              >
                Explain
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

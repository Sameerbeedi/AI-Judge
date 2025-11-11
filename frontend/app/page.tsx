'use client';

import { useState } from 'react';
import axios from 'axios';
import { Upload, Scale, FileText, MessageSquare, Gavel } from 'lucide-react';
import { useDropzone } from 'react-dropzone';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface Message {
  side: string;
  text: string;
  isFollowUp?: boolean;
  response?: string;
}

export default function Home() {
  const [caseId] = useState(() => `case_${Date.now()}`);
  const [stage, setStage] = useState<'input' | 'verdict' | 'followup'>('input');
  const [sideAText, setSideAText] = useState('');
  const [sideBText, setSideBText] = useState('');
  const [sideAFiles, setSideAFiles] = useState<File[]>([]);
  const [sideBFiles, setSideBFiles] = useState<File[]>([]);
  const [verdict, setVerdict] = useState('');
  const [followUps, setFollowUps] = useState<Message[]>([]);
  const [followUpCount, setFollowUpCount] = useState(0);
  const [currentFollowUp, setCurrentFollowUp] = useState('');
  const [currentSide, setCurrentSide] = useState<'A' | 'B'>('A');
  const [loading, setLoading] = useState(false);

  const onDropA = (acceptedFiles: File[]) => {
    setSideAFiles(prev => [...prev, ...acceptedFiles]);
  };

  const onDropB = (acceptedFiles: File[]) => {
    setSideBFiles(prev => [...prev, ...acceptedFiles]);
  };

  const { getRootProps: getRootPropsA, getInputProps: getInputPropsA } = useDropzone({
    onDrop: onDropA,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'text/plain': ['.txt']
    }
  });

  const { getRootProps: getRootPropsB, getInputProps: getInputPropsB } = useDropzone({
    onDrop: onDropB,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'text/plain': ['.txt']
    }
  });

  const handleSubmitCase = async () => {
    if (!sideAText && sideAFiles.length === 0) {
      alert('Side A must provide evidence');
      return;
    }
    if (!sideBText && sideBFiles.length === 0) {
      alert('Side B must provide evidence');
      return;
    }

    setLoading(true);
    try {
      // Create case
      await axios.post(`${API_URL}/api/case/create`, { case_id: caseId });

      // Upload Side A files
      if (sideAFiles.length > 0) {
        const formDataA = new FormData();
        sideAFiles.forEach(file => formDataA.append('files', file));
        await axios.post(`${API_URL}/api/case/${caseId}/upload/A`, formDataA);
      }

      // Upload Side B files
      if (sideBFiles.length > 0) {
        const formDataB = new FormData();
        sideBFiles.forEach(file => formDataB.append('files', file));
        await axios.post(`${API_URL}/api/case/${caseId}/upload/B`, formDataB);
      }

      // Submit text arguments
      if (sideAText) {
        await axios.post(`${API_URL}/api/case/${caseId}/argument/A`, { text: sideAText });
      }
      if (sideBText) {
        await axios.post(`${API_URL}/api/case/${caseId}/argument/B`, { text: sideBText });
      }

      // Get verdict
      const verdictRes = await axios.post(`${API_URL}/api/case/${caseId}/get-verdict`);
      setVerdict(verdictRes.data.verdict);
      setStage('verdict');
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Error submitting case');
    } finally {
      setLoading(false);
    }
  };

  const handleFollowUp = async () => {
    if (!currentFollowUp.trim()) return;
    if (followUpCount >= 5) {
      alert('Maximum follow-ups reached');
      return;
    }

    setLoading(true);
    try {
      const response = await axios.post(`${API_URL}/api/case/${caseId}/follow-up`, {
        case_id: caseId,
        side: currentSide,
        argument: currentFollowUp
      });

      setFollowUps(prev => [...prev, {
        side: currentSide,
        text: currentFollowUp,
        isFollowUp: true,
        response: response.data.response.response
      }]);

      setFollowUpCount(prev => prev + 1);
      setCurrentFollowUp('');
      setStage('followup');
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Error submitting follow-up');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="text-center mb-12">
          <div className="flex items-center justify-center gap-4 mb-4">
            <Scale className="w-16 h-16 text-judge-gold gavel-animation" />
            <h1 className="text-5xl font-bold text-judge-gold">AI Judge</h1>
          </div>
          <p className="text-gray-300 text-lg">Digital Justice System - Mock Trial Platform</p>
          <p className="text-sm text-gray-500 mt-2">Case ID: {caseId}</p>
        </div>

        {stage === 'input' && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* Side A */}
            <div className="bg-gradient-to-br from-blue-900/30 to-blue-800/20 rounded-2xl p-8 border-2 border-blue-500/50">
              <div className="flex items-center gap-3 mb-6">
                <div className="w-12 h-12 bg-blue-500 rounded-full flex items-center justify-center">
                  <span className="text-2xl font-bold">A</span>
                </div>
                <h2 className="text-2xl font-bold">Plaintiff / Side A</h2>
              </div>

              <div className="space-y-6">
                <div>
                  <label className="block text-sm font-medium mb-2">Written Arguments</label>
                  <textarea
                    value={sideAText}
                    onChange={(e) => setSideAText(e.target.value)}
                    placeholder="Enter your case arguments, evidence, and legal reasoning..."
                    className="w-full h-40 p-4 bg-black/30 border border-blue-500/30 rounded-lg focus:outline-none focus:border-blue-500 text-white placeholder-gray-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">Upload Documents</label>
                  <div
                    {...getRootPropsA()}
                    className="border-2 border-dashed border-blue-500/50 rounded-lg p-8 text-center cursor-pointer hover:border-blue-500 transition-colors"
                  >
                    <input {...getInputPropsA()} />
                    <Upload className="w-12 h-12 mx-auto mb-4 text-blue-500" />
                    <p className="text-gray-300">Drop files here or click to upload</p>
                    <p className="text-sm text-gray-500 mt-2">PDF, DOCX, TXT</p>
                  </div>
                  {sideAFiles.length > 0 && (
                    <div className="mt-4 space-y-2">
                      {sideAFiles.map((file, idx) => (
                        <div key={idx} className="flex items-center gap-2 text-sm text-gray-300">
                          <FileText className="w-4 h-4" />
                          <span>{file.name}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Side B */}
            <div className="bg-gradient-to-br from-red-900/30 to-red-800/20 rounded-2xl p-8 border-2 border-red-500/50">
              <div className="flex items-center gap-3 mb-6">
                <div className="w-12 h-12 bg-red-500 rounded-full flex items-center justify-center">
                  <span className="text-2xl font-bold">B</span>
                </div>
                <h2 className="text-2xl font-bold">Defendant / Side B</h2>
              </div>

              <div className="space-y-6">
                <div>
                  <label className="block text-sm font-medium mb-2">Written Arguments</label>
                  <textarea
                    value={sideBText}
                    onChange={(e) => setSideBText(e.target.value)}
                    placeholder="Enter your case arguments, evidence, and legal reasoning..."
                    className="w-full h-40 p-4 bg-black/30 border border-red-500/30 rounded-lg focus:outline-none focus:border-red-500 text-white placeholder-gray-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">Upload Documents</label>
                  <div
                    {...getRootPropsB()}
                    className="border-2 border-dashed border-red-500/50 rounded-lg p-8 text-center cursor-pointer hover:border-red-500 transition-colors"
                  >
                    <input {...getInputPropsB()} />
                    <Upload className="w-12 h-12 mx-auto mb-4 text-red-500" />
                    <p className="text-gray-300">Drop files here or click to upload</p>
                    <p className="text-sm text-gray-500 mt-2">PDF, DOCX, TXT</p>
                  </div>
                  {sideBFiles.length > 0 && (
                    <div className="mt-4 space-y-2">
                      {sideBFiles.map((file, idx) => (
                        <div key={idx} className="flex items-center gap-2 text-sm text-gray-300">
                          <FileText className="w-4 h-4" />
                          <span>{file.name}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}

        {stage === 'input' && (
          <div className="mt-8 text-center">
            <button
              onClick={handleSubmitCase}
              disabled={loading}
              className="px-12 py-4 bg-judge-gold text-judge-darker font-bold text-lg rounded-lg hover:bg-yellow-500 transition-colors disabled:opacity-50 disabled:cursor-not-allowed pulse-glow"
            >
              {loading ? 'Processing...' : 'Submit Case for Judgment'}
            </button>
          </div>
        )}

        {(stage === 'verdict' || stage === 'followup') && (
          <div className="space-y-8">
            {/* AI Judge Verdict */}
            <div className="bg-gradient-to-br from-judge-gold/20 to-yellow-900/20 rounded-2xl p-8 border-2 border-judge-gold verdict-appear">
              <div className="flex items-center gap-4 mb-6">
                <Gavel className="w-12 h-12 text-judge-gold" />
                <h2 className="text-3xl font-bold text-judge-gold">AI Judge's Verdict</h2>
              </div>
              <div className="prose prose-invert max-w-none">
                <pre className="whitespace-pre-wrap text-gray-200 font-sans">{verdict}</pre>
              </div>
            </div>

            {/* Follow-up Arguments */}
            {followUps.length > 0 && (
              <div className="space-y-6">
                <h3 className="text-2xl font-bold text-center text-judge-gold">Follow-up Arguments</h3>
                {followUps.map((followUp, idx) => (
                  <div key={idx} className="space-y-4">
                    <div className={`rounded-xl p-6 ${followUp.side === 'A' ? 'bg-blue-900/30 border-2 border-blue-500/50' : 'bg-red-900/30 border-2 border-red-500/50'}`}>
                      <div className="flex items-center gap-3 mb-3">
                        <div className={`w-8 h-8 ${followUp.side === 'A' ? 'bg-blue-500' : 'bg-red-500'} rounded-full flex items-center justify-center font-bold`}>
                          {followUp.side}
                        </div>
                        <span className="font-semibold">Follow-up Argument</span>
                      </div>
                      <p className="text-gray-200">{followUp.text}</p>
                    </div>
                    <div className="bg-judge-gold/10 rounded-xl p-6 border border-judge-gold/30">
                      <div className="flex items-center gap-3 mb-3">
                        <Gavel className="w-6 h-6 text-judge-gold" />
                        <span className="font-semibold text-judge-gold">Judge's Response</span>
                      </div>
                      <pre className="whitespace-pre-wrap text-gray-200 font-sans">{followUp.response}</pre>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Follow-up Input */}
            {followUpCount < 5 && (
              <div className="bg-judge-darker/50 rounded-2xl p-8 border-2 border-judge-gold/30">
                <h3 className="text-xl font-bold mb-4 text-judge-gold">
                  Submit Follow-up Argument ({5 - followUpCount} remaining)
                </h3>
                <div className="space-y-4">
                  <div className="flex gap-4">
                    <button
                      onClick={() => setCurrentSide('A')}
                      className={`flex-1 py-3 rounded-lg font-semibold transition-colors ${
                        currentSide === 'A'
                          ? 'bg-blue-500 text-white'
                          : 'bg-blue-900/30 text-blue-300 hover:bg-blue-900/50'
                      }`}
                    >
                      Side A
                    </button>
                    <button
                      onClick={() => setCurrentSide('B')}
                      className={`flex-1 py-3 rounded-lg font-semibold transition-colors ${
                        currentSide === 'B'
                          ? 'bg-red-500 text-white'
                          : 'bg-red-900/30 text-red-300 hover:bg-red-900/50'
                      }`}
                    >
                      Side B
                    </button>
                  </div>
                  <textarea
                    value={currentFollowUp}
                    onChange={(e) => setCurrentFollowUp(e.target.value)}
                    placeholder="Present your follow-up argument. Challenge the verdict, present new perspectives, or provide additional evidence..."
                    className="w-full h-32 p-4 bg-black/30 border border-judge-gold/30 rounded-lg focus:outline-none focus:border-judge-gold text-white placeholder-gray-500"
                  />
                  <button
                    onClick={handleFollowUp}
                    disabled={loading || !currentFollowUp.trim()}
                    className="w-full py-3 bg-judge-gold text-judge-darker font-bold rounded-lg hover:bg-yellow-500 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {loading ? 'Submitting...' : 'Submit Follow-up'}
                  </button>
                </div>
              </div>
            )}

            {followUpCount >= 5 && (
              <div className="bg-judge-gold/20 rounded-2xl p-8 border-2 border-judge-gold text-center">
                <Gavel className="w-16 h-16 mx-auto mb-4 text-judge-gold" />
                <h3 className="text-2xl font-bold text-judge-gold mb-2">Case Closed</h3>
                <p className="text-gray-300">Maximum follow-up arguments reached. The final verdict stands.</p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

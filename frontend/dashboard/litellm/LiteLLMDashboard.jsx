import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Textarea } from '@/components/ui/textarea';

const LiteLLMDashboard = () => {
  const [status, setStatus] = useState(null);
  const [metrics, setMetrics] = useState(null);
  const [knowledgeGraph, setKnowledgeGraph] = useState(null);
  const [nodes, setNodes] = useState(null);
  const [prompt, setPrompt] = useState('');
  const [response, setResponse] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 5000);
    return () => clearInterval(interval);
  }, []);

  const fetchStatus = async () => {
    try {
      const res = await fetch('http://localhost:8000/litellm/status');
      const data = await res.json();
      setStatus(data);
    } catch (error) {
      console.error('Failed to fetch status:', error);
    }
  };

  const fetchMetrics = async () => {
    try {
      const res = await fetch('http://localhost:8000/litellm/metrics');
      const data = await res.json();
      setMetrics(data.metrics);
    } catch (error) {
      console.error('Failed to fetch metrics:', error);
    }
  };

  const fetchKnowledgeGraph = async () => {
    try {
      const res = await fetch('http://localhost:8000/litellm/knowledge-graph');
      const data = await res.json();
      setKnowledgeGraph(data.knowledge_graph);
    } catch (error) {
      console.error('Failed to fetch knowledge graph:', error);
    }
  };

  const fetchNodes = async () => {
    try {
      const res = await fetch('http://localhost:8000/litellm/nodes');
      const data = await res.json();
      setNodes(data.nodes);
    } catch (error) {
      console.error('Failed to fetch nodes:', error);
    }
  };

  const handleComplete = async () => {
    if (!prompt.trim()) return;
    setLoading(true);
    try {
      const res = await fetch('http://localhost:8000/litellm/complete', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          prompt,
          enable_guardrails: true,
          enable_reflection: true,
          enable_holographic: true
        })
      });
      const data = await res.json();
      setResponse(data);
    } catch (error) {
      console.error('Failed to complete:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">🌟 ASIM Chaitanya Router (LiteLLM)</h1>
        <Badge variant={status?.available ? 'default' : 'destructive'}>
          {status?.available ? 'Online' : 'Offline'}
        </Badge>
      </div>

      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="models">Models</TabsTrigger>
          <TabsTrigger value="chat">Chat</TabsTrigger>
          <TabsTrigger value="knowledge">Knowledge Graph</TabsTrigger>
          <TabsTrigger value="nodes">Mesh Network</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card>
              <CardHeader>
                <CardTitle>Total Models</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-4xl font-bold">{status?.models || 0}</div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle>Available</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-4xl font-bold">{status?.available ? '✅' : '❌'}</div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle>Knowledge Entries</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-4xl font-bold">{knowledgeGraph ? Object.keys(knowledgeGraph).length : 0}</div>
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Features</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-2">
                <Badge variant="secondary">🛡️ ASIM Guardrails</Badge>
                <Badge variant="secondary">🔒 Zero Trust</Badge>
                <Badge variant="secondary">✨ Ethical Alignment</Badge>
                <Badge variant="secondary">🔄 Self-Reflection Loop</Badge>
                <Badge variant="secondary">🌐 Holographic Distribution</Badge>
                <Badge variant="secondary">🔐 Quantum Encryption</Badge>
                <Badge variant="secondary">⚖️ Load Balancing</Badge>
                <Badge variant="secondary">🧠 Ensemble Intelligence</Badge>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="models" className="space-y-4">
          <Button onClick={fetchMetrics}>Refresh Metrics</Button>
          {metrics && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {Object.entries(metrics).map(([model, data]) => (
                <Card key={model}>
                  <CardHeader>
                    <CardTitle className="text-lg">{model}</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-2">
                    <div>
                      <div className="text-sm text-gray-500">Success Rate</div>
                      <Progress value={data.success_rate * 100} />
                    </div>
                    <div>
                      <div className="text-sm text-gray-500">Ethical Score</div>
                      <Progress value={data.ethical_score * 100} />
                    </div>
                    <div>
                      <div className="text-sm text-gray-500">Consciousness Score</div>
                      <Progress value={data.consciousness_score * 100} />
                    </div>
                    <div className="grid grid-cols-2 gap-2 text-sm">
                      <div>
                        <span className="text-gray-500">Latency:</span> {data.latency.toFixed(2)}s
                      </div>
                      <div>
                        <span className="text-gray-500">Requests:</span> {data.total_requests}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>

        <TabsContent value="chat" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Chat with ASIM Chaitanya Router</CardTitle>
              <CardDescription>Multi-model intelligence with guardrails and ethical alignment</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <Textarea
                placeholder="Enter your prompt..."
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                rows={4}
              />
              <Button onClick={handleComplete} disabled={loading}>
                {loading ? 'Processing...' : 'Send'}
              </Button>
              {response && (
                <div className="space-y-4">
                  <Card>
                    <CardHeader>
                      <CardTitle>Response</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <p className="whitespace-pre-wrap">{response.response}</p>
                    </CardContent>
                  </Card>
                  {response.guardrails && (
                    <Card>
                      <CardHeader>
                        <CardTitle>Guardrails</CardTitle>
                      </CardHeader>
                      <CardContent className="space-y-2">
                        <div>
                          <span className="text-gray-500">Passed:</span>{' '}
                          {response.guardrails.passed ? '✅' : '❌'}
                        </div>
                        <div>
                          <span className="text-gray-500">Ethical Score:</span>{' '}
                          {response.guardrails.ethical_score.toFixed(2)}
                        </div>
                        {response.guardrails.violations.length > 0 && (
                          <div>
                            <span className="text-gray-500">Violations:</span>
                            <ul className="list-disc list-inside">
                              {response.guardrails.violations.map((v, i) => (
                                <li key={i}>{v}</li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </CardContent>
                    </Card>
                  )}
                  {response.reflection && (
                    <Card>
                      <CardHeader>
                        <CardTitle>Self-Reflection</CardTitle>
                      </CardHeader>
                      <CardContent className="space-y-2">
                        <div>
                          <span className="text-gray-500">Verified:</span>{' '}
                          {response.reflection.verified ? '✅' : '❌'}
                        </div>
                        <div>
                          <span className="text-gray-500">Score:</span>{' '}
                          {response.reflection.verification_score.toFixed(2)}
                        </div>
                      </CardContent>
                    </Card>
                  )}
                  <div className="text-sm text-gray-500">
                    Model: {response.model} | Latency: {response.latency.toFixed(2)}s
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="knowledge" className="space-y-4">
          <Button onClick={fetchKnowledgeGraph}>Refresh Knowledge Graph</Button>
          {knowledgeGraph && (
            <Card>
              <CardHeader>
                <CardTitle>Holographic Knowledge Graph</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-sm text-gray-500 mb-2">
                  {Object.keys(knowledgeGraph).length} entries
                </div>
                <div className="space-y-2 max-h-96 overflow-y-auto">
                  {Object.entries(knowledgeGraph).map(([id, data]) => (
                    <div key={id} className="p-2 bg-gray-50 rounded">
                      <div className="text-xs text-gray-500">{id}</div>
                      <div className="text-sm">{JSON.stringify(data.data).substring(0, 100)}...</div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="nodes" className="space-y-4">
          <Button onClick={fetchNodes}>Refresh Nodes</Button>
          {nodes && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {Object.entries(nodes).map(([nodeId, node]) => (
                <Card key={nodeId}>
                  <CardHeader>
                    <CardTitle className="text-lg">{nodeId}</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-2">
                    <div>
                      <span className="text-gray-500">Status:</span>{' '}
                      <Badge variant={node.status === 'online' ? 'default' : 'destructive'}>
                        {node.status}
                      </Badge>
                    </div>
                    <div>
                      <span className="text-gray-500">Role:</span> {node.role}
                    </div>
                    <div>
                      <span className="text-gray-500">IP:</span> {node.ip_address}:{node.port}
                    </div>
                    <div>
                      <span className="text-gray-500">Capabilities:</span>
                      <div className="flex flex-wrap gap-1 mt-1">
                        {node.capabilities.map((cap, i) => (
                          <Badge key={i} variant="outline">{cap}</Badge>
                        ))}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default LiteLLMDashboard;

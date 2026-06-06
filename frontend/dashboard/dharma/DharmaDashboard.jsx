/**
 * Nepal Digital Dharma Framework Dashboard
 * ========================================
 * Frontend component for dharma framework visualization and control
 */

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';

const DharmaDashboard = () => {
  const [dharmaStatus, setDharmaStatus] = useState(null);
  const [ethicalScore, setEthicalScore] = useState(0);
  const [selectedCountry, setSelectedCountry] = useState('nepal');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDharmaStatus();
  }, []);

  const fetchDharmaStatus = async () => {
    try {
      const response = await fetch('/dharma/status');
      const data = await response.json();
      setDharmaStatus(data);
      setLoading(false);
    } catch (error) {
      console.error('Failed to fetch dharma status:', error);
      setLoading(false);
    }
  };

  const evaluateEthicalScore = async (action) => {
    try {
      const response = await fetch('/dharma/evaluate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action, country: selectedCountry })
      });
      const data = await response.json();
      setEthicalScore(data.ethical_score);
    } catch (error) {
      console.error('Failed to evaluate ethical score:', error);
    }
  };

  if (loading) {
    return <div className="p-8">Loading Dharma Framework...</div>;
  }

  return (
    <div className="p-8 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">🕉️ Nepal Digital Dharma Framework</h1>
        <Badge variant={dharmaStatus?.available ? 'default' : 'destructive'}>
          {dharmaStatus?.available ? 'Active' : 'Inactive'}
        </Badge>
      </div>

      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="layers">Layers</TabsTrigger>
          <TabsTrigger value="countries">Countries</TabsTrigger>
          <TabsTrigger value="ethics">Ethics</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card>
              <CardHeader>
                <CardTitle>Framework Status</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span>Layers Active:</span>
                    <span>{dharmaStatus?.status?.layers_active || 0}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Ethical Principles:</span>
                    <span>{dharmaStatus?.status?.ethical_principles || 0}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Countries:</span>
                    <span>{dharmaStatus?.status?.countries_registered || 0}</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Ethical Score</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-4xl font-bold">{(ethicalScore * 100).toFixed(0)}%</div>
                <div className="text-sm text-muted-foreground mt-2">
                  Current ethical compliance
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Active Country</CardTitle>
              </CardHeader>
              <CardContent>
                <select
                  value={selectedCountry}
                  onChange={(e) => setSelectedCountry(e.target.value)}
                  className="w-full p-2 border rounded"
                >
                  <option value="nepal">Nepal</option>
                  <option value="india">India</option>
                  <option value="china">China</option>
                  <option value="usa">USA</option>
                  <option value="japan">Japan</option>
                  <option value="germany">Germany</option>
                </select>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="layers" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <LayerCard title="Pingala" description="Binary/Combinatorial Optimization" endpoint="pingala" />
            <LayerCard title="Shulba" description="Geometric Algorithms" endpoint="shulba" />
            <LayerCard title="Panini" description="Grammar Parsing" endpoint="panini" />
            <LayerCard title="Nyaya" description="Logic Reasoning" endpoint="nyaya" />
            <LayerCard title="Upanishad" description="Ethics Layer" endpoint="upanishad" />
            <LayerCard title="Tantra" description="Pattern Integration" endpoint="tantra" />
          </div>
        </TabsContent>

        <TabsContent value="countries" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Country-Specific Dharma</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <CountryCard country="Nepal" values="Ahimsa, Satya, Dharma" />
                <CountryCard country="India" values="Dharma, Karma, Seva" />
                <CountryCard country="China" values="Harmony, Benevolence, Righteousness" />
                <CountryCard country="USA" values="Freedom, Democracy, Equality" />
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="ethics" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Ethical Evaluation</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <Button onClick={() => evaluateEthicalScore({ action_type: 'test', safe: true })}>
                  Evaluate Test Action
                </Button>
                <div className="grid grid-cols-2 gap-4 mt-4">
                  <EthicsPrinciple name="Satya (Truth)" status="active" />
                  <EthicsPrinciple name="Ahimsa (Non-violence)" status="active" />
                  <EthicsPrinciple name="Dharma (Duty)" status="active" />
                  <EthicsPrinciple name="Karma (Accountability)" status="active" />
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

const LayerCard = ({ title, description, endpoint }) => {
  const [stats, setStats] = useState(null);

  useEffect(() => {
    fetch(`/dharma/layers/${endpoint}`)
      .then(res => res.json())
      .then(data => setStats(data.stats))
      .catch(console.error);
  }, [endpoint]);

  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-sm text-muted-foreground mb-2">{description}</p>
        {stats && (
          <div className="text-xs">
            <div>Methods: {stats.methods_available?.length || 0}</div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

const CountryCard = ({ country, values }) => (
  <div className="p-4 border rounded">
    <h3 className="font-semibold">{country}</h3>
    <p className="text-sm text-muted-foreground">{values}</p>
  </div>
);

const EthicsPrinciple = ({ name, status }) => (
  <div className="flex items-center justify-between p-3 border rounded">
    <span>{name}</span>
    <Badge variant={status === 'active' ? 'default' : 'secondary'}>
      {status}
    </Badge>
  </div>
);

export default DharmaDashboard;

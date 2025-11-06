import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { Separator } from '../ui/separator';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { TrendingUp, Users, Lightbulb, ArrowRight, Star } from 'lucide-react';

interface AISummarySectionProps {
  metadata?: {
    model?: string;
    generatedAt?: string;
  };
}

export function AISummarySection({ metadata }: AISummarySectionProps) {
  // Mock data - in production this would come from props
  const executiveSummary = "Participants showed strong interest in ease-of-use features and integration capabilities across all user segments. Price sensitivity emerged as a significant theme, with 60% of participants expressing concerns about value proposition. Mobile accessibility and cross-platform compatibility were consistently highlighted as critical requirements.";

  const keyInsights = [
    { id: 1, text: "Usability is the primary concern", impact: "Critical", mentions: 24 },
    { id: 2, text: "Mobile access is highly valued", impact: "High", mentions: 18 },
    { id: 3, text: "Integration needs vary by role", impact: "High", mentions: 15 },
    { id: 4, text: "Price sensitivity across segments", impact: "Medium", mentions: 12 }
  ];

  const themeData = [
    { name: 'Usability', value: 35, color: '#F27405' },
    { name: 'Pricing', value: 25, color: '#F29F05' },
    { name: 'Mobile', value: 20, color: '#28a745' },
    { name: 'Integration', value: 15, color: '#17a2b8' },
    { name: 'Other', value: 5, color: '#6c757d' }
  ];

  const sentimentData = [
    { segment: 'Tech Pros', positive: 85, neutral: 10, negative: 5 },
    { segment: 'Small Biz', positive: 65, neutral: 25, negative: 10 },
    { segment: 'Marketing', positive: 70, neutral: 20, negative: 10 }
  ];

  const surprisingFindings = [
    "Advanced users prefer simplified interfaces over feature complexity",
    "Freemium model concerns affect team adoption decisions",
    "Strong preference for self-serve onboarding over training sessions"
  ];

  const segments = [
    { 
      name: "Tech-Savvy Professionals", 
      size: "40%", 
      sentiment: "positive",
      topNeeds: ["API access", "Customization", "Integrations"]
    },
    { 
      name: "Small Business Owners", 
      size: "35%", 
      sentiment: "neutral",
      topNeeds: ["Cost-effective", "Reliability", "Mobile access"]
    },
    { 
      name: "Marketing Teams", 
      size: "25%", 
      sentiment: "positive",
      topNeeds: ["Collaboration", "Campaign tools", "Analytics"]
    }
  ];

  const recommendations = [
    { text: "Prioritize UX improvements", impact: "Critical", timeline: "Q1 2024" },
    { text: "Develop mobile-first approach", impact: "Critical", timeline: "Q1 2024" },
    { text: "Create tiered pricing model", impact: "High", timeline: "Q2 2024" },
    { text: "Expand integration ecosystem", impact: "High", timeline: "Q2 2024" }
  ];

  const getImpactColor = (impact: string) => {
    switch (impact) {
      case 'Critical': return 'bg-brand-orange text-white';
      case 'High': return 'bg-brand-gold text-white';
      default: return 'bg-muted text-muted-foreground';
    }
  };

  const getSentimentColor = (sentiment: string) => {
    switch (sentiment) {
      case 'positive': return 'text-green-600';
      case 'neutral': return 'text-amber-600';
      default: return 'text-red-600';
    }
  };

  return (
    <div className="space-y-8">
      {/* Executive Summary Hero */}
      <Card className="bg-gradient-to-br from-brand-orange/5 to-brand-gold/5 border-border">
        <CardHeader>
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 rounded-full bg-brand-orange flex items-center justify-center">
              <Star className="w-5 h-5 text-white" />
            </div>
            <h2>Executive Summary</h2>
          </div>
        </CardHeader>
        <CardContent>
          <p className="text-foreground leading-relaxed text-lg">
            {executiveSummary}
          </p>
        </CardContent>
      </Card>

      {/* Key Metrics Row */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card className="bg-card border-border">
          <CardContent className="pt-6">
            <div className="text-center">
              <div className="text-4xl mb-2 text-brand-orange">24</div>
              <p className="text-sm text-muted-foreground">Total Insights</p>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-card border-border">
          <CardContent className="pt-6">
            <div className="text-center">
              <div className="text-4xl mb-2 text-brand-orange">73%</div>
              <p className="text-sm text-muted-foreground">Positive Sentiment</p>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-card border-border">
          <CardContent className="pt-6">
            <div className="text-center">
              <div className="text-4xl mb-2 text-brand-orange">4</div>
              <p className="text-sm text-muted-foreground">Critical Actions</p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Key Insights */}
        <Card className="bg-card border-border">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-brand-orange" />
              Key Insights
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {keyInsights.map((insight) => (
              <div key={insight.id} className="space-y-2">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex items-start gap-3 flex-1">
                    <div className="w-6 h-6 rounded-full bg-brand-orange text-white flex items-center justify-center text-sm shrink-0">
                      {insight.id}
                    </div>
                    <div className="flex-1">
                      <p className="text-foreground">{insight.text}</p>
                      <p className="text-sm text-muted-foreground mt-1">
                        {insight.mentions} mentions in discussion
                      </p>
                    </div>
                  </div>
                  <Badge className={getImpactColor(insight.impact)}>
                    {insight.impact}
                  </Badge>
                </div>
                {insight.id < keyInsights.length && <Separator />}
              </div>
            ))}
          </CardContent>
        </Card>

        {/* Theme Distribution */}
        <Card className="bg-card border-border">
          <CardHeader>
            <CardTitle>Discussion Themes</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={250}>
              <PieChart>
                <Pie
                  data={themeData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, value }) => `${name}: ${value}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {themeData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Sentiment by Segment */}
      <Card className="bg-card border-border">
        <CardHeader>
          <CardTitle>Sentiment by Segment</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={sentimentData}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,0,0,0.1)" />
              <XAxis dataKey="segment" stroke="hsl(var(--muted-foreground))" />
              <YAxis stroke="hsl(var(--muted-foreground))" />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: 'hsl(var(--card))',
                  border: '1px solid hsl(var(--border))',
                  borderRadius: '8px'
                }}
              />
              <Bar dataKey="positive" stackId="a" fill="#28a745" name="Positive" />
              <Bar dataKey="neutral" stackId="a" fill="#ffc107" name="Neutral" />
              <Bar dataKey="negative" stackId="a" fill="#dc3545" name="Negative" />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Surprising Findings */}
      <Card className="bg-card border-border">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Lightbulb className="w-5 h-5 text-brand-gold" />
            Surprising Findings
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {surprisingFindings.map((finding, index) => (
              <div key={index} className="flex gap-3 items-start">
                <div className="w-2 h-2 rounded-full bg-brand-gold shrink-0 mt-2" />
                <p className="text-foreground">{finding}</p>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Segment Summary */}
      <div>
        <h2 className="mb-6">Segment Overview</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {segments.map((segment, index) => (
            <Card key={index} className="bg-card border-border hover:shadow-lg transition-shadow">
              <CardHeader>
                <div className="flex items-start justify-between gap-2 mb-2">
                  <h3>{segment.name}</h3>
                  <Badge variant="outline" className="shrink-0">
                    {segment.size}
                  </Badge>
                </div>
                <div className={`flex items-center gap-2 ${getSentimentColor(segment.sentiment)}`}>
                  <div className="w-2 h-2 rounded-full bg-current" />
                  <span className="text-sm capitalize">{segment.sentiment}</span>
                </div>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground mb-3">Top Needs:</p>
                <div className="space-y-2">
                  {segment.topNeeds.map((need, idx) => (
                    <div key={idx} className="flex items-center gap-2">
                      <ArrowRight className="w-4 h-4 text-brand-orange shrink-0" />
                      <span className="text-sm text-foreground">{need}</span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>

      {/* Strategic Recommendations */}
      <Card className="bg-card border-border">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Users className="w-5 h-5 text-brand-orange" />
            Strategic Recommendations
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {recommendations.map((rec, index) => (
              <div key={index}>
                <div className="flex items-start justify-between gap-4 py-3">
                  <div className="flex gap-3 flex-1">
                    <div className="w-6 h-6 rounded-full bg-brand-orange text-white flex items-center justify-center text-sm shrink-0">
                      {index + 1}
                    </div>
                    <p className="text-foreground">{rec.text}</p>
                  </div>
                  <div className="flex gap-2 shrink-0">
                    <Badge className={getImpactColor(rec.impact)}>
                      {rec.impact}
                    </Badge>
                    <Badge variant="outline" className="border-border text-muted-foreground">
                      {rec.timeline}
                    </Badge>
                  </div>
                </div>
                {index < recommendations.length - 1 && <Separator />}
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Metadata Footer */}
      {metadata && (
        <div className="flex items-center justify-center gap-4 text-sm text-muted-foreground pt-4 border-t border-border">
          <span>Generated by {metadata.model || 'AI'}</span>
          <span>•</span>
          <span>
            {new Date(metadata.generatedAt || Date.now()).toLocaleDateString('en-US', {
              month: 'short',
              day: 'numeric',
              hour: '2-digit',
              minute: '2-digit'
            })}
          </span>
        </div>
      )}
    </div>
  );
}

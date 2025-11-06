import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Slider } from './ui/slider';
import { Checkbox } from './ui/checkbox';
import { Label } from './ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Progress } from './ui/progress';
import { ArrowLeft, Filter, Download, Share, TrendingUp, Users, BarChart3, PieChart, MessageSquare, Grid3x3, Sparkles, ThumbsUp, ThumbsDown, Minus } from 'lucide-react';
import { BarChart, Bar, PieChart as RechartsPieChart, Cell, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line, Pie, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar } from 'recharts';

interface SurveyResultsProps {
  survey: any;
  onBack: () => void;
}

const mockResults = {
  overview: {
    totalResponses: 1000,
    completionRate: 94,
    averageTime: "4.2 minutes",
    responseQuality: "High"
  },
  nps: {
    score: 42,
    promoters: 450,
    passives: 350,
    detractors: 200,
    breakdown: [
      { score: 0, count: 10 },
      { score: 1, count: 15 },
      { score: 2, count: 20 },
      { score: 3, count: 25 },
      { score: 4, count: 30 },
      { score: 5, count: 35 },
      { score: 6, count: 65 },
      { score: 7, count: 150 },
      { score: 8, count: 200 },
      { score: 9, count: 220 },
      { score: 10, count: 230 }
    ]
  },
  demographics: {
    gender: [
      { name: 'Female', value: 520, percentage: 52 },
      { name: 'Male', value: 450, percentage: 45 },
      { name: 'Other', value: 30, percentage: 3 }
    ],
    age: [
      { name: '18-24', value: 180, percentage: 18 },
      { name: '25-34', value: 320, percentage: 32 },
      { name: '35-44', value: 280, percentage: 28 },
      { name: '45-54', value: 150, percentage: 15 },
      { name: '55+', value: 70, percentage: 7 }
    ],
    income: [
      { name: 'Under $30k', value: 120, percentage: 12 },
      { name: '$30k-$50k', value: 280, percentage: 28 },
      { name: '$50k-$75k', value: 300, percentage: 30 },
      { name: '$75k-$100k', value: 200, percentage: 20 },
      { name: 'Over $100k', value: 100, percentage: 10 }
    ]
  },
  questions: [
    {
      id: 1,
      title: "What's most important when choosing an e-commerce platform?",
      type: "single-choice",
      responses: [
        { option: "Ease of use", count: 450, percentage: 45 },
        { option: "Price", count: 280, percentage: 28 },
        { option: "Features", count: 170, percentage: 17 },
        { option: "Brand reputation", count: 100, percentage: 10 }
      ]
    },
    {
      id: 2,
      title: "How much would you pay monthly for premium features?",
      type: "single-choice",
      responses: [
        { option: "$0-10", count: 300, percentage: 30 },
        { option: "$10-25", count: 420, percentage: 42 },
        { option: "$25-50", count: 200, percentage: 20 },
        { option: "$50+", count: 80, percentage: 8 }
      ]
    },
    {
      id: 3,
      title: "Rate the importance of mobile app support",
      type: "rating-scale",
      average: 4.2,
      responses: [
        { rating: 1, count: 20, percentage: 2 },
        { rating: 2, count: 50, percentage: 5 },
        { rating: 3, count: 180, percentage: 18 },
        { rating: 4, count: 320, percentage: 32 },
        { rating: 5, count: 430, percentage: 43 }
      ]
    },
    {
      id: 4,
      title: "How likely are you to recommend our product?",
      type: "nps",
      npsScore: 42,
      responses: mockResults?.nps?.breakdown || []
    },
    {
      id: 5,
      title: "Product Experience Evaluation",
      type: "matrix",
      matrixData: {
        rows: ["Ease of Use", "Performance", "Design", "Value for Money"],
        columns: ["Poor", "Fair", "Good", "Very Good", "Excellent"],
        data: [
          [5, 10, 25, 35, 25],
          [8, 12, 30, 32, 18],
          [3, 8, 20, 40, 29],
          [12, 18, 28, 25, 17]
        ]
      }
    },
    {
      id: 6,
      title: "Rank features by importance",
      type: "ranking",
      rankingData: [
        { feature: "Performance", avgRank: 1.8, rank1: 45, rank2: 30, rank3: 15, rank4: 10 },
        { feature: "Security", avgRank: 2.1, rank1: 35, rank2: 35, rank3: 20, rank4: 10 },
        { feature: "Design", avgRank: 2.9, rank1: 15, rank2: 25, rank3: 40, rank4: 20 },
        { feature: "Price", avgRank: 3.2, rank1: 5, rank2: 10, rank3: 25, rank4: 60 }
      ]
    }
  ],
  crossTab: {
    question1: "Most important factor",
    question2: "Willingness to pay",
    data: [
      { segment: "Ease of use", low: 180, medium: 200, high: 70 },
      { segment: "Price", low: 150, medium: 100, high: 30 },
      { segment: "Features", low: 50, medium: 80, high: 40 },
      { segment: "Brand", low: 30, medium: 40, high: 30 }
    ]
  },
  sentiment: {
    positive: 73,
    neutral: 19,
    negative: 8
  },
  keyInsights: [
    "45% prioritize ease of use over all other factors",
    "42% willing to pay $10-25/month for premium features", 
    "Mobile support rated 4.2/5 in importance",
    "Age 25-34 segment shows highest engagement",
    "Female respondents 15% more price-sensitive",
    "NPS Score of 42 indicates good product-market fit",
    "Performance ranked as #1 most important feature"
  ]
};

const COLORS = ['#F27405', '#F29F05', '#28a745', '#17a2b8', '#6f42c1'];

export function SurveyResults({ survey, onBack }: SurveyResultsProps) {
  const [selectedFilters, setSelectedFilters] = useState({
    gender: [] as string[],
    ageRange: [18, 65] as number[],
    income: [] as string[]
  });
  const [activeTab, setActiveTab] = useState('overview');
  const [crossTabQuestion1, setCrossTabQuestion1] = useState('1');
  const [crossTabQuestion2, setCrossTabQuestion2] = useState('2');

  const toggleGenderFilter = (gender: string) => {
    setSelectedFilters(prev => ({
      ...prev,
      gender: prev.gender.includes(gender)
        ? prev.gender.filter(g => g !== gender)
        : [...prev.gender, gender]
    }));
  };

  const toggleIncomeFilter = (income: string) => {
    setSelectedFilters(prev => ({
      ...prev,
      income: prev.income.includes(income)
        ? prev.income.filter(i => i !== income)
        : [...prev.income, income]
    }));
  };

  const npsData = mockResults.nps;
  const promoterPercentage = ((npsData.promoters / mockResults.overview.totalResponses) * 100).toFixed(1);
  const passivePercentage = ((npsData.passives / mockResults.overview.totalResponses) * 100).toFixed(1);
  const detractorPercentage = ((npsData.detractors / mockResults.overview.totalResponses) * 100).toFixed(1);

  return (
    <div className="max-w-[1920px] mx-auto space-y-6 px-2 sm:px-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="ghost" onClick={onBack}>
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Surveys
          </Button>
          <div>
            <h1 className="text-foreground mb-2">{survey.title}</h1>
            <p className="text-muted-foreground">Survey Results & Analytics</p>
          </div>
        </div>
        <div className="flex gap-2">
          <Button variant="outline">
            <Share className="w-4 h-4 mr-2" />
            Share
          </Button>
          <Button variant="outline">
            <Download className="w-4 h-4 mr-2" />
            Export
          </Button>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="bg-card border border-border">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm text-muted-foreground flex items-center gap-2">
              <Users className="w-4 h-4" />
              Total Responses
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl text-foreground">{mockResults.overview.totalResponses.toLocaleString()}</p>
          </CardContent>
        </Card>

        <Card className="bg-card border border-border">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm text-muted-foreground">Completion Rate</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl text-foreground">{mockResults.overview.completionRate}%</p>
          </CardContent>
        </Card>

        <Card className="bg-card border border-border">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm text-muted-foreground">Average Time</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl text-foreground">{mockResults.overview.averageTime}</p>
          </CardContent>
        </Card>

        <Card className="bg-card border border-border">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm text-muted-foreground flex items-center gap-2">
              <TrendingUp className="w-4 h-4" />
              NPS Score
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-baseline gap-2">
              <p className="text-3xl text-foreground">{npsData.score}</p>
              <Badge variant="outline" className="bg-green-50 dark:bg-green-950/20 text-green-700 dark:text-green-400 border-green-200 dark:border-green-800">
                Good
              </Badge>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Content */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
        <TabsList className="bg-muted">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="nps">
            <TrendingUp className="w-4 h-4 mr-2" />
            NPS Analysis
          </TabsTrigger>
          <TabsTrigger value="questions">Questions</TabsTrigger>
          <TabsTrigger value="cross-tab">
            <Grid3x3 className="w-4 h-4 mr-2" />
            Cross-Tab
          </TabsTrigger>
          <TabsTrigger value="demographics">Demographics</TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-6">
          {/* Sentiment */}
          <Card className="bg-card border border-border">
            <CardHeader>
              <CardTitle className="text-foreground flex items-center gap-2">
                <MessageSquare className="w-5 h-5 text-brand-orange" />
                Overall Sentiment
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm text-muted-foreground">Positive</span>
                    <span className="text-sm text-foreground">{mockResults.sentiment.positive}%</span>
                  </div>
                  <Progress value={mockResults.sentiment.positive} className="h-2" />
                </div>
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm text-muted-foreground">Neutral</span>
                    <span className="text-sm text-foreground">{mockResults.sentiment.neutral}%</span>
                  </div>
                  <Progress value={mockResults.sentiment.neutral} className="h-2" />
                </div>
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm text-muted-foreground">Negative</span>
                    <span className="text-sm text-foreground">{mockResults.sentiment.negative}%</span>
                  </div>
                  <Progress value={mockResults.sentiment.negative} className="h-2" />
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Key Insights */}
          <Card className="bg-card border border-border">
            <CardHeader>
              <CardTitle className="text-foreground flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-brand-gold" />
                AI-Generated Insights
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="space-y-3">
                {mockResults.keyInsights.map((insight, index) => (
                  <li key={index} className="flex items-start gap-3 text-sm text-foreground">
                    <span className="text-brand-orange mt-1">•</span>
                    <span>{insight}</span>
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>
        </TabsContent>

        {/* NPS Analysis Tab */}
        <TabsContent value="nps" className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <Card className="bg-card border border-border">
              <CardHeader className="pb-3">
                <CardTitle className="text-sm text-muted-foreground flex items-center gap-2">
                  <ThumbsUp className="w-4 h-4 text-green-600" />
                  Promoters (9-10)
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-3xl text-foreground mb-1">{npsData.promoters}</p>
                <p className="text-sm text-muted-foreground">{promoterPercentage}% of responses</p>
                <Progress value={parseFloat(promoterPercentage)} className="h-2 mt-3" />
              </CardContent>
            </Card>

            <Card className="bg-card border border-border">
              <CardHeader className="pb-3">
                <CardTitle className="text-sm text-muted-foreground flex items-center gap-2">
                  <Minus className="w-4 h-4 text-yellow-600" />
                  Passives (7-8)
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-3xl text-foreground mb-1">{npsData.passives}</p>
                <p className="text-sm text-muted-foreground">{passivePercentage}% of responses</p>
                <Progress value={parseFloat(passivePercentage)} className="h-2 mt-3" />
              </CardContent>
            </Card>

            <Card className="bg-card border border-border">
              <CardHeader className="pb-3">
                <CardTitle className="text-sm text-muted-foreground flex items-center gap-2">
                  <ThumbsDown className="w-4 h-4 text-red-600" />
                  Detractors (0-6)
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-3xl text-foreground mb-1">{npsData.detractors}</p>
                <p className="text-sm text-muted-foreground">{detractorPercentage}% of responses</p>
                <Progress value={parseFloat(detractorPercentage)} className="h-2 mt-3" />
              </CardContent>
            </Card>
          </div>

          <Card className="bg-card border border-border">
            <CardHeader>
              <CardTitle className="text-foreground">NPS Score Distribution</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={npsData.breakdown}>
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                  <XAxis 
                    dataKey="score" 
                    stroke="hsl(var(--muted-foreground))"
                    tick={{ fill: 'hsl(var(--muted-foreground))' }}
                  />
                  <YAxis 
                    stroke="hsl(var(--muted-foreground))"
                    tick={{ fill: 'hsl(var(--muted-foreground))' }}
                  />
                  <Tooltip 
                    contentStyle={{
                      backgroundColor: 'hsl(var(--card))',
                      border: '1px solid hsl(var(--border))',
                      borderRadius: '8px'
                    }}
                  />
                  <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                    {npsData.breakdown.map((entry, index) => (
                      <Cell 
                        key={`cell-${index}`} 
                        fill={
                          entry.score <= 6 ? '#ef4444' : 
                          entry.score <= 8 ? '#f59e0b' : 
                          '#10b981'
                        } 
                      />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          <Card className="bg-muted/50 border border-border">
            <CardHeader>
              <CardTitle className="text-foreground text-sm">NPS Score Interpretation</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">Score Range</span>
                <Badge variant="outline">{npsData.score}</Badge>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">Classification</span>
                <Badge variant="outline" className="bg-green-50 dark:bg-green-950/20 text-green-700 dark:text-green-400 border-green-200 dark:border-green-800">
                  Good (30-50)
                </Badge>
              </div>
              <p className="text-xs text-muted-foreground pt-2">
                Your NPS score indicates strong product-market fit with room for improvement. Focus on converting passives to promoters.
              </p>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Questions Tab */}
        <TabsContent value="questions" className="space-y-6">
          {mockResults.questions.map((question) => (
            <Card key={question.id} className="bg-card border border-border">
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <CardTitle className="text-foreground mb-2">{question.title}</CardTitle>
                    <Badge variant="outline" className="text-xs">
                      {question.type === 'single-choice' && 'Single Choice'}
                      {question.type === 'rating-scale' && 'Rating Scale'}
                      {question.type === 'nps' && 'NPS Question'}
                      {question.type === 'matrix' && 'Matrix Question'}
                      {question.type === 'ranking' && 'Ranking Question'}
                    </Badge>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                {/* Single/Multiple Choice */}
                {question.type === 'single-choice' && (
                  <div className="space-y-3">
                    {question.responses.map((response: any, index: number) => (
                      <div key={index}>
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-sm text-muted-foreground">{response.option}</span>
                          <span className="text-sm text-foreground">{response.percentage}%</span>
                        </div>
                        <Progress value={response.percentage} className="h-2" />
                      </div>
                    ))}
                  </div>
                )}

                {/* Rating Scale */}
                {question.type === 'rating-scale' && (
                  <div>
                    <div className="mb-4">
                      <p className="text-sm text-muted-foreground mb-1">Average Rating</p>
                      <p className="text-2xl text-foreground">{question.average}/5</p>
                    </div>
                    <ResponsiveContainer width="100%" height={200}>
                      <BarChart data={question.responses}>
                        <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                        <XAxis 
                          dataKey="rating" 
                          stroke="hsl(var(--muted-foreground))"
                          tick={{ fill: 'hsl(var(--muted-foreground))' }}
                        />
                        <YAxis 
                          stroke="hsl(var(--muted-foreground))"
                          tick={{ fill: 'hsl(var(--muted-foreground))' }}
                        />
                        <Tooltip 
                          contentStyle={{
                            backgroundColor: 'hsl(var(--card))',
                            border: '1px solid hsl(var(--border))',
                            borderRadius: '8px'
                          }}
                        />
                        <Bar dataKey="count" fill="#F27405" radius={[4, 4, 0, 0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                )}

                {/* Matrix Question */}
                {question.type === 'matrix' && question.matrixData && (
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr>
                          <th className="text-left p-2 text-muted-foreground"></th>
                          {question.matrixData.columns.map((col: string, idx: number) => (
                            <th key={idx} className="text-center p-2 text-muted-foreground">{col}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {question.matrixData.rows.map((row: string, rowIdx: number) => (
                          <tr key={rowIdx} className="border-t border-border">
                            <td className="p-2 text-foreground">{row}</td>
                            {question.matrixData.data[rowIdx].map((value: number, colIdx: number) => (
                              <td key={colIdx} className="text-center p-2">
                                <div className="flex items-center justify-center">
                                  <div 
                                    className="w-full max-w-[60px] h-8 flex items-center justify-center rounded"
                                    style={{
                                      backgroundColor: `rgba(242, 116, 5, ${value / 100})`,
                                      color: value > 50 ? 'white' : 'inherit'
                                    }}
                                  >
                                    {value}%
                                  </div>
                                </div>
                              </td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}

                {/* Ranking Question */}
                {question.type === 'ranking' && question.rankingData && (
                  <div className="space-y-3">
                    {question.rankingData.map((item: any, index: number) => (
                      <div key={index} className="border border-border rounded-lg p-4">
                        <div className="flex items-center justify-between mb-3">
                          <div className="flex items-center gap-3">
                            <Badge variant="outline" className="text-lg px-3">#{index + 1}</Badge>
                            <div>
                              <p className="text-sm text-foreground">{item.feature}</p>
                              <p className="text-xs text-muted-foreground">Avg. Rank: {item.avgRank}</p>
                            </div>
                          </div>
                        </div>
                        <div className="grid grid-cols-4 gap-2">
                          <div className="text-center">
                            <p className="text-xs text-muted-foreground mb-1">1st</p>
                            <p className="text-sm text-foreground">{item.rank1}%</p>
                          </div>
                          <div className="text-center">
                            <p className="text-xs text-muted-foreground mb-1">2nd</p>
                            <p className="text-sm text-foreground">{item.rank2}%</p>
                          </div>
                          <div className="text-center">
                            <p className="text-xs text-muted-foreground mb-1">3rd</p>
                            <p className="text-sm text-foreground">{item.rank3}%</p>
                          </div>
                          <div className="text-center">
                            <p className="text-xs text-muted-foreground mb-1">4th</p>
                            <p className="text-sm text-foreground">{item.rank4}%</p>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </TabsContent>

        {/* Cross-Tab Analysis */}
        <TabsContent value="cross-tab" className="space-y-6">
          <Card className="bg-card border border-border">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-foreground flex items-center gap-2">
                  <Grid3x3 className="w-5 h-5 text-brand-orange" />
                  Cross-Tabulation Analysis
                </CardTitle>
                <div className="flex gap-2">
                  <Select value={crossTabQuestion1} onValueChange={setCrossTabQuestion1}>
                    <SelectTrigger className="w-[200px]">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {mockResults.questions.slice(0, 3).map((q, idx) => (
                        <SelectItem key={idx} value={String(idx + 1)}>Q{idx + 1}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <span className="text-muted-foreground self-center">×</span>
                  <Select value={crossTabQuestion2} onValueChange={setCrossTabQuestion2}>
                    <SelectTrigger className="w-[200px]">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {mockResults.questions.slice(0, 3).map((q, idx) => (
                        <SelectItem key={idx} value={String(idx + 1)}>Q{idx + 1}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={400}>
                <BarChart data={mockResults.crossTab.data}>
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                  <XAxis 
                    dataKey="segment" 
                    stroke="hsl(var(--muted-foreground))"
                    tick={{ fill: 'hsl(var(--muted-foreground))' }}
                  />
                  <YAxis 
                    stroke="hsl(var(--muted-foreground))"
                    tick={{ fill: 'hsl(var(--muted-foreground))' }}
                  />
                  <Tooltip 
                    contentStyle={{
                      backgroundColor: 'hsl(var(--card))',
                      border: '1px solid hsl(var(--border))',
                      borderRadius: '8px'
                    }}
                  />
                  <Bar dataKey="low" fill="#F27405" name="Low ($0-10)" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="medium" fill="#F29F05" name="Medium ($10-25)" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="high" fill="#28a745" name="High ($25+)" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>

              <div className="mt-6 p-4 border border-border rounded-lg bg-muted/30">
                <p className="text-sm text-foreground mb-2">Key Findings:</p>
                <ul className="space-y-1 text-sm text-muted-foreground">
                  <li>• Respondents prioritizing "Ease of use" show higher willingness to pay</li>
                  <li>• Price-conscious segment focuses on cost over features</li>
                  <li>• Feature enthusiasts correlate with premium pricing acceptance</li>
                </ul>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Demographics Tab */}
        <TabsContent value="demographics" className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Gender */}
            <Card className="bg-card border border-border">
              <CardHeader>
                <CardTitle className="text-foreground">Gender</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={200}>
                  <RechartsPieChart>
                    <Pie
                      data={mockResults.demographics.gender}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ name, percentage }) => `${name} ${percentage}%`}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {mockResults.demographics.gender.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </RechartsPieChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            {/* Age */}
            <Card className="bg-card border border-border">
              <CardHeader>
                <CardTitle className="text-foreground">Age Distribution</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {mockResults.demographics.age.map((age, index) => (
                    <div key={index}>
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-sm text-muted-foreground">{age.name}</span>
                        <span className="text-sm text-foreground">{age.percentage}%</span>
                      </div>
                      <Progress value={age.percentage} className="h-2" />
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Income */}
            <Card className="bg-card border border-border">
              <CardHeader>
                <CardTitle className="text-foreground">Income</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {mockResults.demographics.income.map((income, index) => (
                    <div key={index}>
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-sm text-muted-foreground">{income.name}</span>
                        <span className="text-sm text-foreground">{income.percentage}%</span>
                      </div>
                      <Progress value={income.percentage} className="h-2" />
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}

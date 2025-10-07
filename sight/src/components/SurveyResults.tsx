import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Slider } from './ui/slider';
import { Checkbox } from './ui/checkbox';
import { Label } from './ui/label';
import { ArrowLeft, Filter, Download, Share, TrendingUp, Users, BarChart3, PieChart, MessageSquare } from 'lucide-react';
import { BarChart, Bar, PieChart as RechartsPieChart, Cell, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line, Pie } from 'recharts';

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
    }
  ],
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
    "Female respondents 15% more price-sensitive"
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

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="ghost" onClick={onBack}>
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Surveys
          </Button>
          <div>
            <h1 className="text-3xl brand-orange">{survey.title}</h1>
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
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="bg-card border border-border">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Total Responses</p>
                <p className="text-2xl brand-orange">{mockResults.overview.totalResponses.toLocaleString()}</p>
              </div>
              <Users className="w-8 h-8 text-primary" />
            </div>
          </CardContent>
        </Card>
        
        <Card className="bg-card border border-border">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Completion Rate</p>
                <p className="text-2xl brand-orange">{mockResults.overview.completionRate}%</p>
              </div>
              <TrendingUp className="w-8 h-8 text-primary" />
            </div>
          </CardContent>
        </Card>
        
        <Card className="bg-card border border-border">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Avg. Time</p>
                <p className="text-2xl brand-orange">{mockResults.overview.averageTime}</p>
              </div>
              <BarChart3 className="w-8 h-8 text-primary" />
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Filters Sidebar */}
        <div className="lg:col-span-1">
          <Card className="bg-card border border-border sticky top-6">
            <CardHeader>
              <CardTitle className="text-card-foreground flex items-center gap-2">
                <Filter className="w-5 h-5" />
                Filters & Segments
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Gender Filter */}
              <div className="space-y-3">
                <Label className="text-sm">Gender</Label>
                <div className="space-y-2">
                  {mockResults.demographics.gender.map((item) => (
                    <div key={item.name} className="flex items-center space-x-2">
                      <Checkbox
                        id={`gender-${item.name}`}
                        checked={selectedFilters.gender.includes(item.name)}
                        onCheckedChange={() => toggleGenderFilter(item.name)}
                      />
                      <label htmlFor={`gender-${item.name}`} className="text-sm text-card-foreground">
                        {item.name} ({item.percentage}%)
                      </label>
                    </div>
                  ))}
                </div>
              </div>

              {/* Age Range Filter */}
              <div className="space-y-3">
                <Label className="text-sm">Age Range</Label>
                <div className="px-2">
                  <Slider
                    value={selectedFilters.ageRange}
                    onValueChange={(value) => setSelectedFilters(prev => ({ ...prev, ageRange: value }))}
                    min={18}
                    max={65}
                    step={1}
                    className="w-full"
                  />
                  <div className="flex justify-between text-xs text-muted-foreground mt-1">
                    <span>{selectedFilters.ageRange[0]}</span>
                    <span>{selectedFilters.ageRange[1]}</span>
                  </div>
                </div>
              </div>

              {/* Income Filter */}
              <div className="space-y-3">
                <Label className="text-sm">Income</Label>
                <div className="space-y-2">
                  {mockResults.demographics.income.map((item) => (
                    <div key={item.name} className="flex items-center space-x-2">
                      <Checkbox
                        id={`income-${item.name}`}
                        checked={selectedFilters.income.includes(item.name)}
                        onCheckedChange={() => toggleIncomeFilter(item.name)}
                      />
                      <label htmlFor={`income-${item.name}`} className="text-sm text-card-foreground">
                        {item.name} ({item.percentage}%)
                      </label>
                    </div>
                  ))}
                </div>
              </div>

              <Button 
                variant="outline" 
                size="sm" 
                className="w-full"
                onClick={() => setSelectedFilters({ gender: [], ageRange: [18, 65], income: [] })}
              >
                Clear Filters
              </Button>
            </CardContent>
          </Card>
        </div>

        {/* Main Results */}
        <div className="lg:col-span-3">
          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList className="bg-muted border border-border shadow-sm">
              <TabsTrigger value="overview" className="data-[state=active]:bg-card data-[state=active]:text-card-foreground data-[state=active]:shadow-sm">Overview</TabsTrigger>
              <TabsTrigger value="questions" className="data-[state=active]:bg-card data-[state=active]:text-card-foreground data-[state=active]:shadow-sm">Questions</TabsTrigger>
              <TabsTrigger value="segments" className="data-[state=active]:bg-card data-[state=active]:text-card-foreground data-[state=active]:shadow-sm">Segments</TabsTrigger>
              <TabsTrigger value="insights" className="data-[state=active]:bg-card data-[state=active]:text-card-foreground data-[state=active]:shadow-sm">Insights</TabsTrigger>
            </TabsList>

            <TabsContent value="overview" className="space-y-6">
              {/* Response Distribution */}
              <Card className="bg-card border border-border">
                <CardHeader>
                  <CardTitle className="text-card-foreground">Response Distribution</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div>
                      <h4 className="text-sm text-muted-foreground mb-4">Gender</h4>
                      <ResponsiveContainer width="100%" height={200}>
                        <RechartsPieChart>
                          <Pie
                            data={mockResults.demographics.gender}
                            cx="50%"
                            cy="50%"
                            innerRadius={40}
                            outerRadius={80}
                            dataKey="value"
                          >
                            {mockResults.demographics.gender.map((entry, index) => (
                              <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                            ))}
                          </Pie>
                          <Tooltip formatter={(value: any) => [value, 'Responses']} />
                        </RechartsPieChart>
                      </ResponsiveContainer>
                    </div>
                    
                    <div>
                      <h4 className="text-sm text-muted-foreground mb-4">Age Groups</h4>
                      <ResponsiveContainer width="100%" height={200}>
                        <BarChart data={mockResults.demographics.age}>
                          <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,0,0,0.1)" />
                          <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                          <YAxis tick={{ fontSize: 12 }} />
                          <Tooltip />
                          <Bar dataKey="value" fill="#F27405" />
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                    
                    <div>
                      <h4 className="text-sm text-muted-foreground mb-4">Income Distribution</h4>
                      <ResponsiveContainer width="100%" height={200}>
                        <BarChart data={mockResults.demographics.income} layout="horizontal">
                          <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,0,0,0.1)" />
                          <XAxis type="number" tick={{ fontSize: 12 }} />
                          <YAxis dataKey="name" type="category" tick={{ fontSize: 10 }} width={80} />
                          <Tooltip />
                          <Bar dataKey="value" fill="#F29F05" />
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="questions" className="space-y-6">
              {mockResults.questions.map((question) => (
                <Card key={question.id} className="bg-card border border-border">
                  <CardHeader>
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <CardTitle className="text-card-foreground text-lg mb-2">
                          Q{question.id}: {question.title}
                        </CardTitle>
                        <Badge variant="outline">
                          {question.type === 'single-choice' ? 'Single Choice' : 
                           question.type === 'rating-scale' ? 'Rating Scale' : 'Multiple Choice'}
                        </Badge>
                      </div>
                      {question.type === 'rating-scale' && (
                        <div className="text-right">
                          <p className="text-sm text-muted-foreground">Average Score</p>
                          <p className="text-2xl brand-orange">{question.average}/5</p>
                        </div>
                      )}
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                      <div>
                        <ResponsiveContainer width="100%" height={300}>
                          {question.type === 'rating-scale' ? (
                            <BarChart data={question.responses}>
                              <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,0,0,0.1)" />
                              <XAxis dataKey="rating" />
                              <YAxis />
                              <Tooltip />
                              <Bar dataKey="count" fill="#F27405" />
                            </BarChart>
                          ) : (
                            <RechartsPieChart>
                              <Pie
                                data={question.responses}
                                cx="50%"
                                cy="50%"
                                innerRadius={60}
                                outerRadius={120}
                                dataKey="count"
                                nameKey="option"
                              >
                                {question.responses.map((entry, index) => (
                                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                ))}
                              </Pie>
                              <Tooltip formatter={(value: any) => [value, 'Responses']} />
                            </RechartsPieChart>
                          )}
                        </ResponsiveContainer>
                      </div>
                      
                      <div className="space-y-3">
                        <h4 className="text-sm text-muted-foreground">Response Breakdown</h4>
                        {question.responses.map((response, index) => (
                          <div key={index} className="flex items-center justify-between p-3 bg-muted/30 rounded-lg">
                            <div className="flex items-center gap-3">
                              <div 
                                className="w-4 h-4 rounded"
                                style={{ backgroundColor: COLORS[index % COLORS.length] }}
                              />
                              <span className="text-sm text-card-foreground">
                                {question.type === 'rating-scale' ? `${response.rating} Star` : response.option}
                              </span>
                            </div>
                            <div className="text-right">
                              <p className="text-sm brand-orange">{response.percentage}%</p>
                              <p className="text-xs text-muted-foreground">{response.count} responses</p>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </TabsContent>

            <TabsContent value="segments" className="space-y-6">
              <Card className="bg-card border border-border">
                <CardHeader>
                  <CardTitle className="text-card-foreground">Segment Comparison</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-center py-12 text-muted-foreground">
                    <PieChart className="w-12 h-12 mx-auto mb-4 text-muted-foreground/50" />
                    <p>Advanced segment comparison coming soon</p>
                    <p className="text-sm">Compare responses across different demographic groups</p>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="insights" className="space-y-6">
              <Card className="bg-card border border-border">
                <CardHeader>
                  <CardTitle className="text-card-foreground">Key Insights</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {mockResults.keyInsights.map((insight, index) => (
                      <div key={index} className="flex items-start gap-3 p-4 bg-muted/30 rounded-lg">
                        <div className="w-6 h-6 rounded-full bg-primary text-primary-foreground flex items-center justify-center text-sm flex-shrink-0">
                          {index + 1}
                        </div>
                        <p className="text-card-foreground">{insight}</p>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>


            </TabsContent>
          </Tabs>
        </div>
      </div>
    </div>
  );
}
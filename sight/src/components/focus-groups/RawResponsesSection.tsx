import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '../ui/accordion';
import { Badge } from '../ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Input } from '../ui/input';
import { Search, User } from 'lucide-react';

interface Response {
  id: number;
  personaName: string;
  personaInitials: string;
  response: string;
  timestamp: string;
  sentiment?: 'positive' | 'neutral' | 'negative';
}

interface Question {
  id: number;
  question: string;
  responses: Response[];
}

// Mock data
const mockQuestions: Question[] = [
  {
    id: 1,
    question: "What features are most important to you when choosing a product like this?",
    responses: [
      {
        id: 1,
        personaName: "Sarah Johnson",
        personaInitials: "SJ",
        response: "I value ease of use and integration with existing tools above everything else. Time-saving features are crucial for my workflow because I manage multiple campaigns simultaneously. The ability to automate repetitive tasks would be a game-changer for my team.",
        timestamp: "2:34 PM",
        sentiment: "positive"
      },
      {
        id: 2,
        personaName: "Michael Chen",
        personaInitials: "MC",
        response: "Advanced customization options and API access are important to me. I need flexibility for different use cases and the ability to integrate deeply with our existing development tools. Scalability is also a key concern as our team grows.",
        timestamp: "2:35 PM",
        sentiment: "positive"
      },
      {
        id: 3,
        personaName: "Emily Rodriguez",
        personaInitials: "ER",
        response: "Cost-effectiveness and reliability are my top priorities. As a small business owner, I need something that works consistently without breaking the bank. Support and documentation are also critical because I don't have a technical team.",
        timestamp: "2:36 PM",
        sentiment: "neutral"
      },
      {
        id: 4,
        personaName: "David Kim",
        personaInitials: "DK",
        response: "The user interface needs to be intuitive and visually appealing. I don't want to spend hours learning a new tool. Good design and thoughtful UX patterns make all the difference in adoption.",
        timestamp: "2:37 PM",
        sentiment: "positive"
      }
    ]
  },
  {
    id: 2,
    question: "How would you typically use this product in your daily work?",
    responses: [
      {
        id: 5,
        personaName: "Sarah Johnson",
        personaInitials: "SJ",
        response: "Primarily for campaign management and team collaboration. I would use it daily for project planning, tracking progress, and coordinating with team members across different time zones.",
        timestamp: "2:40 PM",
        sentiment: "positive"
      },
      {
        id: 6,
        personaName: "Michael Chen",
        personaInitials: "MC",
        response: "For prototyping and development workflows. Integration with development tools would be essential - things like GitHub, Jira, and our CI/CD pipeline. I'd expect to use it multiple times throughout the day.",
        timestamp: "2:41 PM",
        sentiment: "neutral"
      },
      {
        id: 7,
        personaName: "Emily Rodriguez",
        personaInitials: "ER",
        response: "To streamline business operations and improve customer communication. I need mobile access since I'm often away from my desk meeting with clients. Quick actions and notifications would be very helpful.",
        timestamp: "2:42 PM",
        sentiment: "positive"
      }
    ]
  },
  {
    id: 3,
    question: "What concerns or hesitations do you have about adopting this type of product?",
    responses: [
      {
        id: 8,
        personaName: "Sarah Johnson",
        personaInitials: "SJ",
        response: "The learning curve for my team and migration from our current tools. We've invested time in our existing workflows, so the transition needs to be smooth and well-supported.",
        timestamp: "2:45 PM",
        sentiment: "neutral"
      },
      {
        id: 9,
        personaName: "Emily Rodriguez",
        personaInitials: "ER",
        response: "Pricing is definitely a concern. I need to see clear ROI before committing to a subscription. Also worried about vendor lock-in and data portability if we decide to switch later.",
        timestamp: "2:46 PM",
        sentiment: "negative"
      },
      {
        id: 10,
        personaName: "David Kim",
        personaInitials: "DK",
        response: "Compatibility with our design tools and whether it supports the file formats we use. Also concerned about performance with large projects.",
        timestamp: "2:47 PM",
        sentiment: "neutral"
      }
    ]
  }
];

export function RawResponsesSection() {
  const [selectedPersona, setSelectedPersona] = useState<string>('all');
  const [selectedQuestion, setSelectedQuestion] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');

  // Extract unique personas
  const personas = Array.from(
    new Set(
      mockQuestions.flatMap(q => q.responses.map(r => r.personaName))
    )
  );

  // Filter questions and responses
  const filteredQuestions = mockQuestions.map(question => {
    let filteredResponses = question.responses;

    // Filter by persona
    if (selectedPersona !== 'all') {
      filteredResponses = filteredResponses.filter(
        r => r.personaName === selectedPersona
      );
    }

    // Filter by search query
    if (searchQuery) {
      filteredResponses = filteredResponses.filter(
        r => r.response.toLowerCase().includes(searchQuery.toLowerCase()) ||
            r.personaName.toLowerCase().includes(searchQuery.toLowerCase())
      );
    }

    return {
      ...question,
      responses: filteredResponses
    };
  }).filter(q => {
    // Filter by selected question
    if (selectedQuestion !== 'all') {
      return q.id === parseInt(selectedQuestion);
    }
    // Only show questions that have responses after filtering
    return q.responses.length > 0;
  });

  const getSentimentColor = (sentiment?: string) => {
    switch (sentiment) {
      case 'positive':
        return 'border-chart-1/30 text-chart-1 bg-chart-1/5';
      case 'negative':
        return 'border-destructive/30 text-destructive bg-destructive/5';
      default:
        return 'border-border text-muted-foreground';
    }
  };

  const totalResponses = filteredQuestions.reduce((sum, q) => sum + q.responses.length, 0);

  return (
    <div className="space-y-6">
      {/* Filters */}
      <Card className="bg-card border border-border shadow-sm">
        <CardHeader>
          <CardTitle className="text-foreground">Filter Responses</CardTitle>
          <p className="text-sm text-muted-foreground">
            Showing {totalResponses} {totalResponses === 1 ? 'response' : 'responses'}
          </p>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Search */}
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <Input
                placeholder="Search responses..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-9"
              />
            </div>

            {/* Persona filter */}
            <Select value={selectedPersona} onValueChange={setSelectedPersona}>
              <SelectTrigger>
                <SelectValue placeholder="All participants" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All participants</SelectItem>
                {personas.map(persona => (
                  <SelectItem key={persona} value={persona}>
                    {persona}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            {/* Question filter */}
            <Select value={selectedQuestion} onValueChange={setSelectedQuestion}>
              <SelectTrigger>
                <SelectValue placeholder="All questions" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All questions</SelectItem>
                {mockQuestions.map(q => (
                  <SelectItem key={q.id} value={q.id.toString()}>
                    Q{q.id}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Responses */}
      {filteredQuestions.length === 0 ? (
        <Card className="bg-card border border-border shadow-sm">
          <CardContent className="text-center py-12">
            <User className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-foreground mb-2">No Responses Found</h3>
            <p className="text-muted-foreground">
              Try adjusting your filters or search query
            </p>
          </CardContent>
        </Card>
      ) : (
        <Accordion type="multiple" defaultValue={filteredQuestions.map(q => `question-${q.id}`)} className="space-y-4">
          {filteredQuestions.map((question) => (
            <AccordionItem 
              key={question.id} 
              value={`question-${question.id}`}
              className="bg-card border border-border rounded-lg shadow-sm overflow-hidden"
            >
              <AccordionTrigger className="px-6 py-4 hover:bg-muted/50 transition-colors [&[data-state=open]]:border-b [&[data-state=open]]:border-border">
                <div className="flex items-start gap-4 text-left flex-1">
                  <Badge className="bg-brand-orange text-white shrink-0 mt-0.5">
                    Q{question.id}
                  </Badge>
                  <div className="flex-1">
                    <h3 className="text-foreground mb-1">{question.question}</h3>
                    <p className="text-sm text-muted-foreground">
                      {question.responses.length} {question.responses.length === 1 ? 'response' : 'responses'}
                    </p>
                  </div>
                </div>
              </AccordionTrigger>
              <AccordionContent className="px-6 py-4">
                <div className="space-y-4">
                  {question.responses.map((response) => (
                    <div 
                      key={response.id} 
                      className="p-4 bg-muted/50 rounded-lg border border-border"
                    >
                      <div className="flex items-start gap-3 mb-3">
                        <div className="w-10 h-10 rounded-full bg-brand-orange flex items-center justify-center shrink-0">
                          <span className="text-white text-sm">
                            {response.personaInitials}
                          </span>
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 flex-wrap mb-1">
                            <span className="text-foreground">{response.personaName}</span>
                            {response.sentiment && (
                              <Badge 
                                variant="outline" 
                                className={getSentimentColor(response.sentiment)}
                              >
                                {response.sentiment}
                              </Badge>
                            )}
                          </div>
                          <span className="text-xs text-muted-foreground">{response.timestamp}</span>
                        </div>
                      </div>
                      <p className="text-foreground leading-relaxed">
                        {response.response}
                      </p>
                    </div>
                  ))}
                </div>
              </AccordionContent>
            </AccordionItem>
          ))}
        </Accordion>
      )}
    </div>
  );
}

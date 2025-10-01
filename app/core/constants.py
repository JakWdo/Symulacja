"""Shared constants for demographic distributions and defaults."""

# Default demographic distributions
DEFAULT_AGE_GROUPS = {
    "18-24": 0.15,
    "25-34": 0.25,
    "35-44": 0.20,
    "45-54": 0.18,
    "55-64": 0.12,
    "65+": 0.10,
}

DEFAULT_GENDERS = {
    "male": 0.49,
    "female": 0.49,
    "non-binary": 0.02,
}

DEFAULT_LOCATIONS = {
    "New York, NY": 0.15,
    "Los Angeles, CA": 0.12,
    "Chicago, IL": 0.10,
    "Houston, TX": 0.08,
    "Phoenix, AZ": 0.06,
    "Philadelphia, PA": 0.06,
    "San Antonio, TX": 0.05,
    "San Diego, CA": 0.05,
    "Dallas, TX": 0.05,
    "San Jose, CA": 0.04,
    "Other": 0.24,
}

DEFAULT_EDUCATION_LEVELS = {
    "High school": 0.25,
    "Some college": 0.20,
    "Bachelor's degree": 0.30,
    "Master's degree": 0.15,
    "Doctorate": 0.05,
    "Other": 0.05,
}

DEFAULT_INCOME_BRACKETS = {
    "< $25k": 0.15,
    "$25k-$50k": 0.20,
    "$50k-$75k": 0.22,
    "$75k-$100k": 0.18,
    "$100k-$150k": 0.15,
    "> $150k": 0.10,
}

# Persona personality defaults - EXPANDED for diversity
DEFAULT_OCCUPATIONS = [
    # Tech & Engineering
    "Software Engineer", "Data Scientist", "UX Designer", "Product Manager", "DevOps Engineer",
    "Cybersecurity Analyst", "AI/ML Engineer", "Cloud Architect", "QA Engineer", "Technical Writer",
    # Business & Management
    "Business Analyst", "Operations Manager", "Project Manager", "Strategy Consultant", "CFO",
    "Entrepreneur", "Startup Founder", "Business Development Manager", "Account Executive",
    # Marketing & Sales
    "Marketing Manager", "Brand Strategist", "Content Creator", "Social Media Manager", "SEO Specialist",
    "Growth Hacker", "Sales Director", "Customer Success Manager", "PR Specialist",
    # Creative & Design
    "Graphic Designer", "Art Director", "Video Editor", "Photographer", "Illustrator",
    "Copywriter", "Creative Director", "Motion Designer", "UI Designer", "Brand Designer",
    # Healthcare & Science
    "Physician", "Nurse Practitioner", "Research Scientist", "Pharmacist", "Physical Therapist",
    "Clinical Psychologist", "Biotech Researcher", "Medical Device Engineer", "Healthcare Administrator",
    # Education & Training
    "University Professor", "High School Teacher", "Corporate Trainer", "Education Consultant",
    "Curriculum Designer", "EdTech Specialist", "School Principal", "Online Course Creator",
    # Finance & Legal
    "Financial Analyst", "Investment Banker", "Accountant", "Tax Consultant", "Lawyer",
    "Paralegal", "Compliance Officer", "Risk Analyst", "Financial Advisor", "Auditor",
    # Service & Hospitality
    "Restaurant Manager", "Hotel Manager", "Event Planner", "Chef", "Travel Agent",
    "Customer Service Manager", "Retail Manager", "Personal Trainer", "Life Coach",
    # Trades & Manual
    "Electrician", "Plumber", "Carpenter", "Mechanic", "HVAC Technician",
    "Construction Manager", "Landscaper", "Real Estate Agent",
    # Arts & Entertainment
    "Musician", "Actor", "Film Producer", "Journalist", "Podcaster", "YouTuber",
    "Gallery Curator", "Fashion Designer", "Interior Designer",
    # Government & Nonprofit
    "Social Worker", "Policy Analyst", "Nonprofit Director", "Community Organizer",
    "Urban Planner", "Environmental Scientist", "Public Health Specialist",
]

DEFAULT_VALUES = [
    # Personal Growth
    "Personal Growth", "Self-Improvement", "Continuous Learning", "Curiosity", "Authenticity",
    "Self-Expression", "Independence", "Autonomy", "Creativity", "Innovation",
    # Relationships & Community
    "Family", "Friendship", "Love", "Community", "Belonging", "Connection", "Empathy",
    "Compassion", "Kindness", "Generosity", "Collaboration", "Teamwork",
    # Achievement & Success
    "Ambition", "Success", "Excellence", "Achievement", "Recognition", "Status",
    "Wealth", "Career Advancement", "Power", "Leadership", "Competition",
    # Ethical & Moral
    "Integrity", "Honesty", "Fairness", "Justice", "Equality", "Diversity",
    "Inclusion", "Respect", "Trust", "Loyalty", "Responsibility",
    # Lifestyle & Wellbeing
    "Health", "Wellness", "Fitness", "Balance", "Work-Life Balance", "Happiness",
    "Joy", "Fun", "Adventure", "Freedom", "Flexibility", "Simplicity",
    # Social & Environmental
    "Sustainability", "Environmentalism", "Social Justice", "Activism", "Philanthropy",
    "Volunteering", "Making a Difference", "Legacy", "Impact",
    # Intellectual & Spiritual
    "Wisdom", "Knowledge", "Truth", "Spirituality", "Mindfulness", "Peace",
    "Tradition", "Heritage", "Culture", "Art", "Beauty",
    # Practical & Security
    "Security", "Stability", "Predictability", "Efficiency", "Productivity",
    "Organization", "Planning", "Pragmatism", "Resourcefulness",
]

DEFAULT_INTERESTS = [
    # Sports & Fitness
    "Running", "Yoga", "Weightlifting", "Cycling", "Swimming", "Hiking", "Rock Climbing",
    "Martial Arts", "CrossFit", "Dance", "Team Sports", "Tennis", "Golf",
    # Arts & Creativity
    "Painting", "Drawing", "Photography", "Videography", "Music", "Playing Instruments",
    "Singing", "Writing", "Poetry", "Creative Writing", "Journaling", "Calligraphy",
    "Sculpture", "Pottery", "Crafting", "Knitting", "Sewing",
    # Technology & Gaming
    "Gaming", "Video Games", "Board Games", "Virtual Reality", "Coding", "Programming",
    "3D Modeling", "Robotics", "Drones", "Smart Home Tech", "Cryptocurrency", "NFTs",
    # Food & Cooking
    "Cooking", "Baking", "Grilling", "Wine Tasting", "Coffee", "Tea", "Craft Beer",
    "Food Blogging", "Recipe Development", "Meal Prep", "Vegetarian Cooking", "International Cuisine",
    # Travel & Adventure
    "Travel", "Backpacking", "Road Trips", "International Travel", "Solo Travel",
    "Adventure Travel", "Camping", "RV Life", "Digital Nomad Lifestyle",
    # Learning & Intellectual
    "Reading", "Audiobooks", "Podcasts", "Online Courses", "Language Learning",
    "History", "Philosophy", "Science", "Astronomy", "Psychology", "Economics",
    # Social & Community
    "Volunteering", "Community Service", "Mentoring", "Networking", "Public Speaking",
    "Activism", "Politics", "Debate", "Social Causes",
    # Entertainment & Media
    "Movies", "TV Shows", "Streaming", "Theater", "Concerts", "Live Music",
    "Festivals", "Stand-up Comedy", "Opera", "Ballet",
    # Nature & Outdoors
    "Gardening", "Bird Watching", "Fishing", "Hunting", "Kayaking", "Surfing",
    "Skiing", "Snowboarding", "Nature Photography", "Wildlife Conservation",
    # Business & Finance
    "Investing", "Stock Market", "Real Estate", "Entrepreneurship", "Side Hustles",
    "Personal Finance", "Budgeting", "Startups", "Business Books",
    # Wellness & Self-Care
    "Meditation", "Mindfulness", "Spa Days", "Massage", "Aromatherapy",
    "Holistic Health", "Natural Remedies", "Mental Health Advocacy",
    # DIY & Making
    "DIY Projects", "Home Improvement", "Woodworking", "Electronics", "Car Restoration",
    "3D Printing", "Model Building", "Home Brewing",
    # Fashion & Style
    "Fashion", "Sustainable Fashion", "Thrifting", "Vintage Shopping", "Makeup",
    "Skincare", "Haircare", "Personal Styling",
    # Collecting & Hobbies
    "Collecting", "Antiques", "Coins", "Stamps", "Vinyl Records", "Sneakers",
    "Action Figures", "Comic Books", "Trading Cards",
]

# Communication styles for persona generation
DEFAULT_COMMUNICATION_STYLES = [
    "direct and concise", "warm and empathetic", "analytical and data-driven",
    "enthusiastic and energetic", "calm and measured", "humorous and lighthearted",
    "formal and professional", "casual and friendly", "thoughtful and reflective",
    "passionate and intense", "diplomatic and tactful", "blunt and honest",
    "storytelling-focused", "question-driven", "visual and metaphorical",
    "collaborative and inclusive", "assertive and confident", "humble and modest",
    "expressive and animated", "reserved and observant",
]

# Decision-making styles
DEFAULT_DECISION_STYLES = [
    "data-driven and analytical", "intuition-based and spontaneous",
    "consensus-seeking and collaborative", "decisive and quick",
    "cautious and risk-averse", "bold and risk-taking",
    "research-heavy and thorough", "experience-based and practical",
    "values-driven and principled", "outcome-focused and pragmatic",
    "consultative with trusted advisors", "independent and self-reliant",
    "deliberate and methodical", "flexible and adaptive",
]

# Life situations for context
DEFAULT_LIFE_SITUATIONS = [
    "single and career-focused", "married without children", "married with young children",
    "single parent", "empty nester", "recently divorced", "engaged and planning wedding",
    "living with roommates", "living alone", "living with parents",
    "recently moved cities", "remote worker", "digital nomad",
    "caregiver for elderly parent", "starting a business", "career transition",
    "recent graduate", "mid-career professional", "approaching retirement",
    "semi-retired", "pursuing further education", "sabbatical",
]

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Separator } from '@/components/ui/separator';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import { ThemeToggle } from '@/components/ui/theme-toggle';
import { useTheme } from '@/hooks/use-theme';
import { Key, User, Bell, Shield, Database, Eye, EyeOff, Palette } from 'lucide-react';

export function Settings() {
  const [showApiKey, setShowApiKey] = useState(false);
  const [apiKey, setApiKey] = useState('sk-1234567890abcdef...');
  const { theme, setTheme } = useTheme();
  const [profile, setProfile] = useState({
    name: 'John Doe',
    email: 'john.doe@company.com',
    role: 'Senior Market Researcher',
    company: 'Research Corp'
  });

  const [notifications, setNotifications] = useState({
    emailNotifications: true,
    discussionComplete: true,
    weeklyReports: false,
    systemUpdates: true
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-semibold text-foreground mb-2">Settings</h1>
        <p className="text-muted-foreground">Manage your account and application preferences</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Profile Settings */}
        <div className="lg:col-span-2 space-y-6">
          <Card className="bg-card border border-border shadow-sm">
            <CardHeader>
              <div className="flex items-center gap-2">
                <User className="w-5 h-5 text-chart-2" />
                <CardTitle className="text-card-foreground">Profile Settings</CardTitle>
              </div>
              <p className="text-muted-foreground">Update your personal information</p>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center gap-4 mb-6">
                <Avatar className="w-16 h-16">
                  <AvatarFallback className="text-white text-xl bg-brand-orange">
                    JD
                  </AvatarFallback>
                </Avatar>
                <div>
                  <Button variant="outline" className="border-border text-foreground hover:text-foreground">
                    Change Avatar
                  </Button>
                  <p className="text-xs text-muted-foreground mt-1">JPG or PNG, max 2MB</p>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="name">Full Name</Label>
                  <Input
                    id="name"
                    value={profile.name}
                    onChange={(e) => setProfile({ ...profile, name: e.target.value })}
                  />
                </div>
                <div>
                  <Label htmlFor="email">Email</Label>
                  <Input
                    id="email"
                    type="email"
                    value={profile.email}
                    onChange={(e) => setProfile({ ...profile, email: e.target.value })}
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="role">Role</Label>
                  <Input
                    id="role"
                    value={profile.role}
                    onChange={(e) => setProfile({ ...profile, role: e.target.value })}
                  />
                </div>
                <div>
                  <Label htmlFor="company">Company</Label>
                  <Input
                    id="company"
                    value={profile.company}
                    onChange={(e) => setProfile({ ...profile, company: e.target.value })}
                  />
                </div>
              </div>

              <div className="flex justify-end">
                <Button className="bg-brand-orange hover:bg-brand-orange/90 text-white">
                  Save Changes
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Appearance Settings */}
          <Card className="bg-card border border-border shadow-sm">
            <CardHeader>
              <div className="flex items-center gap-2">
                <Palette className="w-5 h-5 text-chart-1" />
                <CardTitle className="text-card-foreground">Appearance</CardTitle>
              </div>
              <p className="text-muted-foreground">Customize the look and feel of your workspace</p>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <Label htmlFor="theme-mode" className="text-card-foreground">Theme</Label>
                  <p className="text-sm text-muted-foreground">Choose between light and dark mode</p>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-sm text-muted-foreground capitalize">{theme}</span>
                  <ThemeToggle />
                </div>
              </div>

              <Separator className="bg-border" />

              <div className="grid grid-cols-2 gap-4">
                <Button
                  variant={theme === 'light' ? 'default' : 'outline'}
                  onClick={() => setTheme('light')}
                  className="justify-start h-auto p-4"
                >
                  <div className="flex flex-col items-start gap-2">
                    <div className="w-6 h-4 rounded border bg-white border-gray-300"></div>
                    <span>Light</span>
                  </div>
                </Button>

                <Button
                  variant={theme === 'dark' ? 'default' : 'outline'}
                  onClick={() => setTheme('dark')}
                  className="justify-start h-auto p-4"
                >
                  <div className="flex flex-col items-start gap-2">
                    <div className="w-6 h-4 rounded border bg-gray-800 border-gray-600"></div>
                    <span>Dark</span>
                  </div>
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* API Configuration */}
          <Card className="bg-card border border-border shadow-sm">
            <CardHeader>
              <div className="flex items-center gap-2">
                <Key className="w-5 h-5 text-chart-5" />
                <CardTitle className="text-card-foreground">API Configuration</CardTitle>
              </div>
              <p className="text-muted-foreground">Manage your Google API key for persona generation</p>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="bg-amber-50 dark:bg-amber-900/20 p-4 rounded-lg border border-amber-200 dark:border-amber-800">
                <div className="flex items-center gap-2 mb-2">
                  <Shield className="w-4 h-4 text-amber-600" />
                  <span className="text-sm font-medium text-amber-800 dark:text-amber-200">Important</span>
                </div>
                <p className="text-sm text-amber-700 dark:text-amber-300">
                  Your API key is stored securely and only used for generating personas and running AI simulations.
                  Never share your API key with others.
                </p>
              </div>

              <div>
                <Label htmlFor="api-key">Google API Key</Label>
                <div className="flex gap-2 mt-1">
                  <div className="relative flex-1">
                    <Input
                      id="api-key"
                      type={showApiKey ? "text" : "password"}
                      value={apiKey}
                      onChange={(e) => setApiKey(e.target.value)}
                      placeholder="Enter your Google API key"
                    />
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      className="absolute right-0 top-0 h-full px-3 text-muted-foreground hover:text-foreground"
                      onClick={() => setShowApiKey(!showApiKey)}
                    >
                      {showApiKey ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </Button>
                  </div>
                  <Button variant="outline">
                    Test Connection
                  </Button>
                </div>
                <p className="text-xs text-muted-foreground mt-1">
                  Get your API key from the <a href="#" className="text-chart-1 hover:underline">Google Cloud Console</a>
                </p>
              </div>

              <div className="flex justify-end">
                <Button className="bg-brand-orange hover:bg-brand-orange/90 text-white">
                  Save API Key
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Notification Settings */}
          <Card className="bg-card border border-border shadow-sm">
            <CardHeader>
              <div className="flex items-center gap-2">
                <Bell className="w-5 h-5 text-chart-3" />
                <CardTitle className="text-card-foreground">Notifications</CardTitle>
              </div>
              <p className="text-muted-foreground">Choose what notifications you'd like to receive</p>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <Label htmlFor="email-notifications" className="text-card-foreground">Email Notifications</Label>
                    <p className="text-sm text-muted-foreground">Receive notifications via email</p>
                  </div>
                  <Switch
                    id="email-notifications"
                    checked={notifications.emailNotifications}
                    onCheckedChange={(checked) =>
                      setNotifications({ ...notifications, emailNotifications: checked })
                    }
                  />
                </div>

                <Separator className="bg-border" />

                <div className="flex items-center justify-between">
                  <div>
                    <Label htmlFor="discussion-complete" className="text-card-foreground">Discussion Complete</Label>
                    <p className="text-sm text-muted-foreground">Notify when focus group discussions finish</p>
                  </div>
                  <Switch
                    id="discussion-complete"
                    checked={notifications.discussionComplete}
                    onCheckedChange={(checked) =>
                      setNotifications({ ...notifications, discussionComplete: checked })
                    }
                  />
                </div>

                <Separator className="bg-border" />

                <div className="flex items-center justify-between">
                  <div>
                    <Label htmlFor="weekly-reports" className="text-card-foreground">Weekly Reports</Label>
                    <p className="text-sm text-muted-foreground">Get weekly summaries of your research activity</p>
                  </div>
                  <Switch
                    id="weekly-reports"
                    checked={notifications.weeklyReports}
                    onCheckedChange={(checked) =>
                      setNotifications({ ...notifications, weeklyReports: checked })
                    }
                  />
                </div>

                <Separator className="bg-border" />

                <div className="flex items-center justify-between">
                  <div>
                    <Label htmlFor="system-updates" className="text-card-foreground">System Updates</Label>
                    <p className="text-sm text-muted-foreground">Important updates about new features and changes</p>
                  </div>
                  <Switch
                    id="system-updates"
                    checked={notifications.systemUpdates}
                    onCheckedChange={(checked) =>
                      setNotifications({ ...notifications, systemUpdates: checked })
                    }
                  />
                </div>
              </div>

              <div className="flex justify-end pt-4">
                <Button className="bg-brand-orange hover:bg-brand-orange/90 text-white">
                  Save Preferences
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Account Status */}
          <Card className="bg-card border border-border shadow-sm">
            <CardHeader>
              <CardTitle className="text-card-foreground">Account Status</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">Plan</span>
                <Badge className="bg-gradient-to-r from-chart-2/10 to-chart-5/10 text-chart-2 border-chart-2/20">
                  Professional
                </Badge>
              </div>

              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">Projects</span>
                <span className="text-card-foreground">12 / ∞</span>
              </div>

              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">Personas Generated</span>
                <span className="text-card-foreground">247</span>
              </div>

              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">API Calls</span>
                <span className="text-card-foreground">1,432 / 5,000</span>
              </div>

              <Separator className="bg-border" />

              <Button variant="outline" className="w-full">
                Upgrade Plan
              </Button>
            </CardContent>
          </Card>

          {/* Data & Privacy */}
          <Card className="bg-card border border-border shadow-sm">
            <CardHeader>
              <div className="flex items-center gap-2">
                <Database className="w-5 h-5 text-chart-4" />
                <CardTitle className="text-card-foreground">Data & Privacy</CardTitle>
              </div>
            </CardHeader>
            <CardContent className="space-y-3">
              <Button variant="outline" className="w-full justify-start">
                Export Data
              </Button>

              <Button variant="outline" className="w-full justify-start">
                Privacy Settings
              </Button>

              <Button
                variant="outline"
                className="w-full justify-start border-destructive/50 text-destructive hover:text-destructive hover:border-destructive"
              >
                Delete Account
              </Button>
            </CardContent>
          </Card>

          {/* Support */}
          <Card className="bg-card border border-border shadow-sm">
            <CardHeader>
              <CardTitle className="text-card-foreground">Support</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <Button variant="outline" className="w-full justify-start">
                Help Center
              </Button>

              <Button variant="outline" className="w-full justify-start">
                Contact Support
              </Button>

              <Button variant="outline" className="w-full justify-start">
                Feature Requests
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

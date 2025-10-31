import { useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Logo } from '@/components/ui/logo';
import { Eye, EyeOff, Mail, Lock, ArrowRight } from 'lucide-react';
import { useTranslation } from 'react-i18next';

export function Login() {
  const { login, register, isLoading } = useAuth();
  const { t } = useTranslation('auth');
  const [isRegisterMode, setIsRegisterMode] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  const [formData, setFormData] = useState({
    email: '',
    password: '',
    full_name: '',
    company: '',
    role: '',
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (isRegisterMode) {
      await register({
        email: formData.email,
        password: formData.password,
        full_name: formData.full_name,
        company: formData.company || undefined,
        role: formData.role || undefined,
      });
    } else {
      await login({
        email: formData.email,
        password: formData.password,
      });
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-background via-background to-sidebar p-4">
      {/* Animated background elements */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute w-96 h-96 -top-48 -left-48 bg-brand-orange/5 rounded-full blur-3xl animate-pulse-slow" />
        <div className="absolute w-96 h-96 -bottom-48 -right-48 bg-chart-1/5 rounded-full blur-3xl animate-pulse-slow" style={{ animationDelay: '1s' }} />
      </div>

      {/* Login Card */}
      <Card className="w-full max-w-md relative z-10 shadow-float border-border">
        <CardHeader className="space-y-4 text-center">
          <div className="flex justify-center">
            <div className="w-16 h-16 rounded-2xl shadow-lg overflow-hidden bg-white dark:bg-sidebar">
              <Logo className="w-full h-full object-cover" />
            </div>
          </div>
          <div>
            <CardTitle className="text-2xl font-semibold text-foreground">
              {isRegisterMode ? t('register.title') : t('login.title')}
            </CardTitle>
            <CardDescription className="text-muted-foreground">
              {isRegisterMode
                ? t('register.subtitle')
                : t('login.subtitle')
              }
            </CardDescription>
          </div>
        </CardHeader>

        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            {isRegisterMode && (
              <>
                <div>
                  <Label htmlFor="full_name">{t('register.fullNameLabel')}</Label>
                  <Input
                    id="full_name"
                    type="text"
                    placeholder={t('register.fullNamePlaceholder')}
                    value={formData.full_name}
                    onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                    required={isRegisterMode}
                    className="mt-1"
                  />
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <Label htmlFor="company">{t('register.companyLabel')}</Label>
                    <Input
                      id="company"
                      type="text"
                      placeholder={t('register.companyPlaceholder')}
                      value={formData.company}
                      onChange={(e) => setFormData({ ...formData, company: e.target.value })}
                      className="mt-1"
                    />
                  </div>
                  <div>
                    <Label htmlFor="role">{t('register.roleLabel')}</Label>
                    <Input
                      id="role"
                      type="text"
                      placeholder={t('register.rolePlaceholder')}
                      value={formData.role}
                      onChange={(e) => setFormData({ ...formData, role: e.target.value })}
                      className="mt-1"
                    />
                  </div>
                </div>
              </>
            )}

            <div>
              <Label htmlFor="email">{isRegisterMode ? t('register.emailLabel') : t('login.emailLabel')}</Label>
              <div className="relative mt-1">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                <Input
                  id="email"
                  type="email"
                  placeholder={isRegisterMode ? t('register.emailPlaceholder') : t('login.emailPlaceholder')}
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  required
                  className="pl-10"
                />
              </div>
            </div>

            <div>
              <Label htmlFor="password">{isRegisterMode ? t('register.passwordLabel') : t('login.passwordLabel')}</Label>
              <div className="relative mt-1">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                <Input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  placeholder={isRegisterMode ? t('register.passwordPlaceholder') : t('login.passwordPlaceholder')}
                  value={formData.password}
                  onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                  required
                  className="pl-10 pr-10"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
              {isRegisterMode && (
                <p className="text-xs text-muted-foreground mt-1">
                  {t('register.passwordHint')}
                </p>
              )}
            </div>

            <Button
              type="submit"
              className="w-full bg-brand-orange hover:bg-brand-orange/90 text-white"
              disabled={isLoading}
            >
              {isLoading ? (
                <div className="flex items-center gap-2">
                  <Logo spinning transparent className="w-4 h-4" />
                  <span>{isRegisterMode ? t('register.submitButton') : t('login.submitButton')}</span>
                </div>
              ) : (
                <div className="flex items-center gap-2">
                  <span>{isRegisterMode ? t('register.submitButtonDefault') : t('login.submitButtonDefault')}</span>
                  <ArrowRight className="w-4 h-4" />
                </div>
              )}
            </Button>

            <div className="text-center text-sm">
              <button
                type="button"
                onClick={() => setIsRegisterMode(!isRegisterMode)}
                className="text-brand-orange hover:underline"
              >
                {isRegisterMode
                  ? t('register.toggleText')
                  : t('login.toggleText')
                }
              </button>
            </div>
          </form>
        </CardContent>
      </Card>

      {/* Footer */}
      <div className="absolute bottom-4 text-center text-sm text-muted-foreground">
        <p>{t('footer.copyright')}</p>
      </div>
    </div>
  );
}

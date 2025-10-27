import { useState, useRef, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Separator } from '@/components/ui/separator';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import { ThemeToggle } from '@/components/ui/theme-toggle';
import { useTheme } from '@/hooks/use-theme';
import { toast } from '@/components/ui/toastStore';
import { settingsApi } from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';
import { getAvatarUrl, getInitials } from '@/lib/avatar';
import {
  User,
  Database,
  Palette,
  Loader2,
  Upload,
  X,
  AlertTriangle,
} from 'lucide-react';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '@/components/ui/alert-dialog';

export function Settings() {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { theme, setTheme } = useTheme();
  const queryClient = useQueryClient();
  const { logout } = useAuth();

  // === QUERIES ===
  const { data: profile, isLoading: isLoadingProfile } = useQuery({
    queryKey: ['settings', 'profile'],
    queryFn: settingsApi.getProfile,
  });

  const { data: stats, isLoading: isLoadingStats } = useQuery({
    queryKey: ['settings', 'stats'],
    queryFn: settingsApi.getStats,
  });

  // Local state for forms
  const [profileForm, setProfileForm] = useState({
    full_name: '',
    role: '',
    company: '',
  });

  // Update forms when data loads from API
  useEffect(() => {
    if (profile) {
      setProfileForm({
        full_name: profile.full_name || '',
        role: profile.role || '',
        company: profile.company || '',
      });
    }
  }, [profile]);

  // === MUTATIONS ===
  const updateProfileMutation = useMutation({
    mutationFn: settingsApi.updateProfile,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['settings', 'profile'] });
      queryClient.invalidateQueries({ queryKey: ['auth', 'me'] });
      toast.success('Profil zaktualizowany pomyślnie');
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.detail || 'Nie udało się zaktualizować profilu');
    },
  });

  const uploadAvatarMutation = useMutation({
    mutationFn: (file: File) => {
      const formData = new FormData();
      formData.append('file', file);
      return settingsApi.uploadAvatar(formData);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['settings', 'profile'] });
      queryClient.invalidateQueries({ queryKey: ['auth', 'me'] });
      toast.success('Awatar przesłany pomyślnie');
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.detail || 'Nie udało się przesłać awatara');
    },
  });

  const deleteAvatarMutation = useMutation({
    mutationFn: settingsApi.deleteAvatar,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['settings', 'profile'] });
      queryClient.invalidateQueries({ queryKey: ['auth', 'me'] });
      toast.success('Awatar usunięty pomyślnie');
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.detail || 'Nie udało się usunąć awatara');
    },
  });

  const deleteAccountMutation = useMutation({
    mutationFn: settingsApi.deleteAccount,
    onSuccess: () => {
      toast.info('Konto usunięte. Do widzenia!');
      logout();
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.detail || 'Nie udało się usunąć konta');
    },
  });

  // === HANDLERS ===
  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Validate file type
    if (!['image/jpeg', 'image/png', 'image/webp'].includes(file.type)) {
      toast.error('Nieprawidłowy typ pliku. Prześlij JPG, PNG lub WEBP');
      return;
    }

    // Validate file size (2MB)
    if (file.size > 2 * 1024 * 1024) {
      toast.error('Plik za duży. Maksymalny rozmiar to 2MB');
      return;
    }

    uploadAvatarMutation.mutate(file);
  };

  const handleProfileSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    updateProfileMutation.mutate(profileForm);
  };


  if (isLoadingProfile || isLoadingStats) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="w-8 h-8 animate-spin text-brand-orange" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-semibold text-foreground mb-2">Ustawienia</h1>
        <p className="text-muted-foreground">Zarządzaj swoim kontem i preferencjami aplikacji</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Profile Settings */}
        <div className="lg:col-span-2 space-y-6">
          <Card className="bg-card border border-border shadow-sm">
            <CardHeader>
              <div className="flex items-center gap-2">
                <User className="w-5 h-5 text-chart-2" />
                <CardTitle className="text-card-foreground">Ustawienia profilu</CardTitle>
              </div>
              <p className="text-muted-foreground">Zaktualizuj swoje dane osobowe</p>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleProfileSubmit} className="space-y-4">
                <div className="flex items-center gap-4 mb-6">
                  <Avatar className="w-16 h-16">
                    {profile?.avatar_url && (
                      <AvatarImage src={getAvatarUrl(profile.avatar_url)} alt={profile.full_name} />
                    )}
                    <AvatarFallback className="text-white text-xl bg-brand-orange">
                      {getInitials(profile?.full_name)}
                    </AvatarFallback>
                  </Avatar>
                  <div className="flex gap-2">
                    <input
                      ref={fileInputRef}
                      type="file"
                      accept="image/jpeg,image/png,image/webp"
                      className="hidden"
                      onChange={handleFileSelect}
                    />
                    <Button
                      type="button"
                      variant="outline"
                      onClick={() => fileInputRef.current?.click()}
                      disabled={uploadAvatarMutation.isPending}
                    >
                      {uploadAvatarMutation.isPending ? (
                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      ) : (
                        <Upload className="w-4 h-4 mr-2" />
                      )}
                      Zmień awatar
                    </Button>
                    {profile?.avatar_url && (
                      <Button
                        type="button"
                        variant="outline"
                        onClick={() => deleteAvatarMutation.mutate()}
                        disabled={deleteAvatarMutation.isPending}
                      >
                        {deleteAvatarMutation.isPending ? (
                          <Loader2 className="w-4 h-4 animate-spin" />
                        ) : (
                          <X className="w-4 h-4" />
                        )}
                      </Button>
                    )}
                  </div>
                  <p className="text-xs text-muted-foreground">JPG, PNG lub WEBP, maks. 2MB</p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="name">Imię i nazwisko</Label>
                    <Input
                      id="name"
                      value={profileForm.full_name}
                      onChange={(e) =>
                        setProfileForm({ ...profileForm, full_name: e.target.value })
                      }
                    />
                  </div>
                  <div>
                    <Label htmlFor="email">Email</Label>
                    <Input id="email" type="email" value={profile?.email} disabled />
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="role">Rola</Label>
                    <Input
                      id="role"
                      value={profileForm.role}
                      onChange={(e) => setProfileForm({ ...profileForm, role: e.target.value })}
                    />
                  </div>
                  <div>
                    <Label htmlFor="company">Firma</Label>
                    <Input
                      id="company"
                      value={profileForm.company}
                      onChange={(e) =>
                        setProfileForm({ ...profileForm, company: e.target.value })
                      }
                    />
                  </div>
                </div>

                <div className="flex justify-end">
                  <Button
                    type="submit"
                    className="bg-brand-orange hover:bg-brand-orange/90 text-white"
                    disabled={updateProfileMutation.isPending}
                  >
                    {updateProfileMutation.isPending && (
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    )}
                    Zapisz zmiany
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>

          {/* Appearance Settings */}
          <Card className="bg-card border border-border shadow-sm">
            <CardHeader>
              <div className="flex items-center gap-2">
                <Palette className="w-5 h-5 text-chart-1" />
                <CardTitle className="text-card-foreground">Wygląd</CardTitle>
              </div>
              <p className="text-muted-foreground">Dostosuj wygląd swojego obszaru roboczego</p>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <Label htmlFor="theme-mode" className="text-card-foreground">
                    Motyw
                  </Label>
                  <p className="text-sm text-muted-foreground">
                    Wybierz tryb jasny lub ciemny
                  </p>
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
                    <span>Jasny</span>
                  </div>
                </Button>

                <Button
                  variant={theme === 'dark' ? 'default' : 'outline'}
                  onClick={() => setTheme('dark')}
                  className="justify-start h-auto p-4"
                >
                  <div className="flex flex-col items-start gap-2">
                    <div className="w-6 h-4 rounded border bg-gray-800 border-gray-600"></div>
                    <span>Ciemny</span>
                  </div>
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
              <CardTitle className="text-card-foreground">Status konta</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">Plan</span>
                <Badge
                  className="bg-gradient-to-r from-chart-2/10 to-chart-5/10 text-chart-2 border-chart-2/20 capitalize"
                >
                  {stats?.plan || 'free'}
                </Badge>
              </div>

              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">Projekty</span>
                <span className="text-card-foreground">{stats?.projects_count || 0}</span>
              </div>

              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">Wygenerowane persony</span>
                <span className="text-card-foreground">{stats?.personas_count || 0}</span>
              </div>

              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">Grupy fokusowe</span>
                <span className="text-card-foreground">{stats?.focus_groups_count || 0}</span>
              </div>

              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">Ankiety</span>
                <span className="text-card-foreground">{stats?.surveys_count || 0}</span>
              </div>

              <Separator className="bg-border" />

              <Button variant="outline" className="w-full" disabled>
                Ulepsz plan
              </Button>
            </CardContent>
          </Card>

          {/* Data & Privacy */}
          <Card className="bg-card border border-border shadow-sm">
            <CardHeader>
              <div className="flex items-center gap-2">
                <Database className="w-5 h-5 text-chart-4" />
                <CardTitle className="text-card-foreground">Dane i prywatność</CardTitle>
              </div>
            </CardHeader>
            <CardContent className="space-y-3">
              <Button variant="outline" className="w-full justify-start" disabled>
                Eksportuj dane
              </Button>

              <Button variant="outline" className="w-full justify-start" disabled>
                Ustawienia prywatności
              </Button>

              <AlertDialog>
                <AlertDialogTrigger asChild>
                  <Button
                    variant="outline"
                    className="w-full justify-start border-destructive/50 text-destructive hover:text-destructive hover:border-destructive"
                  >
                    <AlertTriangle className="w-4 h-4 mr-2" />
                    Usuń konto
                  </Button>
                </AlertDialogTrigger>
                <AlertDialogContent>
                  <AlertDialogHeader>
                    <AlertDialogTitle>Czy na pewno chcesz to zrobić?</AlertDialogTitle>
                    <AlertDialogDescription>
                      Ta akcja jest nieodwracalna. Spowoduje to trwałe usunięcie Twojego konta i
                      wszystkich danych z naszych serwerów, w tym:
                      <ul className="list-disc list-inside mt-2 space-y-1">
                        <li>Wszystkie projekty i persony</li>
                        <li>Dyskusje grup fokusowych i wyniki ankiet</li>
                        <li>Twój profil i ustawienia</li>
                      </ul>
                    </AlertDialogDescription>
                  </AlertDialogHeader>
                  <AlertDialogFooter>
                    <AlertDialogCancel>Anuluj</AlertDialogCancel>
                    <AlertDialogAction
                      onClick={() => deleteAccountMutation.mutate()}
                      className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                      disabled={deleteAccountMutation.isPending}
                    >
                      {deleteAccountMutation.isPending && (
                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      )}
                      Usuń konto
                    </AlertDialogAction>
                  </AlertDialogFooter>
                </AlertDialogContent>
              </AlertDialog>
            </CardContent>
          </Card>

          {/* Support */}
          <Card className="bg-card border border-border shadow-sm">
            <CardHeader>
              <CardTitle className="text-card-foreground">Wsparcie</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <Button variant="outline" className="w-full justify-start" disabled>
                Centrum pomocy
              </Button>

              <Button variant="outline" className="w-full justify-start" disabled>
                Kontakt z pomocą techniczną
              </Button>

              <Button variant="outline" className="w-full justify-start" disabled>
                Prośby o funkcje
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

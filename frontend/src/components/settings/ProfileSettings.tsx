import { useRef } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { User, Loader2, Upload, X } from 'lucide-react';
import { useTranslation } from '@/i18n/hooks';
import { toast } from '@/components/ui/toastStore';
import { settingsApi } from '@/lib/api';
import { getAvatarUrl, getInitials } from '@/lib/avatar';
import type { APIError } from '@/types';

interface ProfileData {
  full_name: string;
  email: string;
  role: string;
  company: string;
  avatar_url?: string;
}

interface ProfileSettingsProps {
  profile: ProfileData | undefined;
  profileForm: {
    full_name: string;
    role: string;
    company: string;
  };
  setProfileForm: (form: { full_name: string; role: string; company: string }) => void;
}

export function ProfileSettings({ profile, profileForm, setProfileForm }: ProfileSettingsProps) {
  const { t } = useTranslation('settings');
  const fileInputRef = useRef<HTMLInputElement>(null);
  const queryClient = useQueryClient();

  const updateProfileMutation = useMutation({
    mutationFn: settingsApi.updateProfile,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['settings', 'profile'] });
      queryClient.invalidateQueries({ queryKey: ['auth', 'me'] });
      toast.success(t('toast.profileUpdateSuccess'));
    },
    onError: (error: APIError) => {
      toast.error(error?.response?.data?.detail || t('profile.updateError'));
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
      toast.success(t('toast.avatarUploadSuccess'));
    },
    onError: (error: APIError) => {
      toast.error(error?.response?.data?.detail || t('profile.avatar.uploadError'));
    },
  });

  const deleteAvatarMutation = useMutation({
    mutationFn: settingsApi.deleteAvatar,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['settings', 'profile'] });
      queryClient.invalidateQueries({ queryKey: ['auth', 'me'] });
      toast.success(t('toast.avatarDeleteSuccess'));
    },
    onError: (error: APIError) => {
      toast.error(error?.response?.data?.detail || t('profile.avatar.deleteError'));
    },
  });

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!['image/jpeg', 'image/png', 'image/webp'].includes(file.type)) {
      toast.error(t('profile.avatar.invalidType'));
      return;
    }

    if (file.size > 2 * 1024 * 1024) {
      toast.error(t('profile.avatar.tooLarge'));
      return;
    }

    uploadAvatarMutation.mutate(file);
  };

  const handleProfileSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    updateProfileMutation.mutate(profileForm);
  };

  return (
    <Card className="bg-card border border-border shadow-sm">
      <CardHeader>
        <div className="flex items-center gap-2">
          <User className="w-5 h-5 text-chart-2" />
          <CardTitle className="text-card-foreground">{t('profile.title')}</CardTitle>
        </div>
        <p className="text-muted-foreground">{t('profile.description')}</p>
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
                {t('profile.avatar.change')}
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
            <p className="text-xs text-muted-foreground">{t('profile.avatar.hint')}</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <Label htmlFor="name">{t('profile.fields.fullName')}</Label>
              <Input
                id="name"
                value={profileForm.full_name}
                onChange={(e) =>
                  setProfileForm({ ...profileForm, full_name: e.target.value })
                }
              />
            </div>
            <div>
              <Label htmlFor="email">{t('profile.fields.email')}</Label>
              <Input id="email" type="email" value={profile?.email} disabled />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <Label htmlFor="role">{t('profile.fields.role')}</Label>
              <Input
                id="role"
                value={profileForm.role}
                onChange={(e) => setProfileForm({ ...profileForm, role: e.target.value })}
              />
            </div>
            <div>
              <Label htmlFor="company">{t('profile.fields.company')}</Label>
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
              {t('profile.saveButton')}
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}

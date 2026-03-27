import { useEffect, useMemo, useState } from 'react';
import { Activity, Clock3, Flame, Plus, Trash2 } from 'lucide-react';
import { motion } from 'framer-motion';
import Layout from '../components/Layout';
import { Card, CardContent } from '../components/ui/card';
import LoadingSpinner from '../components/LoadingSpinner';
import { useAuth } from '../contexts/AuthContext';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import api from '../api/axios';
import ProfileHeader from '../components/profile/ProfileHeader';
import SocialLinks from '../components/profile/SocialLinks';
import Skills from '../components/profile/Skills';
import Projects from '../components/profile/Projects';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '../components/ui/dialog';
import { Input } from '../components/ui/input';
import { Textarea } from '../components/ui/textarea';
import { Button } from '../components/ui/button';

const DEFAULT_SKILLS = ['Python', 'Django', 'React', 'Machine Learning', 'SQL'];
const EMPTY_PROJECT = { title: '', description: '', tech_stack_csv: '', github_url: '' };

function toRelativeTime(dateValue) {
  if (!dateValue) return 'Unknown';
  const value = new Date(dateValue).getTime();
  const now = Date.now();
  const diffSeconds = Math.max(0, Math.floor((now - value) / 1000));

  if (diffSeconds < 60) return 'just now';
  if (diffSeconds < 3600) return `${Math.floor(diffSeconds / 60)} min ago`;
  if (diffSeconds < 86400) return `${Math.floor(diffSeconds / 3600)} hours ago`;
  if (diffSeconds < 604800) return `${Math.floor(diffSeconds / 86400)} days ago`;
  return new Date(dateValue).toLocaleDateString();
}

function parseCsvTags(value) {
  return value
    .split(',')
    .map((tag) => tag.trim())
    .filter(Boolean);
}

function ActivitySnapshot({ profile }) {
  const activity = profile?.activity_snapshot || {};
  const recent = activity.recent_submissions || [];

  return (
    <motion.section
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, delay: 0.2 }}
      className="space-y-3"
    >
      <h2 className="text-lg font-semibold text-foreground">Activity Snapshot</h2>
      <Card className="bg-card border border-border/70 rounded-xl">
        <CardContent className="p-4 space-y-4">
          <div className="flex flex-col md:flex-row gap-4 md:gap-8 text-sm">
            <div className="flex items-center gap-2 text-muted-foreground">
              <Clock3 className="h-4 w-4" />
              <span>Last active: {toRelativeTime(activity.last_active)}</span>
            </div>
            {Number(activity.current_streak || 0) > 0 ? (
              <div className="flex items-center gap-2 text-muted-foreground">
                <Flame className="h-4 w-4" />
                <span>Current streak: {activity.current_streak} days</span>
              </div>
            ) : null}
          </div>

          <div className="space-y-2">
            <div className="flex items-center gap-2 text-sm text-foreground font-medium">
              <Activity className="h-4 w-4" />
              Recent submissions
            </div>
            {recent.length ? (
              <div className="space-y-2">
                {recent.slice(0, 2).map((item) => {
                  const accepted = String(item.status || '').toUpperCase() === 'ACCEPTED';
                  return (
                    <div key={item.id} className="flex items-center justify-between rounded-lg border border-border/60 bg-muted/10 px-3 py-2">
                      <div className="min-w-0">
                        <p className="text-sm text-foreground truncate">{item.problem_title}</p>
                        <p className="text-xs text-muted-foreground">{toRelativeTime(item.created_at)}</p>
                      </div>
                      <span className={`text-xs px-2 py-1 rounded-full border ${accepted ? 'border-emerald-500/50 text-emerald-400' : 'border-rose-500/50 text-rose-400'}`}>
                        {item.status}
                      </span>
                    </div>
                  );
                })}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">No recent submissions yet.</p>
            )}
          </div>
        </CardContent>
      </Card>
    </motion.section>
  );
}

function BioSection({ bio }) {
  return (
    <motion.section
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, delay: 0.25 }}
      className="space-y-3"
    >
      <h2 className="text-lg font-semibold text-foreground">Bio</h2>
      <Card className="bg-card border border-border/70 rounded-xl">
        <CardContent className="p-4 text-sm md:text-base text-muted-foreground">
          {bio || 'Focused on building real-time ML systems and scalable backend architectures.'}
        </CardContent>
      </Card>
    </motion.section>
  );
}

function EditProfileDialog({ open, onOpenChange, profile, onSave, isSaving }) {
  const [form, setForm] = useState({
    display_name: '',
    tagline: '',
    avatar_url: '',
    github_url: '',
    linkedin_url: '',
    portfolio_url: '',
    bio: '',
    skills_csv: '',
    projects: [EMPTY_PROJECT],
  });

  useEffect(() => {
    const mappedProjects = (profile?.projects || []).slice(0, 4).map((project) => ({
      title: project.title || '',
      description: project.description || '',
      tech_stack_csv: (project.tech_stack || []).join(', '),
      github_url: project.github_url || '',
    }));

    setForm({
      display_name: profile?.display_name || profile?.full_name || '',
      tagline: profile?.tagline || '',
      avatar_url: profile?.avatar_url || '',
      github_url: profile?.github_url || '',
      linkedin_url: profile?.linkedin_url || '',
      portfolio_url: profile?.portfolio_url || '',
      bio: profile?.bio || '',
      skills_csv: (profile?.skills || []).join(', '),
      projects: mappedProjects.length ? mappedProjects : [EMPTY_PROJECT],
    });
  }, [profile, open]);

  const updateField = (field, value) => {
    setForm((prev) => ({ ...prev, [field]: value }));
  };

  const updateProject = (index, field, value) => {
    setForm((prev) => ({
      ...prev,
      projects: prev.projects.map((project, projectIndex) => (
        projectIndex === index ? { ...project, [field]: value } : project
      )),
    }));
  };

  const addProject = () => {
    setForm((prev) => {
      if (prev.projects.length >= 4) return prev;
      return { ...prev, projects: [...prev.projects, { ...EMPTY_PROJECT }] };
    });
  };

  const removeProject = (index) => {
    setForm((prev) => {
      const next = prev.projects.filter((_, idx) => idx !== index);
      return { ...prev, projects: next.length ? next : [{ ...EMPTY_PROJECT }] };
    });
  };

  const submit = (event) => {
    event.preventDefault();
    const projects = form.projects
      .map((project) => ({
        title: project.title.trim(),
        description: project.description.trim(),
        tech_stack: parseCsvTags(project.tech_stack_csv),
        github_url: project.github_url.trim(),
      }))
      .filter((project) => project.title && project.description)
      .slice(0, 4);

    onSave({
      display_name: form.display_name.trim(),
      tagline: form.tagline.trim(),
      avatar_url: form.avatar_url.trim(),
      github_url: form.github_url.trim(),
      linkedin_url: form.linkedin_url.trim(),
      portfolio_url: form.portfolio_url.trim(),
      bio: form.bio.trim(),
      skills: parseCsvTags(form.skills_csv).slice(0, 12),
      projects,
    });
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-4xl bg-card border-border/70">
        <DialogHeader>
          <DialogTitle>Edit Developer Identity</DialogTitle>
          <DialogDescription>
            Keep it concise and professional. Showcase identity, social presence, stack, and 2-4 real projects.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={submit} className="space-y-4 max-h-[72vh] overflow-y-auto pr-1">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <Input placeholder="Full name" value={form.display_name} onChange={(e) => updateField('display_name', e.target.value)} />
            <Input placeholder="Tagline" value={form.tagline} onChange={(e) => updateField('tagline', e.target.value)} />
            <Input placeholder="Avatar URL" value={form.avatar_url} onChange={(e) => updateField('avatar_url', e.target.value)} />
            <Input placeholder="Skills (comma separated, max 12)" value={form.skills_csv} onChange={(e) => updateField('skills_csv', e.target.value)} />
            <Input placeholder="GitHub URL" value={form.github_url} onChange={(e) => updateField('github_url', e.target.value)} />
            <Input placeholder="LinkedIn URL" value={form.linkedin_url} onChange={(e) => updateField('linkedin_url', e.target.value)} />
            <Input placeholder="Portfolio website URL" value={form.portfolio_url} onChange={(e) => updateField('portfolio_url', e.target.value)} />
          </div>

          <Textarea
            placeholder="Bio (2-3 lines)"
            value={form.bio}
            onChange={(e) => updateField('bio', e.target.value)}
            rows={3}
          />

          <div className="space-y-3 border border-border/60 rounded-xl p-3">
            <div className="flex items-center justify-between">
              <p className="text-sm font-medium text-foreground">Highlighted Projects (max 4)</p>
              <Button type="button" variant="outline" size="sm" onClick={addProject} disabled={form.projects.length >= 4}>
                <Plus className="h-4 w-4 mr-1" />
                Add Project
              </Button>
            </div>

            <div className="space-y-3">
              {form.projects.map((project, index) => (
                <div key={`project-${index}`} className="grid grid-cols-1 md:grid-cols-2 gap-2 border border-border/50 rounded-lg p-3">
                  <Input
                    placeholder="Project title"
                    value={project.title}
                    onChange={(e) => updateProject(index, 'title', e.target.value)}
                  />
                  <Input
                    placeholder="Project GitHub URL"
                    value={project.github_url}
                    onChange={(e) => updateProject(index, 'github_url', e.target.value)}
                  />
                  <Input
                    placeholder="One-line description"
                    value={project.description}
                    onChange={(e) => updateProject(index, 'description', e.target.value)}
                    className="md:col-span-2"
                  />
                  <Input
                    placeholder="Tech stack (comma separated)"
                    value={project.tech_stack_csv}
                    onChange={(e) => updateProject(index, 'tech_stack_csv', e.target.value)}
                    className="md:col-span-2"
                  />
                  <div className="md:col-span-2 flex justify-end">
                    <Button type="button" variant="ghost" size="sm" onClick={() => removeProject(index)}>
                      <Trash2 className="h-4 w-4 mr-1" />
                      Remove
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="flex justify-end gap-2">
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={isSaving}>
              {isSaving ? 'Saving...' : 'Save changes'}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}

export default function Profile() {
  const { user: authUser, isLoading, fetchUser } = useAuth();
  const queryClient = useQueryClient();
  const [isEditOpen, setIsEditOpen] = useState(false);

  const { data: profileData } = useQuery({
    queryKey: ['portfolio-profile'],
    queryFn: async () => {
      const res = await api.get('/api/profile/');
      return res.data;
    },
    enabled: !!authUser?.id,
    refetchOnWindowFocus: true,
  });

  const updateProfileMutation = useMutation({
    mutationFn: async (payload) => {
      const res = await api.put('/api/profile/update/', payload);
      return res.data;
    },
    onSuccess: async (data) => {
      queryClient.setQueryData(['portfolio-profile'], data);
      await fetchUser();
      setIsEditOpen(false);
    },
  });

  const user = useMemo(() => {
    const merged = { ...(profileData || authUser || {}) };
    if (!Array.isArray(merged.skills) || merged.skills.length === 0) {
      merged.skills = DEFAULT_SKILLS;
    }
    return merged;
  }, [profileData, authUser]);

  if (isLoading) {
    return (
      <Layout>
        <div className="min-h-[60vh] flex items-center justify-center">
          <LoadingSpinner />
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="container mx-auto px-4 lg:px-8 py-10 max-w-6xl space-y-6">
        <ProfileHeader profile={user} onEdit={() => setIsEditOpen(true)} />
        <SocialLinks profile={user} />
        <Skills skills={user?.skills || []} />
        <Projects projects={user?.projects || []} />
        <ActivitySnapshot profile={user} />
        <BioSection bio={user?.bio} />

        <EditProfileDialog
          open={isEditOpen}
          onOpenChange={setIsEditOpen}
          profile={user}
          onSave={(payload) => updateProfileMutation.mutate(payload)}
          isSaving={updateProfileMutation.isPending}
        />

        {updateProfileMutation.isError ? (
          <Card className="border-rose-500/40 bg-rose-950/20">
            <CardContent className="p-4 text-sm text-rose-300">
              Failed to save profile updates. Please verify your links and try again.
            </CardContent>
          </Card>
        ) : null}

        {updateProfileMutation.isSuccess ? (
          <Card className="border-emerald-500/40 bg-emerald-950/20">
            <CardContent className="p-4 text-sm text-emerald-300">
              Profile updated successfully.
            </CardContent>
          </Card>
        ) : null}
      </div>
    </Layout>
  );
}

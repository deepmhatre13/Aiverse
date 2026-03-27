import { Calendar, Mail, Pencil } from 'lucide-react';
import { motion } from 'framer-motion';
import { Button } from '../ui/button';
import { Card, CardContent } from '../ui/card';

function getInitials(name, username) {
  const base = (name || username || 'U').trim();
  const parts = base.split(/\s+/).filter(Boolean);
  if (parts.length >= 2) {
    return `${parts[0][0]}${parts[1][0]}`.toUpperCase();
  }
  return base.slice(0, 2).toUpperCase();
}

export default function ProfileHeader({ profile, onEdit }) {
  const joined = profile?.joined_at
    ? new Date(profile.joined_at).toLocaleDateString('en-US', { month: 'long', year: 'numeric' })
    : 'Unknown';

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, ease: 'easeOut' }}
    >
      <Card className="bg-card border border-border/70 rounded-2xl shadow-sm">
        <CardContent className="p-6 md:p-8">
          <div className="grid grid-cols-1 lg:grid-cols-[auto,1fr,auto] items-start lg:items-center gap-6">
            <div className="h-24 w-24 rounded-full border border-border/70 bg-muted/20 flex items-center justify-center overflow-hidden">
                {profile?.avatar_url ? (
                  <img src={profile.avatar_url} alt="Profile avatar" className="h-full w-full object-cover" />
                ) : (
                  <span className="text-2xl font-semibold text-foreground">
                    {getInitials(profile?.full_name, profile?.username)}
                  </span>
                )}
            </div>

            <div className="space-y-3 min-w-0">
              <h1 className="text-2xl md:text-3xl font-semibold text-foreground truncate">
                {profile?.full_name || profile?.display_name || profile?.username || 'Developer'}
              </h1>
              <p className="text-sm md:text-base text-muted-foreground max-w-2xl truncate">
                {profile?.tagline || 'ML Engineer | Problem Solver | Backend Systems'}
              </p>
              <div className="grid gap-1 text-xs md:text-sm text-muted-foreground">
                <div className="flex items-center gap-2 min-w-0">
                  <Mail className="h-4 w-4 shrink-0" />
                  <span className="truncate">{profile?.email || 'No email available'}</span>
                </div>
                <div className="flex items-center gap-2">
                  <Calendar className="h-4 w-4 shrink-0" />
                  <span>Joined {joined}</span>
                </div>
              </div>
            </div>

            <Button onClick={onEdit} className="self-start lg:self-center">
              <Pencil className="mr-2 h-4 w-4" />
              Edit Profile
            </Button>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}

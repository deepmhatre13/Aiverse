import { Github } from 'lucide-react';
import { motion } from 'framer-motion';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';

function normalizeUrl(value) {
  if (!value) return '';
  return value.startsWith('http://') || value.startsWith('https://') ? value : `https://${value}`;
}

export default function Projects({ projects = [] }) {
  const visibleProjects = projects.slice(0, 4);

  return (
    <motion.section
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, delay: 0.15 }}
      className="space-y-3"
    >
      <h2 className="text-lg font-semibold text-foreground">Projects / Work</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {visibleProjects.length ? (
          visibleProjects.map((project) => {
            const githubLink = normalizeUrl(project.github_url);
            return (
              <Card key={project.id || project.title} className="bg-card border border-border/70 rounded-xl">
                <CardHeader className="pb-2">
                  <CardTitle className="text-base md:text-lg text-foreground">{project.title}</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <p className="text-sm text-muted-foreground line-clamp-2">{project.description}</p>
                  <div className="flex flex-wrap gap-2">
                    {(project.tech_stack || []).slice(0, 6).map((tech) => (
                      <span
                        key={`${project.title}-${tech}`}
                        className="px-2.5 py-1 rounded-full text-xs border border-border/80 bg-muted/15 text-foreground"
                      >
                        {tech}
                      </span>
                    ))}
                  </div>
                  {githubLink ? (
                    <Button asChild variant="outline" size="sm">
                      <a href={githubLink} target="_blank" rel="noreferrer">
                        <Github className="h-4 w-4 mr-2" />
                        View on GitHub
                      </a>
                    </Button>
                  ) : (
                    <span className="text-xs text-muted-foreground">Add GitHub link</span>
                  )}
                </CardContent>
              </Card>
            );
          })
        ) : (
          <Card className="bg-card border border-border/70 rounded-xl md:col-span-2">
            <CardContent className="p-4 text-sm text-muted-foreground">
              Add 2-4 highlighted projects to showcase your work.
            </CardContent>
          </Card>
        )}
      </div>
    </motion.section>
  );
}

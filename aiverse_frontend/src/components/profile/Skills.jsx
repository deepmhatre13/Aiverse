import { motion } from 'framer-motion';
import { Card, CardContent } from '../ui/card';

export default function Skills({ skills = [] }) {
  const visibleSkills = skills.slice(0, 12);

  return (
    <motion.section
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, delay: 0.1 }}
      className="space-y-3"
    >
      <h2 className="text-lg font-semibold text-foreground">Skills & Stack</h2>
      <Card className="bg-card border border-border/70 rounded-xl">
        <CardContent className="p-4 flex flex-wrap gap-2">
          {visibleSkills.length ? (
            visibleSkills.map((skill) => (
              <span
                key={skill}
                className="px-3 py-1.5 rounded-full text-xs md:text-sm border border-border/80 bg-muted/15 text-foreground"
              >
                {skill}
              </span>
            ))
          ) : (
            <span className="text-sm text-muted-foreground">Add 8-12 core skills to represent your stack.</span>
          )}
        </CardContent>
      </Card>
    </motion.section>
  );
}

import React, { useEffect, useState } from 'react';
import { Trophy, TrendingUp, TrendingDown, Minus, Star, Target, Zap } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';

const MyRankCard = ({ rank, previousRank, score, problemsSolved, isLoading = false }) => {
  const [animatedScore, setAnimatedScore] = useState(0);
  const [animatedRank, setAnimatedRank] = useState(0);

  useEffect(() => {
    if (score !== undefined) {
      const duration = 1500;
      const steps = 60;
      const increment = score / steps;
      let current = 0;
      
      const timer = setInterval(() => {
        current += increment;
        if (current >= score) {
          setAnimatedScore(score);
          clearInterval(timer);
        } else {
          setAnimatedScore(Math.floor(current));
        }
      }, duration / steps);

      return () => clearInterval(timer);
    }
  }, [score]);

  useEffect(() => {
    if (typeof rank !== 'number' || rank <= 0) {
      setAnimatedRank(0);
      return;
    }
    if (rank !== undefined) {
      const duration = 1000;
      const steps = 30;
      const startRank = Math.max(rank + 50, 1);
      const decrement = (startRank - rank) / steps;
      let current = startRank;
      
      const timer = setInterval(() => {
        current -= decrement;
        if (current <= rank) {
          setAnimatedRank(rank);
          clearInterval(timer);
        } else {
          setAnimatedRank(Math.floor(current));
        }
      }, duration / steps);

      return () => clearInterval(timer);
    }
  }, [rank]);

  const getRankChange = () => {
    if (!previousRank || !rank) return 0;
    return previousRank - rank;
  };

  const rankChange = getRankChange();

  const getRankIcon = () => {
    if (rank === 1) return <Trophy className="h-8 w-8 text-yellow-500" />;
    if (rank === 2) return <Trophy className="h-8 w-8 text-gray-400" />;
    if (rank === 3) return <Trophy className="h-8 w-8 text-amber-600" />;
    return <Target className="h-8 w-8 text-primary" />;
  };

  if (isLoading) {
    return (
      <Card className="bg-gradient-to-br from-primary/10 to-primary/5 border-primary/20">
        <CardContent className="p-6">
          <div className="animate-pulse space-y-4">
            <div className="h-6 bg-muted rounded w-1/3" />
            <div className="h-12 bg-muted rounded w-1/2" />
            <div className="grid grid-cols-3 gap-4">
              <div className="h-16 bg-muted rounded" />
              <div className="h-16 bg-muted rounded" />
              <div className="h-16 bg-muted rounded" />
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="bg-gradient-to-br from-primary/10 to-primary/5 border-primary/20 overflow-hidden relative">
      {/* Decorative elements */}
      <div className="absolute top-0 right-0 w-32 h-32 bg-primary/5 rounded-full -translate-y-1/2 translate-x-1/2" />
      <div className="absolute bottom-0 left-0 w-24 h-24 bg-primary/5 rounded-full translate-y-1/2 -translate-x-1/2" />
      
      <CardContent className="p-6 relative">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            {getRankIcon()}
            <div>
              <p className="text-sm text-muted-foreground font-medium">Your Rank</p>
              <div className="flex items-center gap-2">
                  <span className="text-4xl font-bold">
                    #{(rank === null || rank === undefined || rank === 0) ? '—' : (animatedRank || rank)}
                  </span>
                {rankChange !== 0 && (
                  <div className={`
                    flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium
                    ${rankChange > 0 
                      ? 'bg-green-500/10 text-green-500' 
                      : 'bg-destructive/10 text-destructive'
                    }
                  `}>
                    {rankChange > 0 ? (
                      <TrendingUp className="h-3 w-3" />
                    ) : (
                      <TrendingDown className="h-3 w-3" />
                    )}
                    {Math.abs(rankChange)}
                  </div>
                )}
              </div>
            </div>
          </div>
          
          <div className="text-right">
            <p className="text-sm text-muted-foreground font-medium">Total Score</p>
            <p className="text-3xl font-bold text-primary">
              {animatedScore.toLocaleString()}
            </p>
          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-3 gap-4">
          <div className="p-3 bg-background/50 rounded-lg text-center">
            <Star className="h-5 w-5 mx-auto mb-1 text-yellow-500" />
            <p className="text-lg font-bold">{problemsSolved || 0}</p>
            <p className="text-xs text-muted-foreground">Problems</p>
          </div>
          <div className="p-3 bg-background/50 rounded-lg text-center">
            <Zap className="h-5 w-5 mx-auto mb-1 text-primary" />
            <p className="text-lg font-bold">{Math.floor((score || 0) / Math.max(problemsSolved || 1, 1))}</p>
            <p className="text-xs text-muted-foreground">Avg Score</p>
          </div>
          <div className="p-3 bg-background/50 rounded-lg text-center">
            <TrendingUp className="h-5 w-5 mx-auto mb-1 text-green-500" />
            <p className="text-lg font-bold">
              {rankChange > 0 ? `+${rankChange}` : rankChange < 0 ? rankChange : '-'}
            </p>
            <p className="text-xs text-muted-foreground">This Week</p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default MyRankCard;

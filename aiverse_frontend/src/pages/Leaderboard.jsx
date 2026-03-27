import { useState, useEffect } from 'react';
import { Trophy, Medal, TrendingUp, TrendingDown, Minus, User, Crown, Flame } from 'lucide-react';
import Layout from '../components/Layout';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Badge } from '../components/ui/badge';
import LoadingSpinner from '../components/LoadingSpinner';
import MyRankCard from '../components/MyRankCard';
import api from '../api/axios';
import { useAuth } from '../contexts/AuthContext';

export default function Leaderboard() {
  const { user } = useAuth();
  const [rankings, setRankings] = useState([]);
  const [myRank, setMyRank] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [period, setPeriod] = useState('all_time');

  useEffect(() => {
    fetchLeaderboard();
    
    // Listen for submission events to refresh leaderboard
    const handleSubmission = () => {
      fetchLeaderboard();
    };
    
    window.addEventListener('submission-completed', handleSubmission);
    
    return () => {
      window.removeEventListener('submission-completed', handleSubmission);
    };
  }, [period]);

  const fetchLeaderboard = async () => {
    try {
      setIsLoading(true);
      const res = await api.get(`/api/leaderboard/?period=${period}&page=1&limit=25`);
      const payload = res?.data || {};

      const results = payload.results || [];
      setRankings(
        results.map((r) => ({
          id: Number(r.user_id),
          rank: r.rank,
          user_id: Number(r.user_id),
          avatar: r.avatar_url,
          name: r.display_name || r.username,
          score: r.score,
          problems_solved: r.problems_solved,
          // Weekly movement vs previous snapshot (backend: previous_rank - current_rank)
          rank_change: r.weekly_delta,
        }))
      );
      setMyRank(payload.me || null);
    } catch (err) {
      console.error('Failed to fetch leaderboard:', err);
      setRankings([]);
      setMyRank(null);
    } finally {
      setIsLoading(false);
    }
  };

  const getRankIcon = (rank) => {
    if (rank === 1) return <Crown className="w-6 h-6 text-yellow-500" />;
    if (rank === 2) return <Medal className="w-5 h-5 text-gray-400" />;
    if (rank === 3) return <Medal className="w-5 h-5 text-amber-600" />;
    return <span className="text-sm font-bold text-muted-foreground">#{rank}</span>;
  };

  const getRankChange = (change) => {
    if (!change || change === 0) {
      return <Minus className="w-4 h-4 text-muted-foreground" />;
    }
    if (change > 0) {
      return (
        <span className="flex items-center gap-0.5 text-green-600 text-xs font-medium">
          <TrendingUp className="w-3 h-3" />
          {change}
        </span>
      );
    }
    return (
      <span className="flex items-center gap-0.5 text-red-500 text-xs font-medium">
        <TrendingDown className="w-3 h-3" />
        {Math.abs(change)}
      </span>
    );
  };

  const getPodiumClass = (rank) => {
    if (rank === 1) return 'bg-gradient-to-br from-yellow-100 to-yellow-50 dark:from-yellow-900/30 dark:to-yellow-900/10 border-yellow-300 dark:border-yellow-700';
    if (rank === 2) return 'bg-gradient-to-br from-gray-100 to-gray-50 dark:from-gray-800/50 dark:to-gray-800/30 border-gray-300 dark:border-gray-600';
    if (rank === 3) return 'bg-gradient-to-br from-amber-100 to-amber-50 dark:from-amber-900/30 dark:to-amber-900/10 border-amber-300 dark:border-amber-700';
    return '';
  };

  const topThree = rankings.slice(0, 3);
  const restOfRankings = rankings.slice(3);

  return (
    <Layout>
      <div className="container mx-auto px-4 lg:px-8 py-12">
        {/* Header */}
        <div className="text-center mb-12">
          <div className="inline-flex items-center gap-2 mb-4">
            <Trophy className="w-8 h-8 text-primary" />
            <h1 className="heading-primary text-foreground">Leaderboard</h1>
          </div>
          <p className="text-muted-foreground max-w-lg mx-auto">
            Compete with fellow ML learners. Climb the ranks by solving problems and completing courses.
          </p>
        </div>

        {/* My Rank Card */}
        {myRank && (
          <div className="mb-8">
            <MyRankCard 
              rank={myRank.rank}
              previousRank={
                typeof myRank.weekly_delta === 'number' && typeof myRank.rank === 'number'
                  ? myRank.rank + myRank.weekly_delta
                  : undefined
              }
              score={myRank.score}
              problemsSolved={myRank.problems_solved}
              isLoading={isLoading}
            />
          </div>
        )}

        {/* Period Tabs */}
        <Tabs value={period} onValueChange={setPeriod} className="mb-8">
          <TabsList className="grid w-full max-w-md mx-auto grid-cols-3">
            <TabsTrigger value="all_time">All Time</TabsTrigger>
            <TabsTrigger value="monthly">This Month</TabsTrigger>
            <TabsTrigger value="weekly">This Week</TabsTrigger>
          </TabsList>
        </Tabs>

        {isLoading ? (
          <LoadingSpinner text="Loading rankings..." />
        ) : (
          <>
            {/* Podium - Top 3 */}
            {topThree.length > 0 && (
              <div className="flex justify-center items-end gap-4 mb-12">
                {/* 2nd Place */}
                {topThree[1] && (
                  <div 
                    className={`card-elevated p-6 text-center w-40 border-2 ${getPodiumClass(2)} animate-fade-in`}
                    style={{ animationDelay: '100ms' }}
                  >
                    <div className="w-16 h-16 rounded-full bg-gray-200 dark:bg-gray-700 flex items-center justify-center mx-auto mb-3">
                      {topThree[1].avatar ? (
                        <img src={topThree[1].avatar} alt="" className="w-full h-full rounded-full object-cover" />
                      ) : (
                        <User className="w-8 h-8 text-gray-500" />
                      )}
                    </div>
                    <Medal className="w-8 h-8 text-gray-400 mx-auto mb-2" />
                    <p className="font-medium text-foreground truncate">{topThree[1].name}</p>
                    <p className="text-2xl font-bold text-foreground">{topThree[1].score}</p>
                    <p className="text-xs text-muted-foreground">{topThree[1].problems_solved} problems</p>
                  </div>
                )}

                {/* 1st Place */}
                {topThree[0] && (
                  <div 
                    className={`card-elevated p-8 text-center w-48 border-2 ${getPodiumClass(1)} animate-fade-in transform scale-105`}
                    style={{ animationDelay: '0ms' }}
                  >
                    <div className="w-20 h-20 rounded-full bg-yellow-200 dark:bg-yellow-800 flex items-center justify-center mx-auto mb-3 ring-4 ring-yellow-400/50">
                      {topThree[0].avatar ? (
                        <img src={topThree[0].avatar} alt="" className="w-full h-full rounded-full object-cover" />
                      ) : (
                        <User className="w-10 h-10 text-yellow-600" />
                      )}
                    </div>
                    <Crown className="w-10 h-10 text-yellow-500 mx-auto mb-2" />
                    <p className="font-semibold text-foreground truncate">{topThree[0].name}</p>
                    <p className="text-3xl font-bold text-foreground">{topThree[0].score}</p>
                    <p className="text-xs text-muted-foreground">{topThree[0].problems_solved} problems</p>
                    {topThree[0].streak > 0 && (
                      <Badge className="mt-2 bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400">
                        <Flame className="w-3 h-3 mr-1" />
                        {topThree[0].streak} day streak
                      </Badge>
                    )}
                  </div>
                )}

                {/* 3rd Place */}
                {topThree[2] && (
                  <div 
                    className={`card-elevated p-6 text-center w-40 border-2 ${getPodiumClass(3)} animate-fade-in`}
                    style={{ animationDelay: '200ms' }}
                  >
                    <div className="w-16 h-16 rounded-full bg-amber-200 dark:bg-amber-800 flex items-center justify-center mx-auto mb-3">
                      {topThree[2].avatar ? (
                        <img src={topThree[2].avatar} alt="" className="w-full h-full rounded-full object-cover" />
                      ) : (
                        <User className="w-8 h-8 text-amber-600" />
                      )}
                    </div>
                    <Medal className="w-8 h-8 text-amber-600 mx-auto mb-2" />
                    <p className="font-medium text-foreground truncate">{topThree[2].name}</p>
                    <p className="text-2xl font-bold text-foreground">{topThree[2].score}</p>
                    <p className="text-xs text-muted-foreground">{topThree[2].problems_solved} problems</p>
                  </div>
                )}
              </div>
            )}

            {/* Rest of Rankings */}
            {restOfRankings.length > 0 && (
              <div className="card-elevated overflow-hidden">
                <table className="w-full">
                  <thead className="bg-muted/50">
                    <tr>
                      <th className="text-left px-6 py-4 text-sm font-medium text-muted-foreground w-24">Rank</th>
                      <th className="text-left px-6 py-4 text-sm font-medium text-muted-foreground">User</th>
                      <th className="text-center px-6 py-4 text-sm font-medium text-muted-foreground w-24">Change</th>
                      <th className="text-right px-6 py-4 text-sm font-medium text-muted-foreground w-32">Problems</th>
                      <th className="text-right px-6 py-4 text-sm font-medium text-muted-foreground w-32">Score</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border">
                    {restOfRankings.map((entry, index) => (
                      <tr 
                        key={entry.id} 
                        className={`hover:bg-muted/30 transition-colors animate-fade-in ${
                          entry.user_id === user?.id ? 'bg-primary/5' : ''
                        }`}
                        style={{ animationDelay: `${(index + 3) * 50}ms` }}
                      >
                        <td className="px-6 py-4">
                          <div className="w-10 h-10 flex items-center justify-center">
                            {getRankIcon(entry.rank)}
                          </div>
                        </td>
                        <td className="px-6 py-4">
                          <div className="flex items-center gap-3">
                            <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center shrink-0">
                              {entry.avatar ? (
                                <img src={entry.avatar} alt="" className="w-full h-full rounded-full object-cover" />
                              ) : (
                                <User className="w-5 h-5 text-primary" />
                              )}
                            </div>
                            <div>
                              <span className="font-medium text-foreground">{entry.name}</span>
                              {entry.user_id === user?.id && (
                                <Badge className="ml-2 text-xs" variant="outline">You</Badge>
                              )}
                            </div>
                          </div>
                        </td>
                        <td className="px-6 py-4 text-center">
                          {getRankChange(entry.rank_change)}
                        </td>
                        <td className="px-6 py-4 text-right text-muted-foreground">
                          {entry.problems_solved}
                        </td>
                        <td className="px-6 py-4 text-right">
                          <span className="font-bold text-foreground">{entry.score}</span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {rankings.length === 0 && (
              <div className="text-center py-12">
                <Trophy className="w-16 h-16 text-muted-foreground mx-auto mb-4 opacity-50" />
                <h3 className="font-serif text-lg font-medium text-foreground mb-2">No rankings yet</h3>
                <p className="text-muted-foreground">Be the first to climb the leaderboard!</p>
              </div>
            )}
          </>
        )}
      </div>
    </Layout>
  );
}

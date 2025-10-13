import { useState, useEffect } from 'react';
import { TrendingUp, DollarSign, Users, Video, Gift, Eye, Heart, Shield, Vote, BarChart3, Crown, ThumbsUp, ThumbsDown, Clock } from 'lucide-react';
import { supabase } from '../../lib/supabase';
import { useAuth } from '../../contexts/AuthContext';
import { useLanguage } from '../../contexts/LanguageContext';

interface CreatorMetrics {
  total_videos: number;
  total_views: number;
  total_engagement: number;
  engagement_score: number;
  profit_share_percentage: number;
}

interface LedgerEntry {
  id: string;
  transaction_type: string;
  amount: number;
  source: string;
  created_at: string;
}

interface CreatorTier {
  tier_name: string;
  governance_access: boolean;
  assigned_at: string;
}

interface TierInfo {
  tier_name: string;
  min_engagement_score: number;
  min_followers: number;
  min_videos: number;
  governance_weight: number;
  benefits: any;
}

interface PlatformMetrics {
  date: string;
  total_users: number;
  active_users: number;
  total_videos: number;
  total_views: number;
  total_engagement: number;
  total_revenue: number;
  total_expenses: number;
  net_profit: number;
}

interface Proposal {
  id: string;
  title: string;
  description: string;
  proposal_type: string;
  status: string;
  voting_ends_at: string;
  created_at: string;
  creator_id: string;
}

export function CreatorDashboard() {
  const { user } = useAuth();
  const { t } = useLanguage();
  const [activeTab, setActiveTab] = useState<'overview' | 'governance' | 'platform'>('overview');
  const [metrics, setMetrics] = useState<CreatorMetrics | null>(null);
  const [balance, setBalance] = useState(0);
  const [ledger, setLedger] = useState<LedgerEntry[]>([]);
  const [tier, setTier] = useState<CreatorTier | null>(null);
  const [tierInfo, setTierInfo] = useState<TierInfo | null>(null);
  const [platformMetrics, setPlatformMetrics] = useState<PlatformMetrics[]>([]);
  const [proposals, setProposals] = useState<Proposal[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (user) {
      loadDashboard();
    }
  }, [user]);

  const loadDashboard = async () => {
    if (!user) return;

    const [metricsRes, currencyRes, ledgerRes, tierRes, proposalsRes] = await Promise.all([
      supabase
        .from('creator_metrics')
        .select('*')
        .eq('creator_id', user.id)
        .maybeSingle(),
      supabase
        .from('virtual_currency')
        .select('balance')
        .eq('user_id', user.id)
        .maybeSingle(),
      supabase
        .from('creator_partnership_ledger')
        .select('*')
        .eq('creator_id', user.id)
        .order('created_at', { ascending: false })
        .limit(10),
      supabase
        .from('creator_tier_assignments')
        .select('*')
        .eq('creator_id', user.id)
        .maybeSingle(),
      supabase
        .from('governance_proposals')
        .select('*')
        .order('created_at', { ascending: false })
        .limit(10),
    ]);

    if (metricsRes.data) setMetrics(metricsRes.data);
    if (currencyRes.data) setBalance(currencyRes.data.balance);
    if (ledgerRes.data) setLedger(ledgerRes.data);
    if (tierRes.data) {
      setTier(tierRes.data);
      loadTierInfo(tierRes.data.tier_name);

      if (tierRes.data.governance_access) {
        loadPlatformMetrics();
      }
    }
    if (proposalsRes.data) setProposals(proposalsRes.data);

    setLoading(false);
  };

  const loadTierInfo = async (tierName: string) => {
    const { data } = await supabase
      .from('creator_tiers')
      .select('*')
      .eq('tier_name', tierName)
      .maybeSingle();

    if (data) setTierInfo(data);
  };

  const loadPlatformMetrics = async () => {
    const { data } = await supabase
      .from('platform_metrics')
      .select('*')
      .order('date', { ascending: false })
      .limit(30);

    if (data) setPlatformMetrics(data);
  };

  const handleVote = async (proposalId: string, vote: 'yes' | 'no' | 'abstain') => {
    if (!user || !tier?.governance_access || !tierInfo) return;

    const { error } = await supabase
      .from('governance_votes')
      .insert({
        proposal_id: proposalId,
        voter_id: user.id,
        vote,
        voting_weight: tierInfo.governance_weight,
      });

    if (!error) {
      alert(`Vote cast: ${vote}`);
      loadDashboard();
    } else {
      alert('Failed to cast vote: ' + error.message);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-black text-white">
        <div>Loading dashboard...</div>
      </div>
    );
  }

  const tierColors = {
    bronze: 'from-orange-700 to-orange-900',
    silver: 'from-gray-400 to-gray-600',
    gold: 'from-yellow-500 to-yellow-700',
    platinum: 'from-cyan-400 to-cyan-600',
    diamond: 'from-purple-500 to-pink-500',
  };

  const tierColor = tierColors[tier?.tier_name as keyof typeof tierColors] || tierColors.bronze;

  return (
    <div className="min-h-screen bg-black text-white p-6 pb-24">
      <div className="max-w-6xl mx-auto">
        <div className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="text-3xl font-bold mb-2">Creator Dashboard</h1>
              <p className="text-gray-400">Track your performance, earnings, and governance</p>
            </div>
            <div className={`flex items-center gap-2 px-4 py-2 bg-gradient-to-r ${tierColor} rounded-xl`}>
              <Crown className="w-5 h-5" />
              <span className="font-bold capitalize">{tier?.tier_name || 'Bronze'} Tier</span>
            </div>
          </div>

          <div className="flex gap-2 mb-6 overflow-x-auto">
            <TabButton
              active={activeTab === 'overview'}
              onClick={() => setActiveTab('overview')}
              icon={<BarChart3 className="w-5 h-5" />}
              label={t('creator.overview')}
            />
            {tier?.governance_access && (
              <>
                <TabButton
                  active={activeTab === 'governance'}
                  onClick={() => setActiveTab('governance')}
                  icon={<Vote className="w-5 h-5" />}
                  label="Governance"
                  badge="Elite"
                />
                <TabButton
                  active={activeTab === 'platform'}
                  onClick={() => setActiveTab('platform')}
                  icon={<TrendingUp className="w-5 h-5" />}
                  label="Platform Insights"
                  badge="Elite"
                />
              </>
            )}
          </div>
        </div>

        {activeTab === 'overview' && (
          <>
            <div className="bg-gradient-to-br from-blue-600 to-cyan-600 rounded-2xl p-6 mb-6">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <p className="text-blue-100 text-sm mb-1">Your Balance</p>
                  <p className="text-4xl font-bold text-white">{balance.toLocaleString()}</p>
                  <p className="text-blue-100 text-sm">coins</p>
                </div>
                <div className="w-16 h-16 bg-white/20 rounded-full flex items-center justify-center">
                  <DollarSign className="w-8 h-8 text-white" />
                </div>
              </div>
              <button className="w-full py-3 bg-white text-blue-600 rounded-lg font-semibold hover:bg-blue-50 transition active:scale-95">
                Withdraw Earnings
              </button>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
              <MetricCard
                icon={<Video className="w-6 h-6" />}
                label="Videos"
                value={metrics?.total_videos.toLocaleString() || '0'}
                color="bg-blue-500/20 text-blue-400"
              />
              <MetricCard
                icon={<Eye className="w-6 h-6" />}
                label="Total Views"
                value={metrics?.total_views.toLocaleString() || '0'}
                color="bg-purple-500/20 text-purple-400"
              />
              <MetricCard
                icon={<Heart className="w-6 h-6" />}
                label="Engagement"
                value={metrics?.total_engagement.toLocaleString() || '0'}
                color="bg-red-500/20 text-red-400"
              />
              <MetricCard
                icon={<TrendingUp className="w-6 h-6" />}
                label="Score"
                value={Math.floor(metrics?.engagement_score || 0).toLocaleString()}
                color="bg-green-500/20 text-green-400"
              />
            </div>

            <div className="bg-gray-900 rounded-2xl p-6 border border-gray-800 mb-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-bold flex items-center gap-2">
                  <Crown className="w-6 h-6 text-yellow-500" />
                  Creator Tier Status
                </h2>
                <span className={`px-4 py-2 bg-gradient-to-r ${tierColor} rounded-lg font-bold capitalize`}>
                  {tier?.tier_name || 'Bronze'}
                </span>
              </div>
              {tierInfo && (
                <>
                  <div className="grid md:grid-cols-3 gap-4 mb-4">
                    <div className="bg-gray-800 rounded-lg p-4">
                      <div className="text-sm text-gray-400 mb-1">Min Engagement Score</div>
                      <div className="text-2xl font-bold text-white">{tierInfo.min_engagement_score.toLocaleString()}</div>
                      <div className="text-xs text-gray-500 mt-1">
                        Your score: {Math.floor(metrics?.engagement_score || 0).toLocaleString()}
                      </div>
                    </div>
                    <div className="bg-gray-800 rounded-lg p-4">
                      <div className="text-sm text-gray-400 mb-1">Min Followers</div>
                      <div className="text-2xl font-bold text-white">{tierInfo.min_followers.toLocaleString()}</div>
                    </div>
                    <div className="bg-gray-800 rounded-lg p-4">
                      <div className="text-sm text-gray-400 mb-1">Min Videos</div>
                      <div className="text-2xl font-bold text-white">{tierInfo.min_videos}</div>
                      <div className="text-xs text-gray-500 mt-1">
                        Your videos: {metrics?.total_videos || 0}
                      </div>
                    </div>
                  </div>
                  <div className="bg-gray-800 rounded-lg p-4">
                    <h3 className="font-bold mb-2 flex items-center gap-2">
                      <Gift className="w-5 h-5 text-blue-400" />
                      Tier Benefits
                    </h3>
                    <ul className="space-y-2">
                      {tierInfo.benefits?.features?.map((feature: string, i: number) => (
                        <li key={i} className="flex items-center gap-2 text-sm text-gray-300">
                          <div className="w-1.5 h-1.5 bg-blue-400 rounded-full" />
                          {feature}
                        </li>
                      ))}
                    </ul>
                    {tier?.governance_access && (
                      <div className="mt-4 p-3 bg-gradient-to-r from-purple-500/20 to-pink-500/20 border border-purple-500/30 rounded-lg">
                        <div className="flex items-center gap-2 text-purple-300 font-semibold">
                          <Shield className="w-5 h-5" />
                          Governance Access Granted
                        </div>
                        <p className="text-xs text-purple-200 mt-1">
                          You can vote on proposals and view platform insights
                        </p>
                      </div>
                    )}
                  </div>
                </>
              )}
            </div>

            <div className="bg-gray-900 rounded-2xl p-6 border border-gray-800 mb-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-bold">Partnership Share</h2>
                <span className="text-2xl font-bold text-blue-400">
                  {metrics?.profit_share_percentage.toFixed(4)}%
                </span>
              </div>
              <p className="text-gray-400 text-sm mb-4">
                Your proportional share of platform net profits based on engagement and contribution
              </p>
              <div className="bg-gray-800 rounded-lg p-4">
                <div className="flex items-center justify-between text-sm mb-2">
                  <span className="text-gray-400">Your Engagement Score</span>
                  <span className="text-white font-semibold">{Math.floor(metrics?.engagement_score || 0).toLocaleString()}</span>
                </div>
                <div className="w-full bg-gray-700 rounded-full h-2 overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-blue-600 to-cyan-600 rounded-full"
                    style={{ width: `${Math.min(100, (metrics?.engagement_score || 0) / 1000)}%` }}
                  />
                </div>
              </div>
            </div>

            <div className="bg-gray-900 rounded-2xl p-6 border border-gray-800">
              <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
                <Gift className="w-6 h-6" />
                Recent Transactions
              </h2>
              {ledger.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  No transactions yet
                </div>
              ) : (
                <div className="space-y-3">
                  {ledger.map((entry) => (
                    <div
                      key={entry.id}
                      className="flex items-center justify-between p-4 bg-gray-800 rounded-lg hover:bg-gray-750 transition"
                    >
                      <div className="flex items-center gap-3">
                        <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                          entry.transaction_type === 'revenue' ? 'bg-green-500/20' :
                          entry.transaction_type === 'distribution' ? 'bg-blue-500/20' :
                          'bg-red-500/20'
                        }`}>
                          <DollarSign className={`w-5 h-5 ${
                            entry.transaction_type === 'revenue' ? 'text-green-400' :
                            entry.transaction_type === 'distribution' ? 'text-blue-400' :
                            'text-red-400'
                          }`} />
                        </div>
                        <div>
                          <div className="font-semibold text-white capitalize">
                            {entry.source}
                          </div>
                          <div className="text-sm text-gray-400">
                            {new Date(entry.created_at).toLocaleDateString()}
                          </div>
                        </div>
                      </div>
                      <div className={`font-bold ${
                        entry.transaction_type === 'revenue' || entry.transaction_type === 'distribution'
                          ? 'text-green-400'
                          : 'text-red-400'
                      }`}>
                        {entry.transaction_type === 'revenue' || entry.transaction_type === 'distribution' ? '+' : '-'}
                        {entry.amount.toLocaleString()}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </>
        )}

        {activeTab === 'governance' && tier?.governance_access && (
          <>
            <div className="bg-gradient-to-r from-purple-600 to-pink-600 rounded-2xl p-6 mb-6 text-white">
              <div className="flex items-center gap-3 mb-4">
                <Vote className="w-8 h-8" />
                <div>
                  <h2 className="text-2xl font-bold">Governance Portal</h2>
                  <p className="text-purple-100">Shape the future of the platform</p>
                </div>
              </div>
              <div className="grid md:grid-cols-2 gap-4">
                <div className="bg-white/10 backdrop-blur-sm rounded-lg p-4">
                  <div className="text-sm text-purple-100 mb-1">Your Voting Weight</div>
                  <div className="text-3xl font-bold">{tierInfo?.governance_weight}x</div>
                </div>
                <div className="bg-white/10 backdrop-blur-sm rounded-lg p-4">
                  <div className="text-sm text-purple-100 mb-1">Active Proposals</div>
                  <div className="text-3xl font-bold">{proposals.filter(p => p.status === 'active').length}</div>
                </div>
              </div>
            </div>

            <div className="space-y-4">
              {proposals.map((proposal) => (
                <ProposalCard
                  key={proposal.id}
                  proposal={proposal}
                  onVote={handleVote}
                  userId={user?.id}
                />
              ))}
              {proposals.length === 0 && (
                <div className="text-center py-12 text-gray-500">
                  No proposals yet
                </div>
              )}
            </div>
          </>
        )}

        {activeTab === 'platform' && tier?.governance_access && (
          <>
            <div className="bg-gradient-to-r from-blue-600 to-cyan-600 rounded-2xl p-6 mb-6 text-white">
              <div className="flex items-center gap-3 mb-4">
                <BarChart3 className="w-8 h-8" />
                <div>
                  <h2 className="text-2xl font-bold">Platform Insights</h2>
                  <p className="text-blue-100">Exclusive metrics for governance partners</p>
                </div>
              </div>
            </div>

            {platformMetrics.length > 0 && (
              <>
                <div className="grid md:grid-cols-4 gap-4 mb-6">
                  <PlatformMetricCard
                    label="Total Users"
                    value={platformMetrics[0].total_users.toLocaleString()}
                    icon={<Users className="w-6 h-6" />}
                    color="blue"
                  />
                  <PlatformMetricCard
                    label="Active Users (7d)"
                    value={platformMetrics[0].active_users.toLocaleString()}
                    icon={<TrendingUp className="w-6 h-6" />}
                    color="green"
                  />
                  <PlatformMetricCard
                    label="Total Videos"
                    value={platformMetrics[0].total_videos.toLocaleString()}
                    icon={<Video className="w-6 h-6" />}
                    color="purple"
                  />
                  <PlatformMetricCard
                    label="Total Views"
                    value={platformMetrics[0].total_views.toLocaleString()}
                    icon={<Eye className="w-6 h-6" />}
                    color="pink"
                  />
                </div>

                <div className="bg-gray-900 rounded-2xl p-6 border border-gray-800 mb-6">
                  <h3 className="text-xl font-bold mb-4">{t('creator.financialOverview')}</h3>
                  <div className="grid md:grid-cols-3 gap-4">
                    <div className="bg-gray-800 rounded-lg p-4">
                      <div className="text-sm text-gray-400 mb-2">Total Revenue</div>
                      <div className="text-2xl font-bold text-green-400">
                        ${platformMetrics[0].total_revenue.toLocaleString()}
                      </div>
                    </div>
                    <div className="bg-gray-800 rounded-lg p-4">
                      <div className="text-sm text-gray-400 mb-2">Total Expenses</div>
                      <div className="text-2xl font-bold text-red-400">
                        ${platformMetrics[0].total_expenses.toLocaleString()}
                      </div>
                    </div>
                    <div className="bg-gray-800 rounded-lg p-4">
                      <div className="text-sm text-gray-400 mb-2">Net Profit</div>
                      <div className="text-2xl font-bold text-blue-400">
                        ${platformMetrics[0].net_profit.toLocaleString()}
                      </div>
                    </div>
                  </div>
                </div>

                <div className="bg-gray-900 rounded-2xl p-6 border border-gray-800">
                  <h3 className="text-xl font-bold mb-4">Historical Metrics (Last 30 Days)</h3>
                  <div className="space-y-3">
                    {platformMetrics.slice(0, 10).map((metric) => (
                      <div key={metric.date} className="flex items-center justify-between p-3 bg-gray-800 rounded-lg">
                        <span className="text-gray-400">{new Date(metric.date).toLocaleDateString()}</span>
                        <div className="flex gap-6 text-sm">
                          <span className="text-blue-400">{metric.active_users} active</span>
                          <span className="text-green-400">${metric.net_profit.toLocaleString()} profit</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </>
            )}
          </>
        )}
      </div>
    </div>
  );
}

function TabButton({ active, onClick, icon, label, badge }: {
  active: boolean;
  onClick: () => void;
  icon: React.ReactNode;
  label: string;
  badge?: string;
}) {
  return (
    <button
      onClick={onClick}
      className={`flex items-center gap-2 px-4 py-2 rounded-lg font-semibold transition whitespace-nowrap ${
        active
          ? 'bg-gradient-to-r from-blue-600 to-cyan-600 text-white'
          : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
      }`}
    >
      {icon}
      {label}
      {badge && (
        <span className="px-2 py-0.5 bg-purple-500 text-xs rounded-full text-white">
          {badge}
        </span>
      )}
    </button>
  );
}

function MetricCard({ icon, label, value, color }: {
  icon: React.ReactNode;
  label: string;
  value: string;
  color: string;
}) {
  return (
    <div className="bg-gray-900 rounded-xl p-4 border border-gray-800">
      <div className={`w-12 h-12 rounded-lg ${color} flex items-center justify-center mb-3`}>
        {icon}
      </div>
      <div className="text-2xl font-bold text-white mb-1">{value}</div>
      <div className="text-sm text-gray-400">{label}</div>
    </div>
  );
}

function PlatformMetricCard({ label, value, icon, color }: {
  label: string;
  value: string;
  icon: React.ReactNode;
  color: string;
}) {
  const colors = {
    blue: 'from-blue-500 to-cyan-500',
    green: 'from-green-500 to-emerald-500',
    purple: 'from-purple-500 to-pink-500',
    pink: 'from-pink-500 to-rose-500',
  };

  return (
    <div className="bg-gray-900 rounded-xl p-4 border border-gray-800">
      <div className={`w-12 h-12 rounded-lg bg-gradient-to-br ${colors[color as keyof typeof colors]} flex items-center justify-center mb-3 text-white`}>
        {icon}
      </div>
      <div className="text-2xl font-bold text-white mb-1">{value}</div>
      <div className="text-sm text-gray-400">{label}</div>
    </div>
  );
}

function ProposalCard({ proposal, onVote, userId }: {
  proposal: Proposal;
  onVote: (id: string, vote: 'yes' | 'no' | 'abstain') => void;
  userId?: string;
}) {
  const [votes, setVotes] = useState<any>(null);

  useEffect(() => {
    loadVotes();
  }, [proposal.id]);

  const loadVotes = async () => {
    const { data } = await supabase.rpc('get_proposal_results', { proposal_uuid: proposal.id });
    if (data && data[0]) setVotes(data[0]);
  };

  const typeColors = {
    feature: 'text-blue-400 bg-blue-500/20',
    policy: 'text-purple-400 bg-purple-500/20',
    budget: 'text-green-400 bg-green-500/20',
    moderation: 'text-red-400 bg-red-500/20',
  };

  const statusColors = {
    active: 'text-green-400 bg-green-500/20',
    passed: 'text-blue-400 bg-blue-500/20',
    rejected: 'text-red-400 bg-red-500/20',
    implemented: 'text-purple-400 bg-purple-500/20',
  };

  const isActive = proposal.status === 'active' && new Date(proposal.voting_ends_at) > new Date();

  return (
    <div className="bg-gray-900 rounded-2xl p-6 border border-gray-800">
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2">
            <span className={`px-3 py-1 rounded-full text-xs font-semibold capitalize ${typeColors[proposal.proposal_type as keyof typeof typeColors]}`}>
              {proposal.proposal_type}
            </span>
            <span className={`px-3 py-1 rounded-full text-xs font-semibold capitalize ${statusColors[proposal.status as keyof typeof statusColors]}`}>
              {proposal.status}
            </span>
          </div>
          <h3 className="text-xl font-bold text-white mb-2">{proposal.title}</h3>
          <p className="text-gray-400 text-sm mb-4">{proposal.description}</p>
          <div className="flex items-center gap-4 text-sm text-gray-500">
            <span className="flex items-center gap-1">
              <Clock className="w-4 h-4" />
              Ends {new Date(proposal.voting_ends_at).toLocaleDateString()}
            </span>
          </div>
        </div>
      </div>

      {votes && (
        <div className="mb-4 p-4 bg-gray-800 rounded-lg">
          <div className="grid grid-cols-3 gap-4 text-center mb-3">
            <div>
              <div className="text-2xl font-bold text-green-400">{votes.yes_votes}</div>
              <div className="text-xs text-gray-400">Yes ({votes.yes_weight}x weight)</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-red-400">{votes.no_votes}</div>
              <div className="text-xs text-gray-400">No ({votes.no_weight}x weight)</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-gray-400">{votes.abstain_votes}</div>
              <div className="text-xs text-gray-400">Abstain</div>
            </div>
          </div>
          <div className="w-full bg-gray-700 rounded-full h-2 overflow-hidden flex">
            <div
              className="bg-green-500"
              style={{ width: `${votes.total_weight > 0 ? (votes.yes_weight / votes.total_weight) * 100 : 0}%` }}
            />
            <div
              className="bg-red-500"
              style={{ width: `${votes.total_weight > 0 ? (votes.no_weight / votes.total_weight) * 100 : 0}%` }}
            />
          </div>
        </div>
      )}

      {isActive && (
        <div className="flex gap-2">
          <button
            onClick={() => onVote(proposal.id, 'yes')}
            className="flex-1 flex items-center justify-center gap-2 py-3 bg-green-500/20 text-green-400 rounded-lg font-semibold hover:bg-green-500/30 transition active:scale-95"
          >
            <ThumbsUp className="w-5 h-5" />
            Vote Yes
          </button>
          <button
            onClick={() => onVote(proposal.id, 'no')}
            className="flex-1 flex items-center justify-center gap-2 py-3 bg-red-500/20 text-red-400 rounded-lg font-semibold hover:bg-red-500/30 transition active:scale-95"
          >
            <ThumbsDown className="w-5 h-5" />
            Vote No
          </button>
          <button
            onClick={() => onVote(proposal.id, 'abstain')}
            className="px-6 py-3 bg-gray-800 text-gray-400 rounded-lg font-semibold hover:bg-gray-700 transition active:scale-95"
          >
            Abstain
          </button>
        </div>
      )}
    </div>
  );
}

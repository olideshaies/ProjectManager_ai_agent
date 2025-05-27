import React, { useState, useEffect } from 'react';
import { Card, CardContent, Typography, Box, CircularProgress, Button } from '@mui/material';
import { format } from 'date-fns';
import { Warning, CheckCircle, Cancel } from '@mui/icons-material';

interface ScoreboardData {
  id: string;
  date: string;
  net_pnl: number;
  profit_factor: number;
  focus_ratio: number;
  milestone_hit: boolean;
  schedule_adherence: number;
  daily_milestone: string;
  milestone_time_set: string;
}

interface ScoreboardWidgetProps {
  onSetMilestone: () => void;
  onUpdateMetrics: () => void;
}

const ScoreboardWidget: React.FC<ScoreboardWidgetProps> = ({ onSetMilestone, onUpdateMetrics }) => {
  const [scoreboard, setScoreboard] = useState<ScoreboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchTodayScoreboard = async () => {
    try {
      const response = await fetch('/api/scoreboard/today');
      if (!response.ok) {
        if (response.status === 404) {
          setScoreboard(null);
        } else {
          throw new Error('Failed to fetch scoreboard');
        }
      } else {
        const data = await response.json();
        setScoreboard(data);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTodayScoreboard();
  }, []);

  if (loading) {
    return (
      <Card sx={{ minWidth: 275, mb: 2 }}>
        <CardContent>
          <Box display="flex" justifyContent="center" alignItems="center" minHeight={200}>
            <CircularProgress />
          </Box>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card sx={{ minWidth: 275, mb: 2, bgcolor: '#fff3f3' }}>
        <CardContent>
          <Typography color="error">{error}</Typography>
        </CardContent>
      </Card>
    );
  }

  if (!scoreboard) {
    return (
      <Card sx={{ minWidth: 275, mb: 2 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Daily Scoreboard
          </Typography>
          <Typography color="textSecondary">
            No scoreboard entry for today. Set your daily milestone to begin tracking.
          </Typography>
          <Button 
            variant="contained" 
            color="primary" 
            sx={{ mt: 2 }}
            onClick={onSetMilestone}
          >
            Set Daily Milestone
          </Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card sx={{ minWidth: 275, mb: 2 }}>
      <CardContent>
        <Box display="flex" alignItems="center" mb={2}>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            Daily Scoreboard
          </Typography>
          {!scoreboard.milestone_hit && (
            <Warning color="warning" />
          )}
        </Box>

        <Box display="grid" gridTemplateColumns="repeat(2, 1fr)" gap={2}>
          <Box>
            <Typography variant="subtitle2" color="textSecondary">
              Net P&L
            </Typography>
            <Typography variant="h6" color={scoreboard.net_pnl >= 0 ? 'success.main' : 'error.main'}>
              ${scoreboard.net_pnl.toFixed(2)} CAD
            </Typography>
          </Box>

          <Box>
            <Typography variant="subtitle2" color="textSecondary">
              Profit Factor
            </Typography>
            <Typography variant="h6">
              {scoreboard.profit_factor.toFixed(2)}
            </Typography>
          </Box>

          <Box>
            <Typography variant="subtitle2" color="textSecondary">
              Focus Ratio
            </Typography>
            <Typography variant="h6">
              {(scoreboard.focus_ratio * 100).toFixed(1)}%
            </Typography>
          </Box>

          <Box>
            <Typography variant="subtitle2" color="textSecondary">
              Schedule Adherence
            </Typography>
            <Typography variant="h6">
              {scoreboard.schedule_adherence.toFixed(1)}%
            </Typography>
          </Box>
        </Box>

        <Box mt={2}>
          <Typography variant="subtitle2" color="textSecondary">
            Daily Milestone
          </Typography>
          <Typography variant="body1" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            {scoreboard.daily_milestone}
            {scoreboard.milestone_hit ? (
              <CheckCircle color="success" fontSize="small" />
            ) : (
              <Cancel color="error" fontSize="small" />
            )}
          </Typography>
        </Box>

        <Box mt={2} display="flex" justifyContent="space-between">
          <Typography variant="caption" color="textSecondary">
            Set at: {format(new Date(scoreboard.milestone_time_set), 'HH:mm')}
          </Typography>
          <Button 
            variant="outlined" 
            size="small"
            onClick={onUpdateMetrics}
          >
            Update Metrics
          </Button>
        </Box>
      </CardContent>
    </Card>
  );
};

export default ScoreboardWidget; 
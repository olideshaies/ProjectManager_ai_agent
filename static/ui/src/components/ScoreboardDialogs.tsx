import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  FormControlLabel,
  Switch,
  Box,
  Typography,
} from '@mui/material';

interface MorningDialogProps {
  open: boolean;
  onClose: () => void;
  onSubmit: (milestone: string) => Promise<void>;
}

export const MorningDialog: React.FC<MorningDialogProps> = ({ open, onClose, onSubmit }) => {
  const [milestone, setMilestone] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async () => {
    if (!milestone.trim()) return;
    
    setLoading(true);
    try {
      await onSubmit(milestone);
      onClose();
    } catch (error) {
      console.error('Failed to set milestone:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>Set Daily Milestone</DialogTitle>
      <DialogContent>
        <Typography variant="body2" color="textSecondary" gutterBottom>
          What is today's ONE Daily Milestone?
        </Typography>
        <TextField
          autoFocus
          margin="dense"
          label="Daily Milestone"
          fullWidth
          multiline
          rows={2}
          value={milestone}
          onChange={(e) => setMilestone(e.target.value)}
          disabled={loading}
        />
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} disabled={loading}>Cancel</Button>
        <Button 
          onClick={handleSubmit} 
          variant="contained" 
          disabled={!milestone.trim() || loading}
        >
          Set Milestone
        </Button>
      </DialogActions>
    </Dialog>
  );
};

interface EveningDialogProps {
  open: boolean;
  onClose: () => void;
  onSubmit: (metrics: {
    netPnl: number;
    profitFactor: number;
    scheduleAdherence: number;
    milestoneHit: boolean;
  }) => Promise<void>;
}

export const EveningDialog: React.FC<EveningDialogProps> = ({ open, onClose, onSubmit }) => {
  const [metrics, setMetrics] = useState({
    netPnl: 0,
    profitFactor: 1,
    scheduleAdherence: 100,
    milestoneHit: false,
  });
  const [loading, setLoading] = useState(false);

  const handleSubmit = async () => {
    setLoading(true);
    try {
      await onSubmit(metrics);
      onClose();
    } catch (error) {
      console.error('Failed to update metrics:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>Update Daily Metrics</DialogTitle>
      <DialogContent>
        <Box display="flex" flexDirection="column" gap={2} mt={1}>
          <TextField
            label="Net P&L (CAD)"
            type="number"
            value={metrics.netPnl}
            onChange={(e) => setMetrics(prev => ({ ...prev, netPnl: parseFloat(e.target.value) }))}
            disabled={loading}
            fullWidth
          />
          
          <TextField
            label="Profit Factor"
            type="number"
            value={metrics.profitFactor}
            onChange={(e) => setMetrics(prev => ({ ...prev, profitFactor: parseFloat(e.target.value) }))}
            disabled={loading}
            fullWidth
          />
          
          <TextField
            label="Schedule Adherence (%)"
            type="number"
            value={metrics.scheduleAdherence}
            onChange={(e) => setMetrics(prev => ({ ...prev, scheduleAdherence: parseFloat(e.target.value) }))}
            disabled={loading}
            fullWidth
          />
          
          <FormControlLabel
            control={
              <Switch
                checked={metrics.milestoneHit}
                onChange={(e) => setMetrics(prev => ({ ...prev, milestoneHit: e.target.checked }))}
                disabled={loading}
              />
            }
            label="Daily Milestone Completed"
          />
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} disabled={loading}>Cancel</Button>
        <Button 
          onClick={handleSubmit} 
          variant="contained" 
          disabled={loading}
        >
          Update Metrics
        </Button>
      </DialogActions>
    </Dialog>
  );
}; 
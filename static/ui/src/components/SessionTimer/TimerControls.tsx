import React from 'react';

interface Props {
  isRunning: boolean;
  onStart: () => void;
  onStop: () => void;
  disabled: boolean;
}

export const TimerControls: React.FC<Props> = ({ 
  isRunning, 
  onStart, 
  onStop,
  disabled
}) => {
  return (
    <div className="timer-controls">
      {!isRunning ? (
        <button 
          onClick={onStart}
          disabled={disabled}
          className="start-button"
        >
          Start Session
        </button>
      ) : (
        <button 
          onClick={onStop}
          className="stop-button"
        >
          Stop Session
        </button>
      )}
    </div>
  );
};

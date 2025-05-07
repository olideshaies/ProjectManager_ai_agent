import React from 'react';

interface Props {
  seconds: number;
}

export const TimerDisplay: React.FC<Props> = ({ seconds }) => {
  // Format seconds into HH:MM:SS
  const formatTime = (totalSeconds: number) => {
    const hours = Math.floor(totalSeconds / 3600);
    const minutes = Math.floor((totalSeconds % 3600) / 60);
    const seconds = totalSeconds % 60;
    
    return [
      hours.toString().padStart(2, '0'),
      minutes.toString().padStart(2, '0'),
      seconds.toString().padStart(2, '0')
    ].join(':');
  };
  
  return (
    <div className="timer-display">
      <span>{formatTime(seconds)}</span>
    </div>
  );
};

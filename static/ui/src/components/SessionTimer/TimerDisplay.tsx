import React from 'react';
import styles from './styles.module.css'; // Import CSS Modules

interface Props {
  seconds: number;
  isRunning: boolean; // Add isRunning prop to show "IN FOCUS"
}

export const TimerDisplay: React.FC<Props> = ({ seconds, isRunning }) => {
  // Format seconds into HH:MM:SS
  const formatTime = (totalSeconds: number) => {
    const hours = Math.floor(totalSeconds / 3600);
    const minutes = Math.floor((totalSeconds % 3600) / 60);
    const secs = totalSeconds % 60; // Renamed to avoid conflict
    
    return [
      hours.toString().padStart(2, '0'),
      minutes.toString().padStart(2, '0'),
      secs.toString().padStart(2, '0')
    ].join(':');
  };
  
  return (
    // Use the CSS module class for the main container
    <div className={styles.timerDisplayContainer}>
      {isRunning && <div className={styles.inFocusLabel}>IN FOCUS</div>}
      <div className={styles.timerDigits}>
        {formatTime(seconds)}
      </div>
    </div>
  );
};

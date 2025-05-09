import React from 'react';
import styles from './styles.module.css'; // Assuming you have styles

interface Props {
  isSessionActive: boolean;
  isRunning: boolean;
  isPaused: boolean;
  onStart: () => void;
  onStop: () => void;
  onPause: () => void;
  onResume: () => void;
  disableStart: boolean;
  disableStop: boolean;
  disablePause: boolean;
  disableResume: boolean;
}

export const TimerControls: React.FC<Props> = ({
  isSessionActive,
  isRunning,
  isPaused,
  onStart,
  onStop,
  onPause,
  onResume,
  disableStart,
  disableStop,
  disablePause,
  disableResume,
}) => {
  return (
    <div className={styles.timerControls}>
      {!isSessionActive ? (
        // Show Start button only if no session is active
        <button
          onClick={onStart}
          disabled={disableStart}
          className={styles.startButton}
        >
          Start Session
        </button>
      ) : (
        // If a session is active, show Pause/Resume and Stop
        <>
          {isRunning && (
            <button
              onClick={onPause}
              disabled={disablePause}
              className={styles.pauseButton} // Add style for pause
            >
              Pause
            </button>
          )}
          {isPaused && (
            <button
              onClick={onResume}
              disabled={disableResume}
              className={styles.resumeButton} // Add style for resume
            >
              Resume
            </button>
          )}
          <button
            onClick={onStop}
            disabled={disableStop}
            className={styles.stopButton}
            style={{ marginLeft: '1rem' }} // Add some spacing
          >
            Stop Session
          </button>
        </>
      )}
    </div>
  );
};

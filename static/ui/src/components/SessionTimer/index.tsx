// components/SessionTimer/index.tsx
import React, { useState, useEffect, useRef } from 'react';
import { TaskSelector } from './TaskSelector';
import { TimerDisplay } from './TimerDisplay';
import { TimerControls } from './TimerControls';
import styles from './styles.module.css';

// Define TypeScript interfaces for our data
interface Task {
  id: string;
  title: string;
  description?: string;
}

// Update TimeSession interface to match backend response (TimeSessionOut)
interface TimeSession {
  id: string; // ID is non-optional once created
  task_id: string;
  goal?: string | null;
  outcome?: string | null;
  start_ts: string; // Use string for fetch response, convert later if needed
  end_ts?: string | null;
  duration?: string | null; // Represent interval as string from JSON
  accumulated_duration: string; // Represent interval as string from JSON
  last_event_ts?: string | null;
}

// Helper to convert ISO duration string (like "0:00:15") to seconds
const durationStringToSeconds = (durationStr: string | null | undefined): number => {
    console.log("[durationStringToSeconds] Input:", durationStr);
    if (!durationStr) {
        console.log("[durationStringToSeconds] durationStr is null/undefined, returning 0.");
        return 0;
    }

    // Check if it's an ISO 8601 duration string
    if (durationStr.startsWith('PT')) {
        let hours = 0;
        let minutes = 0;
        let seconds = 0;

        // Remove 'PT'
        let remaining = durationStr.substring(2);

        const hoursMatch = remaining.match(/(\d+)H/);
        if (hoursMatch) {
            hours = parseInt(hoursMatch[1], 10);
            remaining = remaining.replace(hoursMatch[0], '');
        }

        const minutesMatch = remaining.match(/(\d+)M/);
        if (minutesMatch) {
            minutes = parseInt(minutesMatch[1], 10);
            remaining = remaining.replace(minutesMatch[0], '');
        }

        const secondsMatch = remaining.match(/(\d+(\.\d+)?)S/);
        if (secondsMatch) {
            seconds = parseFloat(secondsMatch[1]);
            // remaining = remaining.replace(secondsMatch[0], ''); // Not needed if S is last
        }

        const totalSeconds = (hours * 3600) + (minutes * 60) + seconds;
        
        if (isNaN(totalSeconds)) {
            console.error("[durationStringToSeconds] ISO Parse: Resulting totalSeconds is NaN. Original:", durationStr, "H:", hours, "M:", minutes, "S:", seconds);
            return 0;
        }
        console.log("[durationStringToSeconds] ISO Parse: Successfully parsed. Returning seconds:", Math.round(totalSeconds));
        return Math.round(totalSeconds);

    } else {
        // Fallback for simple number string (your previous logic)
        // Or if you expect colon-separated, reinstate that logic here with a check
        const numSeconds = parseFloat(durationStr);
        if (isNaN(numSeconds)) {
            console.error("[durationStringToSeconds] Fallback Parse: Failed to parse as float, returning 0. Original:", durationStr);
            return 0;
        }
        console.log("[durationStringToSeconds] Fallback Parse: Parsed as float. Returning seconds:", Math.round(numSeconds));
        return Math.round(numSeconds);
    }
};

export const SessionTimer: React.FC = () => {
  // State hooks to manage component data
  const [tasks, setTasks] = useState<Task[]>([]);
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);
  const [currentSession, setCurrentSession] = useState<TimeSession | null>(null);
  const [displayTime, setDisplayTime] = useState(0); // Seconds to show on the clock
  const intervalRef = useRef<number | null>(null); // Ref to store interval ID
  
  // --- Determine current state (Move this declaration up) ---
  // Ensure these default to false if currentSession is null
  const isSessionActive = !!currentSession && !currentSession.end_ts;
  const isRunning = isSessionActive && !!currentSession.last_event_ts;
  const isPaused = isSessionActive && !currentSession.last_event_ts;
  
  // Load tasks on component mount
  useEffect(() => {
    const loadTasks = async () => {
      try {
        // Adding trailing slash based on previous redirect diagnosis
        const response = await fetch('/tasks/');
        if (!response.ok) throw new Error('Failed to load tasks');
        const data = await response.json();
        setTasks(data);
      } catch (error) {
        console.error('Error loading tasks:', error);
      }
    };
    
    loadTasks();
  }, []);
  
  // Timer logic - Original timer based on simple isRunning state
  // This useEffect seems redundant now that we have the more complex one below
  // Commenting it out to avoid conflict and rely on the state-driven timer logic
  /*
  useEffect(() => {
    let timerInterval: number | null = null;
    if (isRunning) { // isRunning is now defined before this hook
      timerInterval = window.setInterval(() => {
        // This logic is superseded by the next useEffect
        // setDisplayTime(prev => prev + 1);
      }, 1000);
    }
    return () => {
      if (timerInterval) window.clearInterval(timerInterval);
    };
  }, [isRunning]); // Dependency is now defined
  */
  
  // Timer Logic - Recalculate display time based on currentSession state
  useEffect(() => {
    // Log when the effect runs and the current state values
    console.log(
      "[Timer Effect] Running. isRunning:", isRunning,
      "isPaused:", isPaused,
      "isSessionActive:", isSessionActive,
      "Session:", currentSession
    );

    // Clear any existing interval at the beginning of the effect
    if (intervalRef.current) {
      console.log("[Timer Effect] Clearing previous interval ID:", intervalRef.current);
      window.clearInterval(intervalRef.current);
      intervalRef.current = null;
    }

    if (isRunning && currentSession?.last_event_ts) {
      console.log("[Timer Effect] State: RUNNING");
      const accumulatedSeconds = durationStringToSeconds(currentSession.accumulated_duration);
      const lastEventTsString = currentSession.last_event_ts;
      const lastEventTime = new Date(lastEventTsString).getTime(); // Milliseconds

      console.log(
        `[Timer Effect] Details for RUNNING: accumulatedSeconds: ${accumulatedSeconds}, ` +
        `last_event_ts string: "${lastEventTsString}", parsed lastEventTime (ms): ${lastEventTime}`
      );

      // Critical check for NaN after parsing lastEventTime
      if (isNaN(lastEventTime)) {
        console.error(
          "[Timer Effect] ERROR: lastEventTime is NaN. This will cause timer issues. " +
          `Problematic last_event_ts string was: "${lastEventTsString}". ` +
          `Falling back to displaying accumulatedSeconds: ${accumulatedSeconds}.`
        );
        setDisplayTime(accumulatedSeconds); // Set to a known good value
        return; // Exit effect to prevent setting an interval with bad data
      }

      const updateTimer = () => {
        const now = Date.now(); // Milliseconds
        const secondsSinceLastEvent = Math.floor((now - lastEventTime) / 1000);
        const newDisplayTime = accumulatedSeconds + secondsSinceLastEvent;
        
        // This log can be very noisy (every second), uncomment if needed for deep debugging
        // console.log(
        //   `[UpdateTimer] now (ms): ${now}, lastEventTime (ms): ${lastEventTime}, ` +
        //   `secondsSinceLastEvent: ${secondsSinceLastEvent}, newDisplayTime: ${newDisplayTime}`
        // );
        setDisplayTime(newDisplayTime);
      };

      updateTimer(); // Call immediately to set the initial time correctly
      intervalRef.current = window.setInterval(updateTimer, 1000);
      console.log("[Timer Effect] Set new interval ID:", intervalRef.current);

    } else if (isPaused && currentSession) {
      console.log("[Timer Effect] State: PAUSED");
      const accumulatedSeconds = durationStringToSeconds(currentSession.accumulated_duration);
      setDisplayTime(accumulatedSeconds);
      console.log(`[Timer Effect] DisplayTime set to accumulatedSeconds (paused): ${accumulatedSeconds}`);

    } else if (!isSessionActive) {
      console.log("[Timer Effect] State: INACTIVE (no session or session ended)");
      setDisplayTime(0);
      console.log("[Timer Effect] DisplayTime set to 0");
    }

    // Cleanup function for when the component unmounts or dependencies change
    return () => {
      if (intervalRef.current) {
        console.log("[Timer Effect Cleanup] Clearing interval ID:", intervalRef.current);
        window.clearInterval(intervalRef.current);
        intervalRef.current = null; // Important to reset ref
      }
    };
  }, [isRunning, isPaused, currentSession, isSessionActive]); // Added isSessionActive to deps
  // Note: isSessionActive was added as a dependency as it's used in the conditions.
  
  // Handler for starting a new session
  const handleStartSession = async () => {
    if (!selectedTask) return;
    // Reset display time visually immediately
    setDisplayTime(0);
    try {
      const response = await fetch('/time_sessions/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          task_id: selectedTask.id,
          goal: 'Focus session', // You could make this editable
        }),
      });
      
      if (!response.ok) {
          const errorData = await response.text(); // Get more error detail
          throw new Error(`Failed to start session: ${response.status} ${errorData}`);
      }
      
      const newSession: TimeSession = await response.json();
      setCurrentSession(newSession);
    } catch (error) {
      console.error('Error starting session:', error);
      setCurrentSession(null); // Reset on error
    }
  };
  
  // --- New Handlers ---
  const handlePauseSession = async () => {
    if (!currentSession || !isRunning) return;
    try {
      const response = await fetch(`/time_sessions/${currentSession.id}/pause`, { method: 'PATCH' });
      if (!response.ok) {
          const errorData = await response.text();
          throw new Error(`Failed to pause: ${response.status} ${errorData}`);
      }
      const updatedSession: TimeSession = await response.json();
      setCurrentSession(updatedSession); // Update state, timer useEffect will handle display
    } catch (error) {
      console.error('Error pausing:', error);
    }
  };

  const handleResumeSession = async () => {
    if (!currentSession || !isPaused) return;
    try {
      const response = await fetch(`/time_sessions/${currentSession.id}/resume`, { method: 'PATCH' });
      if (!response.ok) {
           const errorData = await response.text();
           throw new Error(`Failed to resume: ${response.status} ${errorData}`);
      }
      const updatedSession: TimeSession = await response.json();
      setCurrentSession(updatedSession); // Update state, timer useEffect will handle display
    } catch (error) {
      console.error('Error resuming:', error);
    }
  };
  // --- End New Handlers ---

  // Handler for stopping the current session
  const handleStopSession = async () => {
    if (!currentSession) return;
    try {
      const response = await fetch(`/time_sessions/${currentSession.id}/stop`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          outcome: 'Completed', // You could make this editable
        }),
      });
      
      if (!response.ok) {
            const errorData = await response.text();
            throw new Error(`Failed to stop session: ${response.status} ${errorData}`);
      }
      
      setCurrentSession(null); // Reset session state, timer useEffect will handle display
    } catch (error) {
      console.error('Error stopping session:', error);
      // Maybe show error, but don't reset session? Depends on desired UX
    }
  };
  
  return (
    <div className={styles.sessionTimer}>
      <h2>Task Timer</h2>
      
      <TaskSelector 
        tasks={tasks}
        selectedTask={selectedTask}
        onSelectTask={setSelectedTask}
        disabled={isSessionActive} // Disable task selection if a session is active (running or paused)
      />
      
      <TimerDisplay 
        seconds={displayTime} 
        isRunning={isRunning} // Pass the isRunning state
      />
      
      <TimerControls
        isSessionActive={isSessionActive} // Pass down overall active state
        isRunning={isRunning}       // Pass down running state
        isPaused={isPaused}         // Pass down paused state
        onStart={handleStartSession}
        onStop={handleStopSession}
        onPause={handlePauseSession}   // Pass down pause handler
        onResume={handleResumeSession} // Pass down resume handler
        // Disable start if no task selected or session already active
        disableStart={!selectedTask || isSessionActive}
        // Disable stop if no session is active
        disableStop={!isSessionActive}
        // Disable pause if session not running
        disablePause={!isRunning}
        // Disable resume if session not paused
        disableResume={!isPaused}
      />
    </div>
  );
};
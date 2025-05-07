// components/SessionTimer/index.tsx
import React, { useState, useEffect } from 'react';
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

interface TimeSession {
  id?: string;
  task_id: string;
  goal?: string;
  start_ts?: Date;
  end_ts?: Date;
  duration?: number;
}

export const SessionTimer: React.FC = () => {
  // State hooks to manage component data
  const [tasks, setTasks] = useState<Task[]>([]);
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  const [sessionTime, setSessionTime] = useState(0);
  const [currentSession, setCurrentSession] = useState<TimeSession | null>(null);
  
  // Load tasks on component mount
  useEffect(() => {
    const loadTasks = async () => {
      try {
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
  
  // Timer logic
  useEffect(() => {
    let timerInterval: number | null = null;
    
    if (isRunning) {
      timerInterval = window.setInterval(() => {
        setSessionTime(prev => prev + 1);
      }, 1000);
    }
    
    // Cleanup function
    return () => {
      if (timerInterval) window.clearInterval(timerInterval);
    };
  }, [isRunning]);
  
  // Handler for starting a new session
  const handleStartSession = async () => {
    if (!selectedTask) return;
    
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
      
      if (!response.ok) throw new Error('Failed to start session');
      
      const newSession = await response.json();
      setCurrentSession(newSession);
      setIsRunning(true);
      setSessionTime(0);
    } catch (error) {
      console.error('Error starting session:', error);
    }
  };
  
  // Handler for stopping the current session
  const handleStopSession = async () => {
    if (!currentSession?.id) return;
    
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
      
      if (!response.ok) throw new Error('Failed to stop session');
      
      setCurrentSession(null);
      setIsRunning(false);
      // You could show a summary or success message here
    } catch (error) {
      console.error('Error stopping session:', error);
    }
  };
  
  return (
    <div className={styles.sessionTimer}>
      <h2>Task Timer</h2>
      
      <TaskSelector 
        tasks={tasks}
        selectedTask={selectedTask}
        onSelectTask={setSelectedTask}
        disabled={isRunning}
      />
      
      <TimerDisplay seconds={sessionTime} />
      
      <TimerControls
        isRunning={isRunning}
        onStart={handleStartSession}
        onStop={handleStopSession}
        disabled={!selectedTask || (isRunning && !currentSession)}
      />
    </div>
  );
};
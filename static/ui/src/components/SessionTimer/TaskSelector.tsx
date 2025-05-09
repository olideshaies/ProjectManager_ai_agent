import React from 'react';

interface Task {
  id: string;
  title: string;
  description?: string;
}

interface Props {
  tasks: Task[];
  selectedTask: Task | null;
  onSelectTask: (task: Task) => void;
  disabled: boolean;
}

export const TaskSelector: React.FC<Props> = ({ 
  tasks, 
  selectedTask, 
  onSelectTask,
  disabled 
}) => {
  return (
    <div className="task-selector">
      <label htmlFor="task-select">Select a Task:</label>
      <select 
        id="task-select"
        value={selectedTask?.id || ''}
        onChange={(e) => {
          const task = tasks.find(t => t.id === e.target.value);
          if (task) onSelectTask(task);
        }}
        disabled={disabled}
      >
        <option value="">-- Select a task --</option>
        {tasks.map(task => (
          <option key={task.id} value={task.id}>
            {task.title}
          </option>
        ))}
      </select>
    </div>
  );
};

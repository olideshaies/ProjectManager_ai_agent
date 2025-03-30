# instructions/roadmap.md

# MVP
- Have a AI Agent acting as a Project manager which I can communicate with by voice and will return me the information by voice.
- Initial tools : create task and store it in db, update or delete task, search for task and list them.

# Current State
- Voice to speech input working
- FastAPI setup with task creation, task search --> using pgscale to store working
- TTS output working
- Debuging the task deletion right now (2025-03-25)

# Next Steps
1. Implement google calendar event based on the task to plan work & be able to reschedule it based on feedback and progress
2. Add short term memory and long term memory to help with context
3. Give agent the ability to suggest and help with reflexion like it was a mentor using current project state and all the other tasks


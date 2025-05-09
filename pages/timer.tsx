import React from 'react';
import { SessionTimer } from '../components/SessionTimer';
import Layout from '../components/Layout'; // Your site layout

export default function TimerPage() {
  return (
    <Layout>
      <h1>Task Timer</h1>
      <p>Select a task and track your time</p>
      
      <SessionTimer />
    </Layout>
  );
}

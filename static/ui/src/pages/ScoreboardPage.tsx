import React, { useState, useEffect, useRef, useCallback } from 'react';
import Chart, { type TooltipItem } from 'chart.js/auto';
import dayjs from 'dayjs';
import customParseFormat from 'dayjs/plugin/customParseFormat';
import utc from 'dayjs/plugin/utc';
import timezone from 'dayjs/plugin/timezone';
import styles from './ScoreboardPage.module.css';

dayjs.extend(customParseFormat);
dayjs.extend(utc);
dayjs.extend(timezone);

// Define types for the data we expect from the API
interface DeepWorkSessionData {
    start_time: string; // ISO string
    duration_minutes: number;
}

// --- START: Interfaces for Aggregated Period Data ---
interface DailyFocusSummary {
    date: string; // YYYY-MM-DD
    totalDeepWorkMinutes: number;
}

interface AggregatedScoreboardMetrics {
    avgNetPnL: number | null;
    avgProfitFactor: number | null;
    avgFocusRatio: number | null;
    avgScheduleAdherence: number | null;
    milestoneCompletionRate: number | null;
    periodDailyMilestoneDescription: string | null;
}

interface ScoreboardAggregatedUIPageData {
    period_description: string;
    metrics: AggregatedScoreboardMetrics;
    deep_work_chart_data: DailyFocusSummary[];
}
// --- END: Interfaces for Aggregated Period Data ---

interface ScoreboardMetrics { // For single day, or AVG values for a period
    netPnL: number | null;
    profitFactor: number | null;
    focusRatio: number | null;
    dailyMilestone: string | null;
    milestoneHit: boolean | null;
    scheduleAdherence: number | null;
}

interface ScoreboardUIPageData {
    entry_date: string; // YYYY-MM-DD
    metrics: ScoreboardMetrics;
    deep_work_chart_data: DeepWorkSessionData[];
}

// Interface for the expected response from the save endpoint (matching Pydantic's ScoreboardTableRow)
interface ScoreboardTableRow {
    date: string; // Or Date, depending on what backend sends and how you want to use it.
                  // Assuming string YYYY-MM-DD for consistency with entry_date.
    netPnL: number | null;
    profitFactor: number | null;
    focusRatio: number | null;
    dailyMilestone: string | null;
    milestoneHit: boolean | null;
    scheduleAdherence: number | null;
}

// Default empty state for input metrics
const defaultInputMetrics: ScoreboardMetrics = {
    netPnL: null,
    profitFactor: null,
    focusRatio: null,
    dailyMilestone: '', // Use empty string for text
    milestoneHit: null,
    scheduleAdherence: null,
};

const ScoreboardPage: React.FC = () => {
    const API_BASE_URL = '/scoreboard';
    const chartRef = useRef<HTMLCanvasElement>(null);
    const chartInstanceRef = useRef<Chart | null>(null);
    const [selectedDate, setSelectedDate] = useState<string>(dayjs().format('YYYY-MM-DD'));
    const [scoreboardData, setScoreboardData] = useState<ScoreboardUIPageData | null>(null);
    const [inputMetrics, setInputMetrics] = useState<ScoreboardMetrics>(defaultInputMetrics);
    const [isLoading, setIsLoading] = useState<boolean>(true);
    const [error, setError] = useState<string | null>(null);
    const [activePeriod, setActivePeriod] = useState<'selectedDate' | 'today' | 'week' | 'month'>('selectedDate');
    const [effectiveDate, setEffectiveDate] = useState<string>(dayjs().format('YYYY-MM-DD'));
    // New state for aggregated data to keep things cleaner for now
    const [aggregatedData, setAggregatedData] = useState<ScoreboardAggregatedUIPageData | null>(null);

    // Placeholder for fetching and setting period-based data
    const loadPeriodData = useCallback(async (startDate: string, endDate: string, periodType: 'week' | 'month') => {
        console.log(`[loadPeriodData] Request for ${periodType}: ${startDate} to ${endDate}`);
        setIsLoading(true);
        setError(null);
        setScoreboardData(null);      // Clear single-day data
        setAggregatedData(null);    // Clear previous aggregated data
        setInputMetrics(defaultInputMetrics); 

        try {
            // NOTE: API_BASE_URL is currently '/scoreboard' due to user preference.
            // Backend endpoint is /ui_data_period (without /api/scoreboard prefix if router is directly under /scoreboard)
            // Or /scoreboard/ui_data_period if router is scoreboard.router and main app prefix is also /scoreboard
            // Assuming router is directly mounted at /scoreboard, so path is /ui_data_period
            const response = await fetch(`${API_BASE_URL}/ui_data_period?start_date_str=${startDate}&end_date_str=${endDate}`);
            
            if (!response.ok) {
                let errorData = { detail: `Failed to fetch ${periodType} data: ${response.status}` };
                try { errorData = await response.json(); } catch (e) { /* ignore */ }
                throw new Error(errorData.detail || `Failed to fetch ${periodType} data`);
            }
            const data: ScoreboardAggregatedUIPageData = await response.json();
            console.log(`[loadPeriodData] ${periodType} data fetched successfully:`, data);
            setAggregatedData(data);

        } catch (err) {
            const errorMessage = err instanceof Error ? err.message : `An unknown error occurred while fetching ${periodType} data.`;
            console.error(`[loadPeriodData] Error:`, errorMessage);
            setError(errorMessage);
            setAggregatedData(null);
        } finally {
            setIsLoading(false);
        }
    }, [API_BASE_URL]);

    // Define loadData with useCallback
    const loadData = useCallback(async (dateToLoad: string) => {
        console.log(`[loadData] Called for date: ${dateToLoad}`);
        if (!dateToLoad) {
            // Potentially clear data or set a specific state if date is invalid/cleared
            setScoreboardData(null);
            setInputMetrics(defaultInputMetrics);
            setIsLoading(false);
            return;
        }
        setIsLoading(true);
        setError(null);
        // console.log(`Loading data for: ${dateToLoad} via ${API_BASE_URL}/ui_data/${dateToLoad}`);
        try {
            const response = await fetch(`${API_BASE_URL}/ui_data/${dateToLoad}`);
            if (!response.ok) {
                if (response.status === 404) {
                    setScoreboardData(null); 
                    setInputMetrics(defaultInputMetrics); 
                    // console.warn(`No scoreboard data found for ${dateToLoad}.`);
                    // setError(`No data found for ${dayjs(dateToLoad).format('MMM DD, YYYY')}. You can input new data.`);
                } else {
                    let errorData = { detail: `Failed to fetch data: ${response.status}` };
                    try {
                        errorData = await response.json();
                    } catch (e) { /* Backend didn't send JSON error, use default */ }
                    throw new Error(errorData.detail || `Failed to fetch data: ${response.status} ${response.statusText}`);
                }
            } else {
                const data: ScoreboardUIPageData = await response.json();
                console.log('[loadData] Data fetched successfully:', data);
                setScoreboardData(data);
                if (data.metrics) {
                    setInputMetrics(data.metrics); 
                } else {
                    setInputMetrics(defaultInputMetrics); 
                }
            }
        } catch (err) {
            const errorMessage = err instanceof Error ? err.message : 'An unknown error occurred while fetching data.';
            // console.error("Error in loadData:", errorMessage);
            setError(errorMessage);
            setScoreboardData(null);
            setInputMetrics(defaultInputMetrics); 
        } finally {
            setIsLoading(false);
        }
    }, [API_BASE_URL]); // Dependencies: things from outside that loadData uses and that might change
                        // setIsLoading, setError, setScoreboardData, setInputMetrics are stable from useState
                        // API_BASE_URL is a constant defined in the component scope

    // Re-enable getTileColor 
    const getTileColor = (metricName: keyof ScoreboardMetrics, value: number | boolean | string | null): string => {
        const targets = {
            netPnL: 100,
            profitFactor: 1.5,
            focusRatio: 0.6, // Raw value 0-1
            milestoneHit: true,
            scheduleAdherence: 80, // Percentage
        };

        const amberThresholds = {
            netPnL: targets.netPnL * 0.6,
            profitFactor: targets.profitFactor * 0.6,
            focusRatio: targets.focusRatio * 0.6,
            scheduleAdherence: targets.scheduleAdherence * 0.6,
        };

        if (value === null || value === undefined) return '';

        switch (metricName) {
            case 'netPnL':
                if (typeof value === 'number') {
                    if (value >= targets.netPnL) return styles.green;
                    if (value >= amberThresholds.netPnL) return styles.amber;
                    return styles.red;
                }
                break;
            case 'profitFactor':
                if (typeof value === 'number') {
                    if (value >= targets.profitFactor) return styles.green;
                    if (value >= amberThresholds.profitFactor) return styles.amber;
                    return styles.red;
                }
                break;
            case 'focusRatio': // Expects value between 0 and 1
                if (typeof value === 'number') {
                    if (value >= targets.focusRatio) return styles.green;
                    if (value >= amberThresholds.focusRatio) return styles.amber;
                    return styles.red;
                }
                break;
            case 'milestoneHit':
                return value ? styles.green : styles.red;
            case 'scheduleAdherence': // Expects value 0-100
                 if (typeof value === 'number') {
                    if (value >= targets.scheduleAdherence) return styles.green;
                    if (value >= amberThresholds.scheduleAdherence) return styles.amber;
                    return styles.red;
                }
                break;
        }
        return '';
    };

    // useEffect to update effectiveDate based on activePeriod or selectedDate (for manual selection)
    useEffect(() => {
        console.log(`[useEffect for period change] activePeriod: ${activePeriod}, selectedDate (manual): ${selectedDate}`);
        if (activePeriod === 'today') {
            const todayStr = dayjs().format('YYYY-MM-DD');
            console.log(`[useEffect for period change] Setting effectiveDate to TODAY: ${todayStr}`);
            setEffectiveDate(todayStr);
            setAggregatedData(null); // Clear aggregated data when switching to single day view
        } else if (activePeriod === 'selectedDate') {
            console.log(`[useEffect for period change] Setting effectiveDate to SELECTED_DATE: ${selectedDate}`);
            setEffectiveDate(selectedDate); 
            setAggregatedData(null); // Clear aggregated data
        } else if (activePeriod === 'week') {
            const startOfWeek = dayjs().startOf('week').format('YYYY-MM-DD');
            const endOfWeekQuery = dayjs().format('YYYY-MM-DD'); // Data up to today for the current week
            console.log(`[useEffect for period change] Week view active: ${startOfWeek} to ${endOfWeekQuery}`);
            setEffectiveDate(''); // Clear effectiveDate to prevent single-day loadData from firing
            loadPeriodData(startOfWeek, endOfWeekQuery, 'week');
        } else if (activePeriod === 'month') {
            const startOfMonth = dayjs().startOf('month').format('YYYY-MM-DD');
            const endOfMonthQuery = dayjs().format('YYYY-MM-DD'); // Data up to today for the current month
            console.log(`[useEffect for period change] Month view active: ${startOfMonth} to ${endOfMonthQuery}`);
            setEffectiveDate(''); // Clear effectiveDate
            loadPeriodData(startOfMonth, endOfMonthQuery, 'month');
        }
    }, [activePeriod, selectedDate, loadPeriodData]); // Added loadPeriodData

    // useEffect for loading data whenever the effectiveDate changes
    useEffect(() => {
        console.log(`[useEffect for loadData] effectiveDate changed to: ${effectiveDate}. Calling loadData.`);
        // Only call loadData if effectiveDate is set AND we are in a single-day view mode.
        // loadPeriodData is called directly from the other useEffect for period changes.
        if (effectiveDate && (activePeriod === 'selectedDate' || activePeriod === 'today')) { 
            loadData(effectiveDate);
        } else if (!effectiveDate && (activePeriod === 'week' || activePeriod === 'month')) {
            // This case means a period was selected, effectiveDate was cleared, and loadPeriodData was called.
            // We might want to ensure isLoading is false if loadPeriodData already handled it.
            // Or, if loadPeriodData sets scoreboardData to null, that might be enough.
            // For now, this branch ensures loadData isn't called with an empty effectiveDate for period views.
            console.log('[useEffect for loadData] In period view, effectiveDate is cleared, loadData skipped.');
        }
    }, [effectiveDate, loadData, activePeriod]); // loadData is stable, added activePeriod

    const metrics = scoreboardData?.metrics; // Re-enable metrics constant

    // Handler for input changes
    const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
        const { name, value, type } = e.target;
        let processedValue: string | number | boolean | null = value;

        if (type === 'checkbox') {
            // Assuming your <select> for milestoneHit returns string "true" or "false"
            if (name === 'milestoneHit') {
                processedValue = value === 'true' ? true : (value === 'false' ? false : null);
            } else {
                processedValue = (e.target as HTMLInputElement).checked; 
            }
        } else if (type === 'number') {
            processedValue = value === '' ? null : parseFloat(value);
        } else if (name === 'dailyMilestone') {
            processedValue = value; // Keep as string
        }

        setInputMetrics(prevMetrics => ({
            ...prevMetrics,
            [name]: processedValue,
        }));
    };

    // Handler for saving metrics
    const handleSaveMetrics = async () => {
        console.log('Attempting to save metrics for date:', selectedDate, 'with data:', inputMetrics);
        // setIsLoading(true); // Let loadData handle master isLoading state
        // setError(null); // Let loadData handle master error state

        try {
            const response = await fetch(`${API_BASE_URL}/metrics/${selectedDate}`, { 
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(inputMetrics),
            });

            if (!response.ok) {
                let errorData = { detail: 'Failed to save metrics. Server responded with an error.' };
                try {
                    errorData = await response.json();
                } catch (e) { /* Backend didn't send JSON error, use default */ }
                throw new Error(errorData.detail || `Failed to save metrics: ${response.status} ${response.statusText}`);
            }

            const savedData: ScoreboardTableRow = await response.json(); 
            console.log('Metrics saved successfully:', savedData);
            alert('Metrics saved successfully!');
            
            // Update input fields directly with the exact saved data for immediate feedback
            setInputMetrics({
                netPnL: savedData.netPnL,
                profitFactor: savedData.profitFactor,
                focusRatio: savedData.focusRatio,
                dailyMilestone: savedData.dailyMilestone,
                milestoneHit: savedData.milestoneHit,
                scheduleAdherence: savedData.scheduleAdherence
            });

            // Trigger a full re-fetch and UI update using the main loadData function
            await loadData(selectedDate);

        } catch (saveError) {
            const errorMessage = saveError instanceof Error ? saveError.message : 'An unknown error occurred while saving.';
            console.error('Error saving metrics:', errorMessage);
            setError(errorMessage); 
            alert(`Error saving metrics: ${errorMessage}`);
        } finally {
            // setIsLoading(false); // isLoading is handled by refreshData or main loadData
        }
    };

    const pageTitleDate = () => {
        if (activePeriod === 'selectedDate' || activePeriod === 'today') {
            return dayjs(effectiveDate).isValid() ? dayjs(effectiveDate).format('MMM DD, YYYY') : "Invalid Date";
        } else if (activePeriod === 'week') {
            // For week, we might need to calculate display range based on what loadPeriodData will eventually fetch
            const startDisplay = dayjs().startOf('week').format('MMM DD'); // Changed from isoWeek to week
            const endDisplay = dayjs().format('MMM DD, YYYY');
            return `Week of ${startDisplay} - ${endDisplay}`;
        } else if (activePeriod === 'month') {
            // For month, display the current month and year
            return dayjs().format('MMMM YYYY'); 
        }
        return "Scoreboard";
    };

    // ---- DEBUG LOG ----
    console.log("[Render] activePeriod:", activePeriod);
    console.log("[Render] isLoading:", isLoading);
    console.log("[Render] error:", error);
    console.log("[Render] scoreboardData:", scoreboardData); // For single day
    console.log("[Render] aggregatedData:", aggregatedData); // For period
    // ---- END DEBUG LOG ----

    const shouldShowSingleDayData = (activePeriod === 'selectedDate' || activePeriod === 'today') && scoreboardData;
    const shouldShowAggregatedData = (activePeriod === 'week' || activePeriod === 'month') && aggregatedData;
    const showDataDisplayArea = !isLoading && !error && (shouldShowSingleDayData || shouldShowAggregatedData);

    // useEffect for Chart.js instance creation and updates
    useEffect(() => {
        if (!chartRef.current) return;
        const canvas = chartRef.current;
        const ctx = canvas.getContext('2d');
        if (!ctx) return;

        // Destroy previous chart instance if it exists
        if (chartInstanceRef.current) {
            chartInstanceRef.current.destroy();
        }

        let chartDataConfig;
        let chartOptionsConfig: any = {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    title: { display: true, text: 'Duration (minutes)' }
                },
                x: {
                    title: { display: true }
                }
            },
            plugins: {
                tooltip: {
                    callbacks: {
                        // Can customize tooltips if needed
                    }
                }
            }
        };

        if (shouldShowAggregatedData && aggregatedData?.deep_work_chart_data) {
            // Configure for aggregated period view (e.g., "This Week")
            chartOptionsConfig.scales.x.title.text = 'Date';
            chartDataConfig = {
                labels: aggregatedData.deep_work_chart_data.map(d => dayjs(d.date).format('MMM DD')), // Format date for label
                datasets: [{
                    label: 'Total Deep Work Minutes',
                    data: aggregatedData.deep_work_chart_data.map(d => d.totalDeepWorkMinutes),
                    borderColor: 'rgb(54, 162, 235)',
                    backgroundColor: 'rgba(54, 162, 235, 0.5)',
                    fill: true,
                    tension: 0.1
                }]
            };
        } else if (shouldShowSingleDayData && scoreboardData?.deep_work_chart_data) {
            // Configure for single day view
            chartOptionsConfig.scales.x.title.text = 'Time of Day';
            chartDataConfig = {
                labels: scoreboardData.deep_work_chart_data.map(s => dayjs(s.start_time).format('HH:mm')), // Format time for label
                datasets: [{
                    label: 'Deep Work Session Duration',
                    data: scoreboardData.deep_work_chart_data.map(s => s.duration_minutes),
                    borderColor: 'rgb(75, 192, 192)',
                    backgroundColor: 'rgba(75, 192, 192, 0.5)',
                    fill: false, // Or true for area chart
                    tension: 0.1
                }]
            };
        } else {
            // No data to display or invalid state, clear the chart or show a message
            // console.log("Chart: No data available for display.");
            // Optionally, display a message on the canvas or clear it.
            // For now, just don't create a chart if there's no data.
            return;
        }

        chartInstanceRef.current = new Chart(ctx, {
            type: 'line', // Or 'bar' based on preference
            data: chartDataConfig,
            options: chartOptionsConfig
        });

        // Cleanup function to destroy chart on component unmount or before re-render
        return () => {
            if (chartInstanceRef.current) {
                chartInstanceRef.current.destroy();
                chartInstanceRef.current = null;
            }
        };
    }, [scoreboardData, aggregatedData, activePeriod, isLoading, shouldShowSingleDayData, shouldShowAggregatedData]); // Dependencies for chart updates

    return (
        <div className={styles.container}>
            <header className={styles.scoreboardHeader}>
            </header>

            <div className={styles.periodSelector}>
                <button
                    className={activePeriod === 'selectedDate' ? styles.activePeriodButton : styles.periodButton}
                    onClick={() => setActivePeriod('selectedDate')}
                >
                    Select Date
                </button>
                <button
                    className={activePeriod === 'today' ? styles.activePeriodButton : styles.periodButton}
                    onClick={() => {
                        console.log("[Today Button Clicked]");
                        setActivePeriod('today');
                    }}
                >
                    Today
                </button>
                <button
                    className={activePeriod === 'week' ? styles.activePeriodButton : styles.periodButton}
                    onClick={() => {
                        setActivePeriod('week');
                        console.log("Week view selected - placeholder for fetching/calculating week data");
                    }}
                >
                    This Week
                </button>
                <button
                    className={activePeriod === 'month' ? styles.activePeriodButton : styles.periodButton}
                    onClick={() => {
                        setActivePeriod('month');
                        console.log("Month view selected - placeholder for fetching/calculating month data");
                    }}
                >
                    This Month
                </button>
            </div>

            {/* Conditionally show the date picker, or adjust its role based on activePeriod */}
            {/* For now, it remains, but its value is primarily for 'selectedDate' mode */}
            <div className={styles.dateSelector}>
                <label htmlFor='scoreboard-date'>Select Date: </label>
                <input 
                    type='date' 
                    id='scoreboard-date' 
                    value={selectedDate}
                    onChange={(e) => {
                        console.log(`[Manual Date Picker Change] New value: ${e.target.value}`);
                        setSelectedDate(e.target.value);
                        setActivePeriod('selectedDate'); // Switch back to 'selectedDate' mode on manual change
                    }}
                    disabled={activePeriod !== 'selectedDate'}
                />
            </div>

            {isLoading && <p>Loading scoreboard...</p>}
            {/* Display error IF there is an error AND we are not loading (to avoid showing old error during new load) */}
            {!isLoading && error && <p className={styles.errorText}>{error}</p>}
            
            {/* Wrap input and display sections in a two-column layout */}
            <div className={styles.mainContentColumns}>
                {/* Left Column for Inputs */}
                <div className={styles.leftColumn}>
                    <section className={styles.inputSection}>
                        <h2>{activePeriod === 'week' || activePeriod === 'month' ? `Summary for ${pageTitleDate()}` : `Input/Edit Metrics for ${pageTitleDate()}`}</h2>
                        {(activePeriod === 'selectedDate' || activePeriod === 'today') && (
                            <>
                                <div className={styles.inputGrid}>
                                    <div className={styles.inputField}>
                                        <label htmlFor="netPnL">Net P&L (CAD):</label>
                                        <input
                                            type="number"
                                            id="netPnL"
                                            name="netPnL"
                                            value={inputMetrics.netPnL === null ? '' : inputMetrics.netPnL}
                                            onChange={handleInputChange}
                                            placeholder="e.g., 150.75"
                                        />
                                    </div>
                                    <div className={styles.inputField}>
                                        <label htmlFor="profitFactor">Profit Factor:</label>
                                        <input
                                            type="number"
                                            id="profitFactor"
                                            name="profitFactor"
                                            step="0.01"
                                            value={inputMetrics.profitFactor === null ? '' : inputMetrics.profitFactor}
                                            onChange={handleInputChange}
                                            placeholder="e.g., 1.75"
                                        />
                                    </div>
                                    <div className={styles.inputField}>
                                        <label htmlFor="focusRatio">Focus Ratio (0-1):</label>
                                        <input
                                            type="number"
                                            id="focusRatio"
                                            name="focusRatio"
                                            step="0.01"
                                            min="0"
                                            max="1"
                                            value={inputMetrics.focusRatio === null ? '' : inputMetrics.focusRatio}
                                            onChange={handleInputChange}
                                            placeholder="e.g., 0.75"
                                        />
                                    </div>
                                    <div className={styles.inputField}>
                                        <label htmlFor="dailyMilestone">Daily Milestone:</label>
                                        <input
                                            type="text"
                                            id="dailyMilestone"
                                            name="dailyMilestone"
                                            value={inputMetrics.dailyMilestone || ''}
                                            onChange={handleInputChange}
                                            placeholder="e.g., Finish report"
                                        />
                                    </div>
                                    <div className={styles.inputField}>
                                        <label htmlFor="milestoneHit">Milestone Hit?</label>
                                        <select
                                            id="milestoneHit"
                                            name="milestoneHit"
                                            value={inputMetrics.milestoneHit === null ? '' : String(inputMetrics.milestoneHit)}
                                            onChange={handleInputChange}
                                        >
                                            <option value="">Select...</option>
                                            <option value="true">Yes</option>
                                            <option value="false">No</option>
                                        </select>
                                    </div>
                                    <div className={styles.inputField}>
                                        <label htmlFor="scheduleAdherence">Schedule Adherence (%):</label>
                                        <input
                                            type="number"
                                            id="scheduleAdherence"
                                            name="scheduleAdherence"
                                            step="1"
                                            min="0"
                                            max="100"
                                            value={inputMetrics.scheduleAdherence === null ? '' : inputMetrics.scheduleAdherence}
                                            onChange={handleInputChange}
                                            placeholder="e.g., 85"
                                        />
                                    </div>
                                </div>
                                <button onClick={handleSaveMetrics} className={styles.saveButton}>
                                    Save Metrics for {dayjs(effectiveDate).isValid() ? dayjs(effectiveDate).format('MMM DD') : "Selected Date"}
                                </button>
                            </>
                        )}
                        {(activePeriod === 'week' || activePeriod === 'month') && (
                            <p>Aggregated data view. Inputs are disabled for period summaries.</p>
                        )}
                    </section>
                </div>

                {/* Right Column for Displaying Metrics and Chart */}
                <div className={styles.rightColumn}>
                    {/* Display sections: only show if not loading, no error, AND scoreboardData is present */} 
                    {showDataDisplayArea && (
                        <>
                            {/* Display-Only Metrics Grid */}
                            <section className={styles.metricsGrid}>
                                <div className={`${styles.metricTile} ${
                                    activePeriod === 'week' && aggregatedData ? getTileColor('netPnL', aggregatedData.metrics.avgNetPnL) :
                                    (activePeriod === 'month' && aggregatedData) ? getTileColor('netPnL', aggregatedData.metrics.avgNetPnL) :
                                    (activePeriod === 'selectedDate' || activePeriod === 'today') && scoreboardData ? getTileColor('netPnL', scoreboardData.metrics.netPnL) : ''
                                }`}>
                                    <h2>{(activePeriod === 'week' || activePeriod === 'month') && aggregatedData ? 'Avg. Net P&L' : 'Net P&L'} (CAD)</h2>
                                    <p className={styles.value}>{
                                        (activePeriod === 'week' || activePeriod === 'month') && aggregatedData ? (aggregatedData.metrics.avgNetPnL?.toFixed(2) ?? '-') :
                                        (activePeriod === 'selectedDate' || activePeriod === 'today') && scoreboardData ? (scoreboardData.metrics.netPnL?.toFixed(2) ?? '-') : '-'
                                    } CAD</p>
                                </div>
                                <div className={`${styles.metricTile} ${
                                    activePeriod === 'week' && aggregatedData ? getTileColor('profitFactor', aggregatedData.metrics.avgProfitFactor) :
                                    (activePeriod === 'month' && aggregatedData) ? getTileColor('profitFactor', aggregatedData.metrics.avgProfitFactor) :
                                    (activePeriod === 'selectedDate' || activePeriod === 'today') && metrics ? getTileColor('profitFactor', metrics.profitFactor) : ''
                                }`}>
                                    <h2>{(activePeriod === 'week' || activePeriod === 'month') && aggregatedData ? 'Avg. Profit Factor' : 'Profit Factor'}</h2>
                                    <p className={styles.value}>{
                                        (activePeriod === 'week' || activePeriod === 'month') && aggregatedData ? (aggregatedData.metrics.avgProfitFactor?.toFixed(2) ?? '-') :
                                        (activePeriod === 'selectedDate' || activePeriod === 'today') && metrics ? (metrics.profitFactor?.toFixed(2) ?? '-') : '-'
                                    }</p>
                                </div>
                                <div className={`${styles.metricTile} ${
                                    activePeriod === 'week' && aggregatedData ? getTileColor('focusRatio', aggregatedData.metrics.avgFocusRatio) :
                                    (activePeriod === 'month' && aggregatedData) ? getTileColor('focusRatio', aggregatedData.metrics.avgFocusRatio) :
                                    (activePeriod === 'selectedDate' || activePeriod === 'today') && metrics ? getTileColor('focusRatio', metrics.focusRatio) : ''
                                }`}>
                                    <h2>{(activePeriod === 'week' || activePeriod === 'month') && aggregatedData ? 'Avg. Focus Ratio' : 'Focus Ratio'}</h2>
                                    <p className={styles.value}>{
                                        (activePeriod === 'week' || activePeriod === 'month') && aggregatedData ?
                                            (aggregatedData.metrics.avgFocusRatio !== null && aggregatedData.metrics.avgFocusRatio !== undefined ? `${(aggregatedData.metrics.avgFocusRatio * 100).toFixed(1)}%` : '-') :
                                        (activePeriod === 'selectedDate' || activePeriod === 'today') && metrics ?
                                            (metrics.focusRatio !== null && metrics.focusRatio !== undefined ? `${(metrics.focusRatio * 100).toFixed(1)}%` : '-') : '-'
                                    }</p>
                                </div>
                                <div className={`${styles.metricTile} ${
                                    /* Daily milestone doesn't usually have a color via getTileColor by default */
                                    (activePeriod === 'selectedDate' || activePeriod === 'today') && metrics ? getTileColor('dailyMilestone', metrics.dailyMilestone) : ''
                                }`}>
                                    <h2>Daily Milestone</h2>
                                    <p className={styles.value}>{
                                        (activePeriod === 'week' || activePeriod === 'month') && aggregatedData ? (aggregatedData.metrics.periodDailyMilestoneDescription ?? '-') :
                                        (activePeriod === 'selectedDate' || activePeriod === 'today') && metrics ? (metrics.dailyMilestone ?? '-') : '-'
                                    }</p>
                                    {/* For week view, if periodDailyMilestoneDescription is long, ensure word-break if needed */}
                                </div>
                                <div className={`${styles.metricTile} ${
                                    (activePeriod === 'week' || activePeriod === 'month') && aggregatedData ? 
                                        ((aggregatedData.metrics.milestoneCompletionRate ?? 0) >= 0.75 ? styles.green : (aggregatedData.metrics.milestoneCompletionRate ?? 0) >= 0.5 ? styles.amber : styles.red) :
                                    (activePeriod === 'selectedDate' || activePeriod === 'today') && metrics ? getTileColor('milestoneHit', metrics.milestoneHit) : ''
                                }`}>
                                    <h2>{(activePeriod === 'week' || activePeriod === 'month') && aggregatedData ? 'Milestone Comp. Rate' : 'Milestone Hit'}</h2>
                                    <p className={styles.value}>{
                                        (activePeriod === 'week' || activePeriod === 'month') && aggregatedData ?
                                            (aggregatedData.metrics.milestoneCompletionRate !== null && aggregatedData.metrics.milestoneCompletionRate !== undefined ? `${(aggregatedData.metrics.milestoneCompletionRate * 100).toFixed(0)}%` : '-') :
                                        (activePeriod === 'selectedDate' || activePeriod === 'today') && metrics ?
                                            (metrics.milestoneHit === null || metrics.milestoneHit === undefined ? '-' : (metrics.milestoneHit ? 'Yes' : 'No')) : '-'
                                    }</p>
                                </div>
                                <div className={`${styles.metricTile} ${
                                    activePeriod === 'week' && aggregatedData ? getTileColor('scheduleAdherence', aggregatedData.metrics.avgScheduleAdherence) :
                                    (activePeriod === 'month' && aggregatedData) ? getTileColor('scheduleAdherence', aggregatedData.metrics.avgScheduleAdherence) :
                                    (activePeriod === 'selectedDate' || activePeriod === 'today') && metrics ? getTileColor('scheduleAdherence', metrics.scheduleAdherence) : ''
                                }`}>
                                    <h2>{(activePeriod === 'week' || activePeriod === 'month') && aggregatedData ? 'Avg. Schedule Adh.' : 'Schedule Adherence (%)'}</h2>
                                    <p className={styles.value}>{
                                        (activePeriod === 'week' || activePeriod === 'month') && aggregatedData ?
                                            (aggregatedData.metrics.avgScheduleAdherence !== null && aggregatedData.metrics.avgScheduleAdherence !== undefined ? `${aggregatedData.metrics.avgScheduleAdherence.toFixed(1)}%` : '-') :
                                        (activePeriod === 'selectedDate' || activePeriod === 'today') && metrics ?
                                            (metrics.scheduleAdherence !== null && metrics.scheduleAdherence !== undefined ? `${metrics.scheduleAdherence}%` : '-') : '-'
                                    }</p>
                                </div>
                            </section>
                            
                            {/* Chart section */}
                            <section className={styles.chartContainer}>
                                 <h2>Deep Work Minutes ({pageTitleDate()})</h2>
                                <canvas ref={chartRef}></canvas>
                            </section>
                        </>
                    )}
                    {/* Message for when there's no data for the selected date or period (and not loading, no error) */}
                    {!isLoading && !error && !scoreboardData && !aggregatedData && (
                        <p>No data available for {pageTitleDate()}. You can input new data above.</p>
                    )}
                </div>
            </div>
        </div>
    );
};

export default ScoreboardPage; 
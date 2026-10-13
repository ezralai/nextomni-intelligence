# NextOmni Analytics Intelligence: Tableau Storyboard & Data Dictionary

## 1. Executive Storyboard Architecture

The Tableau Workbook is structured as a 4-tab interactive executive story designed for continuous monitoring, quantified-self diagnostics, and academic optimization.

```
+-----------------------------------------------------------------------------------------+
|                              NEXTOMNI EXECUTIVE STORYBOARD                              |
+----------------------------+-----------------------------+------------------------------+
| Tab 1: Executive KPI Radar | Tab 2: Circadian & Flow     | Tab 3: Habit Survival &      | Tab 4: AI Prescriptive   |
| (High-Level Weekly Pulse)  | Deep-Dive (Cognitive Clock) | Longevity (Attrition Risk)   | Action Center (Forecast) |
+----------------------------+-----------------------------+------------------------------+
```

---

## 2. Comprehensive Data Dictionary (ROCCC Framework Audit)

Each telemetry source has been audited using Google's **ROCCC** framework:
- **R**eliable: Sourced directly from PostgreSQL transactional application database.
- **O**riginal: First-party user telemetry logged at millisecond timestamps.
- **C**omprehensive: Spans all life dimensions (academic, bio-circadian, atomic habits, cognitive journal).
- **C**urrent: Daily real-time sync with rolling window aggregates.
- **C**ited: Internal NextOmni schema v2.4 specification.

| Table Name | Column Name | Data Type | Role | Business Definition & Calculation | ROCCC Audit Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `focus_sessions` | `session_id` | String | Dimension | Unique UUID per Pomodoro or deep work block. | Reliable & Unique |
| `focus_sessions` | `session_date` | Date | Dimension | Date session occurred (YYYY-MM-DD). | Synchronized UTC |
| `focus_sessions` | `actual_duration_min` | Integer | Measure | Elapsed focus duration excluding pauses. | System-captured |
| `focus_sessions` | `interruption_count` | Integer | Measure | Context switches / notification interruptions. | Sensor / Keylogger proxy |
| `focus_sessions` | `flow_score` | Float | Measure | Subjective Flow State metric (1.0 to 10.0 scale). | User debrief post-timer |
| `focus_sessions` | `is_deep_work` | Boolean | Dimension | Flag: Duration $\ge 45\text{m}$, Interruptions $\le 1$, Flow $\ge 7$. | Derived boolean |
| `circadian_energy_logs` | `time_block` | String | Dimension | Circadian 4-tier partition: Morning, Afternoon, Evening, Night. | Chronobiology standard |
| `circadian_energy_logs` | `energy_level` | Float | Measure | Rated cognitive alertness score (1.0 to 5.0). | Bi-hourly check-in |
| `circadian_energy_logs` | `sleep_hours_prev_night` | Float | Measure | Duration of sleep prior to target date. | Wearable / Manual log |
| `circadian_energy_logs` | `caffeine_intake_mg` | Float | Measure | Cumulative caffeine consumed (mg). | Nutrition logger |
| `habit_logs` | `habit_category` | String | Dimension | Functional category: Deep Work, Fitness, Mind, Wellness. | Taxonomic tag |
| `habit_logs` | `is_completed` | Boolean | Measure | Daily binary adherence check (0 = missed, 1 = completed). | Atomic checkbox |
| `journal_entries` | `mood_score` | Integer | Measure | Mood rating (1 = distressed, 5 = peak optimism). | Likert scale |
| `journal_entries` | `burnout_label` | Boolean | Dimension | Ground truth binary indicator for cognitive exhaustion. | Weekly clinical proxy |

---

## 3. Production Tableau Calculated Fields & LOD Expressions

Copy and paste these exact formulas into Tableau Desktop / Cloud:

### 3.1 Level of Detail (LOD): User Weekly Benchmark Average
```tableau
// [LOD_User_Weekly_Avg_Focus_Hours]
// Calculates baseline weekly hours irrespective of active dashboard filtering
{ FIXED [User Id], DATETRUNC('week', [Session Date]) : 
    SUM([Actual Duration Min]) / 60.0 
}
```

### 3.2 Level of Detail (LOD): Circadian Peak Energy per User
```tableau
// [LOD_Max_Energy_Block_Per_Day]
// Identifies the peak energetic block per day to calculate chronotype misalignment
{ FIXED [User Id], [Log Date] : 
    MAX([Energy Level]) 
}
```

### 3.3 Dynamic Flow State Category (Dimension)
```tableau
// [Calc_Flow_State_Tier]
IF [Flow Score] >= 8.5 THEN "Deep Flow (Hyperfocus)"
ELSEIF [Flow Score] >= 6.5 THEN "Sustainable Flow"
ELSEIF [Flow Score] >= 4.0 THEN "Sub-optimal / Distracted"
ELSE "Cognitive Friction / Stagnant"
END
```

### 3.4 Chronotype Misalignment Index (Measure)
```tableau
// [Calc_Chronotype_Misalignment_Penalty]
// Quantifies hours studied during low-energy night troughs
IF [Time Block] = 'night' AND [Actual Duration Min] > 45 THEN 
    ([Actual Duration Min] / 60.0) * 1.5 
ELSE 
    0.0 
END
```

### 3.5 Habit Longevity Resilience Index (Measure)
```tableau
// [Calc_Habit_Completion_Rate_7D]
// Rolling 7-day completion rate evaluated using INCLUDE
{ INCLUDE [Habit Category] : 
    SUM(IF [Is Completed] = 1 THEN 1 ELSE 0 END) / COUNT([Log Date]) 
}
```

### 3.6 Burnout Hazard Warning Alert (Status Flag)
```tableau
// [Calc_Burnout_Alert_Status]
IF [Calc_Habit_Completion_Rate_7D] < 0.50 AND [Avg Flow Score (7D)] < 5.5 THEN "CRITICAL: High Burnout Risk"
ELSEIF [Calc_Habit_Completion_Rate_7D] < 0.70 OR [Avg Flow Score (7D)] < 6.5 THEN "WARNING: Early Strain Detected"
ELSE "NOMINAL: Peak Cognitive Reserve"
END
```

---

## 4. Tableau Dashboard Wireframes & Visual Hierarchy

### Tab 1: Executive KPI Radar (High-Level Pulse)
```
+-------------------------------------------------------------------------------------------------------+
|  NEXTOMNI // EXECUTIVE LIFE & STUDY RADAR                        Filter: [Semester v]  [Date Range v] |
+-------------------------------------------------------------------------------------------------------+
|  [ KPI 1 ]                 | [ KPI 2 ]                 | [ KPI 3 ]                 | [ KPI 4 ]        |
|  Total Focus Hours         | Deep Work Ratio           | 7-Day Habit Adherence     | Burnout Risk     |
|  142.5 hrs (+12% vs LW)    | 68.4% (Target >60%)       | 82.1% (Nominal)           | LOW (0.18 Prob)  |
+--------------------------------------------------------+----------------------------------------------+
|  [ SHEET 1: Dual-Axis Temporal Trend ]                 | [ SHEET 2: Course Effort Allocation ]        |
|  Line: 7-Day Rolling Focus Minutes                     | Treemap: Hours spent per Course Code         |
|  Bar: Daily Interruption Count                         | - CS-301 (Distributed Systems): 42%         |
|  (Hover for Session Breakdown)                         | - CS-420 (Deep Learning): 35%                |
|                                                        | - STAT-410 (Bayesian Stat): 23%              |
+--------------------------------------------------------+----------------------------------------------+
|  [ SHEET 3: Habit Streak Heatmap Matrix ]                                                             |
|  Rows: Habit Titles | Columns: Calendar Weeks (W1 - W26) | Color: Completion % (Dark Indigo to Emerald)|
+-------------------------------------------------------------------------------------------------------+
```

### Tab 2: Circadian & Flow Deep-Dive (Cognitive Clock)
```
+-------------------------------------------------------------------------------------------------------+
|  CIRCADIAN CHRONOTYPE & FLOW STATE DEEP-DIVE                     Parameter: [Select Time Block v]     |
+-------------------------------------------------------------------------------------------------------+
|  [ SHEET 4: Circadian Rhythm vs Actual Study Heatmap ] | [ SHEET 5: Flow Score vs Interruptions ]     |
|  X-Axis: Hour of Day (00:00 to 23:00)                  | Scatter Plot with Linear Trendline           |
|  Y-Axis: Day of Week (Mon - Sun)                       | X: Interruption Count | Y: Flow Score        |
|  Color: Background Alertness Rating                    | Points sized by Duration, colored by DeepWork|
|  Overlay: Scatter Dots showing Focus Session Start     |                                              |
+--------------------------------------------------------+----------------------------------------------+
|  [ SHEET 6: Sleep & Caffeine Impact Matrix ]                                                          |
|  Box-and-Whisker: Flow Score distribution grouped by Sleep Duration tiers (<6h, 6-7.5h, 7.5h+)       |
|  Color-coded by Caffeine Tier (<100mg, 100-250mg, >250mg)                                             |
+-------------------------------------------------------------------------------------------------------+
```

### Interactive Actions & Filters to Configure in Tableau:
1. **Highlight Action**: Hovering on any course code in the Course Effort Treemap highlights its corresponding sessions in the Flow Scatter plot.
2. **Filter Action (Drill-Down)**: Clicking any day in the Habit Matrix filters Tab 2 to display the hourly circadian energy and focus sessions for that specific date.
3. **Parameter Control**: `[Target Weekly Focus Hours Parameter]` with an adjustable slider (15 to 40 hours) dynamically recalculates the delta KPI gauge on Tab 1.

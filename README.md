# Energy Optimization Simulated Annealing

## Overview
This project models an energy optimization problem in a constrained system where multiple operating parameters influence total energy consumption.

Using simulated annealing, the system searches for near-optimal configurations accounting for varying energy demands and production requirements

High peak energy demand increases operational cost and may exceed plant capacity limits.

By smoothing energy usage across time, companies can:
- Reduce peak energy costs
- Improve system stability
- Avoid overload risks

## Features
- The problem is formulated as a scheduling optimization problem with discrete decision variables.

Simulated Annealing is used to iteratively explore production schedules by:
- Randomly modifying production sequences
- Accepting suboptimal solutions probabilistically
- Converging toward a global optimum

This approach is suitable due to:
- Non-linear energy interactions
- Large combinatorial search space
- Presence of local minima

## Objective Function
Minimize: max(Σ Energy Demand at time t)

Subject to:
- All products planned must be produced
- No overlapping production

## Tech Stack
- Python
- NumPy / Pandas
- Simulated Annealing (custom implementation)
- Data Visualization (Matplotlib)

## Input Data

- Production Plan.csv
- Product Energy Demand.csv

Sample data is provided in the /data folder.

## How to Run
- Update data/Production Plan.csv to reflect Production Plan to optimize
- Update data/Product Energy Demand.csv if there are any updates or new products
- Run all in main.ipynb

## Example Use Case
The system accepts production schedules and energy demand data as input and generates an optimized production sequence that minimizes peak energy usage.

## Results / Screenshots

Here is the sample result before optimization

![CombinedBenchmark](screenshots/benchmark_combined_stream_energy.png)

Here is the actual result post optimization
![CombinedOptimized](screenshots/optimized_combined_stream_energy.png)

- Peak energy demand reduced from ~9000 to ~3500 units
- Approximate reduction: 60%

## Trade-offs
- Increased total production time due to staggered scheduling

## Future Improvements
- Convert to app for better User Experience

## Lessons Learned
- Application of Integer Programming, Simulated Annealing

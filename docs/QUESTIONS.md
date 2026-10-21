 # 10 real questions my user will ask

These are questions firmware QA engineers and embedded developers may ask while checking Apache NuttX RTOS configurations.

| # | Question | Where the answer is (document, page) | Needs more than one page? |
|---|---|---|---|
| 1 | Which Kconfig options control the watchdog timer, and what are their defaults? | Watchdog-related Kconfig files; exact paths to be verified | Yes |
| 2 | What does CONFIG_SCHED_TICKLESS depend on? | Kconfig definition for CONFIG_SCHED_TICKLESS; exact path to be verified | No |
| 3 | Which board configuration shows a low-power sleep example? | Board configuration files and relevant examples; exact paths to be verified | Yes |
| 4 | Which options control task stack sizes, and what are their defaults? | Scheduler and board Kconfig definitions; exact paths to be verified | Yes |
| 5 | Which drivers can be enabled for my flight-controller board? | Board configuration and driver Kconfig files | Yes |
| 6 | Which configuration options are available for power management on a battery-powered device? | Power-management Kconfig files and board configurations | Yes |
| 7 | Which configuration options relate to networking and security? | Networking, security, and driver Kconfig files | Yes |
| 8 | What risks should I investigate if a watchdog-related configuration is disabled? | Watchdog definitions, help text, dependencies, and implementation | Yes |
| 9 | Which settings changed between two versions of my board configuration? | Git diff and the relevant board configuration file | Yes |
| 10 | What is the correct watchdog timeout for my specific drone flight controller? | Requires device-specific requirements and engineering verification; repository information alone may be insufficient | No |

**Note:** File paths and line numbers will be added after checking the actual NuttX source. The multi-source requirements and the unanswered question will be verified during implementation.

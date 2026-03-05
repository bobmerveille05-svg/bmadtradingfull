# Requirements Document

## Introduction

The BMAD-Trading System is a rigorous framework for developing trading strategies with complete traceability from concept to deployment. The system enforces the philosophy: "No code is written before the logic is proven on paper. No strategy is deployed before statistical proof is irrefutable." It provides an orchestrated workflow through five specialized agents (ANALYST, QUANT, CODER, TESTER, AUDITOR) with mandatory quality gates ensuring that only statistically validated strategies reach production.

## Glossary

- **Orchestrator**: The command-line interface and state management system that coordinates workflow phases and agent activation
- **ANALYST**: The agent responsible for capturing trading ideas and producing strategy specifications
- **QUANT**: The agent responsible for transforming specifications into mathematical logic models
- **CODER**: The agent responsible for generating executable code for trading platforms
- **TESTER**: The agent responsible for executing all testing levels
- **AUDITOR**: The agent responsible for statistical certification
- **Gate**: A quality checkpoint with mandatory criteria that must be 100% satisfied before proceeding
- **STRATEGY_SPEC**: The artifact document containing the complete trading strategy specification
- **LOGIC_MODEL**: The artifact document containing mathematical formulas, state machines, and pseudo-code
- **BMAD_PC**: The platform-agnostic pseudo-code language used for logic representation
- **Artifact**: A versioned document produced by an agent (STRATEGY-SPEC.md, LOGIC-MODEL.md, SOURCE-CODE, TEST-REPORT.md, PROOF-CERTIFICATE.md)
- **Traceability_Map**: The complete mapping from specification rules to logic to code to tests
- **Rule_ID**: A unique identifier linking requirements across all artifacts
- **MT4**: MetaTrader 4 trading platform using MQL4 language
- **MT5**: MetaTrader 5 trading platform using MQL5 language
- **Pine_Script**: TradingView platform scripting language version 5
- **Backtest**: Historical simulation of strategy performance using past market data
- **Walk_Forward_Analysis**: Robustness test dividing data into training and testing periods
- **Monte_Carlo_Simulation**: Robustness test using randomized trade sequences
- **Sharpe_Ratio**: Risk-adjusted return metric calculated as (return - risk_free_rate) / standard_deviation
- **Maximum_Drawdown**: The largest peak-to-trough decline in account equity
- **Win_Rate**: Percentage of profitable trades out of total trades
- **Profit_Factor**: Ratio of gross profit to gross loss
- **Emergency_Stop_Criteria**: Predefined thresholds that trigger automatic strategy deactivation

## Requirements

### Requirement 1: Orchestrator Command Interface

**User Story:** As a trader, I want to control the system through commands, so that I can navigate the workflow and access system functions.

#### Acceptance Criteria

1. THE Orchestrator SHALL accept the command "/start" to initiate a new strategy development session
2. THE Orchestrator SHALL accept the command "/status" to display the current phase, active agent, and gate status
3. THE Orchestrator SHALL accept the command "/gate" to display the current gate checklist and validation status
4. THE Orchestrator SHALL accept the command "/rollback" to return to the previous phase
5. THE Orchestrator SHALL accept the command "/agent" to display information about the currently active agent
6. THE Orchestrator SHALL accept the command "/spec" to display the STRATEGY_SPEC artifact
7. THE Orchestrator SHALL accept the command "/logic" to display the LOGIC_MODEL artifact
8. THE Orchestrator SHALL accept the command "/code" to display generated source code artifacts
9. THE Orchestrator SHALL accept the command "/test" to display the TEST-REPORT artifact
10. THE Orchestrator SHALL accept the command "/proof" to display the PROOF-CERTIFICATE artifact
11. THE Orchestrator SHALL accept the command "/export" to package all artifacts for deployment
12. THE Orchestrator SHALL accept the command "/audit" to display the complete Traceability_Map
13. THE Orchestrator SHALL accept the command "/checklist" to display all gate checklists and their status

### Requirement 2: Orchestrator State Management

**User Story:** As a system component, I need the orchestrator to maintain workflow state, so that the system can track progress and enforce phase sequencing.

#### Acceptance Criteria

1. THE Orchestrator SHALL maintain the current phase state with values: SPEC, LOGIC, CODE, TEST, or PROOF
2. THE Orchestrator SHALL maintain the current gate status with values: PENDING, IN_PROGRESS, PASSED, or FAILED
3. THE Orchestrator SHALL maintain a list of all generated artifacts with their file paths and timestamps
4. THE Orchestrator SHALL persist state to disk after each phase transition
5. WHEN the Orchestrator starts, THE Orchestrator SHALL restore state from disk if a previous session exists
6. THE Orchestrator SHALL maintain a session identifier unique to each strategy development workflow

### Requirement 3: Agent Routing and Activation

**User Story:** As the orchestrator, I need to activate the correct agent for each phase, so that specialized work is performed by the appropriate component.

#### Acceptance Criteria

1. WHEN the phase is SPEC, THE Orchestrator SHALL activate the ANALYST agent
2. WHEN the phase is LOGIC, THE Orchestrator SHALL activate the QUANT agent
3. WHEN the phase is CODE, THE Orchestrator SHALL activate the CODER agent
4. WHEN the phase is TEST, THE Orchestrator SHALL activate the TESTER agent
5. WHEN the phase is PROOF, THE Orchestrator SHALL activate the AUDITOR agent
6. THE Orchestrator SHALL provide the active agent with access to all previous phase artifacts
7. THE Orchestrator SHALL prevent agent activation if the previous gate has not passed

### Requirement 4: ANALYST Agent Questionnaire

**User Story:** As a trader, I want to answer structured questions about my trading idea, so that the system can capture my strategy completely.

#### Acceptance Criteria

1. WHEN the ANALYST is activated, THE ANALYST SHALL present a questionnaire covering strategy concept, market context, entry rules, exit rules, risk management, and filters
2. THE ANALYST SHALL accept responses in English or French
3. THE ANALYST SHALL validate that all mandatory questionnaire sections are completed before proceeding
4. THE ANALYST SHALL allow the trader to provide examples and edge cases for each rule
5. WHEN the questionnaire is complete, THE ANALYST SHALL generate a STRATEGY_SPEC artifact

### Requirement 5: STRATEGY_SPEC Artifact Generation

**User Story:** As the ANALYST, I need to produce a complete strategy specification, so that the QUANT can transform it into mathematical logic.

#### Acceptance Criteria

1. THE ANALYST SHALL generate a STRATEGY_SPEC artifact in Markdown format
2. THE STRATEGY_SPEC SHALL include sections: Overview, Market_Context, Entry_Rules, Exit_Rules, Risk_Management, Filters, and Edge_Cases
3. THE STRATEGY_SPEC SHALL assign a unique Rule_ID to each trading rule in the format "R-XXX"
4. THE STRATEGY_SPEC SHALL include natural language descriptions for each rule
5. THE STRATEGY_SPEC SHALL include trader-provided examples for each rule
6. THE STRATEGY_SPEC SHALL be saved to disk with filename "STRATEGY-SPEC.md"
7. THE STRATEGY_SPEC SHALL include a version number and timestamp

### Requirement 6: GATE-01 Validation

**User Story:** As the orchestrator, I need to validate that the specification is complete, so that only high-quality specs proceed to logic modeling.

#### Acceptance Criteria

1. WHEN GATE-01 validation is requested, THE Orchestrator SHALL verify that all 9 GATE-01 criteria are satisfied
2. THE Orchestrator SHALL verify that all mandatory sections are present in the STRATEGY_SPEC
3. THE Orchestrator SHALL verify that each rule has a unique Rule_ID
4. THE Orchestrator SHALL verify that entry rules are clearly defined
5. THE Orchestrator SHALL verify that exit rules are clearly defined
6. THE Orchestrator SHALL verify that risk management rules are specified
7. THE Orchestrator SHALL verify that market context is documented
8. THE Orchestrator SHALL verify that edge cases are identified
9. THE Orchestrator SHALL verify that examples are provided for key rules
10. IF any GATE-01 criterion fails, THEN THE Orchestrator SHALL set gate status to FAILED and prevent phase transition
11. WHEN all GATE-01 criteria pass, THE Orchestrator SHALL set gate status to PASSED and allow transition to LOGIC phase

### Requirement 7: QUANT Agent Logic Transformation

**User Story:** As the QUANT, I need to transform natural language rules into mathematical logic, so that the strategy can be implemented precisely.

#### Acceptance Criteria

1. WHEN the QUANT is activated, THE QUANT SHALL read the STRATEGY_SPEC artifact
2. THE QUANT SHALL transform each Rule_ID into mathematical formulas using standard notation
3. THE QUANT SHALL create a state machine diagram representing strategy states and transitions
4. THE QUANT SHALL generate BMAD_PC pseudo-code for each rule
5. THE QUANT SHALL create truth tables for complex conditional logic
6. THE QUANT SHALL maintain Rule_ID traceability from STRATEGY_SPEC to LOGIC_MODEL
7. WHEN logic transformation is complete, THE QUANT SHALL generate a LOGIC_MODEL artifact

### Requirement 8: LOGIC_MODEL Artifact Generation

**User Story:** As the QUANT, I need to produce a complete logic model, so that the CODER can generate executable code.

#### Acceptance Criteria

1. THE QUANT SHALL generate a LOGIC_MODEL artifact in Markdown format
2. THE LOGIC_MODEL SHALL include sections: Mathematical_Formulas, State_Machine, Pseudo_Code, Truth_Tables, and Variable_Definitions
3. THE LOGIC_MODEL SHALL reference Rule_IDs from the STRATEGY_SPEC for each formula
4. THE LOGIC_MODEL SHALL define all variables with their types, ranges, and units
5. THE LOGIC_MODEL SHALL include state transition conditions in the state machine
6. THE LOGIC_MODEL SHALL use BMAD_PC syntax for all pseudo-code
7. THE LOGIC_MODEL SHALL be saved to disk with filename "LOGIC-MODEL.md"
8. THE LOGIC_MODEL SHALL include a version number and timestamp

### Requirement 9: GATE-02 Validation

**User Story:** As the orchestrator, I need to validate that the logic is mathematically sound, so that only verified logic proceeds to code generation.

#### Acceptance Criteria

1. WHEN GATE-02 validation is requested, THE Orchestrator SHALL verify that all 7 GATE-02 criteria are satisfied
2. THE Orchestrator SHALL verify that all rules from STRATEGY_SPEC are represented in LOGIC_MODEL
3. THE Orchestrator SHALL verify that all formulas are mathematically valid
4. THE Orchestrator SHALL verify that the state machine has no unreachable states
5. THE Orchestrator SHALL verify that all variables are defined with types and ranges
6. THE Orchestrator SHALL verify that BMAD_PC pseudo-code is syntactically correct
7. THE Orchestrator SHALL verify that truth tables cover all input combinations
8. IF any GATE-02 criterion fails, THEN THE Orchestrator SHALL set gate status to FAILED and prevent phase transition
9. WHEN all GATE-02 criteria pass, THE Orchestrator SHALL set gate status to PASSED and allow transition to CODE phase

### Requirement 10: CODER Agent Platform Selection

**User Story:** As a trader, I want to specify which trading platforms to target, so that I receive code for my preferred platforms.

#### Acceptance Criteria

1. WHEN the CODER is activated, THE CODER SHALL prompt the trader to select target platforms from: MT4, MT5, Pine_Script, or ALL
2. THE CODER SHALL accept multiple platform selections
3. THE CODER SHALL generate code for each selected platform
4. WHERE MT4 is selected, THE CODER SHALL generate MQL4 code
5. WHERE MT5 is selected, THE CODER SHALL generate MQL5 code
6. WHERE Pine_Script is selected, THE CODER SHALL generate Pine Script v5 code

### Requirement 11: CODER Agent Code Generation

**User Story:** As the CODER, I need to translate BMAD_PC logic into platform-specific code, so that the strategy can execute on trading platforms.

#### Acceptance Criteria

1. WHEN the CODER generates code, THE CODER SHALL read the LOGIC_MODEL artifact
2. THE CODER SHALL translate each BMAD_PC statement into platform-specific syntax using translation tables
3. THE CODER SHALL include traceability comments linking code sections to Rule_IDs
4. THE CODER SHALL implement indicators, signals, filters, risk management, and trailing stops as specified
5. THE CODER SHALL follow platform-specific best practices for code structure
6. THE CODER SHALL include error handling for invalid inputs and market conditions
7. THE CODER SHALL generate code that compiles without errors on the target platform
8. THE CODER SHALL maintain consistent variable naming across all platforms

### Requirement 12: Source Code Artifact Structure

**User Story:** As the CODER, I need to structure generated code consistently, so that it is maintainable and traceable.

#### Acceptance Criteria

1. THE CODER SHALL include a header comment block with strategy name, version, generation date, and BMAD system version
2. THE CODER SHALL organize code into sections: Inputs, Variables, Initialization, Main_Logic, Entry_Functions, Exit_Functions, and Risk_Management
3. THE CODER SHALL include a traceability comment before each function in the format "// Rule_ID: R-XXX"
4. THE CODER SHALL save MT4 code with filename "[strategy_name]_MT4.mq4"
5. THE CODER SHALL save MT5 code with filename "[strategy_name]_MT5.mq5"
6. THE CODER SHALL save Pine_Script code with filename "[strategy_name]_Pine.pine"
7. THE CODER SHALL include inline comments explaining complex logic

### Requirement 13: GATE-03 Validation

**User Story:** As the orchestrator, I need to validate that generated code meets quality standards, so that only production-ready code proceeds to testing.

#### Acceptance Criteria

1. WHEN GATE-03 validation is requested, THE Orchestrator SHALL verify that all 6 GATE-03 criteria are satisfied
2. THE Orchestrator SHALL verify that code compiles without errors on the target platform
3. THE Orchestrator SHALL verify that all Rule_IDs from LOGIC_MODEL are present in code comments
4. THE Orchestrator SHALL verify that code structure follows the standardized template
5. THE Orchestrator SHALL verify that error handling is implemented
6. THE Orchestrator SHALL verify that all variables from LOGIC_MODEL are declared in code
7. IF any GATE-03 criterion fails, THEN THE Orchestrator SHALL set gate status to FAILED and prevent phase transition
8. WHEN all GATE-03 criteria pass, THE Orchestrator SHALL set gate status to PASSED and allow transition to TEST phase

### Requirement 14: TESTER Agent Unit Testing

**User Story:** As the TESTER, I need to verify individual functions work correctly, so that basic functionality is validated before integration testing.

#### Acceptance Criteria

1. WHEN the TESTER executes unit tests, THE TESTER SHALL test each entry rule function with valid and invalid inputs
2. THE TESTER SHALL test each exit rule function with valid and invalid inputs
3. THE TESTER SHALL test each risk management function with boundary values
4. THE TESTER SHALL test each indicator calculation function with known input-output pairs
5. THE TESTER SHALL record pass/fail status for each unit test
6. THE TESTER SHALL record execution time for each unit test
7. WHEN a unit test fails, THE TESTER SHALL record the input values, expected output, and actual output

### Requirement 15: TESTER Agent Integration Testing

**User Story:** As the TESTER, I need to verify that components work together correctly, so that the complete strategy logic is validated.

#### Acceptance Criteria

1. WHEN the TESTER executes integration tests, THE TESTER SHALL use predefined market scenarios covering trending, ranging, and volatile conditions
2. THE TESTER SHALL verify that entry signals trigger correctly in each scenario
3. THE TESTER SHALL verify that exit signals trigger correctly in each scenario
4. THE TESTER SHALL verify that risk management limits are enforced in each scenario
5. THE TESTER SHALL verify that filters prevent trades when conditions are not met
6. THE TESTER SHALL record pass/fail status for each integration test scenario
7. WHEN an integration test fails, THE TESTER SHALL record the scenario, expected behavior, and actual behavior

### Requirement 16: TESTER Agent Backtesting

**User Story:** As the TESTER, I need to simulate strategy performance on historical data, so that I can measure profitability and risk metrics.

#### Acceptance Criteria

1. WHEN the TESTER executes backtests, THE TESTER SHALL use historical market data spanning at least 2 years
2. THE TESTER SHALL calculate and record the following 18 metrics: Total_Trades, Win_Rate, Profit_Factor, Sharpe_Ratio, Maximum_Drawdown, Average_Win, Average_Loss, Largest_Win, Largest_Loss, Consecutive_Wins, Consecutive_Losses, Average_Trade_Duration, Total_Return, Annualized_Return, Risk_Reward_Ratio, Recovery_Factor, Expectancy, and Calmar_Ratio
3. THE TESTER SHALL generate an equity curve showing account balance over time
4. THE TESTER SHALL generate a trade distribution histogram
5. THE TESTER SHALL record the date range of the backtest
6. THE TESTER SHALL record the initial capital and final capital
7. THE TESTER SHALL identify the worst drawdown period with start and end dates

### Requirement 17: TESTER Agent Robustness Testing

**User Story:** As the TESTER, I need to verify that the strategy performs consistently across different conditions, so that I can assess its reliability.

#### Acceptance Criteria

1. WHEN the TESTER executes robustness tests, THE TESTER SHALL perform Walk_Forward_Analysis with at least 5 time periods
2. THE TESTER SHALL perform Monte_Carlo_Simulation with at least 1000 iterations
3. THE TESTER SHALL perform sensitivity analysis by varying each input parameter by ±20%
4. THE TESTER SHALL record performance metrics for each Walk_Forward_Analysis period
5. THE TESTER SHALL record the distribution of returns from Monte_Carlo_Simulation
6. THE TESTER SHALL identify which parameters have the greatest impact on performance
7. THE TESTER SHALL calculate the stability score as the standard deviation of returns across all robustness tests

### Requirement 18: TEST-REPORT Artifact Generation

**User Story:** As the TESTER, I need to document all test results, so that the AUDITOR can perform statistical certification.

#### Acceptance Criteria

1. THE TESTER SHALL generate a TEST-REPORT artifact in Markdown format
2. THE TEST-REPORT SHALL include sections: Unit_Test_Results, Integration_Test_Results, Backtest_Results, Robustness_Test_Results, and Summary
3. THE TEST-REPORT SHALL include all 18 backtest metrics with their values
4. THE TEST-REPORT SHALL include charts for equity curve and trade distribution
5. THE TEST-REPORT SHALL include pass/fail counts for unit and integration tests
6. THE TEST-REPORT SHALL include robustness test results with stability scores
7. THE TEST-REPORT SHALL be saved to disk with filename "TEST-REPORT.md"
8. THE TEST-REPORT SHALL include a version number and timestamp

### Requirement 19: GATE-04 Validation

**User Story:** As the orchestrator, I need to validate that testing is complete and meets minimum standards, so that only tested strategies proceed to certification.

#### Acceptance Criteria

1. WHEN GATE-04 validation is requested, THE Orchestrator SHALL verify that all 7 GATE-04 criteria are satisfied
2. THE Orchestrator SHALL verify that all unit tests have passed
3. THE Orchestrator SHALL verify that all integration tests have passed
4. THE Orchestrator SHALL verify that backtest includes at least 100 trades
5. THE Orchestrator SHALL verify that all 18 backtest metrics are calculated
6. THE Orchestrator SHALL verify that Walk_Forward_Analysis is performed
7. THE Orchestrator SHALL verify that Monte_Carlo_Simulation is performed
8. IF any GATE-04 criterion fails, THEN THE Orchestrator SHALL set gate status to FAILED and prevent phase transition
9. WHEN all GATE-04 criteria pass, THE Orchestrator SHALL set gate status to PASSED and allow transition to PROOF phase

### Requirement 20: AUDITOR Agent Statistical Evaluation

**User Story:** As the AUDITOR, I need to evaluate the strategy on multiple dimensions, so that I can determine if it meets certification standards.

#### Acceptance Criteria

1. WHEN the AUDITOR performs evaluation, THE AUDITOR SHALL assess the strategy on 5 axes: Edge, Robustness, Risk, Compliance, and Exploitability
2. THE AUDITOR SHALL assign a score from 0 to 4 points for the Edge axis based on Profit_Factor and Win_Rate
3. THE AUDITOR SHALL assign a score from 0 to 4 points for the Robustness axis based on Walk_Forward_Analysis consistency and Monte_Carlo_Simulation results
4. THE AUDITOR SHALL assign a score from 0 to 4 points for the Risk axis based on Maximum_Drawdown and Sharpe_Ratio
5. THE AUDITOR SHALL assign a score from 0 to 3 points for the Compliance axis based on rule adherence and traceability
6. THE AUDITOR SHALL assign a score from 0 to 3 points for the Exploitability axis based on trade frequency and parameter sensitivity
7. THE AUDITOR SHALL calculate the total score as the sum of all axis scores with a maximum of 18 points

### Requirement 21: AUDITOR Agent Certification Decision

**User Story:** As the AUDITOR, I need to make a certification decision based on statistical evidence, so that only proven strategies are approved for deployment.

#### Acceptance Criteria

1. WHEN the total score is between 16 and 18 points, THE AUDITOR SHALL assign certification status CERTIFIED
2. WHEN the total score is between 12 and 15 points, THE AUDITOR SHALL assign certification status CONDITIONAL
3. WHEN the total score is between 8 and 11 points, THE AUDITOR SHALL assign certification status REJECTED
4. WHEN the total score is between 0 and 7 points, THE AUDITOR SHALL assign certification status ABANDONED
5. WHERE certification status is CONDITIONAL, THE AUDITOR SHALL specify required improvements before deployment
6. WHERE certification status is REJECTED, THE AUDITOR SHALL specify critical issues that must be addressed
7. WHERE certification status is ABANDONED, THE AUDITOR SHALL recommend discontinuing the strategy

### Requirement 22: AUDITOR Agent Emergency Stop Criteria

**User Story:** As the AUDITOR, I need to define emergency stop criteria, so that the strategy can be automatically deactivated if performance degrades in live trading.

#### Acceptance Criteria

1. WHERE certification status is CERTIFIED or CONDITIONAL, THE AUDITOR SHALL define Emergency_Stop_Criteria
2. THE AUDITOR SHALL specify a maximum drawdown threshold that triggers emergency stop
3. THE AUDITOR SHALL specify a minimum Win_Rate threshold that triggers emergency stop
4. THE AUDITOR SHALL specify a maximum consecutive losses threshold that triggers emergency stop
5. THE AUDITOR SHALL specify a time-based review period for monitoring live performance
6. THE AUDITOR SHALL specify actions to take when Emergency_Stop_Criteria are triggered

### Requirement 23: PROOF-CERTIFICATE Artifact Generation

**User Story:** As the AUDITOR, I need to document the certification decision and supporting evidence, so that traders have statistical proof before deployment.

#### Acceptance Criteria

1. THE AUDITOR SHALL generate a PROOF-CERTIFICATE artifact in Markdown format
2. THE PROOF-CERTIFICATE SHALL include sections: Executive_Summary, Five_Axis_Evaluation, Certification_Decision, Emergency_Stop_Criteria, and Post_Certification_Plan
3. THE PROOF-CERTIFICATE SHALL include the score for each of the 5 axes with justification
4. THE PROOF-CERTIFICATE SHALL include the total score and certification status
5. THE PROOF-CERTIFICATE SHALL include statistical evidence supporting the certification decision
6. THE PROOF-CERTIFICATE SHALL include Emergency_Stop_Criteria with specific thresholds
7. THE PROOF-CERTIFICATE SHALL be saved to disk with filename "PROOF-CERTIFICATE.md"
8. THE PROOF-CERTIFICATE SHALL include a version number and timestamp
9. THE PROOF-CERTIFICATE SHALL include the AUDITOR signature and certification date

### Requirement 24: Traceability Map Generation

**User Story:** As the orchestrator, I need to maintain complete traceability from requirements to code, so that every implementation detail can be traced back to its origin.

#### Acceptance Criteria

1. THE Orchestrator SHALL generate a Traceability_Map linking each Rule_ID across all artifacts
2. THE Traceability_Map SHALL show the mapping: STRATEGY_SPEC Rule_ID → LOGIC_MODEL formula → Source code function → Test case
3. THE Traceability_Map SHALL identify any Rule_IDs that are missing from subsequent artifacts
4. THE Traceability_Map SHALL be saved to disk with filename "TRACEABILITY-MAP.md"
5. WHEN the "/audit" command is executed, THE Orchestrator SHALL display the Traceability_Map
6. THE Traceability_Map SHALL include a completeness percentage showing how many rules are fully traced

### Requirement 25: Artifact Export and Packaging

**User Story:** As a trader, I want to export all artifacts as a deployment package, so that I can deploy the strategy to my trading platform.

#### Acceptance Criteria

1. WHEN the "/export" command is executed, THE Orchestrator SHALL create a deployment package containing all artifacts
2. THE Orchestrator SHALL include STRATEGY-SPEC.md in the deployment package
3. THE Orchestrator SHALL include LOGIC-MODEL.md in the deployment package
4. THE Orchestrator SHALL include all generated source code files in the deployment package
5. THE Orchestrator SHALL include TEST-REPORT.md in the deployment package
6. THE Orchestrator SHALL include PROOF-CERTIFICATE.md in the deployment package
7. THE Orchestrator SHALL include TRACEABILITY-MAP.md in the deployment package
8. THE Orchestrator SHALL create a README.md file with deployment instructions
9. THE Orchestrator SHALL compress the deployment package into a ZIP file with filename "[strategy_name]_BMAD_v[version].zip"
10. THE Orchestrator SHALL save the deployment package to the current directory

### Requirement 26: Rollback Functionality

**User Story:** As a trader, I want to return to a previous phase if I need to make changes, so that I can refine my strategy without starting over.

#### Acceptance Criteria

1. WHEN the "/rollback" command is executed, THE Orchestrator SHALL transition to the previous phase
2. THE Orchestrator SHALL preserve all artifacts from the current phase before rollback
3. THE Orchestrator SHALL reset the current gate status to PENDING after rollback
4. THE Orchestrator SHALL notify the user which phase is now active after rollback
5. IF the current phase is SPEC, THEN THE Orchestrator SHALL reject the rollback command
6. THE Orchestrator SHALL allow multiple consecutive rollbacks to earlier phases

### Requirement 27: Multi-Language Support

**User Story:** As a French-speaking trader, I want to interact with the system in French, so that I can work in my preferred language.

#### Acceptance Criteria

1. THE Orchestrator SHALL detect the user's language preference from system settings or explicit selection
2. WHERE the language preference is French, THE Orchestrator SHALL present all prompts and messages in French
3. WHERE the language preference is English, THE Orchestrator SHALL present all prompts and messages in English
4. THE ANALYST SHALL accept questionnaire responses in French or English regardless of interface language
5. THE Orchestrator SHALL generate artifact filenames in English regardless of interface language
6. THE Orchestrator SHALL preserve the original language of user inputs in STRATEGY_SPEC

### Requirement 28: Session Persistence and Recovery

**User Story:** As a trader, I want my work to be saved automatically, so that I can resume if the system is interrupted.

#### Acceptance Criteria

1. THE Orchestrator SHALL save state to disk after each artifact is generated
2. THE Orchestrator SHALL save state to disk after each gate validation
3. THE Orchestrator SHALL save state to disk after each phase transition
4. WHEN the Orchestrator starts, THE Orchestrator SHALL check for existing session state
5. IF existing session state is found, THEN THE Orchestrator SHALL prompt the user to resume or start new
6. WHEN resuming a session, THE Orchestrator SHALL restore the phase, gate status, and artifact references
7. THE Orchestrator SHALL save session state to a file named ".bmad-session.json" in the working directory

### Requirement 29: BMAD_PC Pseudo-Code Language

**User Story:** As the QUANT, I need a standardized pseudo-code language, so that logic can be expressed consistently before platform-specific translation.

#### Acceptance Criteria

1. THE QUANT SHALL use BMAD_PC syntax for all pseudo-code in LOGIC_MODEL
2. BMAD_PC SHALL support the following constructs: IF-THEN-ELSE, WHILE, FOR, FUNCTION, RETURN, AND, OR, NOT
3. BMAD_PC SHALL support mathematical operators: +, -, *, /, %, ^, <, >, <=, >=, ==, !=
4. BMAD_PC SHALL support market data access functions: CLOSE(offset), OPEN(offset), HIGH(offset), LOW(offset), VOLUME(offset)
5. BMAD_PC SHALL support indicator functions: SMA(period), EMA(period), RSI(period), MACD(fast, slow, signal), ATR(period)
6. BMAD_PC SHALL use UPPERCASE for keywords and functions
7. BMAD_PC SHALL use descriptive variable names in lowercase_with_underscores

### Requirement 30: Translation Tables for Code Generation

**User Story:** As the CODER, I need translation tables to convert BMAD_PC to platform-specific syntax, so that code generation is consistent and accurate.

#### Acceptance Criteria

1. THE CODER SHALL maintain a translation table mapping BMAD_PC constructs to MQL4 syntax
2. THE CODER SHALL maintain a translation table mapping BMAD_PC constructs to MQL5 syntax
3. THE CODER SHALL maintain a translation table mapping BMAD_PC constructs to Pine Script v5 syntax
4. THE translation tables SHALL include mappings for all BMAD_PC keywords, operators, and functions
5. THE translation tables SHALL include platform-specific function signatures
6. THE translation tables SHALL include platform-specific data type conversions
7. WHEN a BMAD_PC construct has no direct equivalent, THE CODER SHALL implement it using multiple platform-specific statements

### Requirement 31: Artifact Versioning

**User Story:** As the orchestrator, I need to version all artifacts, so that changes can be tracked and previous versions can be referenced.

#### Acceptance Criteria

1. THE Orchestrator SHALL assign a version number to each artifact in the format "v[major].[minor]"
2. WHEN an artifact is first created, THE Orchestrator SHALL assign version "v1.0"
3. WHEN an artifact is regenerated after rollback, THE Orchestrator SHALL increment the minor version number
4. THE Orchestrator SHALL include the version number in the artifact header
5. THE Orchestrator SHALL maintain a version history file listing all artifact versions with timestamps
6. THE Orchestrator SHALL save previous versions with filename "[artifact_name]_v[version].md"

### Requirement 32: Gate Checklist Display

**User Story:** As a trader, I want to see detailed gate checklists, so that I understand what criteria must be met before proceeding.

#### Acceptance Criteria

1. WHEN the "/checklist" command is executed, THE Orchestrator SHALL display all gate checklists
2. THE Orchestrator SHALL display GATE-01 checklist with 9 criteria and their pass/fail status
3. THE Orchestrator SHALL display GATE-02 checklist with 7 criteria and their pass/fail status
4. THE Orchestrator SHALL display GATE-03 checklist with 6 criteria and their pass/fail status
5. THE Orchestrator SHALL display GATE-04 checklist with 7 criteria and their pass/fail status
6. THE Orchestrator SHALL indicate which criteria are currently failing with specific error messages
7. THE Orchestrator SHALL display the overall gate pass percentage

### Requirement 33: Error Handling and Validation Messages

**User Story:** As a user, I want clear error messages when validation fails, so that I know what needs to be corrected.

#### Acceptance Criteria

1. WHEN a gate criterion fails, THE Orchestrator SHALL display a specific error message explaining the failure
2. WHEN a command is invalid, THE Orchestrator SHALL display available commands
3. WHEN an artifact is missing, THE Orchestrator SHALL display which artifact is required and which phase generates it
4. WHEN a file operation fails, THE Orchestrator SHALL display the file path and error reason
5. IF a user attempts to skip a phase, THEN THE Orchestrator SHALL display a message explaining the mandatory workflow sequence
6. THE Orchestrator SHALL log all errors to a file named "bmad-errors.log"

### Requirement 34: Platform-Specific Code Standards

**User Story:** As the CODER, I need to follow platform-specific best practices, so that generated code is idiomatic and maintainable.

#### Acceptance Criteria

1. WHERE the target platform is MT4, THE CODER SHALL use OnInit(), OnDeinit(), and OnTick() event handlers
2. WHERE the target platform is MT5, THE CODER SHALL use OnInit(), OnDeinit(), and OnTick() event handlers with MT5-specific order management functions
3. WHERE the target platform is Pine_Script, THE CODER SHALL use Pine Script v5 syntax with strategy() declaration
4. THE CODER SHALL declare input parameters using platform-specific input syntax
5. THE CODER SHALL use platform-specific position management functions
6. THE CODER SHALL implement platform-specific error codes and handling
7. THE CODER SHALL follow platform-specific naming conventions for functions and variables

### Requirement 35: Backtest Metric Calculations

**User Story:** As the TESTER, I need to calculate metrics accurately, so that performance evaluation is reliable.

#### Acceptance Criteria

1. THE TESTER SHALL calculate Win_Rate as (winning_trades / total_trades) * 100
2. THE TESTER SHALL calculate Profit_Factor as gross_profit / gross_loss
3. THE TESTER SHALL calculate Sharpe_Ratio as (average_return - risk_free_rate) / standard_deviation_of_returns
4. THE TESTER SHALL calculate Maximum_Drawdown as the largest peak-to-trough decline in equity
5. THE TESTER SHALL calculate Expectancy as (win_rate * average_win) - (loss_rate * average_loss)
6. THE TESTER SHALL calculate Calmar_Ratio as annualized_return / Maximum_Drawdown
7. THE TESTER SHALL calculate Recovery_Factor as net_profit / Maximum_Drawdown
8. THE TESTER SHALL use a risk_free_rate of 2% per annum for Sharpe_Ratio calculation unless specified otherwise
9. IF gross_loss is zero, THEN THE TESTER SHALL set Profit_Factor to infinity
10. IF Maximum_Drawdown is zero, THEN THE TESTER SHALL set Calmar_Ratio and Recovery_Factor to infinity

### Requirement 36: Walk-Forward Analysis Implementation

**User Story:** As the TESTER, I need to perform walk-forward analysis, so that I can assess strategy robustness across different time periods.

#### Acceptance Criteria

1. WHEN performing Walk_Forward_Analysis, THE TESTER SHALL divide historical data into at least 5 consecutive periods
2. THE TESTER SHALL use 70% of each period for in-sample optimization and 30% for out-of-sample testing
3. THE TESTER SHALL calculate performance metrics for each out-of-sample period
4. THE TESTER SHALL calculate the average performance across all out-of-sample periods
5. THE TESTER SHALL calculate the standard deviation of performance across all out-of-sample periods
6. THE TESTER SHALL identify the best and worst performing out-of-sample periods
7. THE TESTER SHALL calculate a consistency score as (1 - coefficient_of_variation) where coefficient_of_variation = standard_deviation / mean

### Requirement 37: Monte Carlo Simulation Implementation

**User Story:** As the TESTER, I need to perform Monte Carlo simulation, so that I can assess the probability distribution of strategy outcomes.

#### Acceptance Criteria

1. WHEN performing Monte_Carlo_Simulation, THE TESTER SHALL execute at least 1000 iterations
2. THE TESTER SHALL randomize the order of historical trades in each iteration while preserving trade outcomes
3. THE TESTER SHALL calculate the final equity for each iteration
4. THE TESTER SHALL calculate the mean final equity across all iterations
5. THE TESTER SHALL calculate the standard deviation of final equity across all iterations
6. THE TESTER SHALL calculate the 5th percentile final equity (worst 5% of outcomes)
7. THE TESTER SHALL calculate the 95th percentile final equity (best 5% of outcomes)
8. THE TESTER SHALL generate a histogram showing the distribution of final equity values

### Requirement 38: Sensitivity Analysis Implementation

**User Story:** As the TESTER, I need to perform sensitivity analysis, so that I can identify which parameters most affect strategy performance.

#### Acceptance Criteria

1. WHEN performing sensitivity analysis, THE TESTER SHALL identify all input parameters from the STRATEGY_SPEC
2. THE TESTER SHALL vary each parameter individually by -20%, -10%, +10%, and +20% from its base value
3. THE TESTER SHALL run a backtest for each parameter variation
4. THE TESTER SHALL calculate the change in Profit_Factor for each parameter variation
5. THE TESTER SHALL rank parameters by their impact on performance
6. THE TESTER SHALL identify parameters where small changes cause large performance swings as high-risk parameters
7. THE TESTER SHALL calculate a robustness score based on the average performance stability across all parameter variations

### Requirement 39: LLM Integration for Agent Execution

**User Story:** As the orchestrator, I need to integrate with LLM services, so that agents can perform their specialized tasks.

#### Acceptance Criteria

1. THE Orchestrator SHALL support integration with Claude and GPT language models
2. THE Orchestrator SHALL provide each agent with a specialized system prompt defining its role and responsibilities
3. THE Orchestrator SHALL provide each agent with access to relevant artifacts from previous phases
4. THE Orchestrator SHALL provide each agent with the BMAD system documentation and templates
5. THE Orchestrator SHALL validate that agent outputs conform to expected artifact formats
6. IF an agent produces invalid output, THEN THE Orchestrator SHALL retry with corrective feedback up to 3 times
7. THE Orchestrator SHALL log all LLM interactions to a file named "bmad-llm-log.txt"

### Requirement 40: Template Management

**User Story:** As the orchestrator, I need to provide templates to agents, so that artifacts are consistently structured.

#### Acceptance Criteria

1. THE Orchestrator SHALL maintain a template for STRATEGY-SPEC.md with predefined sections
2. THE Orchestrator SHALL maintain a template for LOGIC-MODEL.md with predefined sections
3. THE Orchestrator SHALL maintain templates for MT4, MT5, and Pine_Script source code with standard structure
4. THE Orchestrator SHALL maintain a template for TEST-REPORT.md with predefined sections
5. THE Orchestrator SHALL maintain a template for PROOF-CERTIFICATE.md with predefined sections
6. THE Orchestrator SHALL provide the appropriate template to each agent when activated
7. THE Orchestrator SHALL validate that generated artifacts match the template structure

### Requirement 41: Configuration Management

**User Story:** As a user, I want to configure system settings, so that I can customize the BMAD system behavior.

#### Acceptance Criteria

1. THE Orchestrator SHALL read configuration from a file named "bmad-config.json" in the working directory
2. THE configuration file SHALL allow setting the preferred language (English or French)
3. THE configuration file SHALL allow setting the default LLM provider (Claude or GPT)
4. THE configuration file SHALL allow setting the minimum number of backtest trades required for GATE-04
5. THE configuration file SHALL allow setting the risk-free rate for Sharpe_Ratio calculation
6. THE configuration file SHALL allow setting the number of Monte_Carlo_Simulation iterations
7. IF the configuration file does not exist, THEN THE Orchestrator SHALL create it with default values
8. THE Orchestrator SHALL validate configuration values and reject invalid settings with error messages

### Requirement 42: Audit Trail Generation

**User Story:** As a compliance officer, I want a complete audit trail, so that I can verify the development process was followed correctly.

#### Acceptance Criteria

1. THE Orchestrator SHALL maintain an audit trail recording all phase transitions with timestamps
2. THE Orchestrator SHALL record all gate validations with pass/fail results and timestamps
3. THE Orchestrator SHALL record all user commands with timestamps
4. THE Orchestrator SHALL record all artifact generations with version numbers and timestamps
5. THE Orchestrator SHALL record all rollback operations with timestamps
6. THE Orchestrator SHALL save the audit trail to a file named "AUDIT-TRAIL.md"
7. WHEN the "/audit" command is executed, THE Orchestrator SHALL display the complete audit trail

### Requirement 43: Risk Management Code Generation

**User Story:** As the CODER, I need to implement risk management rules precisely, so that position sizing and stop losses are enforced correctly.

#### Acceptance Criteria

1. THE CODER SHALL implement position sizing based on risk percentage per trade as specified in STRATEGY_SPEC
2. THE CODER SHALL implement stop loss placement based on ATR, fixed points, or percentage as specified in STRATEGY_SPEC
3. THE CODER SHALL implement take profit placement based on risk-reward ratio or fixed points as specified in STRATEGY_SPEC
4. THE CODER SHALL implement maximum daily loss limits if specified in STRATEGY_SPEC
5. THE CODER SHALL implement maximum open positions limits if specified in STRATEGY_SPEC
6. THE CODER SHALL implement trading time filters if specified in STRATEGY_SPEC
7. THE CODER SHALL validate that risk management code prevents position sizes exceeding account balance

### Requirement 44: Trailing Stop Implementation

**User Story:** As the CODER, I need to implement trailing stops, so that profits can be protected as trades move favorably.

#### Acceptance Criteria

1. WHERE trailing stops are specified in STRATEGY_SPEC, THE CODER SHALL implement trailing stop logic
2. THE CODER SHALL implement ATR-based trailing stops if specified
3. THE CODER SHALL implement fixed-point trailing stops if specified
4. THE CODER SHALL implement percentage-based trailing stops if specified
5. THE CODER SHALL ensure trailing stops only move in the favorable direction
6. THE CODER SHALL implement trailing stop activation based on minimum profit threshold if specified
7. THE CODER SHALL use platform-specific trailing stop functions where available

### Requirement 45: Filter Implementation

**User Story:** As the CODER, I need to implement filters that prevent trades under unfavorable conditions, so that the strategy only trades when conditions are optimal.

#### Acceptance Criteria

1. WHERE filters are specified in STRATEGY_SPEC, THE CODER SHALL implement filter logic that must pass before entry signals are executed
2. THE CODER SHALL implement trend filters based on moving averages if specified
3. THE CODER SHALL implement volatility filters based on ATR if specified
4. THE CODER SHALL implement time-of-day filters if specified
5. THE CODER SHALL implement day-of-week filters if specified
6. THE CODER SHALL implement news event filters if specified
7. THE CODER SHALL ensure that all filters must pass before a trade is allowed

### Requirement 46: State Machine Validation

**User Story:** As the QUANT, I need to validate the state machine, so that the strategy logic has no unreachable states or infinite loops.

#### Acceptance Criteria

1. WHEN generating the LOGIC_MODEL, THE QUANT SHALL verify that all states in the state machine are reachable from the initial state
2. THE QUANT SHALL verify that all states have at least one exit transition
3. THE QUANT SHALL verify that terminal states are clearly identified
4. THE QUANT SHALL verify that all transition conditions are mutually exclusive or prioritized
5. THE QUANT SHALL verify that no state has transitions that could cause infinite loops without exit conditions
6. IF validation fails, THEN THE QUANT SHALL report the specific issue and request clarification from the ANALYST

### Requirement 47: Truth Table Generation

**User Story:** As the QUANT, I need to generate truth tables for complex conditions, so that all logical combinations are explicitly documented.

#### Acceptance Criteria

1. WHEN a rule has multiple boolean conditions combined with AND/OR operators, THE QUANT SHALL generate a truth table
2. THE truth table SHALL list all input variables as columns
3. THE truth table SHALL list all possible input combinations as rows
4. THE truth table SHALL include an output column showing the result for each combination
5. THE truth table SHALL be formatted in Markdown table syntax
6. THE QUANT SHALL verify that the truth table covers all 2^n combinations where n is the number of boolean inputs
7. THE QUANT SHALL include the truth table in the LOGIC_MODEL artifact

### Requirement 48: Variable Definition Standards

**User Story:** As the QUANT, I need to define all variables precisely, so that the CODER can implement them correctly.

#### Acceptance Criteria

1. THE QUANT SHALL define each variable with a name, type, range, unit, and initial value
2. THE QUANT SHALL use types: INTEGER, FLOAT, BOOLEAN, STRING, PRICE, VOLUME, or DATETIME
3. THE QUANT SHALL specify numeric ranges in the format [min, max] or (min, max) for exclusive bounds
4. THE QUANT SHALL specify units for price (pips, points, currency), time (seconds, minutes, bars), and percentage values
5. THE QUANT SHALL identify which variables are inputs (configurable) versus calculated (derived)
6. THE QUANT SHALL include all variable definitions in a dedicated section of the LOGIC_MODEL
7. THE QUANT SHALL ensure variable names are descriptive and follow lowercase_with_underscores convention

### Requirement 49: Indicator Calculation Specifications

**User Story:** As the QUANT, I need to specify indicator calculations precisely, so that the CODER implements them correctly across all platforms.

#### Acceptance Criteria

1. WHEN an indicator is used in the strategy, THE QUANT SHALL specify the exact calculation formula
2. THE QUANT SHALL specify the period/length parameter for each indicator
3. THE QUANT SHALL specify the price input (close, open, high, low, typical, weighted) for each indicator
4. THE QUANT SHALL specify how the indicator handles the initial bars where insufficient data exists
5. THE QUANT SHALL specify any smoothing or averaging methods used
6. THE QUANT SHALL reference standard indicator definitions (e.g., Wilder's RSI, Exponential Moving Average)
7. WHERE custom indicators are used, THE QUANT SHALL provide the complete calculation formula step-by-step

### Requirement 50: Entry Signal Logic Specification

**User Story:** As the QUANT, I need to specify entry signal logic precisely, so that the CODER implements exact entry conditions.

#### Acceptance Criteria

1. THE QUANT SHALL specify entry conditions as boolean expressions using defined variables and indicators
2. THE QUANT SHALL specify whether entry signals are evaluated on bar close or tick-by-tick
3. THE QUANT SHALL specify whether multiple entries are allowed or only one position at a time
4. THE QUANT SHALL specify entry signal priority if multiple signals can occur simultaneously
5. THE QUANT SHALL specify whether entry requires confirmation over multiple bars
6. THE QUANT SHALL specify separate logic for long and short entries
7. THE QUANT SHALL include entry signal logic in the LOGIC_MODEL with Rule_ID references

### Requirement 51: Exit Signal Logic Specification

**User Story:** As the QUANT, I need to specify exit signal logic precisely, so that the CODER implements exact exit conditions.

#### Acceptance Criteria

1. THE QUANT SHALL specify exit conditions as boolean expressions using defined variables and indicators
2. THE QUANT SHALL specify whether exits are evaluated on bar close or tick-by-tick
3. THE QUANT SHALL specify exit priority when multiple exit conditions are met simultaneously
4. THE QUANT SHALL specify separate logic for stop loss, take profit, and signal-based exits
5. THE QUANT SHALL specify whether partial exits are allowed
6. THE QUANT SHALL specify time-based exit conditions if applicable
7. THE QUANT SHALL include exit signal logic in the LOGIC_MODEL with Rule_ID references

### Requirement 52: Code Compilation Verification

**User Story:** As the CODER, I need to verify that generated code compiles, so that syntax errors are caught before testing.

#### Acceptance Criteria

1. WHERE the target platform is MT4, THE CODER SHALL verify that generated MQL4 code compiles without errors using MetaEditor or equivalent
2. WHERE the target platform is MT5, THE CODER SHALL verify that generated MQL5 code compiles without errors using MetaEditor or equivalent
3. WHERE the target platform is Pine_Script, THE CODER SHALL verify that generated Pine Script code passes TradingView syntax validation
4. IF compilation fails, THEN THE CODER SHALL analyze the error messages and regenerate the code with corrections
5. THE CODER SHALL attempt compilation up to 3 times before reporting failure to the Orchestrator
6. THE CODER SHALL log all compilation errors and corrections to the audit trail

### Requirement 53: Code Comment Standards

**User Story:** As the CODER, I need to include comprehensive comments, so that generated code is maintainable and understandable.

#### Acceptance Criteria

1. THE CODER SHALL include a file header comment with strategy name, description, version, generation date, and BMAD system version
2. THE CODER SHALL include a traceability comment before each function in the format "// Rule_ID: R-XXX - [description]"
3. THE CODER SHALL include inline comments explaining complex calculations
4. THE CODER SHALL include comments documenting input parameters with their valid ranges
5. THE CODER SHALL include comments documenting the purpose of each major code section
6. THE CODER SHALL include comments documenting any platform-specific workarounds or limitations
7. THE CODER SHALL use the platform's standard comment syntax (// for single-line, /* */ for multi-line)

### Requirement 54: Integration Test Scenario Library

**User Story:** As the TESTER, I need predefined test scenarios, so that integration testing is comprehensive and consistent.

#### Acceptance Criteria

1. THE TESTER SHALL maintain a library of at least 10 predefined market scenarios
2. THE scenario library SHALL include trending up scenarios with strong momentum
3. THE scenario library SHALL include trending down scenarios with strong momentum
4. THE scenario library SHALL include ranging/sideways scenarios with low volatility
5. THE scenario library SHALL include high volatility scenarios with large price swings
6. THE scenario library SHALL include gap scenarios with price discontinuities
7. THE scenario library SHALL include scenarios with false breakouts
8. THE scenario library SHALL include scenarios with sustained trends
9. THE scenario library SHALL include scenarios with trend reversals
10. THE scenario library SHALL include scenarios with low liquidity conditions
11. Each scenario SHALL include expected strategy behavior (entry, exit, or no trade)

### Requirement 55: Test Data Management

**User Story:** As the TESTER, I need access to historical market data, so that backtesting and robustness testing can be performed.

#### Acceptance Criteria

1. THE TESTER SHALL support importing historical data in CSV format with columns: timestamp, open, high, low, close, volume
2. THE TESTER SHALL validate that imported data has no missing bars or gaps
3. THE TESTER SHALL validate that imported data has consistent timeframes
4. THE TESTER SHALL support multiple timeframes: M1, M5, M15, M30, H1, H4, D1
5. THE TESTER SHALL support multiple instruments: forex pairs, stocks, commodities, cryptocurrencies
6. IF data quality issues are detected, THEN THE TESTER SHALL report the specific issues and request corrected data
7. THE TESTER SHALL cache imported data to improve performance for repeated tests

### Requirement 56: Equity Curve Generation

**User Story:** As the TESTER, I need to generate equity curves, so that visual performance analysis is available.

#### Acceptance Criteria

1. WHEN backtesting is complete, THE TESTER SHALL generate an equity curve showing account balance over time
2. THE equity curve SHALL plot time on the x-axis and account balance on the y-axis
3. THE equity curve SHALL mark entry points with green markers
4. THE equity curve SHALL mark exit points with red markers
5. THE equity curve SHALL highlight drawdown periods with shaded regions
6. THE equity curve SHALL include a horizontal line showing the initial capital
7. THE TESTER SHALL save the equity curve as an image file named "[strategy_name]_equity_curve.png"
8. THE TESTER SHALL embed the equity curve image in the TEST-REPORT artifact

### Requirement 57: Trade Distribution Analysis

**User Story:** As the TESTER, I need to analyze trade distribution, so that I can identify patterns in wins and losses.

#### Acceptance Criteria

1. WHEN backtesting is complete, THE TESTER SHALL generate a histogram showing the distribution of trade returns
2. THE histogram SHALL use bins of appropriate size based on the range of returns
3. THE histogram SHALL use green bars for positive returns and red bars for negative returns
4. THE TESTER SHALL calculate and display the mean trade return on the histogram
5. THE TESTER SHALL calculate and display the median trade return on the histogram
6. THE TESTER SHALL identify outlier trades (returns beyond 2 standard deviations)
7. THE TESTER SHALL save the histogram as an image file named "[strategy_name]_trade_distribution.png"
8. THE TESTER SHALL embed the histogram image in the TEST-REPORT artifact

### Requirement 58: Performance Metric Thresholds

**User Story:** As the AUDITOR, I need defined thresholds for performance metrics, so that scoring is objective and consistent.

#### Acceptance Criteria

1. THE AUDITOR SHALL use the following thresholds for Edge axis scoring: Profit_Factor >= 2.0 and Win_Rate >= 50% = 4 points, Profit_Factor >= 1.5 and Win_Rate >= 45% = 3 points, Profit_Factor >= 1.2 and Win_Rate >= 40% = 2 points, Profit_Factor >= 1.0 and Win_Rate >= 35% = 1 point, otherwise 0 points
2. THE AUDITOR SHALL use the following thresholds for Risk axis scoring: Sharpe_Ratio >= 2.0 and Maximum_Drawdown <= 10% = 4 points, Sharpe_Ratio >= 1.5 and Maximum_Drawdown <= 15% = 3 points, Sharpe_Ratio >= 1.0 and Maximum_Drawdown <= 20% = 2 points, Sharpe_Ratio >= 0.5 and Maximum_Drawdown <= 30% = 1 point, otherwise 0 points
3. THE AUDITOR SHALL use the following thresholds for Robustness axis scoring: Walk_Forward consistency >= 80% and Monte_Carlo 5th percentile positive = 4 points, Walk_Forward consistency >= 70% and Monte_Carlo 5th percentile >= -10% = 3 points, Walk_Forward consistency >= 60% and Monte_Carlo 5th percentile >= -20% = 2 points, Walk_Forward consistency >= 50% = 1 point, otherwise 0 points
4. THE AUDITOR SHALL use the following thresholds for Compliance axis scoring: 100% traceability and all gates passed = 3 points, 90% traceability and all gates passed = 2 points, 80% traceability = 1 point, otherwise 0 points
5. THE AUDITOR SHALL use the following thresholds for Exploitability axis scoring: Trade frequency 20-100 per year and low parameter sensitivity = 3 points, Trade frequency 10-200 per year and moderate parameter sensitivity = 2 points, Trade frequency 5-300 per year = 1 point, otherwise 0 points

### Requirement 59: Post-Certification Monitoring Plan

**User Story:** As the AUDITOR, I need to define a monitoring plan, so that live performance can be tracked against expectations.

#### Acceptance Criteria

1. WHERE certification status is CERTIFIED or CONDITIONAL, THE AUDITOR SHALL define a monitoring plan in the PROOF-CERTIFICATE
2. THE monitoring plan SHALL specify the review frequency (daily, weekly, or monthly)
3. THE monitoring plan SHALL specify which metrics to monitor: Win_Rate, Profit_Factor, Maximum_Drawdown, and Sharpe_Ratio
4. THE monitoring plan SHALL specify acceptable deviation ranges for each monitored metric
5. THE monitoring plan SHALL specify actions to take if metrics deviate beyond acceptable ranges
6. THE monitoring plan SHALL specify a minimum number of trades before statistical significance can be assessed
7. THE monitoring plan SHALL specify a recertification schedule (quarterly, semi-annually, or annually)

### Requirement 60: Documentation Export

**User Story:** As a trader, I want comprehensive documentation in the deployment package, so that I understand how to deploy and monitor the strategy.

#### Acceptance Criteria

1. WHEN creating the deployment package, THE Orchestrator SHALL generate a README.md file
2. THE README.md SHALL include an overview of the strategy
3. THE README.md SHALL include deployment instructions for each target platform
4. THE README.md SHALL include the Emergency_Stop_Criteria from the PROOF-CERTIFICATE
5. THE README.md SHALL include the monitoring plan from the PROOF-CERTIFICATE
6. THE README.md SHALL include contact information for support
7. THE README.md SHALL include the certification status and date
8. THE README.md SHALL include a disclaimer about trading risks

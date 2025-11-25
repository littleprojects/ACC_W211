# Safety

To fulfill automotive safety standards, this project follows the principles of ISO 26262.

---

## ISO 26262 – Key Definitions

- **Safety**: Absence of unreasonable risk.  
- **Functional Safety**: Absence of unreasonable risk due to hazards caused by malfunctioning behavior of E/E systems.  
- **Malfunctioning Behavior**: Failure or unintended behavior of an item with respect to its design intent.  
- **Hazard**: Potential source of harm caused by malfunctioning behavior.  
- **Hazardous Event**: Combination of a hazard and an operational situation.  
- **Risk**: Combination of the probability of occurrence of harm and the severity of that harm.  

---

## HARA – Hazard Analysis and Risk Assessment

HARA is the method used to identify and categorize hazardous events of items, and to specify safety goals and ASILs related to the prevention or mitigation of associated hazards, in order to avoid unreasonable risk.

- **ASIL** – Automotive Safety Integrity Level  

---

### Item Definition

The item in this project is an ECU capable of manipulating longitudinal vehicle dynamics.  
Key functions include:  
- Acceleration (via throttle pedal)  
- Deceleration (via braking)  

The ECU applies to the following systems:  
- Cruise Control  
- Adaptive Cruise Control (ACC) with radar sensor  
- Speed Limiter  

---

### Situation Analysis

Operational situations considered:  
- Parking  
- Low-speed driving  
- High-speed driving  
- Cornering  

---

### Determination of Hazards

Potential hazards include:  
- **Drop-out group**  
  - Software crash  
  - Connection failure  
  - Hardware failure  
- Unexpected acceleration  
- Unexpected deceleration  

---

### Determination of Hazardous Events

Hazardous events are defined as combinations of operational situations and hazards, with their potential consequences.  
Detailed event determination will be performed in later stages of analysis.  

---

### Classification of Hazardous Events

Hazardous events are classified according to:  
- **Severity** – from no injuries to fatal outcomes  
- **Exposure** – from incredible (very rare) to high probability  
- **Controllability** – from generally controllable to difficult or uncontrollable  
- **System Stability** – ability of the system to maintain safe operation  

---

### ASIL Determination

ASIL ratings range from **A** (least stringent) to **D** (most stringent).  
Higher ASIL levels require more rigorous hardware, software, and testing measures.  

---

### Risk Assessment

- **Parking**  
  - Drop-out → no risk  
  - Acceleration → no risk (vehicle typically in P, controllable via braking)  
  - Deceleration → no risk  

- **Low-speed driving**  
  - Drop-out → no risk, controllable  
  - Acceleration → low risk, controllable via braking  
  - Deceleration → low risk, controllable via pedal  

- **High-speed driving**  
  - Drop-out → low risk, controllable  
  - Acceleration → high risk → requires safety measures  
  - Deceleration → high risk → requires safety measures  

- **Cornering**  
  - Drop-out → low risk, controllable  
  - Acceleration → high risk → requires safety measures  
  - Deceleration → high risk → requires safety measures  

---

## Safety Goals

Safety measures are required to make high-risk scenarios controllable and reduce risks to acceptable levels.

Countermeasures for unexpected acceleration or deceleration:  
- Implementation of shutdown / switch-off functions (via braking, dedicated Off button, or error detection).  
- Implementation of driver override functions (pedal inputs always take priority).  
- Limitation of maximum acceleration and deceleration torque.  
- Limitation of acceleration and deceleration rates (jerk control).  

Vehicle-level support:  
- If the system drops out (no CAN messages for a short time), ACC shall be automatically disabled.  
- Pedal commands (throttle or braking) shall always override ACC.  
- Vehicle subsystems (ABS, ESP) shall support controllability in critical 
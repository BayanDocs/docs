# WBN-NNNN: Short title

- **Status:** Draft | Confirmed | Superseded by WBN-NNNN
- **Question:** one precise question
- **Word build(s) observed:** e.g. Microsoft 365 Current Channel, version and build number
- **Compatibility modes covered:** e.g. 15; 14 (not yet: 12, 11)
- **Fonts used:** families and file hashes on the reference machine
- **Confidence:** High (rule explains every observation) | Medium | Low
- **Related:** work packages, other notes, engine modules

## Why it matters

Which documents and features this affects, and how badly layout diverges if we get it wrong.

## Probes

Description of the generated probe set: which parameter varies, its range and step, and where the probe documents and generator settings are stored (T0 corpus identifiers).

## Observations

Tables or charts of Word's ground truth for the probes: positions, break points, heights. Link to the stored artifacts.

## Rule

The behavior, stated precisely enough to implement, with formulas in BLU or the units Word appears to use, and the rounding at each step.

## Counter-examples and limits

Anything the rule does not explain yet; conditions under which it was not tested.

## Implementation and tests

Engine module that implements the rule; tests and T0 probes that lock it in.

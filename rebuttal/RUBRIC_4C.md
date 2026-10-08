# Task 4c labelling rubric (committed before any site is read)

Operationalises PREREG_R1.md section 4c. The question for each site is whether a
falsy or degenerate value (NaN, None, empty collection, zero that stands for
"missing") can reach it under supported use and silently change the output.

| Label | Rule |
|---|---|
| GUARDED | An explicit NaN / None / emptiness check dominates the site in the same function, or the language raises on the degenerate input (for example `max([])` raises ValueError), so the failure is loud rather than silent. |
| UNREACHABLE | The degenerate input is excluded by construction or by the configuration the repository ships with (a collection built non-empty, a constant, an asserted precondition, a fixed config). |
| REACHABLE_UNGUARDED | A degenerate input is possible under supported use AND, if it occurs, the result changes silently (for example `any([])` is False so a check passes, `all([])` is True, a NaN first element wins or loses a comparison, a missing key set is taken from the first element). |
| NOT_APPLICABLE | The matched pattern involves no value that can be degenerate in this sense (loop counters, shapes, string handling, literal constants), or the site does not feed a verdict, selection or aggregation. |

## Rules

1. Decide from the file and the configuration it ships with, reading other files
   when needed and citing them. If it cannot be established, use the more
   cautious label: UNREACHABLE only when exclusion is demonstrated, otherwise
   REACHABLE_UNGUARDED only when silent change is demonstrated; an undecidable
   site is recorded as NOT_APPLICABLE with the note "undecidable" and counted
   separately in the report.
2. A site where a degenerate input would crash is GUARDED, not
   REACHABLE_UNGUARDED.
3. Report per repository and overall; the REACHABLE_UNGUARDED proportion carries
   a Wilson 95% interval; every positive is listed with file, line and pinned
   SHA. Repositories searched with nothing found stay in the table.
4. Labels are the labeller's judgement from the code; a quarter are relabelled
   in a fresh pass and six go to the user.

# Refinery Presentation Audit

## Implemented Boundary

Current State, Regimes, Symptoms, Canada, Food, Housing and Affordability now resolve structured geography/topic evidence through the generated `presentation-manifest.json`. Their current interpretation, confidence, coverage, evidence rows and observation dates originate in the Python pipeline. Flat aliases such as `current_state_canada` and `symptoms_us` have been replaced by canonical keys such as `canada:current-state` and `us:symptoms`.

The Canadian diagnostic narrative is generated from the current regime and symptoms whose status is active, emerging or fading. Inactive and insufficient-data symptoms remain available in detailed rule outputs but are excluded from the top diagnostic narrative.

## Stable Copy

Page titles, glossary definitions, control labels, methodology headings and explanations of concepts such as z-scores are stable educational interface copy. They do not describe the current data state and may remain in TypeScript or move to a future content catalogue for editorial consistency.

## Remaining Migration Work

Several research pages still contain stable statements of already validated historical findings in their headers or section introductions. Those statements are not live classifications, but they should eventually reference generated model-card or findings contracts so publication wording cannot drift from the research outputs.

Priority candidates are Liquidity, Physical Market, Oil Prices, Equities, Economy, Energy Burden, Labour and Output Quality. The new presentation contract supports this migration without creating page-specific React logic.

# Citation ledger, v2

Checked 2026-11-03 and 2026-11-04 by opening the primary page (publisher, arXiv, ICLR, ACM) or the Crossref record for
the DOI. Status follows `paper-citation-verification`: VERIFIED (metadata matched and the supporting passage was
located in the text on the page), METADATA-ONLY (the record exists and its metadata matched; usable only as an existence
or definition pointer), REMOVED. A second pass by another reader is still to do and is listed at the end.

Author lists: where the source has more than about ten authors the bib file gives the first authors and "and others";
the full count is in the Notes column.

| Key | Source opened | Status | Supports (and the passage) | Notes |
|---|---|---|---|---|
| damour2022underspecification | jmlr.org/papers/v23/20-1335.html | VERIFIED | A pipeline is underspecified when it "can return many distinct predictors with equivalently strong test performance" (abstract) | JMLR 23(226):1-61, 2022; 36 authors |
| salaudeen2025misspecified | arxiv.org/abs/2504.00186 | VERIFIED | Derives conditions for a shift to reveal reliance on spurious features and audits leading OOD datasets (abstract) | Venue "Published in TMLR 08/25" taken from the arXiv comment; the TMLR page was not opened |
| geirhos2020shortcut | nature.com/articles/s42256-020-00257-z; Crossref | VERIFIED | Shortcuts are "decision rules that perform well on standard benchmarks but fail to transfer" (abstract) | Nat Mach Intell 2(11):665-673, 10 Nov 2020; 7 authors |
| oakdenrayner2020hidden | dl.acm.org/doi/10.1145/3368555.3384468 | VERIFIED | Hidden stratification: poor performance on unidentified subsets, effects over 20% relative (abstract) | ACM CHIL 2020, pp. 151-159, 2 Apr 2020; the ML4H 2019 extended abstract (arXiv:1909.12475) is a different version |
| kapoor2023leakage | cell.com/patterns/fulltext/S2666-3899(23)00159-9; Crossref | VERIFIED | Leakage "affects at least 294 studies across 17 fields" (bigger picture) | Patterns 4(9):100804, Sept 2023 |
| wynants2020prediction | bmj.com/content/369/bmj.m1328; Crossref abstract | VERIFIED with a correction | Final update: 545 of 606 prognostic models at high risk of bias; "Most published prediction model studies were poorly reported and at high risk of bias" | BMJ 369:m1328. The submitted text said "essentially none fit for clinical use"; the source does not say that, so the claim was rewritten. Living review, update 4 |
| roberts2021common | nature.com/articles/s42256-021-00307-0; Crossref | VERIFIED | "none of the models identified are of potential clinical use due to methodological flaws and/or underlying biases" (abstract; chest radiograph and CT models only) | Nat Mach Intell 3(3):199-217, 15 Mar 2021; 54 authors listed incl. a group author |
| singer2016sepsis3 | jamanetwork.com/journals/jama/fullarticle/2492881; Crossref | VERIFIED | The updated definitions and criteria; citation line "JAMA. 2016;315(8):801-810" | 19 authors |
| johnson2023mimiciv | Crossref | VERIFIED (metadata) | Dataset reference | Sci Data 10(1):1, 3 Jan 2023; 13 authors |
| pollard2018eicu | Crossref | VERIFIED (metadata) | Dataset reference | Sci Data 5:180178, 11 Sep 2018; 6 authors |
| reyna2020early | Crossref | VERIFIED (metadata) | Challenge dataset reference | Crit Care Med 48(2):210-217, Feb 2020; 8 authors |
| goldberger2000physiobank | ahajournals.org/doi/10.1161/01.cir.101.23.e215; Crossref | VERIFIED (metadata) | PhysioNet reference | Circulation 101(23), 13 Jun 2000; the end page "e220" was not on any page opened, so the bib gives e215 only |
| bellamy2019aif360 | Crossref (doi.org page not available) | VERIFIED (metadata) | The toolkit exists; its metrics and mitigation algorithms (arXiv abstract) | IBM J Res Dev 63(4/5):4:1-4:15, Jul 2019; arXiv v1 had a different subtitle |
| gulrajani2021search | iclr.cc/virtual/2021/poster/2998; arXiv abstract | VERIFIED | DomainBed with model selection criteria; ERM competitive (abstract) | ICLR 2021 poster |
| yang2022leakage | arxiv.org/abs/2209.03345 | VERIFIED | Static analysis to detect common forms of data leakage in notebooks (abstract); the three category names are from our own run of the tool | ASE 2022 per the round-1 ledger (programme page); arXiv v1 7 Sep 2022 |
| subotic2022leakage | microsoft.com Research publication page | VERIFIED | Static data-leakage analysis intended for development time (abstract) | SOAP 2022, June 2022 |
| kupferman2003vacuity | link.springer.com/article/10.1007/s100090100062; Crossref | VERIFIED | Suspecting an error when model checking succeeds; vacuous satisfaction; "Beer et al. described a method for the detection of vacuous satisfaction" (abstract) | STTT 4(2):224-233, Feb 2003; Kupferman and Vardi |
| beer1997vacuity | Crossref | METADATA-ONLY | Existence; the attribution of vacuity detection comes from the Kupferman and Vardi abstract | LNCS (CAV 1997) pp. 279-290; the volume number 1254 came from search results only and is not in the bib |
| cohen1960kappa | Crossref | METADATA-ONLY | Existence of the kappa statistic (definition pointer) | Educ Psychol Meas 20(1):37-46, Apr 1960 |

## Removed

- landis1977measurement: the attribution of the 0.60 boundary to this paper could not be checked in its full text. The paper
  now calls 0.60 a conventional threshold with no clinical derivation and does not cite it.
- mahajan2021domain: never cited in the text.
- Statements removed or rewritten because the source does not say them: "systematic reviews found essentially none fit for
  clinical use" (Wynants).

## Second pass still to do

Another reader reopens every URL above, rechecks metadata and the passage, and settles disagreements against the source.
Counts today: 19 entries; 17 VERIFIED (one of them, wynants2020prediction, with a correction to the claim),
2 METADATA-ONLY (beer1997vacuity, cohen1960kappa); 2 removed (landis1977measurement, mahajan2021domain).

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
| salaudeen2025misspecified | arxiv.org/abs/2504.00186 | VERIFIED | Derives conditions for a shift to reveal reliance on spurious features and audits leading OOD datasets (abstract) | Venue and year: arXiv comment "Published in TMLR 08/25" and NSF Public Access record (publisher TMLR, 2025); the TMLR page itself was not opened and the month is not given in the bib |
| geirhos2020shortcut | nature.com/articles/s42256-020-00257-z; Crossref | VERIFIED | Shortcuts are "decision rules that perform well on standard benchmarks but fail to transfer" (abstract) | Nat Mach Intell 2(11):665-673, 10 Nov 2020; 7 authors |
| oakdenrayner2020hidden | dl.acm.org/doi/10.1145/3368555.3384468 | VERIFIED | Hidden stratification: poor performance on unidentified subsets, effects over 20% relative (abstract) | ACM CHIL 2020, pp. 151-159, 2 Apr 2020; the ML4H 2019 extended abstract (arXiv:1909.12475) is a different version |
| kapoor2023leakage | cell.com/patterns/fulltext/S2666-3899(23)00159-9; Crossref | VERIFIED | Leakage "affects at least 294 studies across 17 fields" (bigger picture) | Patterns 4(9):100804, Sept 2023 |
| wynants2020prediction | bmj.com/content/369/bmj.m1328; Crossref abstract | VERIFIED with a correction | Final update: 545 of 606 prognostic models at high risk of bias; "Most published prediction model studies were poorly reported and at high risk of bias" | BMJ 369:m1328. The submitted text said "essentially none fit for clinical use"; the source does not say that, so the claim was rewritten. Living review, update 4 |
| roberts2021common | nature.com/articles/s42256-021-00307-0; Crossref | VERIFIED | "none of the models identified are of potential clinical use due to methodological flaws and/or underlying biases" (abstract; chest radiograph and CT models only) | Nat Mach Intell 3(3):199-217, 15 Mar 2021; 54 authors listed incl. a group author |
| singer2016sepsis3 | jamanetwork.com/journals/jama/fullarticle/2492881; Crossref | VERIFIED | The updated definitions and criteria; citation line "JAMA. 2016;315(8):801-810" | 19 authors |
| johnson2023mimiciv | Crossref | METADATA-ONLY | Dataset reference | Sci Data 10(1):1, 3 Jan 2023; 13 authors |
| pollard2018eicu | Crossref | METADATA-ONLY | Dataset reference | Sci Data 5:180178, 11 Sep 2018; 6 authors |
| reyna2020early | Crossref | METADATA-ONLY | Challenge dataset reference | Crit Care Med 48(2):210-217, Feb 2020; 8 authors |
| goldberger2000physiobank | ahajournals.org/doi/10.1161/01.cir.101.23.e215; Crossref | METADATA-ONLY | PhysioNet reference | Circulation 101(23), 13 Jun 2000; pages e215-e220 confirmed by the Europe PMC record (pageInfo E215-20), PMID 10851218 |
| bellamy2019aif360 | Crossref (doi.org page not available) | METADATA-ONLY | The toolkit exists; its metrics and mitigation algorithms (arXiv abstract) | IBM J Res Dev 63(4/5):4:1-4:15, Jul 2019; arXiv v1 had a different subtitle |
| gulrajani2021search | iclr.cc/virtual/2021/poster/2998; arXiv abstract | VERIFIED | DomainBed with model selection criteria; ERM competitive (abstract) | ICLR 2021 poster |
| yang2022leakage | arxiv.org/abs/2209.03345 | VERIFIED | Static analysis to detect common forms of data leakage in notebooks (abstract); the three category names are from our own run of the tool | Crossref (ACM, doi 10.1145/3551349.3556918): Proceedings of the 37th IEEE/ACM International Conference on Automated Software Engineering (ASE '22), pp. 1-12, 10 Oct 2022; arXiv v1 7 Sep 2022 |
| subotic2022leakage | microsoft.com Research publication page | VERIFIED | Static data-leakage analysis intended for development time (abstract) | SOAP 2022, June 2022 |
| kupferman2003vacuity | link.springer.com/article/10.1007/s100090100062; Crossref | VERIFIED | Suspecting an error when model checking succeeds; vacuous satisfaction; "Beer et al. described a method for the detection of vacuous satisfaction" (abstract) | STTT 4(2):224-233, Feb 2003; Kupferman and Vardi |
| beer1997vacuity | Springer chapter page, doi.org/10.1007/3-540-63166-6_28 (opened 2026-11-13); DBLP conf/cav/BeerBER97 | VERIFIED (abstract) | Defines a vacuous pass and extends vacuity to other trivial passes in temporal logic; shows how to detect it for w-ACTL (abstract: "We call this a vacuous pass") | LNCS 1254 (CAV 1997) pp. 279-290; four authors confirmed; full text not opened |
| schuirmann1987comparison | PubMed record PMID 3450848 (abstract read 2026-11-27) | VERIFIED (abstract) | Compares the two one-sided tests procedure with the power approach for assessing equivalence of average bioavailability, and states that it leads to the same conclusion as Westlake's approach based on the usual 1-2 alpha confidence interval (abstract) | D. J. Schuirmann, J Pharmacokinet Biopharm 15(6):657-680, Dec 1987, doi 10.1007/BF01068419; full text not opened; not yet cited in the paper |
| cohen1960kappa | Crossref | METADATA-ONLY | Existence of the kappa statistic (definition pointer) | Educ Psychol Meas 20(1):37-46, Apr 1960 |
| breck2017mltest | research.google pub page; Crossref (10.1109/BigData.2017.8258038) | VERIFIED | "we present 28 specific tests and monitoring needs" (abstract) | IEEE Big Data 2017, pp. 1123-1132; 5 authors |
| breck2019datavalidation | proceedings.mlsys.org abstract page and the paper PDF | VERIFIED | presents a data validation system that detects anomalies in data fed into ML pipelines, deployed in TFX at Google (abstract) | SysML 2019 (2nd SysML Conference); author order taken from the PDF title page (the proceedings page lists a different order) |
| chorev2022deepchecks | jmlr.org/papers/v23/22-0281.html | VERIFIED | a Python library for validating ML models and data (abstract) | JMLR 23(285):1-6, 2022; 10 authors |
| mchugh2012kappa | PMC3900052; Europe PMC record | VERIFIED | "Cohen's suggested interpretation may be too lenient for health related studies" (abstract) | Biochem Med 22(3):276-282, 2012 |
| cfr1607 | law.cornell.edu/cfr/text/29/1607.4 (eCFR mirror) | VERIFIED | paragraph D: a selection rate below four-fifths (80%) of the highest rate is generally regarded as evidence of adverse impact; larger differences resting on small numbers may not indicate it | regulation, no pagination; the eCFR page redirected to an unblock page and was not used |
| kearns2018gerrymandering | proceedings.mlr.press/v80/kearns18a.html | VERIFIED | classifiers fair on each pre-defined group can violate fairness on structured subgroups (abstract) | PMLR 80:2564-2572, 2018 |
| kerr1998harking | Europe PMC record (opened 2026-11-17) | VERIFIED | HARKing defined as presenting a post hoc hypothesis as if a priori (abstract on the Europe PMC record; read directly, full text not opened) | PSPR 2(3):196-217, 1998 |
| simmons2011falsepositive | Europe PMC record (opened 2026-11-17) | VERIFIED | flexibility in data collection and analysis raises false-positive rates (abstract on the Europe PMC record; read directly, full text not opened) | Psychol Sci 22(11):1359-1366, 2011 |
| zech2018variable | journals.plos.org page; Europe PMC record; PLOS Med primary page | VERIFIED | CNNs did better on internal than on outside hospital data in 3 of 5 comparisons and identified hospital system and department (abstract, primary PLOS page, opened 2026-11-17: "3 out of 5 natural comparisons"; "CNNs robustly identified hospital system and department") | PLOS Med 15(11):e1002683, 2018; 6 authors |
| degrave2021shortcuts | nature.com/articles/s42256-021-00338-7; Crossref | VERIFIED | systems rely on confounding factors rather than medical pathology (abstract) | Nat Mach Intell 3(7):610-619, 31 May 2021 |
| rhee2017sepsis | PMC5710396; Europe PMC record; Crossref | VERIFIED | clinical-criteria incidence +0.6% per year (flat), claims-based +10.3% per year (read twice with different questions) | JAMA 318(13):1241-1249, 2017; 20 authors plus a group |
| vincent1996sofa | Crossref | METADATA-ONLY | the SOFA score exists | Intensive Care Med 22(7):707-710, 1996; 9 authors |
| saeb2017usecase | Europe PMC record; Crossref | VERIFIED | record-wise cross-validation often massively overestimates accuracy; subject-wise mirrors the clinical use case (abstract) | GigaScience 6(5):1-9 (gix019), 2017 |
| dwork2015reusable | science.org/doi/10.1126/science.aaa9375 | VERIFIED | adaptive analysis risks false discoveries; a method to reuse a holdout safely (abstract) | Science 349(6248):636-638, 2015 |
| ding2021retiring | arxiv.org/abs/2108.04884; NeurIPS poster page; the NeurIPS proceedings PDF | VERIFIED | new datasets derived from US Census surveys for fair ML (abstract) | NeurIPS 2021 (Advances in Neural Information Processing Systems 34) |
| angwin2016machinebias | propublica.org article page | VERIFIED | article exists; byline order from the page | published 2016-05-23; accessed 2026-11-04 |
| ucicadult | archive.ics.uci.edu/dataset/2/adult | VERIFIED (page) | dataset page: donated 4/30/1996, 48,842 instances; the file we use is adult.data (32,561 rows) | no creator names on the page excerpt, so none are given |
| gardner2023tableshift | proceedings.neurips.cc 2023 Datasets and Benchmarks abstract page | VERIFIED | a distribution shift benchmark of 15 tabular tasks (abstract) | NeurIPS 2023 Datasets and Benchmarks Track |
| collegescorecard | collegescorecard.ed.gov/data/ | VERIFIED (page) | the most-recent institution-level file (24 MB zip) exists | file Most-Recent-Cohorts-Institution_11022026.zip; accessed 2026-11-04 |
| clopper1934confidence | Crossref | METADATA-ONLY | exact binomial confidence limits | Biometrika 26(4):404-413, 1934 |
| efron1979bootstrap | Crossref | METADATA-ONLY | the bootstrap | Ann Stat 7(1):1-26, 1979 |
| jia2011mutation | Crossref doi 10.1109/TSE.2010.62 (checked 2026-11-11) | VERIFIED | A survey of the development of mutation testing (title); cited only as the source of the idea of seeded faults | IEEE TSE 37(5):649-678, 2011; Jia, Harman |
| barr2015oracle | Crossref doi 10.1109/TSE.2014.2372785 (checked 2026-11-11) | VERIFIED | A survey of the oracle problem in software testing (title); cited only for the problem of deciding that an output is correct | IEEE TSE 41(5):507-525, 2015; Barr, Harman, McMinn, Shahbaz, Yoo |
| rabanser2019failing | arxiv.org/abs/1810.11953 v4 (checked 2026-11-11) | VERIFIED | ML systems "tend to fail silently" on unexpected inputs; the paper studies methods for detecting dataset shift (abstract) | arXiv comment: NeurIPS 2019; Rabanser, Guennemann, Lipton; NeurIPS volume 32. Abstract level only; the paper's claim stays at that level |
| wolff2019probast | Europe PMC index record for DOI 10.7326/M18-1376 (opened 2026-11-19; the publisher page returned 403) | METADATA-ONLY | A tool to assess risk of bias and applicability of prediction model studies (title; abstract: "a tool for assessing the risk of bias (ROB) and applicability") | Ann Intern Med 170(1):51-58, Jan 2019; 9 authors plus a group author; cited as an existence pointer |
| collins2024tripodai | Europe PMC index record for DOI 10.1136/bmj-2023-078378 (2026-11-19; publisher 403) | METADATA-ONLY | Updated guidance for reporting clinical prediction models (title); no abstract on the record | BMJ 385:e078378, Apr 2024; 34 authors; existence pointer |
| mongan2020claim | Europe PMC index record for DOI 10.1148/ryai.2020200029 (2026-11-19; publisher 403) | METADATA-ONLY | A checklist and guide for authors and reviewers on AI in medical imaging (title); the index lists it as an editorial; no abstract | Radiol Artif Intell 2(2):e200029, Mar 2020; existence pointer |

## Removed

- landis1977measurement: the attribution of the 0.60 boundary to this paper could not be checked in its full text. The paper
  now calls 0.60 a conventional threshold with no clinical derivation and does not cite it.
- mahajan2021domain: never cited in the text.
- Statements removed or rewritten because the source does not say them: "systematic reviews found essentially none fit for
  clinical use" (Wynants).

## Second pass still to do

Another reader reopens every URL above, rechecks metadata and the passage, and settles disagreements against the source.
Counts on 2026-11-04 before the sweep: 19 entries; 17 VERIFIED (one of them, wynants2020prediction, with a correction to the claim),
2 METADATA-ONLY (beer1997vacuity, cohen1960kappa; beer1997vacuity upgraded on 2026-11-13); 2 removed (landis1977measurement, mahajan2021domain).

## Pass of 2026-11-17

Zech, Kerr and Simmons were re-read on the primary or Europe PMC record instead of a summarizer, and their entries now say so. Entries that were checked only at the level of record metadata and are cited as dataset or method pointers are relabelled METADATA-ONLY (Johnson, Pollard, Reyna, Goldberger, Vincent, Clopper and Pearson, Efron, Bellamy; Cohen was already). Counts: 46 entries, 34 VERIFIED, 12 METADATA-ONLY (all existence or dataset pointers), 0 unverified.

## Second pass, 2026-11-04 (same reader, different routes)

Rechecked by a second route: Goldberger (Europe PMC, pages); Yang et al. (ACM record via Crossref: proceedings title, pages, date);
Salaudeen et al. (NSF Public Access record). Claims in the text were rechecked against the abstracts: the Sepsis-3 sentence
now attributes only the criteria to Singer et al.; window scoring is described as ours. Still open: an independent second reader
(a person other than the drafter), and the TMLR page for Salaudeen et al.

## Sweep of 2026-11-04 (related topics and data sources)

Added 21 entries: testing and validating ML systems (Breck 2017, Breck 2019, Chorev 2022), thresholds as conventions (McHugh 2012,
29 CFR 1607.4), granularity and adaptive reuse (Saeb 2017, Kearns 2018, Dwork 2015), post hoc rules (Kerr 1998, Simmons 2011), clinical
confounds and labels (Zech 2018, DeGrave 2021, Rhee 2017, Vincent 1996), data sources (Ding 2021, Angwin 2016, UCI Adult, Gardner 2023,
College Scorecard) and statistics (Clopper and Pearson 1934, Efron 1979). Total 43 entries: 42 VERIFIED (of which Vincent, Clopper and
Pearson, Efron, Johnson, Pollard, Reyna, Goldberger, Singer are metadata-level checks of a dataset or method reference), 1 METADATA-ONLY
(cohen1960kappa). Summarizer-read abstracts (Kerr, Simmons, Zech) have exact Crossref or Europe PMC metadata but their
abstracts were read through a summarizer; the paper's claims about them stay at the level of the abstract. `v2/scripts/cite_check.py`
confirms that every cited key is in the bibliography, every entry is cited, and every entry has a row here.
| lipsitch2010negative | PubMed record PMID 20335814 (opened 2026-11-25; PMC full text PMC3053408 exists, abstract read) | VERIFIED | negative controls detect confounding and other sources of error in observational studies | abstract | "negative controls help to identify and resolve confounding as well as other sources of error" (paraphrase of abstract; authors Lipsitch, Tchetgen Tchetgen, Cohen; Epidemiology 21(3):383-388, May 2010; DOI 10.1097/EDE.0b013e3181d61eeb) | 2026-11-25 |
| feinstein1990high | PubMed record PMID 2348207 (opened 2026-11-25; DOI resolves, publisher page not readable) | VERIFIED | kappa depends on the marginal totals of the agreement table (high observed agreement can give low kappa under marginal imbalance) | abstract | "a high value of p0 can be drastically lowered by a substantial imbalance in the table's marginal totals" | J Clin Epidemiol 43(6):543-549, 1990; DOI 10.1016/0895-4356(90)90158-L; abstract only, so the claim is limited to the abstract's statement | 2026-11-25 |
| adebayo2018sanity | arXiv abs 1810.03292 v3, arXiv HTML read in part (about 59% verbatim), NeurIPS abstract page (opened 2026-11-25) | VERIFIED | model-parameter and data randomization tests show some saliency methods are independent of the model and data | abstract; Sections 1, 3, 4 | "some existing saliency methods are independent both of the model and of the data generating process" | NeurIPS 31, 2018; authors Adebayo, Gilmer, Muelly, Goodfellow, Hardt, Kim; arXiv v3 updates the Guided Backprop experiments, conclusions unchanged | 2026-11-25 |

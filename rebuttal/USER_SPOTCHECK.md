# Spot check for the user: Task 3b labels

Six of the 53 sampled sites, chosen at random (seed 20261008). Please label each
independently using the rubric below, from the code shown (and the repository file if you
need more context), WITHOUT looking at `rebuttal/results/task3b_labels.json`. Then tell me
your six labels; I will report percent agreement.

Labels: CONTAMINATED, DISCLOSED_ORACLE, AMBIGUOUS, SOUND, NOT_SELECTION. Rules are in
`rebuttal/RUBRIC_3B.md`. In one line: CONTAMINATED = the same held-out / OOD / test split drives
the selection and is the split of the number reported as held-out or zero-shot;
SOUND = selection on train or source validation, reported on another split;
NOT_SELECTION = the pattern matched but nothing is being chosen; AMBIGUOUS = cannot be
established from the file and its shipped configuration.

## Site 1: MIMIC-IV-Data-Pipeline @ 43ff2393da, `model/behrt_train.py` lines 215-219

```python
  209                 train_loss, train_time_cost = run_epoch(e, trainload, device)
  210                 val_loss, val_time_cost,pred, label = eval(valload, False, device)
  211                 train_loss = train_loss / math.ceil((train_params["train_data_len"] / train_params['batch_size']))
  212                 val_loss = val_loss / math.ceil((train_params["val_data_len"] / train_params['batch_size']))
  213                 print('TRAIN {}\t{} secs\n'.format(train_loss, train_time_cost))
  214                 print('EVAL {}\t{} secs\n'.format(val_loss, val_time_cost))
  215                 if val_loss < best_val:
  216                     print("** ** * Saving fine - tuned model ** ** * ")
  217                     model_to_save = behrt.module if hasattr(behrt, 'module') else behrt
  218                     save_model(model_to_save.state_dict(), './saved_models/checkpoint/behrt')
  219                     best_val = val_loss
  220             return train_loss, val_loss
  221 
  222 
  223         #%%
```

Your label: ______
Selection split / reported split: ______

## Site 2: HIRID-ICU-Benchmark @ bee770094b, `icu_benchmarks/synthetic_data/collect_stats.py` lines 35-35

```python
   29 
   30 
   31 def _collect_variable_stats(df, grp_var, val_var) -> pyspark.sql.DataFrame:
   32     return df.groupby(grp_var).agg(sf.mean(val_var).alias('mean'),
   33                                    sf.stddev(val_var).alias('standard_deviation'),
   34                                    sf.count(val_var).alias('count'),
   35                                    sf.min(val_var).alias('min'),
   36                                    sf.max(val_var).alias('max'),
   37                                    (sf.sum(sf.col(val_var) - sf.floor(val_var)).alias(
   38                                        'rounding_remainders')))
   39 
```

Your label: ______
Selection split / reported split: ______

## Site 3: MIMIC-IV-Data-Pipeline @ 43ff2393da, `preprocessing/hosp_module_preproc/feature_selection_icu.py` lines 169-223

```python
  163         summary=summary.fillna(0)
  164         summary.to_csv('./data/summary/chart_summary.csv',index=False)
  165         summary['itemid'].to_csv('./data/summary/chart_features.csv',index=False)
  166 
  167     print("[SUCCESSFULLY SAVED FEATURE SUMMARY]")
  168     
  169 def features_selection_icu(cohort_output, diag_flag,proc_flag,med_flag,out_flag,chart_flag,group_diag,group_med,group_proc,group_out,group_chart):
  170     if diag_flag:
  171         if group_diag:
  172             print("[FEATURE SELECTION DIAGNOSIS DATA]")
  173             diag = pd.read_csv("./data/features/preproc_diag_icu.csv.gz", compression='gzip',header=0)
  174             features=pd.read_csv("./data/summary/diag_features.csv",header=0)
  175             diag=diag[diag['new_icd_code'].isin(features['new_icd_code'].unique())]
  176         
  177             print("Total number of rows",diag.shape[0])
  178             diag.to_csv("./data/features/preproc_diag_icu.csv.gz", compression='gzip', index=False)
  179             print("[SUCCESSFULLY SAVED DIAGNOSIS DATA]")
  180     
  181     if med_flag:       
  182         if group_med:   
  183             print("[FEATURE SELECTION MEDICATIONS DATA]")
  184             med = pd.read_csv("./data/features/preproc_med_icu.csv.gz", compression='gzip',header=0)
  185             features=pd.read_csv("./data/summary/med_features.csv",header=0)
  186             med=med[med['itemid'].isin(features['itemid'].unique())]
  187             print("Total number of rows",med.shape[0])
```

Your label: ______
Selection split / reported split: ______

## Site 4: TPC-LoS-prediction @ aa2a602c1a, `models/final_experiment_scripts/best_hyperparameters.py` lines 50-75

```python
   44         c['learning_rate'] = 0.00221
   45         c['temp_dropout_rate'] = 0.05
   46         c['temp_kernels'] = [11] * 8
   47         c['point_sizes'] = [5] * 8
   48     return c
   49 
   50 def best_lstm(c):
   51     c = best_global(c)
   52     c['mode'] = 'test'
   53     if c['dataset'] == 'eICU':
   54         c['batch_size'] = 512
   55         c['n_layers'] = 2
   56         c['hidden_size'] = 128
   57         c['learning_rate'] = 0.00129
   58         c['lstm_dropout_rate'] = 0.2
   59         if c['percentage_data'] < 25:
   60             c['n_epochs'] = 4
   61         elif c['percentage_data'] == 25:
   62             c['n_epochs'] = 5
   63         elif c['percentage_data'] == 50:
   64             c['n_epochs'] = 6
   65         else:
   66             c['n_epochs'] = 8
   67     elif c['dataset'] == 'MIMIC':
   68         c['no_diag'] = True
```

Your label: ______
Selection split / reported split: ______

## Site 5: Benchmarking_DL_MIMICIII @ eae5f27719, `Codes/SuperLearnerPyVer/python/pgbart/src/bart_utils.py` lines 1179-1179

```python
 1173     except AssertionError:
 1174         print('Failed to obtain the right solution: beta_init = %s, q = %s, ' \
 1175                 'gdtrc(solution, alpha, min_val) = %s' \
 1176                 % (init_val, q, gdtrc(solution, alpha, min_val)))
 1177         print('Trying a new initial value for beta')
 1178         # new_init = alpha / min_val / 5
 1179         new_init = max(0.001, init_val * 0.9)       # seems to work for compute_gamma_param(min_val, 3.0, 0.9)
 1180         # very low values of new_init (~0) seem to crash; haven't tested for arbitrary combinations of alpha and q
 1181         solution = compute_gamma_param(min_val, alpha, q, new_init)
 1182     return float(solution)
 1183 
```

Your label: ______
Selection split / reported split: ______

## Site 6: TPC-LoS-prediction @ aa2a602c1a, `models/final_experiment_scripts/best_hyperparameters.py` lines 77-96

```python
   71         c['hidden_size'] = 128
   72         c['learning_rate'] = 0.00163
   73         c['lstm_dropout_rate'] = 0.25
   74         c['n_epochs'] = 8
   75     return c
   76 
   77 def best_cw_lstm(c):
   78     c['mode'] = 'test'
   79     c['channelwise'] = True
   80     # carry over the best parameters from lstm, including global
   81     c = best_lstm(c)
   82     if c['dataset'] == 'eICU':
   83         c['hidden_size'] = 8
   84         if c['percentage_data'] < 25:
   85             c['n_epochs'] = 15
   86         elif c['percentage_data'] == 25 or c['task'] == 'mortality':
   87             c['n_epochs'] = 20
   88         elif c['percentage_data'] == 50:
   89             c['n_epochs'] = 25
   90         else:
   91             c['n_epochs'] = 30
   92     elif c['dataset'] == 'MIMIC':
   93         c['no_diag'] = True
   94         c['hidden_size'] = 8
   95         c['n_epochs'] = 20
```

Your label: ______
Selection split / reported split: ______

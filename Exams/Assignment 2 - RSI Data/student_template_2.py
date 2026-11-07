"""ENGR 315 Assignment 2: RSI analysis using Modules 3, 4, and 5."""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import ttest_1samp, norm, chisquare, t, sem


df = pd.read_csv('../../data/drop-jump/all_participant_data_rsi.csv')
alpha = 0.05

force_plate_rsi = df['force_plate_rsi'].to_numpy()
accel_rsi = df['accelerometer_rsi'].to_numpy()

# Task 1: a paired t-test is a one-sample t-test of the paired differences
difference = force_plate_rsi - accel_rsi
t_value, p_value = ttest_1samp(difference, popmean=0, alternative='two-sided')

print('Task 1: Paired t-test')
print('H0: The population mean force plate - accelerometer difference is zero.')
print('H1: The population mean force plate - accelerometer difference is not zero.')
print('Number of paired trials:', len(difference))
print('Force plate mean RSI (m/s):', np.mean(force_plate_rsi))
print('Accelerometer mean RSI (m/s):', np.mean(accel_rsi))
print('Mean paired difference (m/s):', np.mean(difference))
print('t-value:', t_value, 'p-value:', p_value)

if p_value < alpha:
    print('Reject H0. There is evidence that the mean RSI differs between methods.')
else:
    print('Fail to reject H0. There is insufficient evidence of a mean difference.')

# Task 2: follow Module 5 distribution-fit.py and chi-square-dist-fit.py.
fitted_mean, fitted_std = norm.fit(accel_rsi)

# Chose yo use wider tail bins than the lecture example because this sample is smaller
# bin boundaries adapt to the fitted mean and standard deviation
bins = np.linspace(fitted_mean - 1.5 * fitted_std,
                   fitted_mean + 1.5 * fitted_std, 7)
bins = np.r_[-np.inf, bins, np.inf]

observed_counts, observed_edges = np.histogram(accel_rsi, bins=bins)
expected_prob = np.diff(norm.cdf(bins, loc=fitted_mean, scale=fitted_std))
expected_counts = expected_prob * len(accel_rsi)

print('\nTask 2: Normal distribution goodness of fit')
print('H0: Accelerometer RSI follows a normal distribution.')
print('H1: Accelerometer RSI does not follow a normal distribution.')
print('Fitted mean:', fitted_mean, 'fitted standard deviation:', fitted_std)
print('Observed counts:', observed_counts)
print('Expected counts:', expected_counts)

# Two degrees of freedom subtracted for fitted mean and stdev
# check expected counts before interpreting the chi-square approximation
if min(expected_counts) >= 5:
    chi_stat, p_value = chisquare(observed_counts, f_exp=expected_counts, ddof=2)
    print('Chi-square statistic:', chi_stat, 'p-value:', p_value)
    print('Degrees of freedom:', len(observed_counts) - 3)
    if p_value < alpha:
        print('Reject H0. The normal distribution is a poor fit by this test.')
    else:
        print('Fail to reject H0. The normal distribution is a reasonable fit by this test.')
else:
    print('Expected counts are too small. Use fewer bins before interpreting the test.')


plt.hist(accel_rsi, bins=9, density=True, edgecolor='k',
         label='Accelerometer RSI')
x = np.linspace(min(accel_rsi), max(accel_rsi), 100)
plt.plot(x, norm.pdf(x, loc=fitted_mean, scale=fitted_std),
         linewidth=2, color='r', label='Fitted normal distribution')
plt.xlabel('Accelerometer RSI (m/s)')
plt.ylabel('Probability density')
plt.title('Accelerometer RSI with Fitted Normal Distribution')
plt.legend()

# Task 3: use string splitting, lists, and the Boolean DataFrame filter
participants = []
for trial in df['trial']:
    participants.append(trial.split('_')[0])
df['participant'] = participants
participant_f = df[df['participant'] == 'F']

print('\nTask 3: Participant F trials')
print(participant_f)

force_f = participant_f['force_plate_rsi'].to_numpy()
accel_f = participant_f['accelerometer_rsi'].to_numpy()

force_lower, force_upper = t.interval(
    confidence=0.95, df=len(force_f) - 1,
    loc=np.mean(force_f), scale=sem(force_f))
accel_lower, accel_upper = t.interval(
    confidence=0.95, df=len(accel_f) - 1,
    loc=np.mean(accel_f), scale=sem(accel_f))

print('Force plate mean RSI (m/s):', np.mean(force_f))
print('Force plate 95% CI for mean RSI (m/s):', force_lower, force_upper)
print('Accelerometer mean RSI (m/s):', np.mean(accel_f))
print('Accelerometer 95% CI for mean RSI (m/s):', accel_lower, accel_upper)
print('These intervals estimate the two means. Overlap alone does not prove agreement.')

plt.show()

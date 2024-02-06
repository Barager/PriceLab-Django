import scipy.stats as stats
import pandas as pd
import numpy as np
from scipy.stats import shapiro, levene
import statsmodels.api as sm

from experiments.models import User

def check_normality_assumption(group1, group2):
    _, p_value1 = shapiro(group1)
    _, p_value2 = shapiro(group2)
    return {'Treatment p-value': round(p_value1, 3), 'Control p-value': round(p_value2, 3)}

def check_homogeneity_of_variances(group1, group2):
    statistic, p_value = levene(group1, group2)
    return {'Statistic': round(statistic, 3), 'p-value': round(p_value, 3)}


def t_test(group1, group2):
    value_column = 'minutes_driven'

    group1_values = group1[value_column].astype(float)
    group2_values = group2[value_column].astype(float)

    statistic, p_value = stats.ttest_ind(group1_values, group2_values, nan_policy='omit')
    result = {'Statistic': round(statistic, 3), 'p-value': round(p_value, 3), 'p-value < 0.05': p_value < 0.05}
    return result

def mann_whitney_u_test(group1, group2):
    statistic, p_value = stats.mannwhitneyu(group1, group2, alternative='two-sided')
    result = {'Statistic': round(statistic, 3), 'p-value': round(p_value, 3), 'p-value < 0.05': p_value < 0.05}
    return result


def covariate_adjustment_test(rides_df, treatment, controls):
    # Fetch User data for treatment and control groups
    treatment_data = User.objects.filter(customer_uuid__in=treatment)
    control_data = User.objects.filter(customer_uuid__in=controls)

    # Convert QuerySets to DataFrames
    treatment_data = pd.DataFrame.from_records(treatment_data.values())
    control_data = pd.DataFrame.from_records(control_data.values())

    # Merge user-level data with ride-level data for treatment group
    merged_treatment = pd.merge(rides_df, treatment_data[['revenue_excl_vat', 'rides', 'clv'] + ['customer_uuid']], on='customer_uuid')

    # Merge user-level data with ride-level data for control group
    merged_control = pd.merge(rides_df, control_data[['revenue_excl_vat', 'rides', 'clv'] + ['customer_uuid']], on='customer_uuid')

    # Combine treatment and control data
    combined_data = pd.concat([merged_treatment, merged_control])

    # Create dummy variable for treatment group
    combined_data['treatment'] = np.where(combined_data['customer_uuid'].isin(treatment_data['customer_uuid']), 1, 0)
    # Define covariates 
    covariates = ['revenue_excl_vat', 'rides', 'clv']#'revenue', 'clv']

    # Add intercept term
    combined_data['intercept'] = 1

    # Create design matrix
    X = combined_data[['intercept', 'treatment'] + covariates]

    # Fit linear regression model
    model = sm.OLS(combined_data['minutes_driven'], X)
    results = model.fit()
    
    # Parse and format params and bse
    params_dict = {param: round(results.params[param], 3) for param in results.params.index}
    bse_dict = {param: round(results.bse[param], 3) for param in results.bse.index}

    # Remove dtype from params and bse
    params_dict.pop('dtype', None)
    bse_dict.pop('dtype', None)
    
    if results.params['treatment'] > 0:
        response_sentence = f"Customers in the treatment group responded by driving {results.params['treatment']:.3f} minutes more on average than those who didn't receive the treatment."
    elif results.params['treatment'] < 0:
        response_sentence = f"Customers in the treatment group responded by driving {abs(results.params['treatment']):.3f} minutes less on average than those who didn't receive the treatment."
    else:
        response_sentence = "There was no significant difference in the driving response between the treatment and control groups."


    # Create a dictionary to store the results
    results_dict = {
        # 'Average Treatment Effect': {
            'ATE': round(results.params['treatment'], 3),
            'SE (Standard Error)': round(results.bse['treatment'], 3),
            'Confidence Interval (95%)': f"[{round(results.conf_int().loc['treatment', 0], 3)} - {round(results.conf_int().loc['treatment', 1],3)}]",
            'Conclusion': response_sentence,
            'Model Details': {
                'Model Equation': f"{params_dict['intercept']} + {params_dict['treatment']} * treatment + {params_dict['revenue_excl_vat']} * revenue_excl_vat + {params_dict['rides']} * rides + {params_dict['clv']} * clv",
                # 'bse': bse_dict,
                'R^2': round(results.rsquared, 3)
            }
        # }
    }

    # Return the results dictionary
    return results_dict

def cupac_test(data):
    # Implement your CUPAC test logic here
    # You may need additional parameters depending on your use case
    # Example: stats.some_cupac_test(data)
    result = 'WOrks'
    return result

def did_test(data):
    # Implement your DiD test logic here
    # You may need additional parameters depending on your use case
    # Example: stats.some_did_test(data)
    result = 'Works'
    return result


def run_tests(data, selected_tests, group1, group2):
    results = {}
    # print(selected_tests)
    
    treatment_data = data[data['customer_uuid'].isin(group1)]['minutes_driven']
    control_data = data[data['customer_uuid'].isin(group2)]['minutes_driven']
    
    
    results['Total Participants'] = len(group1) + len(group2)
    results['Treatment Group Size'] = len(group1)
    results['Control Group Size'] = len(group2)
    
    # Check assumptions and perform relevant tests
    results['Normality Test'] = check_normality_assumption(treatment_data, control_data)
    results['Homogeneity of Variances'] = check_homogeneity_of_variances(treatment_data, control_data)
    
    # Perform relevant tests based on assumptions
    if results['Normality Test']['Treatment p-value'] > 0.05 and results['Normality Test']['Control p-value'] > 0.05 and results['Homogeneity of Variances']['p-value'] > 0.05:
        results['T-Test'] = t_test(treatment_data, control_data)
    else:
        results['Mann-Whitney U Test'] = mann_whitney_u_test(treatment_data, control_data)
        
    # Additional post-hoc tests
    if 'Covariate Adjustment' in selected_tests:
        results['Average Treatment Effect'] = covariate_adjustment_test(data, group1, group2)
    if 'cupac_test' in selected_tests:
        results['cupac_test'] = cupac_test(data)
    if 'did_test' in selected_tests:
        results['did_test'] = did_test(data)
        
    # print(results)
    return results
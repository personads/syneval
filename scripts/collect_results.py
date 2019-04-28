import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import argparse, glob, json

import numpy as np

def load_results(path):
    res = []
    for cur_path in glob.glob(os.path.join(path, '*.json')):
        with open(cur_path, 'r', encoding='utf8') as fop:
            cur_res = json.load(fop)
            # skip incomplete sessions
            if None in cur_res:
                print("[Warning] Skipping incomplete session at '%s'." % cur_path)
                continue
            res.append(cur_res)
    return np.array(res)

def load_task(config_path):
    truths, options = [], []
    with open(config_path, 'r', encoding='utf8') as fop:
        config = json.load(fop)
    options = [task['options'] for task in config['tasks']]
    truths = [task['options'][task['truth']] for task in config['tasks']]
    truth_idcs = [task['truth'] for task in config['tasks']]
    return np.array(truth_idcs), np.array(truths), np.array(options)

def get_choice_matrix(results, options):
    # convert results into (task, choices) choice count matrix
    mat_choices = np.zeros((results.shape[1], 3))
    for res_idx in range(results.shape[0]):
        for task_idx in range(results.shape[1]):
            choice_idx = np.where(options[task_idx] == results[res_idx, task_idx])
            mat_choices[task_idx, choice_idx] += 1
    return mat_choices

def calc_accuracies(results, truths):
    mat_truths = np.repeat(truths.reshape((1, truths.shape[0])), results.shape[0], axis=0)
    matches = np.sum(results == mat_truths, axis=1)
    accuracies = matches / truths.shape[0]
    return accuracies

def calc_kappa(choices, num_choices=3):
    '''Calculate Fleiss' Kappa (based on https://en.wikibooks.org/wiki/Algorithm_Implementation/Statistics/Fleiss'_kappa)'''
    num_evals = np.sum(choices[0])
    num_tasks = choices.shape[0]

    p = [0.0] * num_choices
    for j in range(num_choices):
        p[j] = 0.0
        for i in range(num_tasks):
            p[j] += choices[i][j]
        p[j] /= num_tasks * num_evals

    P = [0.0] * num_tasks
    for i in range(num_tasks):
        P[i] = 0.0
        for j in range(num_choices):
            P[i] += choices[i][j] * choices[i][j]
        P[i] = (P[i] - num_evals) / (num_evals * (num_evals - 1))

    Pbar = sum(P) / num_tasks
    PbarE = 0.0
    for pj in p:
        PbarE += pj * pj

    kappa = (Pbar - PbarE) / (1 - PbarE)
    return kappa

if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser(description='SynEval Result Aggregation')
    arg_parser.add_argument('config_path', help='path evaluation configuration JSON')
    arg_parser.add_argument('result_path', help='path result files')
    args = arg_parser.parse_args()

    # load data
    results = load_results(args.result_path)
    truth_idcs, truths, options = load_task(args.config_path)
    print("Loaded %d evaluation sessions with %d tasks each." % (results.shape[0], truths.shape[0]))

    # calculate accuracy
    accuracies = calc_accuracies(results, truths)
    print("Accuracy: %.2f avg, %.2f stddev, %.2f max, %.2f min" % (np.mean(accuracies), np.std(accuracies), np.max(accuracies), np.min(accuracies)))
    print(" ", accuracies)

    # calculate interevaluator agreement
    choices = get_choice_matrix(results, options)
    max_agreement = np.max(choices)
    max_agreement_idcs = np.where(choices == max_agreement)[0]
    kappa = calc_kappa(choices)
    print("Fleiss' Kappa: %.2f (max agreement: %.2f%% (%d tasks))." % (kappa, (max_agreement * 100)/results.shape[0], max_agreement_idcs.size))
    print(" ", max_agreement_idcs)

    correct_choice_counts = [choices[task_idx, truth_idx] for task_idx, truth_idx in enumerate(truth_idcs)]
    max_correct_choices = np.max(correct_choice_counts)
    max_correct_choices_idcs = np.where(correct_choice_counts == max_correct_choices)[0]
    print("Maximum correct choices: %.2f%% (%d tasks)" % ((max_correct_choices*100)/results.shape[0], max_correct_choices_idcs.size))
    print(" ", max_correct_choices_idcs)
    min_correct_choices = np.min(correct_choice_counts)
    min_correct_choices_idcs = np.where(correct_choice_counts == min_correct_choices)[0]
    print("Minimum correct choices: %.2f%% (%d tasks)" % ((min_correct_choices*100)/results.shape[0], min_correct_choices_idcs.size))
    print(" ", min_correct_choices_idcs)

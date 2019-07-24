import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import argparse, glob, json

import matplotlib.pyplot as plt
import numpy as np

from matplotlib.offsetbox import *
from matplotlib.patches import *
from PIL import Image

def load_results(path):
    res = []
    skip_count = 0
    for cur_path in glob.glob(os.path.join(path, '*.json')):
        with open(cur_path, 'r', encoding='utf8') as fop:
            cur_res = json.load(fop)
            # skip incomplete sessions
            if None in cur_res:
                skip_count += 1
                continue
            res.append(cur_res)
    if skip_count > 0: print("[Warning] Skipped %d incomplete sessions." % skip_count)
    return np.array(res)

def load_task(config):
    truths, options = [], []
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
    arg_parser.add_argument('--plot', action='store_true', help='plot results')
    arg_parser.add_argument('--data_path', help='path to data (required for plotting)')
    args = arg_parser.parse_args()

    # load config
    with open(args.config_path, 'r', encoding='utf8') as fop:
        config = json.load(fop)
    truth_idcs, truths, options = load_task(config)
    
    # load results
    results = load_results(args.result_path)

    print("Loaded %d evaluation sessions with %d tasks each." % (results.shape[0], truths.shape[0]))

    # calculate accuracy
    accuracies = calc_accuracies(results, truths)
    print("Accuracy: %.2f avg, %.2f stddev, %.2f max, %.2f min" % (np.mean(accuracies), np.std(accuracies), np.max(accuracies), np.min(accuracies)))
    print(" ", accuracies)

    # calculate accuracy per class
    choices = get_choice_matrix(results, options)
    print("Accuracy per class:")
    for class_idx, class_dsc in enumerate(config['classes']):
        class_correct = choices[[ti for ti, t in enumerate(truth_idcs) if t == class_idx], class_idx]
        class_accuracy = np.sum(class_correct) / np.sum(choices[:, class_idx])
        print("  '%s': %.2f avg" % (class_dsc, class_accuracy))

    # calculate interevaluator agreement
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

    # plot accuracy
    if args.plot:
        plot_str = []
        for ti, ccc in enumerate(correct_choice_counts):
            plot_str.append('task %d: %d\\%%' % (ti + 1, (ccc * 100)/results.shape[0]))
        print("Plot description:")
        print('Percentages of correct choices: ' + ', '.join(plot_str) + '.\n')

        fig, ax = plt.subplots(figsize=(12, 3))
        width = 0.15
        colors = ['dimgrey', 'darkgrey', 'lightgrey']
        # colors = ['orchid', 'royalblue', 'coral']
        x_pos = np.arange(20, dtype=float)
        ax.set_xlim([-.5, 19.5])
        ax.set_ylim([-100, 100])

        for oi in range(3):
            # get position
            positions = x_pos
            if oi == 0:
                positions = x_pos - width
            elif oi == 2:
                positions = x_pos + width

            # plot bars
            option_choices = np.maximum(((np.array(choices[:, oi])/results.shape[0]) * 100), np.ones(choices.shape[0]))
            option_bars = ax.bar(positions, option_choices, width, color=colors[oi])

            # set colors for correct bars
            for bi in [i for i in range(choices.shape[0]) if truth_idcs[i] == oi]:
                option_bars[bi].set_color('limegreen')

        # create rule lines
        ax.hlines([25, 50, 75, 100], -1, 20, colors='lightgrey', linestyles='dashed', linewidths=1, zorder=0)
        ax.vlines(np.arange(0.5, 20, 1), 0, 100, colors='darkgrey', linestyles='solid', linewidths=1, zorder=0)
        ax.plot([-1, 20], [np.mean(accuracies)*100, np.mean(accuracies)*100], color='limegreen', linestyle='dashed', linewidth=1, zorder=0)
        # ax.plot([-1, 20], [(np.mean(accuracies) - np.std(accuracies))*100, (np.mean(accuracies) - np.std(accuracies))*100], color='palegreen', linestyle='dashed', linewidth=1, zorder=0)
        # ax.plot([-1, 20], [(np.mean(accuracies) + np.std(accuracies))*100, (np.mean(accuracies) + np.std(accuracies))*100], color='palegreen', linestyle='dashed', linewidth=1, zorder=0)
        # create ticks
        ax.get_xaxis().set_ticks(np.arange(20, dtype=int))
        ax.set_xticklabels(np.arange(1, 21, 1, dtype=int))
        ax.spines['bottom'].set_position('center')
        ax.get_yaxis().set_ticks(np.arange(0, 101, 25, dtype=int))
        ax.plot([-1, 20], [-100, -100], 'k-')
        # add images
        for ti, task in enumerate(options):
            for oi, option in enumerate(task):
                img = Image.open(os.path.join(args.data_path, '%d_orig.png' % option))
                img = img.resize((32, 32))
                y_pos = -32 - (oi * 25)
                bboxprops = dict(lw=6., ec=colors[oi])
                if option == truths[ti]:
                    bboxprops = dict(lw=6., ec='limegreen')
                ab = AnnotationBbox(OffsetImage(img, zoom=.6, cmap='gray'), (ti, y_pos), pad=0., bboxprops=bboxprops)
                ax.add_artist(ab)
        # show plot
        fig.tight_layout()
        fig.savefig(os.path.join(args.result_path, 'results.pdf'))
        plt.show()

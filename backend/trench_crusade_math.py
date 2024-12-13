# -*- coding: utf-8 -*-

from collections import Counter
from itertools import combinations_with_replacement, product
from scipy.stats import binom
import matplotlib.pyplot as plt

# Thresholds for injury rolls
injury_thresholds = {
    "no_effect": 1,
    "blood_marker": (2, 6),
    "downed": (7, 8),
    "out_of_action": 9
}

def compute(modified_dice: int = 0, extra_d6: bool = False, flat_modifier: int = 0):
    """
    Compute the distribution of outcomes for varying types of rolls.
    - Baseline is 2d6 summed.
    - `modified_dice` can add or subtract dice for advantage/disadvantage.
    - `extra_d6` determines if an additional die is added to the roll.
    - `flat_modifier` applies a constant modifier to the result.

    Args:
        modified_dice (int): The number of additional or fewer dice compared to 2d6.
                             Positive values add dice (advantage), negative values remove dice (disadvantage).
        extra_d6 (bool): Whether to add an extra die outside of the advantage/disadvantage mechanics.
        flat_modifier (int): A flat value added to or subtracted from the final result.

    Returns:
        Counter: Distribution of outcomes as {sum: probability}.
    """
    base_dice = 2  # Baseline is 2d6
    num_dice = base_dice + abs(modified_dice)
    if num_dice < 2:
        raise ValueError("Number of dice cannot be less than 2.")

    # Generate all possible outcomes for the main rolls
    all_rolls = combinations_with_replacement(range(1, 7), num_dice)

    # Calculate sums based on modified_dice
    if modified_dice > 0:  # Advantage: select top 2
        selected_sums = [sum(sorted(roll, reverse=True)[:2]) for roll in all_rolls]
    elif modified_dice < 0:  # Disadvantage: select bottom 2
        selected_sums = [sum(sorted(roll)[:2]) for roll in all_rolls]
    else:  # No modification: just sum the two dice
        selected_sums = [sum(roll) for roll in all_rolls]

    # If extra_d6 is True, add an additional roll
    if extra_d6:
        # Generate all possible outcomes for the extra d6
        extra_die_rolls = range(1, 7)
        extended_sums = []
        for selected_sum in selected_sums:
            for extra_roll in extra_die_rolls:
                extended_sums.append(selected_sum + extra_roll)
        selected_sums = extended_sums

    # Apply the flat modifier
    modified_sums = [s + flat_modifier for s in selected_sums]

    # Compute probabilities
    total_outcomes = len(selected_sums)
    distribution = Counter(modified_sums)
    for key in distribution:
        distribution[key] /= total_outcomes

    return distribution

def compute_success_distribution(modified_dice: int=0, num_rolls: int=1, extra_d6: bool=False, flat_modifier: int=0, threshold: int=7, ):
    """
    Compute the distribution of successes for a given number of rolls.

    Args:
        modified_dice (int): The number of additional or fewer dice compared to 2d6.
        extra_d6 (bool): Whether to add an extra die outside of the advantage/disadvantage mechanics.
        flat_modifier (int): A flat value added to or subtracted from the final result.
        threshold (int): The minimum value required for a roll to count as a "success."
        num_rolls (int): The number of rolls to make (attacks, checks, etc.).

    Returns:
        dict: The distribution of successes as {success_count: probability}.
    """
    # Compute the distribution of single roll outcomes
    outcome_distribution = compute(modified_dice, extra_d6, flat_modifier)

    # Compute the probability of a single roll being a success
    success_probability = sum(prob for outcome, prob in outcome_distribution.items() if outcome >= threshold)

    # Use the binomial distribution to compute the probability of 0, 1, ..., num_rolls successes
    success_distribution = {
        k: binom.pmf(k, num_rolls, success_probability)
        for k in range(num_rolls + 1)
    }

    return success_distribution


def compute_blood_markers_for_hit(injury_params: dict, thresholds: dict, is_downed: bool = False):
    """
    Compute the blood marker distribution for a single injury roll.

    Args:
        injury_params (dict): Parameters for the injury roll (modified_dice, extra_d6, flat_modifier).
        thresholds (dict): Thresholds for injury outcomes.
        is_downed (bool): Whether the unit is already downed.

    Returns:
        dict: Distribution of blood markers for a single injury roll.
    """
    # Adjust modified_dice if the unit is Downed
    modified_dice = injury_params['modified_dice'] + (1 if is_downed else 0)

    # Compute the injury roll distribution
    injury_roll_distribution = compute(
        modified_dice=modified_dice,
        extra_d6=injury_params['extra_d6'],
        flat_modifier=injury_params['flat_modifier']
    )
    print(injury_roll_distribution)

    blood_marker_distribution = Counter()
    out_of_action_probability = 0

    # Classify outcomes based on thresholds
    for roll, prob in injury_roll_distribution.items():
        if roll <= thresholds['no_effect']:
            continue  # No effect
        elif thresholds['blood_marker'][0] <= roll <= thresholds['blood_marker'][1]:
            blood_marker_distribution[1] += prob
        elif thresholds['downed'][0] <= roll <= thresholds['downed'][1]:
            if is_downed:
                blood_marker_distribution[2] += prob
            else:
                blood_marker_distribution[1] += prob
                is_downed = True
        elif roll >= thresholds['out_of_action']:
            out_of_action_probability += prob

    # Normalize probabilities
    total_prob = sum(blood_marker_distribution.values()) + out_of_action_probability
    for key in blood_marker_distribution:
        blood_marker_distribution[key] /= total_prob

    return blood_marker_distribution, out_of_action_probability / total_prob



def compute_injury_outcome_refined(hit_distribution: dict, injury_params: dict, thresholds: dict):
    """
    Refined computation of blood marker and Out of Action probabilities.

    Args:
        hit_distribution (dict): Distribution of successful hits as {hits: probability}.
        injury_params (dict): Parameters for the injury rolls (modified_dice, extra_d6, flat_modifier).
        thresholds (dict): Thresholds for injury outcomes.

    Returns:
        dict: Combined distribution of blood markers and Out of Action probabilities.
    """
    combined_blood_marker_distribution = Counter()
    total_out_of_action_probability = 0

    # Iterate over each possible number of hits and its probability
    for hits, hit_prob in hit_distribution.items():
        # Initialize the state for the current hit count
        blood_marker_distribution = Counter({0: 1.0})  # Start with no blood markers
        out_of_action_probability = 0

        for _ in range(hits):
            new_blood_marker_distribution = Counter()
            for current_blood_markers, current_prob in blood_marker_distribution.items():
                # Compute the blood marker distribution for a single hit
                is_downed = current_blood_markers > 0  # Unit is downed if it already has markers
                single_blood_distribution, single_out_action_prob = compute_blood_markers_for_hit(
                    injury_params, thresholds, is_downed
                )

                # Update the blood marker distribution for this hit
                for blood, prob in single_blood_distribution.items():
                    new_blood_marker_distribution[current_blood_markers + blood] += current_prob * prob

                # Update Out of Action probability
                out_of_action_probability += current_prob * single_out_action_prob

            blood_marker_distribution = new_blood_marker_distribution

        # Combine the results for this hit count
        for blood, prob in blood_marker_distribution.items():
            combined_blood_marker_distribution[blood] += hit_prob * prob
        total_out_of_action_probability += hit_prob * out_of_action_probability

    # Normalize combined probabilities
    total_prob = sum(combined_blood_marker_distribution.values()) + total_out_of_action_probability
    for key in combined_blood_marker_distribution:
        combined_blood_marker_distribution[key] /= total_prob

    return {
        "blood_marker_distribution": combined_blood_marker_distribution,
        "out_of_action_probability": total_out_of_action_probability / total_prob
    }


def plot_distributions_with_out_of_action_fixed(hit_distribution, injury_outcome):
    """
    Plot the hit success distribution and injury outcome distributions,
    including "Out of Action" as a separate red bar on the blood marker chart.

    Args:
        hit_distribution (dict): Distribution of successful hits as {hits: probability}.
        injury_outcome (dict): Distribution of injury outcomes containing blood_marker_distribution and out_of_action_probability.
    """
    # Extract blood marker distribution and Out of Action probability
    blood_marker_distribution = injury_outcome["blood_marker_distribution"]
    out_of_action_probability = injury_outcome["out_of_action_probability"]

    # Prepare hit distribution data
    hits, hit_probs = zip(*sorted(hit_distribution.items()))

    # Prepare blood marker distribution data
    blood_markers = list(blood_marker_distribution.keys()) + [max(blood_marker_distribution.keys()) + 1]
    blood_probs = list(blood_marker_distribution.values()) + [out_of_action_probability]
    labels = list(map(str, blood_marker_distribution.keys())) + ["Out of Action"]

    # Plot hit success distribution
    plt.figure(figsize=(12, 5))

    plt.subplot(1, 2, 1)
    plt.bar(hits, hit_probs, width=0.8, edgecolor='black', alpha=0.7)
    plt.title("Hit Success Distribution")
    plt.xlabel("Number of Hits")
    plt.ylabel("Probability")
    plt.xticks(hits)
    plt.grid(axis="y", linestyle="--", alpha=0.7)

    # Plot injury outcome distribution
    plt.subplot(1, 2, 2)
    bar_colors = ['blue'] * len(blood_marker_distribution) + ['red']
    plt.bar(range(len(blood_markers)), blood_probs, width=0.8, edgecolor='black', alpha=0.7, color=bar_colors)
    plt.title("Injury Outcome Distribution")
    plt.xlabel("Outcome")
    plt.ylabel("Probability")
    plt.xticks(range(len(blood_markers)), labels, rotation=45)
    plt.grid(axis="y", linestyle="--", alpha=0.7)

    # Show plots
    plt.tight_layout()
    plt.show()

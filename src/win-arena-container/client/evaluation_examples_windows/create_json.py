import os
import json
import math
import random

def get_directory_structure(base_dir, filter_out_categories=None):
    directory_structure = {}
    total_files_count = 0

    subdirectories = sorted(
        (entry for entry in os.scandir(base_dir) if entry.is_dir()),
        key=lambda entry: entry.name,
    )
    for subdirectory in subdirectories:
        subdir = subdirectory.path
        if filter_out_categories:
            if any(category in subdir for category in filter_out_categories):
                print(f"Skipping directory: {subdir}")
                continue

        subdir_name = subdirectory.name
        file_names = [
            os.path.splitext(file.name)[0]
            for file in sorted(os.scandir(subdir), key=lambda entry: entry.name)
            if file.is_file() and file.name.lower().endswith(".json")
        ]
        directory_structure[subdir_name] = file_names
        total_files_count += len(file_names)

        # Print the count of files per subdirectory
        print(f"Directory: {subdir_name}, File count: {len(file_names)}")

    return directory_structure, total_files_count


def stratified_random_sample(directory_structure, sample_ratio=0.3, seed=None):
    """Randomly sample the given proportion of files from every category."""
    if not 0 <= sample_ratio <= 1:
        raise ValueError("sample_ratio must be between 0 and 1")

    random_generator = random.Random(seed)
    sampled_structure = {}
    total_sampled_count = 0

    for category, file_names in directory_structure.items():
        sample_count = math.ceil(len(file_names) * sample_ratio)
        sampled_files = random_generator.sample(sorted(file_names), sample_count)
        sampled_structure[category] = sampled_files
        total_sampled_count += sample_count

        print(
            f"Category: {category}, Original count: {len(file_names)}, "
            f"Sampled count: {sample_count}"
        )

    return sampled_structure, total_sampled_count


def main(
    base_dir,
    output_file,
    filter_out_categories=None,
    mode="all",
    seed=None,
):
    directory_structure, total_files_count = get_directory_structure(base_dir, filter_out_categories)

    if mode == "sample":
        directory_structure, total_files_count = stratified_random_sample(
            directory_structure,
            sample_ratio=0.3,
            seed=seed,
        )
    elif mode != "all":
        raise ValueError('mode must be either "all" or "sample"')
    
    with open(output_file, 'w') as f:
        json.dump(directory_structure, f, indent=4)
    
    # Print the total number of files
    print(f"Total file count: {total_files_count}")

if __name__ == "__main__":
    base_dir = "examples"
    mode = "all"  # "all": all tasks; "sample": stratified 30% sample
    output_file = "test_all.json"
    filter_out_categories = None

    main(
        base_dir,
        output_file,
        filter_out_categories,
        mode=mode,
        seed=42,
    )

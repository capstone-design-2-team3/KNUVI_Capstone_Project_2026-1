# pipeline.py

import os

def run_training():

    print("========== TRAINING ==========")

    os.system("python train.py")


def run_inference():

    print("========== INFERENCE ==========")

    os.system(
        "python inference.py"
    )


def run_analysis():

    print("========== ANALYSIS ==========")

    os.system(
        "python analyzer.py"
    )


if __name__ == "__main__":

    run_training()

    run_inference()

    run_analysis()

    print("========== ALL COMPLETE ==========")

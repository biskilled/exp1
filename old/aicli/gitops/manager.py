# gitops/manager.py
import subprocess

def checkout_branch(name):
    result = subprocess.run(
        ["git", "rev-parse", "--verify", name],
        capture_output=True,
        text=True
    )

    if result.returncode == 0:
        subprocess.run(["git", "checkout", name])
    else:
        subprocess.run(["git", "checkout", "-b", name])


def get_current_branch():
    result = subprocess.run(
        ["git", "branch", "--show-current"],
        capture_output=True,
        text=True
    )
    return result.stdout.strip()


def get_diff():
    result = subprocess.run(
        ["git", "diff"],
        capture_output=True,
        text=True
    )
    return result.stdout


def commit_and_push(message):
    subprocess.run(["git", "add", "."])
    subprocess.run(["git", "commit", "-m", message])
    subprocess.run(["git", "push"])
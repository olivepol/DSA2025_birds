# DSA2025_birds
Data Structures and Algorithms

### We will build the most beautiful app you have ever seen! Watch and see!

## Project description
Our webapp will ...

## Setting Up the Environment

1. Clone the repo:

git clone https://github.com/olivepol/DSA2025_birds
cd <repo-folder>

2. Set up the environment:

    For Python:

conda env create -f environment.yml
conda activate DSA2025_birds_webapp

3. Run the app:

    Python:

flask run


4. Keep Dependencies Up-to-Date:

    If you or a collaborator add new dependencies, update the configuration file and share it with others.
        Conda: Update environment.yml:

conda env export --no-builds > environment.yml

5. Document Changes:

    Use the README.md or commit messages to notify collaborators when the environment changes.


4. Regular Updates:

    Collaborators should periodically update their environments:
        Conda:

conda env update --file environment.yml --prune

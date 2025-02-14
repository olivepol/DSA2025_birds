# DSA2025_birds
Data Structures and Algorithms

### We will build the most beautiful app you have ever seen! Watch and see!



## Setting Up the Environment

1. Clone the repository:
bash
   git clone <repo-url>
   cd <repo-folder>

2. Keep Dependencies Up-to-Date:

    If you or a collaborator add new dependencies, update the configuration file and share it with others.
        Conda: Update environment.yml:

conda env export --no-builds > environment.yml

3. Document Changes:

    Use the README.md or commit messages to notify collaborators when the environment changes.


4. Regular Updates:

    Collaborators should periodically update their environments:
        Conda:

conda env update --file environment.yml --prune

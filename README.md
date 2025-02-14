# DSA2025_birds
Data Structures and Algorithms

### We will build the most beautiful app you have ever seen! Watch and see!



## Setting Up the Environment

1. Clone the repository:
bash
   git clone <repo-url>
   cd <repo-folder>

2. Access the environment
   
To make your environment accessible to collaborators via your GitHub repository, you should share the environment configuration rather than the actual environment itself. This allows your collaborators to recreate the environment on their machines without including the bulky environment files or dependencies in the repo.
Steps to Share an Environment
1. Export Your Environment Configuration

Export the environment to a configuration file.

For Conda:

    Export the environment to a .yml file:

conda env export --no-builds > environment.yml

    The --no-builds flag ensures portability by excluding platform-specific details.
    The generated environment.yml might look like this:

Add environment.yml to your repository:

    git add environment.yml
    git commit -m "Add environment file"
    git push origin main



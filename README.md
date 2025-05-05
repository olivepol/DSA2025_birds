# DSA2025_birds
Data Structures and Algorithms

### We will build the most beautiful app you have ever seen! Watch and see!

---

## Project Description

**Birds** is a web application that helps users discover and match courses offered by the **Volkshochschule Berlin (VHS)** based on their interests and preferences. Instead of relying on basic keyword searches, the app uses **semantic similarity** and **consensus ranking** to provide relevant, personalized course recommendations.

This project was developed as part of the DSA 2025 course by the team **Birds**:
Elena Lopez, Fanus Ghorjani, Hanna Getachew, Matheus Galiza, Oliver Pollex, Padmavathi Reddy, Sauradeep Bhattacharyya.

---

## Does the Project Do What It Is Intended To Do?

Yes. The application successfully matches users with VHS courses that are relevant to their interests, while also balancing personal preferences (like price sensitivity) with platform goals (such as promoting under-enrolled courses). We use a semantic matching algorithm and a consensus-based ranking system to ensure fair and intelligent recommendations.

---

## Key Features

- 🏠 **Home Page**: Overview and navigation
- 🔎 **Courses Page**:
  - Keyword-based semantic search
  - Multi-criteria filtering
  - Sorted results table
  - Ranking based on user preferences and platform goals

---

## Matching Algorithm and Design Rationale

Initially, we explored string-based methods like Levenshtein distance, but they were too sensitive to spelling and failed to capture intent—especially in a multilingual context.

Instead, we use **semantic embeddings** via `sentence-transformers`. This approach encodes both user queries and course descriptions into vector representations that capture meaning. We then compute **cosine similarity** between vectors to identify relevant courses.

To respect user priorities (e.g., budget) and platform strategies (e.g., promoting specific courses), we implement a **preference-based scoring system** and combine rankings using the **Kemeny-Young consensus algorithm**.

---

## Consensus Ranking: Why Kemeny?

We chose **Kemeny-Young** to merge user and platform rankings fairly.

- ✅ Balances both sets of preferences
- ✅ Avoids arbitrary weightings
- ✅ Minimizes total pairwise disagreement between lists

**How it works**:
- Each input ranking (user, platform) is treated as a vote.
- The algorithm calculates pairwise disagreements across all possible rankings.
- The ranking with the fewest total disagreements is chosen as the final consensus.

---

## Problems We Faced

- 🔤 **String Matching Limitations**: Keyword-based search was insufficient for intent detection.
- 🌐 **Multilingual Data**: Dealing with German-language data required semantic solutions (we worked with translation APIs but the data was very large, so it took a long time).
- 🔧 **Integration Issues**: Full integration between the backend and the HTML UI is ongoing. A lightweight test version is currently functional.
- 🧩 **Parallel Development**: Backend/frontend components evolved separately, which introduced temporary mismatches.

---

## Setting Up the Environment

### 1. Clone the repo:

```bash
git clone https://github.com/olivepol/DSA2025_birds
cd DSA2025_birds
```

### 2. Set up the environment:

```bash
conda env create -f environment.yml
conda activate DSA2025_birds_webapp
```

### 3. Run the app:

```bash
flask run
```

### 4. Keep dependencies up to date:

```bash
conda env export --no-builds > environment.yml
```

### 5. Collaborator Updates:

Periodically update your local environment:

```bash
conda env update --file environment.yml --prune
```

---

## Hosted Version

You can access a hosted demo of the application at:

🔗 **https://dsabirds.pythonanywhere.com**

> Username: `dsabirds`  
> Password: `HertieDSA2025-birds`

---

## Project Status

✅ Core functionality complete  
🛠️ Full UI integration in progress  
🚀 Demo version live

---

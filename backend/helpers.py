from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from .models import Question, TestLog, User


def detect_drift_from_logs(logs: list[dict]) -> bool:
    if len(logs) < 2:
        return False
    recent = logs[-2:]
    if all(not log.get("correct", True) for log in recent):
        return True
    latest = logs[-1]
    return (
        latest.get("difficulty", "").lower() == "easy"
        and int(latest.get("time_taken_seconds") or 0) > 60
    )


def detect_drift(db: Session, user_id: int, topic: Optional[str] = None) -> bool:
    recent_query = (
        db.query(TestLog)
        .join(Question, TestLog.question_id == Question.id)
        .filter(TestLog.user_id == user_id)
    )
    if topic:
        recent_query = recent_query.filter(Question.topic == topic)
    recent = recent_query.order_by(TestLog.created_at.desc()).limit(2).all()
    log_payload = [
        {
            "time_taken_seconds": log.time_taken_seconds,
            "difficulty": log.question.difficulty if log.question else None,
            "correct": log.is_correct,
        }
        for log in reversed(recent)
    ]
    return detect_drift_from_logs(log_payload)


def mock_rag_pipeline(topic: str) -> str:
    return f"[RAG Generated] Here is a simplified concept summary for {topic}..."


def serialize_question(question: Question) -> dict:
    return {
        "id": question.id,
        "topic": question.topic,
        "difficulty": question.difficulty,
        "text": question.text,
        "options": question.options or [],
    }


def recent_question_ids(
    db: Session,
    user_id: int,
    topic: Optional[str] = None,
    limit: int = 3,
) -> list[int]:
    rows_query = (
        db.query(TestLog.question_id)
        .join(Question, TestLog.question_id == Question.id)
        .filter(TestLog.user_id == user_id)
    )
    if topic:
        rows_query = rows_query.filter(Question.topic == topic)
    rows = rows_query.order_by(TestLog.created_at.desc()).limit(limit).all()
    return [row[0] for row in rows if row[0] is not None]


def pick_question(
    db: Session,
    user: User,
    topic: Optional[str] = None,
    drift_detected: Optional[bool] = None,
) -> Optional[Question]:
    is_drifting = user.drift_detected if drift_detected is None else drift_detected
    target_difficulty = "medium"
    if is_drifting or user.current_skill < 0.4:
        target_difficulty = "easy"
    elif user.current_skill > 0.7:
        target_difficulty = "hard"

    recent_ids = recent_question_ids(db, user.id, topic=topic, limit=3)

    candidate_query = db.query(Question).filter(Question.difficulty == target_difficulty)
    if topic:
        candidate_query = candidate_query.filter(Question.topic == topic)
    if recent_ids:
        candidate_query = candidate_query.filter(~Question.id.in_(recent_ids))
    candidate = candidate_query.order_by(func.random()).first()
    if candidate:
        return candidate

    fallback_query = db.query(Question).filter(Question.difficulty == target_difficulty)
    if topic:
        fallback_query = fallback_query.filter(Question.topic == topic)
    fallback = fallback_query.order_by(func.random()).first()
    if fallback:
        return fallback

    any_query = db.query(Question)
    if topic:
        any_query = any_query.filter(Question.topic == topic)
    if recent_ids:
        any_query = any_query.filter(~Question.id.in_(recent_ids))
    candidate = any_query.order_by(func.random()).first()
    if candidate:
        return candidate

    return db.query(Question).order_by(func.random()).first()


def seed_if_empty(db: Session) -> None:
    if db.query(Question).count() > 0:
        return

    seeds = [
        Question(
            topic="Arrays",
            difficulty="easy",
            text="What is the time complexity of accessing an element in an array?",
            options=["O(n)", "O(log n)", "O(1)", "O(n log n)"],
            correct_option="C",
            correct="O(1)",
        ),
        Question(
            topic="Arrays",
            difficulty="easy",
            text="Which data structure property makes arrays efficient for index-based lookup?",
            options=[
                "Contiguous memory allocation",
                "Automatic sorting",
                "Hash-based access",
                "Recursive storage",
            ],
            correct_option="A",
            correct="Contiguous memory allocation",
        ),
        Question(
            topic="Arrays",
            difficulty="easy",
            text="What happens when you access an array index outside its valid range in most languages?",
            options=[
                "It always returns zero",
                "It may raise an error or exception",
                "It sorts the array first",
                "It duplicates the last element",
            ],
            correct_option="B",
            correct="It may raise an error or exception",
        ),
        Question(
            topic="Arrays",
            difficulty="easy",
            text="Which operation is usually expensive in the middle of a fixed-size array?",
            options=[
                "Reading by index",
                "Updating by index",
                "Inserting an element",
                "Comparing two values",
            ],
            correct_option="C",
            correct="Inserting an element",
        ),
        Question(
            topic="Arrays",
            difficulty="medium",
            text="Find the missing number in an array of 1 to N.",
            options=[
                "Use n*(n+1)/2 - sum(array)",
                "Sort the array and pick the middle element",
                "Use binary search on indexes",
                "Use two pointers from both ends",
            ],
            correct_option="A",
            correct="Use n*(n+1)/2 - sum(array)",
        ),
        Question(
            topic="Arrays",
            difficulty="medium",
            text="Which technique is commonly used to find a pair with a target sum in a sorted array?",
            options=[
                "Binary lifting",
                "Two pointers",
                "Union-find",
                "Level-order traversal",
            ],
            correct_option="B",
            correct="Two pointers",
        ),
        Question(
            topic="Arrays",
            difficulty="medium",
            text="What is the usual time complexity of binary search on a sorted array?",
            options=["O(1)", "O(log n)", "O(n)", "O(n log n)"],
            correct_option="B",
            correct="O(log n)",
        ),
        Question(
            topic="Arrays",
            difficulty="medium",
            text="Which preprocessing helps answer many range sum queries quickly?",
            options=[
                "Prefix sums",
                "Heapify the array",
                "Topological order",
                "Union-find compression",
            ],
            correct_option="A",
            correct="Prefix sums",
        ),
        Question(
            topic="Arrays",
            difficulty="hard",
            text="Explain the logic for trapping rain water problem.",
            options=[
                "Greedy DFS traversal",
                "Two pointers with left_max and right_max tracking",
                "Only prefix sums are enough",
                "Simple binary search over heights",
            ],
            correct_option="B",
            correct="Two pointers with left_max and right_max tracking",
        ),
        Question(
            topic="Arrays",
            difficulty="hard",
            text="What is the key idea behind Kadane's algorithm?",
            options=[
                "Track the best subarray ending at the current index",
                "Sort the array first",
                "Use a stack for every element",
                "Compare only the first and last values",
            ],
            correct_option="A",
            correct="Track the best subarray ending at the current index",
        ),
        Question(
            topic="DP",
            difficulty="easy",
            text="What is the base case for Fibonacci DP?",
            options=["n <= 1", "n == 2", "n > 2", "No base case is required"],
            correct_option="A",
            correct="n <= 1",
        ),
        Question(
            topic="DP",
            difficulty="easy",
            text="What does DP usually optimize compared to plain recursion?",
            options=[
                "Keyboard shortcuts",
                "Repeated subproblem computation",
                "File storage size only",
                "Network latency",
            ],
            correct_option="B",
            correct="Repeated subproblem computation",
        ),
        Question(
            topic="DP",
            difficulty="easy",
            text="Which property is commonly associated with dynamic programming problems?",
            options=[
                "Overlapping subproblems",
                "Randomized pivots",
                "Disjoint set merging",
                "Only tree traversals",
            ],
            correct_option="A",
            correct="Overlapping subproblems",
        ),
        Question(
            topic="DP",
            difficulty="easy",
            text="In bottom-up DP, where do we typically start?",
            options=[
                "From the answer and move backwards randomly",
                "From base cases and build upwards",
                "From graph edges only",
                "From the largest subproblem first without order",
            ],
            correct_option="B",
            correct="From base cases and build upwards",
        ),
        Question(
            topic="DP",
            difficulty="medium",
            text="Why is memoization useful in dynamic programming?",
            options=[
                "It sorts the states before processing",
                "It avoids recomputing overlapping subproblems",
                "It reduces all problems to greedy solutions",
                "It removes the need for base cases",
            ],
            correct_option="B",
            correct="It avoids recomputing overlapping subproblems",
        ),
        Question(
            topic="DP",
            difficulty="medium",
            text="What does the state usually represent in DP?",
            options=[
                "A complete final answer only",
                "A smaller subproblem description",
                "The color of nodes in a graph",
                "The runtime of the compiler",
            ],
            correct_option="B",
            correct="A smaller subproblem description",
        ),
        Question(
            topic="DP",
            difficulty="medium",
            text="In 0/1 knapsack DP, which choice is considered for each item?",
            options=[
                "Take it or leave it",
                "Sort it or reverse it",
                "Push it into a queue",
                "Only take fractional amounts",
            ],
            correct_option="A",
            correct="Take it or leave it",
        ),
        Question(
            topic="DP",
            difficulty="medium",
            text="Which traversal order often works for 2D tabulation problems?",
            options=[
                "Any random order",
                "An order where dependencies are already computed",
                "Strictly depth-first recursion only",
                "Only descending diagonals",
            ],
            correct_option="B",
            correct="An order where dependencies are already computed",
        ),
        Question(
            topic="DP",
            difficulty="hard",
            text="Which DP state choice is most important when designing a solution?",
            options=[
                "Choosing colors for the UI",
                "Defining subproblems that capture enough information",
                "Using recursion in every solution",
                "Avoiding transitions between states",
            ],
            correct_option="B",
            correct="Defining subproblems that capture enough information",
        ),
        Question(
            topic="DP",
            difficulty="hard",
            text="What is the key optimization in space-optimized DP?",
            options=[
                "Store only states needed for future transitions",
                "Always use hash maps instead of arrays",
                "Replace loops with recursion",
                "Sort the input at every step",
            ],
            correct_option="A",
            correct="Store only states needed for future transitions",
        ),
        Question(
            topic="Graphs",
            difficulty="easy",
            text="Which traversal uses a queue?",
            options=["DFS", "BFS", "Topological sort", "Dijkstra only"],
            correct_option="B",
            correct="BFS",
        ),
        Question(
            topic="Graphs",
            difficulty="easy",
            text="What does an edge represent in a graph?",
            options=[
                "A relationship between two vertices",
                "The height of a tree",
                "A sorted position in an array",
                "A memoized DP state",
            ],
            correct_option="A",
            correct="A relationship between two vertices",
        ),
        Question(
            topic="Graphs",
            difficulty="easy",
            text="Which traversal usually uses recursion or an explicit stack?",
            options=["BFS", "DFS", "Prim's algorithm", "Kruskal's algorithm"],
            correct_option="B",
            correct="DFS",
        ),
        Question(
            topic="Graphs",
            difficulty="easy",
            text="A graph with no cycles and connected is called what?",
            options=["Heap", "Tree", "Trie", "Matrix"],
            correct_option="B",
            correct="Tree",
        ),
        Question(
            topic="Graphs",
            difficulty="medium",
            text="When is topological sorting valid?",
            options=[
                "For any undirected graph",
                "Only for weighted graphs",
                "For directed acyclic graphs",
                "Only when every node has degree two",
            ],
            correct_option="C",
            correct="For directed acyclic graphs",
        ),
        Question(
            topic="Graphs",
            difficulty="medium",
            text="What does BFS guarantee in an unweighted graph?",
            options=[
                "The lexicographically smallest path",
                "The shortest path in number of edges",
                "A minimum spanning tree",
                "A topological order",
            ],
            correct_option="B",
            correct="The shortest path in number of edges",
        ),
        Question(
            topic="Graphs",
            difficulty="medium",
            text="Which algorithm is commonly used to detect cycles in an undirected graph with DSU?",
            options=[
                "Union-find",
                "Bellman-Ford",
                "Kadane's algorithm",
                "Binary search",
            ],
            correct_option="A",
            correct="Union-find",
        ),
        Question(
            topic="Graphs",
            difficulty="medium",
            text="What information does an adjacency list store efficiently?",
            options=[
                "All-pairs shortest paths",
                "Neighbors of each vertex",
                "Only edge weights sorted",
                "The graph drawing coordinates",
            ],
            correct_option="B",
            correct="Neighbors of each vertex",
        ),
        Question(
            topic="Graphs",
            difficulty="hard",
            text="Why does Dijkstra's algorithm fail with negative edge weights?",
            options=[
                "It requires an adjacency matrix",
                "Its greedy choice can become invalid later",
                "It only works on trees",
                "It cannot process more than one source",
            ],
            correct_option="B",
            correct="Its greedy choice can become invalid later",
        ),
        Question(
            topic="Graphs",
            difficulty="hard",
            text="Which algorithm can handle shortest paths with negative edges if there is no negative cycle?",
            options=["Dijkstra", "Bellman-Ford", "Kruskal", "Prim"],
            correct_option="B",
            correct="Bellman-Ford",
        ),
    ]
    db.add_all(seeds)
    db.commit()

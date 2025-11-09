"""
Mutation testing configuration for mutmut
https://mutmut.readthedocs.io/
"""


def pre_mutation(context):
    """
    Called before each mutation is tested.
    Can be used to skip certain mutations.
    """
    # Skip mutations in test files
    if "test_" in context.filename:
        context.skip = True

    # Skip mutations in migration files
    if "alembic/versions" in context.filename:
        context.skip = True


def post_mutation(context):
    """
    Called after each mutation is tested.
    Can be used for custom reporting.
    """
    pass


# Paths to mutate
paths_to_mutate = "src/"

# Paths to exclude from mutation
paths_to_exclude = [
    "tests/",
    "alembic/",
    "__pycache__/",
    ".venv/",
]

# Test command
tests_dir = "tests/"
test_command = "pytest -x --tb=short"

# Runner configuration
runner = "python"

# Coverage threshold (percentage)
coverage_threshold = 80

# Mutation operators to use
dict_synonyms = ["dict", "OrderedDict", "defaultdict"]

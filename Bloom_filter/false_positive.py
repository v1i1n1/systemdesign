
import redis

# Connect to Redis Stack
r = redis.Redis(
    host="localhost",
    port=6380,
    decode_responses=True
)

FILTER_NAME = "false_positive_demo"

# Step 1: Delete previous filter
r.delete(FILTER_NAME)

# Step 2: Create filter with high error rate
r.execute_command(
    "BF.RESERVE",
    FILTER_NAME,
    0.5,
    10
)

print("Bloom Filter created!")
print("Error rate: 50%")
print("Expected capacity: 10")

# Step 3: Insert only three usernames
actual_users = [
    "vinayaka",
    "rahul",
    "priya"
]

for user in actual_users:
    r.execute_command(
        "BF.ADD",
        FILTER_NAME,
        user
    )

print("\nActual users:", actual_users)

# Step 4: Search for usernames never inserted
print("\nSearching for false positives...")

found = False

for i in range(10000):

    username = f"unknown_user_{i}"

    result = r.execute_command(
        "BF.EXISTS",
        FILTER_NAME,
        username
    )

    if result == 1:

        print("\nFALSE POSITIVE FOUND!")
        print("Username:", username)
        print("Bloom Filter: Possibly exists")
        print("Actual database: User does not exist")

        found = True
        break

if not found:
    print("\nNo false positive found in this trial.")

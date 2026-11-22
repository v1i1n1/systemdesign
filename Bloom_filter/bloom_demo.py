
# Simple Bloom Filter implementation
# 8-bit array and one hash function

bit_array = [0] * 8

# Hash function
def hash_function(word):
    hash_values = {
        "apple": 3,
        "ball": 6,
        "cat": 2,
        "dog": 5,
        "elephant": 6
    }

    return hash_values[word] % 8


# Insert an item
def add(word):
    position = hash_function(word)

    bit_array[position] = 1

    print(f"Inserted {word} -> bit {position}")


# Check an item
def check(word):
    position = hash_function(word)

    if bit_array[position] == 0:
        print(f"{word}: Definitely NOT present")
    else:
        print(f"{word}: MAYBE present")


# Insert three words
add("apple")
add("ball")
add("cat")

print("\nBit Array:")
print(bit_array)

print("\nChecking words:")

check("dog")
check("elephant")
check("apple")

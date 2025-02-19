import pickle
import os

# Set up the path to the pickle file
project_dir = os.path.join('/Users', 'anikalakhani', 'neurobio240', 'nn-playground')
pickle_path = os.path.join(project_dir, 'biased_cars_1', 'att_dict_simplified.p')

# Load and examine the pickle file
with open(pickle_path, 'rb') as f:
    att_dict = pickle.load(f)

# Print 5 sample entries
print("Sample entries from the attribute dictionary:")
print("-" * 50)
for i, (image_name, attributes) in enumerate(list(att_dict.items())[:5]):
    print(f"Image {i+1}:")
    print(f"Filename: {image_name}")
    print(f"Class label: {attributes[3]}")  # The class label is at index 3
    print()

# Look up specific filename
while True:
    filename = input("\nEnter a filename to look up (or 'q' to quit): ")
    if filename.lower() == 'q':
        break
        
    if filename in att_dict:
        print(f"Class label for {filename}: {att_dict[filename][3]}")
    else:
        print(f"File '{filename}' not found in the attribute dictionary") 
# -*- coding: utf-8 -*-
"""identifying_cars.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1UznUmJpmeB36nG8eeo7Nat1h_N4NOOCd

I used Perplexity.AI's Pro model to help with this assignment. Below was my prompt:

Attached is my existing code [I attached the Assignment 1 file], which uses the MNIST dataset on a homemade CNN. here is a tutorial to create a custom dataloader for more complicated datasets: https://github.com/MorganBDT/pytorch_data_loader_tutorial and here is another relevant resource: https://pytorch.org/tutorials/beginner/basics/data_tutorial.html

1. Walk me through the contents of the above websites. Teach me the basics of creating a custom dataloader (conceptually).
2. Show me step-by-step how to create a custom dataloader for the following dataset: https://dataverse.harvard.edu/api/access/datafile/5347218 (corresponding data labels can be found here: https://dataverse.harvard.edu/api/access/datafile/5793795)

These are more specific instructions: "a. Write a new Dataset class that does the following: for all images which have a label in att_dict_simplified.p, read the images from the given directories and the labels from the dictionary. For each sub-folder under biased_cars_1/, training data is located under 'train/images/' and validation data is under 'val/images/'. The original train/val split provided by the dataset should be used. Images under the 'labels' folders can be ignored for this assignment.

Note: The folder structure of the dataset should be left as-is: the approach of writing a script to re-organize the data is less helpful for learning than writing a Dataset class that uses the original structure, which is a bit convoluted (which is helpful for learning how to deal with such a situation)"
"""

## IMPORTS
# ML imports
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms, models
from PIL import Image
import pickle
import matplotlib.pyplot as plt
import os

## DEVICE CONFIGURATION
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(f"Using device: {device}")

# Remove Google Drive mounting and Colab-specific download code
# Instead, assume the dataset is already downloaded and extracted to your project directory

## DEFINE PROJECT DIRECTORY
# Update this path to your project directory
project_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.join(project_dir, 'biased_cars_1')
att_dict_path = os.path.join(root_dir, 'att_dict_simplified.p')

## CREATING DATASET CLASS
# Structure is very similar to online PyTorch tutorial, except I'm not doing transform/target_transform
class BiasedCarsDataset(Dataset):
    def __init__(self, root_dir, att_dict_path, transform=None, is_train=True):
        """
        Args:
            root_dir (string): Directory with all the images.
            att_dict_path (string): Path to the att_dict_simplified.p file.
            transform (callable, optional): Optional transform to be applied
                on a sample.
            is_train (bool): If True, load training data; otherwise, load validation data.
        """
        self.root_dir = root_dir
        self.transform = transform
        self.is_train = is_train
        
        # Load labels from att_dict_simplified.p
        print(f"Loading attribute dictionary from {att_dict_path}")
        with open(att_dict_path, 'rb') as f:
            self.att_dict = pickle.load(f)
        
        self.image_list = []
        self._load_images()
        
        if len(self.image_list) == 0:
            raise ValueError("No valid images found in the dataset!")
        
        # Get unique car model labels (4th element, index 3)
        self.num_classes = len(set(self.att_dict[key][3] for key in self.att_dict))
        print(f"Found {self.num_classes} unique car model classes")

    def _load_images(self):
        """Load the images from the specified directory structure."""
        split_type = 'train' if self.is_train else 'val'
        print(f"\nLoading {split_type} images from {self.root_dir}")
        
        # Debug: Print a few sample keys from att_dict
        print("\nSample keys from attribute dictionary:")
        sample_keys = list(self.att_dict.keys())[:5]
        print(sample_keys)
        
        total_images = 0
        for car_class in os.listdir(self.root_dir):
            car_class_path = os.path.join(self.root_dir, car_class)
            
            if not os.path.isdir(car_class_path) or car_class == '__pycache__':
                continue
            
            images_dir = os.path.join(car_class_path, split_type, 'images')
            
            if not os.path.exists(images_dir):
                print(f"Warning: Directory not found: {images_dir}")
                continue
            
            print(f"\nProcessing {car_class}: {images_dir}")
            
            image_files = [f for f in os.listdir(images_dir) 
                         if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
            
            for image_name in image_files:
                # Use the full image name as the key
                if image_name in self.att_dict:
                    image_path = os.path.join(images_dir, image_name)
                    car_model_label = self.att_dict[image_name][3]
                    self.image_list.append((image_path, car_model_label))
                    total_images += 1
                    if total_images < 5:  # Debug first few successful matches
                        print(f"Successfully matched image: {image_name}")
                        print(f"Label: {car_model_label}")
                else:
                    print(f"Warning: No label found for image {image_name}")
        
        print(f"\nSuccessfully loaded {total_images} images for {split_type} split")
        
        if total_images == 0:
            print("\nAttribute dictionary information:")
            print(f"Number of labels in att_dict: {len(self.att_dict)}")
            print("First few keys in att_dict:", list(self.att_dict.keys())[:5])
            print("\nFirst few image names:", image_files[:5] if image_files else "No images found")
            raise ValueError("No valid images found in the dataset!")

    def __len__(self):
        return len(self.image_list) # same as in PyTorch tutorial

    def __getitem__(self, idx):
        image_path, car_model_label = self.image_list[idx]
        try:
            image = Image.open(image_path).convert('RGB')  # Ensure consistent color format
            if self.transform:
                image = self.transform(image)
            return image, car_model_label
        except FileNotFoundError:
            print(f"Error: Image not found at {image_path}")
            return None  # Handle the error as needed (e.g., return a default image or skip)

## DATA TRANSFORMS
# Define data transformations (based this part off of the data loader GitHub we were given)
data_transforms = {
    'train': transforms.Compose([
        transforms.Resize((224, 224)),  # Resize for ResNet18 (did this instead of a ResizeCrop)
        transforms.RandomHorizontalFlip(),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])  # ImageNet normalization (took the numbers from the GitHub)
    ]),
    'val': transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]) # (took the numbers from the GitHub)
    ]),
}

## TRAINING AND TESTING DATA
# Create Dataset instances based on the predetermined splits in the dataset that use the flag is_train for training data
train_dataset = BiasedCarsDataset(root_dir, att_dict_path, transform=data_transforms['train'], is_train=True)
val_dataset = BiasedCarsDataset(root_dir, att_dict_path, transform=data_transforms['val'], is_train=False)

## CREATE DATA LOADERS FOR TRAIN AND TEST DATA
train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True, num_workers=0)  # Set to 0 for Windows
val_loader = DataLoader(val_dataset, batch_size=32, shuffle=False, num_workers=0)

## SAVE NUMBER OF CLASSES FOUND IN DATASET
# This will prove useful so that we can reshape our model accordingly
num_classes = len(set(train_dataset.att_dict[key][3] for key in train_dataset.att_dict))
print(f"Number of classes: {num_classes}")

## LOADING THE RESNET18 MODEL
# Load pre-trained ResNet18 model as per assignment instructions
model = models.resnet18(pretrained=True)
print("Loaded ResNet18 model")

# Modify the final fully connected layer (since we need it to actually match the number of classes)
# We need there to be as many final neurons as there are classes because the value of a given neuron represents the strength of the prediction of that class
num_ftrs = model.fc.in_features
model.fc = nn.Linear(num_ftrs, num_classes)

model = model.to(device) # if we can, move it to the GPU to save time (if it is available)

## LOSS FUNCTION AND OPTIMIZER (SIMILAR TO ASSIGNMENT 1)
# Define loss function
criterion = nn.CrossEntropyLoss() # same as in assignment 1

# Define optimizer
optimizer = optim.Adam(model.parameters(), lr=1e-2) # same as in assignment 1, except .Adam; I asked Perplexity what it thought was best

# After I got initial results, I asked Cursor (Claude 3.5 Sonnet) how it would improve the accuracy of the model
# It suggested a lower learning rate with a scheduler
# optimizer = optim.Adam(model.parameters(), lr=1e-4, weight_decay=1e-2)
# scheduler = optim.lr_scheduler.StepLR(optimizer, step_size=7, gamma=0.1)

# From Perplexity: "Adam is generally better than SGD, but you can experiment" (note that we used .SGD in Assignment 1)

## TRAINING LOOP AND PRINT RESULTS
# Training loop
def train_model(model, train_loader, val_loader, criterion, optimizer, num_epochs=5):
    train_losses, val_losses, val_accuracies = [], [], []

    for epoch in range(num_epochs): # loop over training epochs
        model.train()  # Set model to training mode
        running_loss = 0.0 # counter for loss function

        # I wonder why we don't use batches here? I guess because we were told to train on all the data?

        for inputs, labels in train_loader:
            inputs = inputs.to(device)
            labels = labels.to(device)

            optimizer.zero_grad()
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()

            running_loss += loss.item() * inputs.size(0)

        epoch_loss = running_loss / len(train_loader.dataset)
        train_losses.append(epoch_loss)

        print("Done training one epoch")

        # Validation
        model.eval()  # Set model to evaluate mode
        val_loss = 0.0
        corrects = 0

        with torch.no_grad():
            for inputs, labels in val_loader:
                inputs = inputs.to(device)
                labels = labels.to(device)

                outputs = model(inputs)
                loss = criterion(outputs, labels)

                val_loss += loss.item() * inputs.size(0)
                _, preds = torch.max(outputs, 1)
                corrects += torch.sum(preds == labels.data)

        val_epoch_loss = val_loss / len(val_loader.dataset)
        val_losses.append(val_epoch_loss)
        val_epoch_acc = corrects.double() / len(val_loader.dataset)
        val_accuracies.append(val_epoch_acc)


        print(f'Epoch {epoch+1}/{num_epochs} - Train Loss: {epoch_loss:.4f} Val Loss: {val_epoch_loss:.4f} Val Acc: {val_epoch_acc:.4f}')

    return train_losses, val_losses, val_accuracies

# TRAIN MODEL AND PLOT RESULTS
num_epochs = 5 # as per the assignment description
# Call model training function previously defined
print("Training model...")
train_losses, val_losses, val_accuracies = train_model(model, train_loader, val_loader, criterion, optimizer, num_epochs)

# Plotting the training and validation loss
plt.figure(figsize=(12, 4))
plt.subplot(1, 2, 1)
plt.plot(train_losses, label='Train Loss')
plt.plot(val_losses, label='Validation Loss')
plt.xlabel('Epoch')
plt.ylabel('Loss')
plt.legend()
plt.title('Training and Validation Loss')

# Plotting the validation accuracy
plt.subplot(1, 2, 2)
plt.plot(val_accuracies, label='Validation Accuracy')
plt.xlabel('Epoch')
plt.ylabel('Accuracy')
plt.legend()
plt.title('Validation Accuracy')

plt.tight_layout()
plt.show()

# Test script to verify dataset and paths
print("\n=== Directory Structure Check ===")
print(f"Project directory: {project_dir}")
print(f"Root directory: {root_dir}")
print(f"Attribute dictionary path: {att_dict_path}")

# Check if directories exist
print("\n=== Path Verification ===")
print(f"Root directory exists: {os.path.exists(root_dir)}")
print(f"Attribute dictionary exists: {os.path.exists(att_dict_path)}")

# List contents of root directory
print("\n=== Root Directory Contents ===")
if os.path.exists(root_dir):
    contents = os.listdir(root_dir)
    print(f"Found {len(contents)} items:")
    for item in contents:
        full_path = os.path.join(root_dir, item)
        if os.path.isdir(full_path):
            print(f"📁 {item}")
        else:
            print(f"📄 {item}")

# Test dataset creation
print("\n=== Dataset Creation Test ===")
try:
    # Create small test datasets
    test_train = BiasedCarsDataset(root_dir, att_dict_path, transform=data_transforms['train'], is_train=True)
    test_val = BiasedCarsDataset(root_dir, att_dict_path, transform=data_transforms['val'], is_train=False)
    
    print(f"\nTraining dataset size: {len(test_train)}")
    print(f"Validation dataset size: {len(test_val)}")
    
    # Test loading a single item
    if len(test_train) > 0:
        sample_img, sample_label = test_train[0]
        print(f"\nSample image shape: {sample_img.shape}")
        print(f"Sample label: {sample_label}")
        
except Exception as e:
    print(f"Error during dataset creation: {str(e)}")

"""# Notes from Perplexity.AI on Custom Dataloaders

**1. Custom DataLoaders: Conceptual Basics (Based on Provided Resources)**

*   **Purpose:** PyTorch's `DataLoader` is a utility that automates batching, shuffling, and parallel data loading. Custom data loaders are essential when your dataset doesn't fit the standard image folder structure or requires specialized loading/preprocessing.
*   **Key Components:**
    *   `Dataset` Class: This is the core. You inherit from `torch.utils.data.Dataset` and implement three essential methods:
        *   `__init__(self, ...)`:  Initialization. This is where you specify the data directory, read your labels, and perform any initial preprocessing.
        *   `__len__(self)`: Returns the total number of samples in your dataset.
        *   `__getitem__(self, idx)`:  This is the most important. Given an index `idx`, it:
            1.  Locates the data sample (e.g., image file).
            2.  Loads the data (e.g., reads the image from disk).
            3.  Applies any necessary transformations (e.g., resizing, normalization).
            4.  Returns the data and its corresponding label as a tuple `(data, label)`.
    *   `DataLoader` Class:  Once you have your `Dataset` class, you create a `DataLoader` instance.  The `DataLoader` takes your `Dataset` object as input and handles batching, shuffling, and parallel loading using multiple worker processes (specified by `num_workers`).

**2. Creating a Custom DataLoader for the Car Dataset**

Okay, let's tackle the car dataset. Here's the structure we need to handle, based on your description:

```
biased_cars_1/
├───0/   (First Category)
│   ├───train/
│   │   └───images/
│   │       ├───image1.jpg
│   │       ├───image2.jpg
│   │       └───...
│   └───val/
│       └───images/
│           ├───image1.jpg
│           ├───image2.jpg
│           └───...
└── att_dict_simplified.p  (Labels)
```
"""
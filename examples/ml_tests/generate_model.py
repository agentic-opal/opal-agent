import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import TensorDataset, DataLoader
from datasets import load_dataset
import numpy as np
import os

from examples.ml_tests.model import SimpleCNN

# ----- 1. Load CIFAR-10 from Hugging Face -----
dataset = load_dataset("cifar10")

train_data = np.array(dataset["train"]["img"])
train_labels = np.array(dataset["train"]["label"])
test_data = np.array(dataset["test"]["img"])
test_labels = np.array(dataset["test"]["label"])

os.makedirs("data", exist_ok=True)
np.save("data/train_images.npy", train_data)
np.save("data/train_labels.npy", train_labels)
np.save("data/test_images.npy", test_data)
np.save("data/test_labels.npy", test_labels)

# ----- 2. Preprocess -----
def preprocess(images):
    images = np.stack([np.array(img) for img in images])
    images = images.transpose((0, 3, 1, 2)) / 255.0  # (N, C, H, W)
    return torch.tensor(images, dtype=torch.float32)

X_train = preprocess(train_data)
y_train = torch.tensor(train_labels, dtype=torch.long)

# Use smaller dataset to speed up
X_train, y_train = X_train[:5000], y_train[:5000]

train_loader = DataLoader(TensorDataset(X_train, y_train), batch_size=64, shuffle=True)


# ----- 4. Train -----
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = SimpleCNN().to(device)
optimizer = optim.Adam(model.parameters(), lr=1e-3)
criterion = nn.CrossEntropyLoss()

for epoch in range(10):
    running_loss = 0.0
    for images, labels in train_loader:
        images, labels = images.to(device), labels.to(device)
        optimizer.zero_grad()
        outputs = model(images)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()
        running_loss += loss.item()
    print(f"Epoch {epoch+1}/10, Loss: {running_loss/len(train_loader):.4f}")

torch.save(model.state_dict(), "cnn_model.pth")
print("Model saved as cnn_model.pth")

# ----- 5. Generate small test dataset -----
X_test = preprocess(test_data[:100])
y_test = np.array(test_labels[:100])
np.save("data/small_test_images.npy", X_test.numpy())
np.save("data/small_test_labels.npy", y_test)
print("Saved small test dataset in data/")

# ----- 6. Function to load model and test dataset -----
def run_inference(test_path_images, test_path_labels):
    model = SimpleCNN()
    model.load_state_dict(torch.load("cnn_model.pth", map_location="cpu"))
    model.eval()

    X = torch.tensor(np.load(test_path_images), dtype=torch.float32)
    y = np.load(test_path_labels)

    with torch.no_grad():
        preds = model(X).argmax(dim=1).numpy()

    accuracy = (preds == y).mean()
    print(f"Inference done. Accuracy: {accuracy:.2%}")
    return preds


# Example usage
if __name__ == "__main__":
    results = run_inference("data/small_test_images.npy", "data/small_test_labels.npy")

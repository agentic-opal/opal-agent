import torch
import numpy as np

from examples.ml_tests.model import SimpleCNN


def run_inference(test_path_images):
    model = SimpleCNN()
    model.load_state_dict(torch.load("cnn_model.pth"))
    model.eval()

    X = torch.tensor(np.load(test_path_images), dtype=torch.float32)

    with torch.no_grad():
        preds = model(X).argmax(dim=1).numpy()

    return preds


if __name__ == "__main__":
    results = run_inference("data/small_test_images.npy", "data/small_test_labels.npy")
    print(results)
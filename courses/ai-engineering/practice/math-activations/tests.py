import warnings

import numpy as np

from solution import relu, sigmoid, softmax


def test_relu_zeroes_negatives():
    got = relu([-2.0, -0.1, 0.0, 3.0])
    assert got is not None, "relu returned None"
    assert np.allclose(got, [0, 0, 0, 3]), f"expected [0, 0, 0, 3], got {np.asarray(got).tolist()}"
    got = relu([[-1, 2], [3, -4]])
    assert np.allclose(got, [[0, 2], [3, 0]]), f"relu should work element-wise on 2-D input, got {np.asarray(got).tolist()}"


def test_sigmoid_values_and_symmetry():
    got = sigmoid([0.0, 2.0, -2.0])
    assert got is not None, "sigmoid returned None"
    assert np.allclose(got, [0.5, 0.8807970779778823, 0.11920292202211755]), f"got {np.asarray(got).tolist()}"
    x = np.linspace(-5, 5, 11)
    assert np.allclose(sigmoid(x) + sigmoid(-x), 1.0), "sigmoid(x) + sigmoid(-x) should be 1"


def test_softmax_known_values_sum_to_one():
    got = softmax([1.0, 2.0, 3.0])
    assert got is not None, "softmax returned None"
    want = np.exp([1, 2, 3]) / np.exp([1, 2, 3]).sum()
    assert np.allclose(got, want), f"expected {want.round(4).tolist()}, got {np.asarray(got).round(4).tolist()}"
    assert np.isclose(np.sum(got), 1.0), "probabilities should sum to 1"


def test_softmax_is_stable_for_huge_logits():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        got = softmax([1000.0, 1001.0, 1002.0])
    assert not np.isnan(got).any(), "got nan: subtract the max logit before np.exp"
    assert np.allclose(got, softmax([0.0, 1.0, 2.0])), f"softmax should ignore a constant shift, got {np.asarray(got).tolist()}"
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        got = softmax([-1000.0, 0.0])
    assert np.allclose(got, [0.0, 1.0]), f"expected [0, 1], got {np.asarray(got).tolist()}"


def test_softmax_works_row_by_row_on_a_batch():
    logits = np.array([[1.0, 2.0, 3.0], [5.0, 5.0, 5.0], [800.0, 0.0, -800.0]])
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        got = softmax(logits)
    assert np.shape(got) == (3, 3), f"expected shape (3, 3), got {np.shape(got)}"
    assert np.allclose(np.sum(got, axis=1), 1.0), f"each row should sum to 1, row sums are {np.sum(got, axis=1).tolist()}"
    assert np.allclose(got[1], [1 / 3] * 3), f"equal logits give equal probabilities, got {got[1].tolist()}"
    assert np.allclose(got[2], [1, 0, 0]), f"expected [1, 0, 0], got {got[2].tolist()}"

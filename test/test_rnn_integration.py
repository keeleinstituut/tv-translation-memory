import os

import numpy as np
import pytest

if not hasattr(np, "sctype2char"):
    np.sctype2char = lambda x: np.dtype(x).char

from TMPreprocessor.Xml.rnn import elmansentlstm as rnn_module
from TMPreprocessor.Xml.rnn.elmansentlstm import model


def _model_dir():
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    return os.path.join(
        repo_root,
        "src",
        "TMPreprocessor",
        "Xml",
        "rnn",
        "data",
        "en-es",
        "alltag-model",
    )


def _infer_dims(model_dir):
    embeddings = np.load(os.path.join(model_dir, "embeddings.npy"))
    w = np.load(os.path.join(model_dir, "W.npy"))
    wifoc = np.load(os.path.join(model_dir, "Wifoc.npy"))

    ne_plus_one, de = embeddings.shape
    nh, nc = w.shape
    cs = wifoc.shape[0] // de

    return {
        "ne": int(ne_plus_one - 1),
        "de": int(de),
        "nh": int(nh),
        "nc": int(nc),
        "cs": int(cs),
    }


@pytest.mark.integration
def test_rnn_compile_and_infer():
    rnn_module.theano.config.cxx = ""
    rnn_module.theano.config.mode = "FAST_COMPILE"

    model_dir = _model_dir()
    dims = _infer_dims(model_dir)

    rnn = model(
        nh=dims["nh"],
        nc=dims["nc"],
        ne=dims["ne"],
        de=dims["de"],
        cs=dims["cs"],
    )
    rnn.load(model_dir)

    np.random.seed(0)
    sent_len = 4
    src_len = 5
    idxs = np.random.randint(0, dims["ne"], size=(sent_len, dims["cs"])).astype("int32")
    z = np.random.randint(0, dims["ne"], size=(src_len,)).astype("int32")
    zy = np.random.randint(0, dims["nc"], size=(src_len,)).astype("int32")

    preds = rnn.classify(idxs, z, zy)
    assert preds.shape[0] == sent_len
    assert np.all((preds >= 0) & (preds < dims["nc"]))


@pytest.mark.integration
def test_lstm_hidden_shape():
    rnn_module.theano.config.cxx = ""
    rnn_module.theano.config.mode = "FAST_COMPILE"

    np.random.seed(0)
    nh = 4
    de = 6
    x = rnn_module.T.matrix()
    lstm = rnn_module.LSTM(nh, de, x, "test")

    f = rnn_module.theano.function([x], lstm.hidden)
    x_val = np.random.randn(5, de).astype(rnn_module.theano.config.floatX)
    out = f(x_val)

    assert out.shape == (5, nh)


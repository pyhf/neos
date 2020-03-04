# AUTOGENERATED! DO NOT EDIT! File to edit: 00_models.ipynb (unless otherwise specified).

__all__ = ['init_config', 'init_model', 'expected_data', 'logpdf', 'hepdata_like', 'Model', 'nn_model_maker']

# Cell
import pyhf
import jax
from jax.config import config
from jax.experimental import stax

# avoid those precision errors!
config.update("jax_enable_x64", True)

pyhf.set_backend(pyhf.tensor.jax_backend())

# Cell
# functional
from collections import namedtuple

_Config = namedtuple("_Config", ["poi_index","npars","suggested_init","suggested_bounds"])

def init_config():
    return _Config(0,2,jax.numpy.asarray([1.0, 1.0]),jax.numpy.asarray(
            [jax.numpy.asarray([0.0, 10.0]), jax.numpy.asarray([0.0, 10.0])]
        ))

Model = namedtuple("Model", ["sig", "nominal", "uncert", "factor", "aux", "config"])

def init_model(spec):
    sig, nominal, uncert = spec
    factor = (nominal / uncert) ** 2
    aux = 1.0 * factor
    config = init_config()
    return Model(sig, nominal, uncert, factor, aux, config)

def expected_data(model, pars, include_auxdata=True):
    mu, gamma = pars
    expected_main = jax.numpy.asarray([gamma * model.nominal + mu * model.sig])
    aux_data = jax.numpy.asarray([model.aux])
    return jax.numpy.concatenate([expected_main, aux_data])

@jax.jit
def logpdf(model, pars, data):
    maindata, auxdata = data
    main, _ = expected_data(model,pars)
    mu, gamma = pars
    main = pyhf.probability.Poisson(main).log_prob(maindata)
    constraint = pyhf.probability.Poisson(gamma * model.factor).log_prob(auxdata)
    # sum log probs over bins
    return jax.numpy.asarray([jax.numpy.sum(main + constraint,axis=0)])


def hepdata_like(signal_data, bkg_data, bkg_uncerts, batch_size=None):
    return init_model([signal_data, bkg_data, bkg_uncerts])



# Cell
def nn_model_maker(nn_params):
    # instantiate nn architecture
    _, predict = stax.serial(stax.Dense(5), stax.Relu, stax.Dense(2), stax.LogSoftmax)
    # grab data
    keys = [1, 2, 3]
    batch_size = 5000
    a, b, c = get_three_blobs(keys, batch_size)
    s, b, db = hists_from_nn_bkg_var(predict, nn_params, a, jax.numpy.asarray([b, c]))

    # arbitrary scaling:
    s, b, db = s / 5.0, b / 10.0, db / 10.0
    print(f"model: {s},{b},{db}")
    m = hepdata_like(s, b, db)
    nompars = m.config.suggested_init
    bonlypars = jax.numpy.asarray([x for x in nompars])
    bonlypars = jax.ops.index_update(bonlypars, m.config.poi_index, 0.0)
    return m, bonlypars
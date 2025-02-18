import numpy as np

from keras_core import initializers
from keras_core import layers
from keras_core import ops
from keras_core import testing


class TimeDistributedTest(testing.TestCase):
    def test_basics(self):
        self.run_layer_test(
            layers.TimeDistributed,
            init_kwargs={"layer": layers.Dense(1, use_bias=False)},
            input_shape=(3, 2, 4),
            expected_output_shape=(3, 2, 1),
            expected_num_trainable_weights=1,
            expected_num_non_trainable_weights=0,
            supports_masking=True,
        )

    def test_build(self):
        inputs = layers.Input(shape=(10, 128, 128, 3), batch_size=32)
        conv_2d_layer = layers.Conv2D(64, (3, 3))
        outputs = layers.TimeDistributed(conv_2d_layer)(inputs)
        self.assertEqual(outputs.shape, (32, 10, 126, 126, 64))

    def test_correctness(self):
        sequence = np.arange(24).reshape((3, 2, 4)).astype("float32")
        layer = layers.Dense(
            1,
            kernel_initializer=initializers.Constant(0.01),
            use_bias=False,
        )
        layer = layers.TimeDistributed(layer=layer)
        output = layer(sequence)
        self.assertAllClose(
            np.array(
                [[[0.06], [0.22]], [[0.38], [0.53999996]], [[0.7], [0.86]]]
            ),
            output,
        )

    def test_masking(self):
        class MaskedDense(layers.Wrapper):
            def __init__(self, units, **kwargs):
                layer = layers.Dense(
                    units,
                    kernel_initializer=initializers.Constant(0.01),
                    use_bias=False,
                )
                super().__init__(layer, **kwargs)
                self.supports_masking = True

            def call(self, inputs, training=False, mask=None):
                unmasked = self.layer.call(inputs)
                if mask is None:
                    return unmasked
                else:
                    return ops.transpose(
                        ops.transpose(unmasked) * ops.cast(mask, inputs.dtype)
                    )

        sequence = np.arange(24).reshape((3, 2, 4)).astype("float32")
        layer = layers.TimeDistributed(layer=MaskedDense(1))
        mask = np.array([[False, True], [True, False], [True, True]])
        output = layer(sequence, mask=mask)
        self.assertAllClose(
            np.array([[[0], [0.22]], [[0.38], [0]], [[0.7], [0.86]]]),
            output,
        )

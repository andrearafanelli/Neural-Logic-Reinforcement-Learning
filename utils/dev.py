import tensorflow as tf

gpus = tf.config.list_physical_devices('GPU')
print([
    f"{tf.config.experimental.get_device_details(gpu).get('device_name', 'unknown')} {gpu.name}"
    for gpu in gpus
])

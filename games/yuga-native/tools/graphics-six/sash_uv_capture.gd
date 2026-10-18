extends "res://tools/visual-rounds/capture_groom.gd"
## Review-only selected sash UV revision; matched source comparison. No runtime geometry or material writes.
## Both branches use this exact helper; admission differs only in three GLBs.
const SOURCE_PINS := {
  "baseline": [
    "e98c9110161e49b653e98b6f4ca1dda997ad891cf73b737abd18f319bb3c2b82",
    "dfa9a41adab7cfd5c60416a66d2b95c4d1ab06d081b64ee7a9f5ff5c7744474b",
    "8b74504c07d38416032ea22e37061d69061baaf0b86e78dec27417c8927e39f9"
  ],
  "candidate": [
    "db4b2ec7a14cad72299d462c1265374f615d5e9d8b8852c4669e1f960f78245e",
    "b5949c9d427e9684a13fa525212eedc87dfa207d2c70fba5ebe6a4b1eda61005",
    "aef8ae5837c0bf0a9ed5850ae649d6368ec1e87c0728d501f1780bba325a9d6a"
  ]
}
const RAW_PATHS := ["res://assets/heroes/rama-hero.glb", "res://assets/heroes/rama-hero-mid.glb", "res://assets/heroes/rama-hero-far.glb"]
const REQUIRED_MOTION := "8c3771a343a0538d749147393d0c407b1fb377d774a91b4cf99734e4852520f8"
const REQUIRED_FINISH := "6eb51ce8f34a3d5a33deb142ca92aaa20505516b0ee8fff3ca445bcab603078a"
const SASH_VERTEX_IDS := [7716, 7717, 7718, 7719, 7720, 7721, 7722, 7723, 7724, 7725, 7726, 7727, 7728, 7729, 7730, 7731, 7732, 7733, 7734, 7735, 7736, 7737, 7738, 7739, 7740, 7741, 7742, 7743, 7744, 7745, 7746, 7747, 7748, 7749, 7750, 7751, 7752, 7753, 7754, 7755, 7756, 7757, 7758, 7759, 7760, 7761, 7762, 7763, 7764, 7765, 7766, 7767, 7768, 7769, 7770, 7771, 7772, 7773, 7774, 7775, 7776, 7777, 7778, 7779, 7780, 7781, 7782, 7783, 7784, 7785, 7786, 7787, 7788, 7789, 7790, 7791, 7792, 7793, 7794, 7795, 7796, 7797, 7798, 7799, 7800, 7801, 7802, 7803, 7804, 7805, 7806, 7807, 7808, 7809, 7810, 7811, 7812, 7813, 7814, 7815, 7816, 7817, 7818, 7819, 7820, 7821, 7822, 7823, 7824, 7825, 7826, 7827, 7828, 7829, 7830, 7831, 7832, 7833, 7834, 7835, 7836, 7837, 7838, 7839, 7840, 7841, 7842, 7843, 7844, 7845, 7846, 7847, 7848, 7849, 7850, 7851, 7852, 7853, 7854, 7855, 7856, 7857, 7858, 7859, 7860, 7861, 7862, 7863, 7864, 7865, 7866, 7867, 7868, 7869, 7870, 7871, 7872, 7873, 7874, 7875, 7876, 7877, 7878, 7879, 7880, 7881, 7882, 7883, 7884, 7885, 7886, 7887, 7888, 7889, 7890, 7891, 7892, 7893, 7894, 7895, 7896, 7897, 7898, 7899, 7900, 7901, 7902, 7903, 7904, 7905, 7906, 7907, 7908, 7909, 7910, 7911, 7912, 7913, 7914, 7915, 7916, 7917, 7918, 7919, 7920, 7921, 7922, 7923, 7924, 7925, 7926, 7927, 7928, 7929, 7930, 7931, 7932, 7933, 7934, 7935, 7936, 7937, 7938, 7939, 7940, 7941, 7942, 7943, 7944, 7945, 7946, 7947, 7948, 7949, 7950, 7951, 7952, 7953, 7954, 7955, 7956, 7957, 7958, 7959, 7960, 7961, 7962, 7963, 7964, 7965, 7966, 7967, 7968, 7969, 7970, 7971, 7972, 7973, 7974, 7975, 7976, 7977, 7978, 7979, 7980, 7981, 7982, 7983, 7984, 7985, 7986, 7987, 7988, 7989, 7990, 7991, 7992, 7993, 7994, 7995, 7996, 7997, 7998, 7999, 8000, 8001, 8002, 8003, 8004, 8005, 8006, 8007, 8008, 8009, 8010, 8011, 8012, 8013, 8014, 8015, 8016, 8017, 8018, 8019, 8020, 8021, 8022, 8023, 8024, 8025, 8026, 8027, 8028, 8029, 8030, 8031, 8032, 8033, 8034, 8035, 8036, 8037, 8038, 8039, 8040, 8041, 8042, 8043, 8044, 8045, 8046, 8047, 8048, 8049, 8050, 8051, 8052, 8053, 8054, 8055, 8056, 8057, 8058, 8059, 8060, 8061, 8062, 8063, 8064, 8065, 8066, 8067, 8068, 8069, 8070, 8071, 8072, 8073, 8074, 8075, 8076, 8077, 8078, 8079, 8080, 8081, 8082, 8083, 8084, 8085, 8086, 8087, 8088, 8089, 8090, 8091, 8092, 8093, 8094, 8095, 8096, 8097, 8098, 8099, 8100, 8101, 8102, 8103, 8104, 8105, 8106, 8107, 8108, 8109, 8110, 8111, 8112, 8113, 8114, 8115, 8116, 8117, 8118, 8119, 8120, 8121, 8122, 8123, 8124, 8125, 8126, 8127, 8128, 8129, 8130, 8131, 8132, 8133, 8134, 8135, 8136, 8137, 8138, 8139, 8140, 8141, 8142, 8143, 8144, 8145, 8146, 8147, 8148, 8149, 8150, 8151, 8152, 8153, 8154, 8155, 8156, 8157, 8158, 8159, 8160, 8161, 8162, 8163, 8164, 8165, 8166, 8167, 8168, 8169, 8170, 8171, 8172, 8173, 8174, 8175, 8176, 8177, 8178, 8179, 8180, 8181, 8182, 8183, 8184, 8185, 8186, 8187, 8188, 8189, 8190, 8191, 8192, 8193, 8194, 8195, 8196, 8197, 8198, 8199, 8200, 8201, 8202, 8203, 8204, 8205, 8206, 8207, 8208, 8209, 8210, 8211, 8212, 8213, 8214, 8215, 8216, 8217, 8218, 8219, 8220, 8221, 8222, 8223, 8224, 8225, 8226, 8227, 8228, 8229, 8230, 8231, 8232, 8233, 8234, 8235, 8236, 8237, 8238, 8239, 8240, 8241, 8242, 8243, 8244, 8245, 8246, 8247, 8248, 8249, 8250, 8251, 8252, 8253, 8254, 8255, 8256, 8257, 8258, 8259, 8260, 8261, 8262, 8263, 8264, 8265, 8266, 8267, 8268, 8269, 8270, 8271, 8272, 8273, 8274, 8275, 8276, 8277, 8278, 8279, 8280, 8281, 8282, 8283, 8284, 8285, 8286, 8287, 8288, 8289, 8290, 8291, 8292, 8293, 8294, 8295, 8296, 8297, 8298, 8299, 8300, 8301, 8302, 8303, 8304, 8305, 8306, 8307, 8308, 8309, 8310, 8311, 8312, 8313, 8314, 8315, 8316, 8317, 8318, 8319, 8320, 8321, 8322, 8323, 8324, 8325, 8326, 8327, 8328, 8329, 8330, 8331, 8332, 8333, 8334, 8335, 8336, 8337, 8338, 8339, 8340, 8341, 8342, 8343, 8344, 8345, 8346, 8347, 8348, 8349, 8350, 8351, 8352, 8353, 8354, 8355, 8356, 8357, 8358, 8359, 8360, 8361, 8362, 8363, 8364, 8365, 8366, 8367, 8368, 8369, 8370, 8371, 8372, 8373, 8374, 8375, 8376, 8377, 8378, 8379, 8380, 8381, 8382, 8383, 8384, 8385, 8386, 8387, 8388, 8389, 8390, 8391, 8392, 8393, 8394, 8395, 8396, 8397, 8398, 8399, 8400, 8401, 8402, 8403, 8404, 8405, 8406, 8407, 8408, 8409, 8410, 8411, 8412, 8413, 8414, 8415, 8416, 8417, 8418, 8419, 8420, 8421, 8422, 8423, 8424, 8425, 8426, 8427, 8428, 8429, 8430, 8431, 8432, 8433, 8434, 8435, 8436, 8437, 8438, 8439, 8440, 8441, 8442, 8443, 8444, 8445, 8446, 8447, 8448, 8449, 8450, 8451, 8452, 8453, 8454, 8455, 8456, 8457, 8458, 8459, 8460, 8461, 8462, 8463, 8464, 8465, 8466, 8467, 8468, 8469, 8470, 8471, 8472, 8473, 8474, 8475, 8476, 8477, 8478, 8479, 8480, 8481, 8482, 8483, 8484, 8485, 8486, 8487, 8488, 8489, 8490, 8491, 8492, 8493, 8494, 8495, 8496, 8497, 8498, 8499, 8500, 8501, 8502, 8503, 8504, 8505, 8506, 8507, 8508, 8509, 8510, 8511, 8512, 8513, 8514, 8515, 8516, 8517, 8518, 8519, 8520, 8521, 8522, 8523, 8524, 8525, 8526, 8527, 8528, 8529, 8530, 8531, 8532, 8533, 8534, 8535, 8536, 8537, 8538, 8539, 8540, 8541, 8542, 8543, 8544, 8545, 8546, 8547, 8548, 8549, 8550, 8551, 8552, 8553, 8554, 8555, 8556, 8557, 8558, 8559, 8560, 8561, 8562, 8563, 8564, 8565, 8566, 8567, 8568, 8569, 8570, 8571, 8572, 8573, 8574, 8575, 8576, 8577, 8578, 8579, 8580, 8581, 8582, 8583, 8584, 8585, 8586, 8587, 8588, 8589, 8590, 8591, 8592, 8593, 8594, 8595, 8596, 8597, 8598, 8599, 8600, 8601, 8602, 8603, 8604, 8605, 8606, 8607, 8608, 8609, 8610, 8611, 8612, 8613, 8614, 8615, 8616, 8617, 8618, 8619, 8620, 8621, 8622, 8623, 8624, 8625, 8626, 8627, 8628, 8629, 8630, 8631, 8632, 8633, 8634, 8635, 8636, 8637, 8638, 8639, 8640, 8641, 8642, 8643, 8644, 8645, 8646, 8647, 8648, 8649, 8650, 8651, 8652, 8653, 8654, 8655, 8656, 8657, 8658, 8659, 8660, 8661, 8662, 8663, 8664, 8665, 8666, 8667, 8668, 8669, 8670, 8671, 8672, 8673, 8674, 8675, 8676, 8677, 8678, 8679, 8680, 8681, 8682, 8683, 8684, 8685, 8686, 8687, 8688, 8689, 8690, 8691, 8692, 8693, 8694, 8695, 8696, 8697, 8698, 8699, 8700, 8701, 8702, 8703, 8704, 8705, 8706, 8707, 8708, 8709, 8710, 8711, 8712, 8713, 8714, 8715, 8716, 8717, 8718, 8719, 8720, 8721, 8722, 8723, 8724, 8725, 8726, 8727, 8728, 8729, 8730, 8731, 8732, 8733, 8734, 8735, 8736, 8737, 8738, 8739, 8740, 8741, 8742, 8743, 8744, 8745, 8746, 8747, 8748, 8749, 8750, 8751, 8752, 8753, 8754, 8755, 8756, 8757, 8758, 8759, 8760, 8761, 8762, 8763, 8764, 8765, 8766, 8767, 8768, 8769, 8770, 8771, 8772, 8773, 8774, 8775, 8776, 8777, 8778, 8779, 8780, 8781, 8782, 8783, 8784, 8785, 8786, 8787, 8788, 8789, 8790, 8791, 8792, 8793, 8794, 8795, 8796, 8797, 8798, 8799, 8800, 8801, 8802, 8803, 8804, 8805, 8806, 8807, 8808, 8809, 8810, 8811, 8812, 8813, 8814, 8815, 8816, 8817, 8818, 8819, 8820, 8821, 8822, 8823, 8824, 8825, 8826, 8827, 8828, 8829, 8830, 8831, 8832, 8833, 8834, 8835, 8836, 8837, 8838, 8839, 8840, 8841, 8842, 8843, 8844, 8845, 8846, 8847, 8848, 8849, 8850, 8851, 8852, 8853, 8854, 8855, 8856, 8857, 8858, 8859, 8860, 8861, 8862, 8863, 8864, 8865, 8866, 8867, 8868, 8869, 8870, 8871, 8872, 8873, 8874, 8875, 8876, 8877, 8878, 8879, 8880, 8881, 8882, 8883, 8884, 8885, 8886, 8887, 8888, 8889, 8890, 8891, 8892, 8893, 8894, 8895, 8896, 8897, 8898, 8899, 8900, 8901, 8902, 8903, 8904, 8905, 8906, 8907, 8908, 8909, 8910, 8911, 8912, 8913, 8914, 8915, 8916, 8917, 8918, 8919, 8920, 8921, 8922, 8923, 8924, 8925, 8926, 8927, 8928, 8929, 8930, 8931, 8932, 8933, 8934, 8935, 8936, 8937, 8938, 8939, 8940, 8941, 8942, 8943, 8944, 8945, 8946, 8947, 8948, 8949, 8950, 8951, 8952, 8953, 8954, 8955, 8956, 8957, 8958, 8959, 8960, 8961, 8962, 8963, 8964, 8965, 8966, 8967, 8968, 8969, 8970, 8971, 8972, 8973, 8974, 8975, 8976, 8977, 8978, 8979, 8980, 8981, 8982, 8983, 8984, 8985, 8986, 8987, 8988, 8989, 8990, 8991, 8992, 8993, 8994, 8995, 8996, 8997, 8998, 8999, 9000, 9001, 9002, 9003, 9004, 9005, 9006, 9007, 9008, 9009, 9010, 9011, 9012, 9013, 9014, 9015, 9016, 9017, 9018, 9019, 9020, 9021, 9022, 9023, 9024, 9025, 9026, 9027, 9028, 9029, 9030, 9031, 9032, 9033, 9034, 9035, 9036, 9037, 9038, 9039, 9040, 9041, 9042, 9043, 9044, 9045, 9046, 9047, 9048, 9049, 9050, 9051, 9052, 9053, 9054, 9055, 9056, 9057, 9058, 9059, 9060, 9061, 9062, 9063, 9064, 9065, 9066, 9067, 9068, 9069, 9070, 9071, 9072, 9073, 9074, 9075, 9076, 9077, 9078, 9079, 9080, 9081, 9082, 9083, 9084, 9085, 9086, 9087, 9088, 9089, 9090, 9091, 9092, 9093, 9094, 9095, 9096, 9097, 9098, 9099, 9100, 9101, 9102, 9103, 9104, 9105, 9106, 9107, 9108, 9109, 9110, 9111, 9112, 9113, 9114, 9115, 9116, 9117, 9118, 9119, 9120, 9121, 9122, 9123, 9124, 9125, 9126, 9127, 9128, 9129, 9130, 9131, 9132, 9133, 9134, 9135, 9136, 9137, 9138, 9139, 9140, 9141, 9142, 9143, 9144, 9145, 9146, 9147, 9148, 9149, 9150, 9151, 9152, 9153, 9154, 9155, 9156, 9157, 9158, 9159, 9160, 9161, 9162, 9163, 9164, 9165, 9166, 9167, 9168, 9169, 9170, 9171, 9172, 9173, 9174, 9175, 9176, 9177, 9178, 9179, 9180, 9181, 9182, 9183, 9184, 9185, 9186, 9187, 9188, 9189, 9190, 9191, 9192, 9193, 9194, 9195, 9196, 9197, 9198, 9199, 9200, 9201, 9202, 9203, 9204, 9205, 9206, 9207, 9208, 9209, 9210, 9211, 9212, 9213, 9214, 9215, 9216, 9217, 9218, 9219, 9220, 9221, 9222, 9223, 9224, 9225, 9226, 9227, 9228, 9229, 9230, 9231, 9232, 9233, 9234, 9235, 9236, 9237, 9238, 9239, 9240, 9241, 9242, 9243, 9244, 9245, 9246, 9247, 9248, 9249, 9250, 9251, 9252, 9253, 9254, 9255, 9256, 9257, 9258, 9259, 9260, 9261, 9262, 9263, 9264, 9265, 9266, 9267, 9268, 9269, 9270, 9271, 9272, 9273, 9274, 9275, 9276, 9277, 9278, 9279, 9280, 9281, 9282, 9283, 9284, 9285, 9286, 9287, 9288, 9289, 9290, 9291, 9292, 9293, 9294, 9295, 9296, 9297, 9298, 9299, 9300, 9301, 9302, 9303, 9304, 9305, 9306, 9307, 9308, 9309, 9310, 9311, 9312, 9313, 9314, 9315, 9316, 9317, 9318, 9319, 9320, 9321, 9322, 9323, 9324, 9325, 9326, 9327, 9328, 9329, 9330, 9331, 9332, 9333, 9334, 9335, 9336, 9337, 9338, 9339, 9340, 9341, 9342, 9343, 9344, 9345, 9346, 9347, 9348, 9349, 9350, 9351, 9352, 9353, 9354, 9355, 9356, 9357, 9358, 9359, 9360, 9361, 9362, 9363, 9364, 9365, 9366, 9367, 9368, 9369, 9370, 9371, 9372, 9373, 9374, 9375, 9376, 9377, 9378, 9379, 9380, 9381, 9382, 9383, 9384, 9385, 9386, 9387, 9388, 9389, 9390, 9391, 9392, 9393, 9394, 9395, 9396, 9397, 9398, 9399, 9400, 9401, 9402, 9403, 9404, 9405, 9406, 9407, 9408, 9409, 9410, 9411, 9412, 9413, 9414, 9415, 9416, 9417, 9418, 9419, 9420, 9421, 9422, 9423, 9424, 9425, 9426, 9427, 9428, 9429, 9430, 9431, 9432, 9433, 9434, 9435, 9436, 9437, 9438, 9439, 9440, 9441, 9442, 9443, 9444, 9445, 9446, 9447, 9448, 9449, 9450, 9451, 9452, 9453, 9454, 9455, 9456, 9457, 9458, 9459, 9460, 9461, 9462, 9463, 9464, 9465, 9466, 9467, 9468, 9469, 9470, 9471, 9472, 9473, 9474, 9475, 9476, 9477, 9478, 9479, 9480, 9481, 9482, 9483, 9484, 9485, 9486, 9487, 9488, 9489, 9490, 9491, 9492, 9493, 9494, 9495, 9496, 9497, 9498, 9499, 9500, 9501, 9502, 9503, 9504, 9505, 9506, 9507, 9508, 9509, 9510, 9511, 9512, 9513, 9514, 9515, 9516, 9517, 9518, 9519, 9520, 9521, 9522, 9523, 9524, 9525, 9526, 9527, 9528, 9529, 9530, 9531, 9532, 9533, 9534, 9535, 9536, 9537, 9538, 9539, 9540, 9541, 9542, 9543, 9544, 9545, 9546, 9547, 9548, 9549, 9550, 9551, 9552, 9553, 9554, 9555, 9556, 9557, 9558, 9559, 9560, 9561, 9562, 9563, 9564, 9565, 9566, 9567, 9568, 9569, 9570, 9571, 9572, 9573, 9574, 9575, 9576, 9577, 9578, 9579, 9580, 9581, 9582, 9583, 9584, 9585, 9586, 9587, 9588, 9589, 9590, 9591, 9592, 9593, 9594, 9595, 9596, 9597, 9598, 9599, 9600, 9601, 9602, 9603, 9604, 9605, 9606, 9607, 9608, 9609, 9610, 9611, 9612, 9613, 9614, 9615, 9616, 9617, 9618, 9619, 9620, 9621, 9622, 9623, 9624, 9625, 9626, 9627, 9628, 9629, 9630, 9631, 9632, 9633, 9634, 9635, 9636, 9637, 9638, 9639, 9640, 9641, 9642, 9643, 9644, 9645, 9646, 9647, 9648, 9649, 9650, 9651, 9652, 9653, 9654, 9655, 9656, 9657, 9658, 9659, 9660, 9661, 9662, 9663, 9664, 9665, 9666, 9667, 9668, 9669, 9670, 9671, 9672, 9673, 9674, 9675, 9676, 9677, 9678, 9679, 9680, 9681, 9682, 9683, 9684, 9685, 9686, 9687, 9688, 9689, 9690, 9691, 9692, 9693, 9694, 9695, 9696, 9697, 9698, 9699, 9700, 9701, 9702, 9703, 9704, 9705, 9706, 9707, 9708, 9709, 9710, 9711, 9712, 9713, 9714, 9715, 9716, 9717, 9718, 9719, 9720, 9721, 9722, 9723, 9724, 9725, 9726, 9727, 9728, 9729, 9730, 9731, 9732, 9733, 9734, 9735, 9736, 9737, 9738, 9739, 9740, 9741, 9742, 9743, 9744, 9745, 9746, 9747, 9748, 9749, 9750, 9751, 9752, 9753, 9754, 9755, 9756, 9757, 9758, 9759, 9760, 9761, 9762, 9763, 9764, 9765, 9766, 9767, 9768, 9769, 9770, 9771, 9772, 9773, 9774, 9775, 9776, 9777, 9778, 9779, 9780, 9781, 9782, 9783, 9784, 9785, 9786, 9787, 9788, 9789]
var branch := ""

func run() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--output="): output=arg.trim_prefix("--output=")
		elif arg.begins_with("--mode="): mode=arg.trim_prefix("--mode=")
		elif arg=="--preflight": preflight=true
		else: finish("Unknown argument "+arg); return
	expected=2
	if mode!="groom-stills": finish("Use --mode=groom-stills"); return
	if not output.is_absolute_path() or DirAccess.dir_exists_absolute(output): finish("Fresh absolute output required"); return
	DirAccess.make_dir_recursive_absolute(output)
	branch=OS.get_environment("YUGA_SASH_REVIEW")
	if not SOURCE_PINS.has(branch): finish("Explicit YUGA_SASH_REVIEW=baseline/candidate required"); return
	for index in RAW_PATHS.size():
		if FileAccess.get_sha256(RAW_PATHS[index])!=SOURCE_PINS[branch][index]: finish("Unexpected raw hero "+RAW_PATHS[index]); return
	if FileAccess.get_sha256("res://scripts/rama_motion.gd")!=REQUIRED_MOTION or FileAccess.get_sha256("res://scripts/rama_surface_finish.gd")!=REQUIRED_FINISH:
		finish("Motion/finish source differs from reviewed component inputs"); return
	if not preflight and (DisplayServer.get_name()!="X11" or RenderingServer.get_current_rendering_method()!="forward_plus"):
		finish("X11 Forward+ required"); return
	seed(741031); root.size=SIZE; root.content_scale_size=SIZE; root.msaa_3d=Viewport.MSAA_2X
	if not preflight: root.show()
	sources=source_hashes()
	contract={"stills":[
		{"id":"rest-front","player_position_m":[19,.4400999976158142,-15],"visual_yaw_degrees":-90,"camera_position_m":[17.2,1.8000999976158143,-15],"look_at_m":[19,1.8000999976158143,-15],"fov_degrees":38,"near_m":.05,"night":false,"required_bounds":"sash"}]}
	scene=load("res://scenes/courtyard.tscn").instantiate(); root.add_child(scene); current_scene=scene
	await draw(6); player=scene.player
	if not player.model_ready or not scene.environment_ready: finish("Actual hero/world missing"); return
	for forbidden in ["FourTaperedTempleWisps","SevenSweptUpperHairLayers","OptionalArrowFletching"]:
		if player.visual.find_child(forbidden,true,false)!=null: finish("Unreviewed optional helper present: "+forbidden); return
	review_camera=Camera3D.new(); scene.add_child(review_camera); review_camera.near=.05; review_camera.far=180
	player.rama_motion.modification_processed.connect(observe_final_pose)
	scene.start_training(); scene.title_light.hide(); await draw(8)
	paused=true; Input.mouse_mode=Input.MOUSE_MODE_VISIBLE
	scene.ui.hide(); freeze_background_time(); set_light(false); cache_geometry()
	sequence_controls.append({"kind":"sash_source_comparison","branch":branch,"default_activation":false,"added_geometry":false,"optional_helpers":false,"rest_contract":contract})
	await groom_stills()
	if not done: await actual_cast_view()
	if not done: finish("")

func actual_cast_view() -> void:
	paused=false
	scene.reset_training(); scene.start_training(); scene.ui.hide(); scene.title_light.hide()
	for action in ["move_left","move_right","move_forward","move_back","fire"]: Input.action_release(action)
	player.global_position=Vector3(-.65,.0001,0); player.velocity=Vector3.ZERO
	player.yaw=0; player.pitch=0; player._update_camera(); player.visual.rotation.y=PI
	player.reset_physics_interpolation(); player.visual.reset_physics_interpolation()
	set_light(false); player.camera.make_current(); await draw(8)
	if not player.is_on_floor(): finish("Actor lacks actual floor contact"); return
	var origin: Vector3=player.camera.project_ray_origin(Vector2(SIZE)*.5)
	var direction: Vector3=player.camera.project_ray_normal(Vector2(SIZE)*.5)
	var hit: Dictionary=scene.get_world_3d().direct_space_state.intersect_ray(PhysicsRayQueryParameters3D.create(origin,origin+direction*80,1|4,[player.get_rid()]))
	if hit.is_empty() or String(hit.collider.name)!="Target03": finish("Actual player aim misses Target03"); return
	scene.rama_runtime.combat_event.connect(record_event)
	var cast: Dictionary=scene.rama_runtime.cast_ability("piercing_dawn")
	if not cast.get("accepted",false): finish("Actual Piercing Dawn refused"); return
	var begin_time: float=scene.rama_runtime.kit.elapsed
	var age:=0.0; var frames:=0
	while age+.000001<.30 and frames<30:
		await draw(1); frames+=1; age=scene.rama_runtime.kit.elapsed-begin_time
	paused=true
	if age>.325 or player.rama_motion.action_stage!="windup" or not player.rama_motion.nocked_arrow.visible:
		finish("Required live nocked windup missing"); return
	var rig: Skeleton3D=player.rama_motion.rig
	var head: int=rig.find_bone("head")
	if head!=104 or posed_globals.size()!=164: finish("Final imported head pose missing"); return
	var center: Vector3=rig.global_transform*posed_globals[head].origin-Vector3.UP*.32
	var offset:=Basis(Vector3.UP,player.visual.global_rotation.y-PI)*Vector3(-1.20,.12,-1.275)
	review_camera.global_position=center+offset; review_camera.look_at(center); review_camera.fov=38
	review_camera.make_current(); review_camera.reset_physics_interpolation()
	player.rama_lod.reset("Sash UV actual cast review"); player.rama_lod.update(review_camera,1.0/30)
	await draw(4)
	sequence_controls.append({"kind":"real_public_cast","cast":normal(cast),"authority_age_s":age,"advanced_render_frames":frames,"aim_hit":normal(hit.position),"collider":String(hit.collider.name),"captured_motion_stage":player.rama_motion.action_stage})
	groom_frame("cast-three-quarter","sash")

func groom_frame(id: String, required: String) -> void:
	super.groom_frame(id,required)
	if done: return
	shots[-1]["sash_branch"]=branch
	shots[-1]["rendered_pose_globals"]=normal(posed_globals)
	shots[-1]["rendered_pose_pin"]=JSON.stringify(normal(posed_globals),"",true,true).sha256_text()
	shots[-1]["scope"]="Sash UV source comparison. Rest is staged; cast uses actual public ability and final modifier pose. Exact selected imported sash vertex projection proves framing only, not visibility, collision or general motion acceptance."

func source_hashes() -> Dictionary:
	var result:=super.source_hashes()
	result.erase("res://tools/visual-rounds/groom_contract.json")
	var helper_path: String=get_script().resource_path
	result[helper_path]=FileAccess.get_sha256(helper_path)
	return result

func imported_bounds(camera: Camera3D, required: String) -> Dictionary:
	var low := Vector2(INF,INF); var high := Vector2(-INF,-INF)
	var head_low := low; var head_high := high
	var count := 0; var head_count := 0; var behind := 0
	var admitted := {}
	for index in SASH_VERTEX_IDS: admitted[index]=true
	var rig: Skeleton3D = player.rama_motion.rig
	if posed_globals.size() != rig.get_bone_count(): return {"passed":false,"failure":"No completed SkeletonModifier3D pose snapshot"}
	for part in geometry:
		var node: MeshInstance3D = part.node
		if not is_instance_valid(node) or not node.is_visible_in_tree(): continue
		if node.name != "RamaHero" or not "Cobalt handwoven silk" in part.name: continue
		var vertices: PackedVector3Array = part.vertices
		var slots: int = part.bones.size()/vertices.size() if part.bones != null and not part.binds.is_empty() else 0
		var transforms: Array[Transform3D] = []
		for bind in part.binds: transforms.append(posed_globals[bind.bone] * bind.inverse)
		var secondary := Vector3.ZERO
		if part.material is ShaderMaterial:
			var value: Variant = part.material.get_shader_parameter("secondary_offset")
			if value is Vector3: secondary = value
		for index in vertices.size():
			if not admitted.has(index): continue
			var rest: Vector3 = vertices[index]
			var is_head: bool = "Swept black hair" in part.name or "RamaFace" in String(node.name) or ("Rama warm skin" in part.name and rest.y>=1.50 and absf(rest.x)<=.18) or "Natural lips" in part.name
			if required == "head" and not is_head: continue
			var point := rest
			for shape in part.shapes.size():
				var delta: Vector3 = part.shapes[shape][Mesh.ARRAY_VERTEX][index]
				if part.shape_mode == Mesh.BLEND_SHAPE_MODE_NORMALIZED: delta -= rest
				point += delta * node.get_blend_shape_value(shape)
			var posed := point
			if slots>0:
				posed = Vector3.ZERO
				for slot in slots: posed += (transforms[part.bones[index*slots+slot]] * point) * part.weights[index*slots+slot]
			var mask: float = clampf(part.colors[index].a,0,1) if part.colors != null else 0.0
			posed += secondary * mask * mask
			var world: Vector3 = (rig.global_transform if slots>0 else node.global_transform) * posed
			var screen: Vector2 = camera.unproject_position(world)
			low = low.min(screen); high = high.max(screen); count += 1
			if is_head: head_low = head_low.min(screen); head_high = head_high.max(screen); head_count += 1
			if camera.is_position_behind(world): behind += 1
	return {"passed":count==SASH_VERTEX_IDS.size() and behind==0 and low.x>=24 and low.y>=24 and high.x<=SIZE.x-24 and high.y<=SIZE.y-24,"required":required,"min":normal(low),"max":normal(high),"head_min":normal(head_low) if head_count>0 else null,"head_max":normal(head_high) if head_count>0 else null,"vertices":count,"head_vertices":head_count,"behind":behind,"margin_pixels":24,"pose_signal_count":pose_signal_count,"pose_signal_physics_frame":last_pose_signal,"scope":"Exact2074 source-mapped imported sash vertices, final modifier pose snapshot, inverse binds, live morphs and actual alpha-squared shader offsets. Projection does not prove visibility or collision clearance."}


func finish(failure: String) -> void:
	if done: return
	done = true
	var after := source_hashes() if not sources.is_empty() else {}
	var report: Dictionary
	if preflight:
		report = {"complete":failure.is_empty() and shots.size()==expected and sources==after,"failure":failure,"shots":shots,"expected":expected,"events":events,"controls":sequence_controls,"source_sha256":sources,"source_after_sha256":after,"source_unchanged":sources==after,"scope":"Headless real-input and final-modifier-pose projection preflight. No framebuffer or rendered art claim."}
	else:
		report = {"schema":1,"kind":"actual-native-visual-rounds","camera_contract":"sash-front-cast-v1","mode":mode,"context":context,"complete":failure.is_empty() and sources==after and shots.size()==expected,"failure":failure,"source_sha256":sources,"source_after_sha256":after,"source_unchanged":sources==after,"shots":shots,"ability_events":events,"sequence_controls":sequence_controls,"expected_raw_pngs":expected,"time_controls":time_controls,"clocks":{"fixed_capture_process_hz":30,"physics_hz":Engine.physics_ticks_per_second,"army_authority_hz":20,"hardware_fps_measured":false},"renderer":RenderingServer.get_current_rendering_method(),"adapter":RenderingServer.get_video_adapter_name(),"godot":Engine.get_version_info(),"wall_elapsed_ms":Time.get_ticks_msec()-started,"scope":"Original Forward+ matched front and actual public cast framebuffers. Fixed30Hz capture is simulation sampling, not hardware FPS. No full gameplay/continuous motion acceptance."}
	# After the last observation only. Dummy audio releases on its real mixer,
	# so a few fast headless process frames do not establish completed cleanup.
	paused = false
	if is_instance_valid(scene):
		for node in scene.find_children("*", "AudioStreamPlayer", true, false): node.stop(); node.stream = null
		scene.queue_free()
	for unused in 8: await process_frame
	var cleanup_started := Time.get_ticks_usec()
	var previous := AudioServer.get_time_since_last_mix()
	var observed := 0
	var samples: Array[Dictionary] = []
	while observed < 2 and Time.get_ticks_usec()-cleanup_started < 250000:
		OS.delay_msec(1)
		var now := AudioServer.get_time_since_last_mix()
		if now+.0002 < previous: observed += 1
		samples.append({"wall_usec":Time.get_ticks_usec()-cleanup_started,"since_mix_s":now,"ticks":observed})
		previous = now
	var wait_usec := Time.get_ticks_usec()-cleanup_started
	for unused in 8: await process_frame
	report.audio_cleanup = {"scope":"Capture shutdown after all shots and scene free; no runtime audio change.","observed_mixer_ticks":observed,"wait_usec":wait_usec,"budget_usec":250000,"samples":samples,"main_cleanup_frames":8}
	report.complete = report.complete and observed == 2 and wait_usec <= 250000
	if output.is_absolute_path() and DirAccess.dir_exists_absolute(output): FileAccess.open(output.path_join("preflight.json" if preflight else "capture.json"),FileAccess.WRITE).store_string(JSON.stringify(report,"  ",true,true)+"\n")
	print("SASH_CAPTURE_COMPLETE ",report.complete," ",failure)
	quit(0 if report.complete else 1)

// Configure the node with one stereo output. An independent Wasm instance keeps
// the audio thread free of match state and main-thread scheduling.
class YugaLimiter extends AudioWorkletProcessor {
  constructor(options) {
    super();
    const { module } = options.processorOptions;
    this.wasm = new WebAssembly.Instance(module, {}).exports;
    this.capacity = this.wasm.mix_init(Math.round(sampleRate));
    if (!this.capacity) throw new Error('Unsupported limiter sample rate');
    this.leftPtr = this.wasm.mix_left_ptr();
    this.rightPtr = this.wasm.mix_right_ptr();
    this.blockLength = 0;
    this.port.postMessage({ type: 'ready', sampleRate, latencyFrames: this.wasm.mix_delay_frames() });
  }

  process(inputs, outputs) {
    const input = inputs[0];
    const out = outputs[0];
    if (!out?.length) return true;
    const total = out[0].length;
    for (let start = 0; start < total; start += this.capacity) {
      const size = Math.min(this.capacity, total - start);
      const memory = this.wasm.memory.buffer;
      if (size !== this.blockLength || this.leftView.buffer !== memory) {
        this.leftView = new Float32Array(memory, this.leftPtr, size);
        this.rightView = new Float32Array(memory, this.rightPtr, size);
        this.blockLength = size;
      }
      const l = input?.[0], r = input?.[1] ?? l;
      if (l) {
        this.leftView.set(l.length === size ? l : l.subarray(start, start + size));
        this.rightView.set(r.length === size ? r : r.subarray(start, start + size));
      } else {
        this.leftView.fill(0);
        this.rightView.fill(0);
      }
      this.wasm.mix_process(size);
      out[0].set(this.leftView, start);
      if (out.length > 1) out[1].set(this.rightView, start);
    }
    return true;
  }
}

registerProcessor('yuga-limiter', YugaLimiter);

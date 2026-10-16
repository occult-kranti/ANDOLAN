/** Original synthesised ambience: no recordings or third-party music. */
export class GameAudio {
  private context?: AudioContext;
  private master?: GainNode;
  private engine?: OscillatorNode;
  private engineGain?: GainNode;
  muted = true;
  async toggle() {
    if (!this.context) {
      this.context = new AudioContext();
      this.master = this.context.createGain(); this.master.gain.value = 0;
      this.master.connect(this.context.destination);
      this.engine = this.context.createOscillator(); this.engine.type = 'triangle';
      this.engineGain = this.context.createGain(); this.engineGain.gain.value = 0;
      this.engine.connect(this.engineGain); this.engineGain.connect(this.master); this.engine.start();
      const buffer = this.context.createBuffer(1, this.context.sampleRate * 3, this.context.sampleRate);
      const data = buffer.getChannelData(0);
      let last = 0;
      for (let i = 0; i < data.length; i++) { last = (last + (Math.random() * 2 - 1) * .02) / 1.02; data[i] = last * 3; }
      const rain = this.context.createBufferSource(); rain.buffer = buffer; rain.loop = true;
      const rainGain = this.context.createGain(); rainGain.gain.value = .08;
      rain.connect(rainGain); rainGain.connect(this.master); rain.start();
    }
    await this.context.resume(); this.muted = !this.muted;
    this.master!.gain.setTargetAtTime(this.muted ? 0 : .35, this.context.currentTime, .15);
    return this.muted;
  }
  update(speed: number, driving: boolean) {
    if (!this.context || !this.engine || !this.engineGain) return;
    this.engine.frequency.setTargetAtTime(43 + Math.abs(speed) * 3, this.context.currentTime, .1);
    this.engineGain.gain.setTargetAtTime(driving ? .1 : 0, this.context.currentTime, .1);
  }
}

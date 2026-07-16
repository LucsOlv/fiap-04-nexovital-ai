// Encoda um AudioBuffer em WAV PCM 16-bit mono.
// O worker lê áudio só como WAV (scipy.io.wavfile); MediaRecorder grava WebM/Opus,
// então convertemos no browser via AudioContext antes de enviar.

export function encodeWav(buffer: AudioBuffer): Blob {
  const sampleRate = buffer.sampleRate;
  const samples = mixToMono(buffer);
  const dataBytes = samples.length * 2; // 16-bit
  const view = new DataView(new ArrayBuffer(44 + dataBytes));

  writeString(view, 0, "RIFF");
  view.setUint32(4, 36 + dataBytes, true);
  writeString(view, 8, "WAVE");
  writeString(view, 12, "fmt ");
  view.setUint32(16, 16, true); // tamanho do bloco fmt
  view.setUint16(20, 1, true); // PCM
  view.setUint16(22, 1, true); // mono
  view.setUint32(24, sampleRate, true);
  view.setUint32(28, sampleRate * 2, true); // byte rate = sampleRate * canais * bytes/amostra
  view.setUint16(32, 2, true); // block align = canais * bytes/amostra
  view.setUint16(34, 16, true); // bits por amostra
  writeString(view, 36, "data");
  view.setUint32(40, dataBytes, true);

  let offset = 44;
  for (let i = 0; i < samples.length; i += 1) {
    const clamped = Math.max(-1, Math.min(1, samples[i]));
    view.setInt16(offset, clamped < 0 ? clamped * 0x8000 : clamped * 0x7fff, true);
    offset += 2;
  }

  return new Blob([view], { type: "audio/wav" });
}

function mixToMono(buffer: AudioBuffer): Float32Array {
  const channels = buffer.numberOfChannels;
  if (channels === 1) return buffer.getChannelData(0);
  const length = buffer.length;
  const out = new Float32Array(length);
  for (let c = 0; c < channels; c += 1) {
    const data = buffer.getChannelData(c);
    for (let i = 0; i < length; i += 1) out[i] += data[i] / channels;
  }
  return out;
}

function writeString(view: DataView, offset: number, text: string): void {
  for (let i = 0; i < text.length; i += 1) view.setUint8(offset + i, text.charCodeAt(i));
}

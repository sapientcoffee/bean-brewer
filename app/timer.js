/**
 * Brew Timer State Machine
 */

export class BrewTimer {
  constructor({ totalSeconds = 180, onTick = () => {}, onComplete = () => {} } = {}) {
    this.totalSeconds = totalSeconds;
    this.remainingSeconds = totalSeconds;
    this.status = "idle"; // idle | running | paused | completed
    this.timerId = null;
    this.onTick = onTick;
    this.onComplete = onComplete;
  }

  start() {
    if (this.status === "running") return;
    this.status = "running";
    this.timerId = setInterval(() => {
      if (this.remainingSeconds > 0) {
        this.remainingSeconds -= 1;
        this.onTick({
          status: this.status,
          remainingSeconds: this.remainingSeconds,
          phase: this.getPhase(),
          progressPercent: Math.round(((this.totalSeconds - this.remainingSeconds) / this.totalSeconds) * 100)
        });
      } else {
        this.complete();
      }
    }, 1000);
  }

  pause() {
    if (this.status !== "running") return;
    clearInterval(this.timerId);
    this.timerId = null;
    this.status = "paused";
    this.onTick({
      status: this.status,
      remainingSeconds: this.remainingSeconds,
      phase: this.getPhase(),
      progressPercent: Math.round(((this.totalSeconds - this.remainingSeconds) / this.totalSeconds) * 100)
    });
  }

  reset(newTotalSeconds) {
    clearInterval(this.timerId);
    this.timerId = null;
    if (typeof newTotalSeconds === "number") {
      this.totalSeconds = newTotalSeconds;
    }
    this.remainingSeconds = this.totalSeconds;
    this.status = "idle";
    this.onTick({
      status: this.status,
      remainingSeconds: this.remainingSeconds,
      phase: this.getPhase(),
      progressPercent: 0
    });
  }

  complete() {
    clearInterval(this.timerId);
    this.timerId = null;
    this.status = "completed";
    this.onComplete();
  }

  getPhase() {
    const elapsed = this.totalSeconds - this.remainingSeconds;
    if (elapsed < 45) return "Bloom Phase (CO2 Release)";
    if (elapsed < (this.totalSeconds * 0.75)) return "Main Extraction Pour";
    return "Drawdown & Settling";
  }

  formatTime(seconds) {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${String(mins).padStart(2, "0")}:${String(secs).padStart(2, "0")}`;
  }
}
